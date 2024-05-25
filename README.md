# modify [vllm@f721096](https://github.com/vllm-project/vllm/tree/f721096d48a7e3b98dffcb9b400bf58989cef64d) for [AlphaMath](https://github.com/MARIO-Math-Reasoning/Super_MARIO) to support value model

## Installation
```
git clone https://github.com/MARIO-Math-Reasoning/vllm
cd vllm
pip install .
```

## modified files
```
vllm/core/scheduler.py
vllm/engine/llm_engine.py
vllm/model_executor/model_loader.py
vllm/model_executor/models/__init__.py
vllm/outputs.py
vllm/sequence.py
vllm/worker/model_runner.py
pyproject.toml # because setuptools 70.0.0 was released May 21 2024, need to pin version of setuptools.
```

## added files
```
tests/test_regression_withvalue.py
vllm/model_executor/models/modeling_value_head.py
```
