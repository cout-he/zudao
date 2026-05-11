# Locked-Width Baselines

这个目录用于放置和现有主流程解耦的 baseline 方法代码。

当前包含两个独立 baseline：

- `two_stage_greedy.py`
  二阶段齐头切贪心启发式，偏工业规则法。
- `pattern_generation.py`
  版型生成法，先枚举可行刀道版型，再做启发式主问题选择。

运行入口：

```bash
python baseline_methods/run_locked_width_experiments.py
```

默认会读取：

- `data/实际生产状态表.xlsx`
- `outputs/实际生产状态表_四宽度混合核对.xlsx`

并锁定以下实验分组在现有结果中的已选母板宽度：

- `G001`
- `G006`
- `G020`
- `G036`
