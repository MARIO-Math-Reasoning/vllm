# modify [vllm@f721096](https://github.com/vllm-project/vllm/tree/f721096d48a7e3b98dffcb9b400bf58989cef64d) for [AlphaMath](https://github.com/MARIO-Math-Reasoning/Super_MARIO) to support value model

## Installation
- Method 1
```bash
git clone https://github.com/MARIO-Math-Reasoning/vllm
cd vllm
pip install -e .
```
- Method 2
  1. Install the original vllm v0.3.3
  ```bash
  git clone https://github.com/vllm-project/vllm.git
  cd vllm
  git checkout f721096
  pip install -e .
  ```
  2. Copy the following modified files and added files from this repo to the above vllm folder.

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
requirements-build.txt # because setuptools 70.0.0 was released May 21 2024, need to pin version of setuptools.
```

## added files
```
tests/test_regression_withvalue.py
vllm/model_executor/models/modeling_value_head.py
```
