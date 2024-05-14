# modify vllm@f721096 for [AlphaMath](https://github.com/MARIO-Math-Reasoning/Super_MARIO) to support value model

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
```

## added files
```
tests/test_regression_withvalue.py
vllm/model_executor/models/modeling_value_head.py
```
