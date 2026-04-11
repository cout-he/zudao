# Project Structure

## Recommended folders

- `core/`
  Core algorithm modules and shared logic.
- `scripts/`
  Entry scripts for experiments and runs.
- `data/`
  Input files such as Excel demand sheets.
- `outputs/`
  Generated figures and result images.

## Current layout

- `core/config.py`
- `core/data_loader.py`
- `core/decoder.py`
- `core/ga_engine.py`
- `core/ga_engine_fast.py`
- `core/genetic_operators.py`
- `core/visualization.py`
- `scripts/main_ours.py`
- `scripts/main_ga.py`
- `scripts/run_fast_ga.py`
- `scripts/test_ga.py`
- `scripts/analyze_optimal.py`
- `scripts/solve_optimal.py`
- `data/产品数据.xlsx`
- `outputs/*.png`

## Recommended commands

Run the fast GA:

```powershell
python scripts/run_fast_ga.py
```

Run the interactive GA entry:

```powershell
python scripts/main_ga.py
```

Run the original model:

```powershell
python scripts/main_ours.py
```
