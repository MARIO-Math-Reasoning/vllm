import random
import torch

from vllm.config import ModelConfig
from vllm.sequence import SamplingParams, SequenceData, SequenceGroupMetadata
from vllm.worker.model_runner import ModelRunner, _BATCH_SIZE_ALIGNMENT


def get_aligned_size(batch_size: int, alignment: int):
    return ((batch_size + alignment - 1) // alignment * alignment)


def test_prepare_prompt():
    model_runner = ModelRunner(None, None, None, None, None)
    model_runner.set_block_size(16)

    batch_size = random.randint(1, 256)
    prompt_lens = []
    seq_group_metadata_list = []
    block_tables = {0: [1]}
    for i in range(batch_size):
        # make sure all tokens fit into one block
        prompt_len = i % (model_runner.block_size - 1) + 1
        prompt_lens.append(prompt_len)
        seq_data = list(range(prompt_len))
        seq_group_metadata_list.append(
            SequenceGroupMetadata(
                request_id=f"test_{i}",
                is_prompt=True,
                seq_data={0: SequenceData(seq_data)},
                sampling_params=SamplingParams(temperature=0),
                block_tables=block_tables,
            ))

    expected_selected_token_indices = []
    selected_token_start_idx = 0
    for prompt_len in prompt_lens:
        expected_selected_token_indices.append(selected_token_start_idx +
                                               prompt_len - 1)
        selected_token_start_idx += prompt_len
    (input_tokens, input_positions, input_metadata, return_prompt_lens, _, _,
     _, _) = (model_runner._prepare_prompt(seq_group_metadata_list))
    assert return_prompt_lens == prompt_lens

    # Verify input metadata is correct for prompts.
    device = model_runner.device
    assert input_metadata.is_prompt is True
    assert torch.allclose(input_metadata.prompt_lens_tensor,
                          torch.tensor(prompt_lens, device=device))
    assert input_metadata.prompt_lens == prompt_lens
    assert input_metadata.num_prompt_tokens == sum(prompt_lens)
    assert input_metadata.num_generation_tokens == 0
    assert input_metadata.max_seq_len == max(prompt_lens)

    # Test subquery start locs.
    start_idx = 0
    start_loc = [start_idx]
    for prompt_len in prompt_lens:
        start_idx += prompt_len
        start_loc.append(start_idx)
    assert torch.allclose(
        input_metadata.subquery_start_loc,
        torch.tensor(start_loc, dtype=torch.int32, device=device))

    # Test seq start locs. Note that for normal prefill it is
    # equivalent to subquery_start_loc.
    start_idx = 0
    seq_start_loc = [start_idx]
    for prompt_len in prompt_lens:
        start_idx += prompt_len
        seq_start_loc.append(start_idx)

    assert torch.allclose(
        input_metadata.seq_start_loc,
        torch.tensor(start_loc, dtype=torch.int32, device=device))
    assert input_metadata.max_context_len is None
    assert torch.allclose(
        input_metadata.context_lens,
        torch.zeros(input_metadata.context_lens.shape[0],
                    dtype=torch.int,
                    device=device))

    expected = torch.tensor([[] for _ in range(len(seq_group_metadata_list))],
                            dtype=torch.int32,
                            device=model_runner.device)
    assert torch.allclose(input_metadata.block_tables, expected)
    # Cuda graph should not be used for prerill.
    assert input_metadata.use_cuda_graph is False
    assert input_metadata.kv_cache_dtype == "auto"

    assert input_tokens.shape == (sum(prompt_lens), )
    assert input_positions.shape == (sum(prompt_lens), )
    torch.testing.assert_close(input_tokens, input_positions)

    sampling_metadata = model_runner._prepare_sample(seq_group_metadata_list,
                                                     prompt_lens,
                                                     subquery_lens=prompt_lens)
    assert input_tokens.shape == (sum(prompt_lens), )
    assert input_positions.shape == (sum(prompt_lens), )
    actual = sampling_metadata.selected_token_indices
    expected = torch.tensor(expected_selected_token_indices,
                            device=actual.device,
                            dtype=actual.dtype)
    torch.testing.assert_close(actual, expected)
    torch.testing.assert_close(input_tokens, input_positions)

    actual = sampling_metadata.selected_token_indices
    expected = torch.tensor(expected_selected_token_indices,
                            device=actual.device,
                            dtype=actual.dtype)
    torch.testing.assert_close(actual, expected)


def test_prepare_decode_cuda_graph():
    model_config = ModelConfig(
        "facebook/opt-125m",
        "facebook/opt-125m",
        tokenizer_mode="auto",
        trust_remote_code=False,
        download_dir=None,
        load_format="dummy",
        seed=0,
        dtype="float16",
        revision=None,
        enforce_eager=False,
    )
    model_runner = ModelRunner(model_config, None, None, None, None)
    model_runner.set_block_size(16)

    batch_size = random.randint(1, 256)
    prompt_lens = []
    seq_group_metadata_list = []
    for i in range(batch_size):
        # make sure all tokens fit into one block
        prompt_len = i % (model_runner.block_size - 1) + 1
        prompt_lens.append(prompt_len)
        seq_data = list(range(prompt_len))
        seq_group_metadata_list.append(
            SequenceGroupMetadata(
                request_id=f"test_{i}",
                is_prompt=False,
                seq_data={0: SequenceData(seq_data)},
                sampling_params=SamplingParams(temperature=0),
                block_tables={0: [1]},
            ))

    input_tokens, input_positions, input_metadata, _, _, _ = (
        model_runner._prepare_decode(seq_group_metadata_list))

    # Verify input metadata is correct for prompts.
    device = model_runner.device
    assert input_metadata.is_prompt is False
    assert input_metadata.prompt_lens is None
    assert input_metadata.num_prompt_tokens == 0
    assert input_metadata.num_generation_tokens == (get_aligned_size(
        len(seq_group_metadata_list), _BATCH_SIZE_ALIGNMENT))
    assert input_metadata.max_seq_len is None
    assert input_metadata.subquery_start_loc is None
    assert input_metadata.seq_start_loc is None
    assert input_metadata.max_context_len == max(prompt_lens)
    assert torch.allclose(
        input_metadata.context_lens[:len(prompt_lens)],
        torch.tensor(prompt_lens, dtype=torch.int, device=device))

    # block table's first index corresponds to each batch, meaning in
    # decoding it is each token.
    assert input_metadata.block_tables.shape[0] == len(input_tokens)
    # Block table's second dim correspondsd to each token's block number.
    # It is padded up to
    assert input_metadata.block_tables.shape[1] == (
        model_runner.get_max_block_per_batch())
    # Cuda graph should not be used for prerill.
    assert input_metadata.use_cuda_graph is True
    assert input_metadata.kv_cache_dtype == "auto"

    assert input_tokens.shape == (get_aligned_size(
        len(seq_group_metadata_list), _BATCH_SIZE_ALIGNMENT), )
    assert input_positions.shape == (get_aligned_size(
        len(seq_group_metadata_list), _BATCH_SIZE_ALIGNMENT), )
    torch.testing.assert_close(input_tokens, input_positions)

    # Verify Sampling
    expected_selected_token_indices = []
    selected_token_start_idx = 0
    for prompt_len in prompt_lens:
        expected_selected_token_indices.append(selected_token_start_idx)
        selected_token_start_idx += 1
    sampling_metadata = model_runner._prepare_sample(seq_group_metadata_list,
                                                     prompt_lens,
                                                     subquery_lens=prompt_lens)
    actual = sampling_metadata.selected_token_indices
    expected = torch.tensor(expected_selected_token_indices,
                            device=actual.device,
                            dtype=actual.dtype)
    torch.testing.assert_close(actual, expected)