# 科隆 Major 2026 — Pick'em 模拟器

[English](README.md)

基于 Elo/比值混合胜率模型的 CS2 Major 瑞士轮模拟器，使用蒙特卡洛方法寻找最优 Pick'em 选择。

## 快速开始

```bash
cd /Users/sunxt/projects/cologne-pickem
python3 main.py --stage 1    # 第一阶段（揭幕战）
python3 main.py --stage 2    # 第二阶段（淘汰赛）
python3 main.py --stage 3    # 第三阶段（传奇组）
```

## 命令行参数

```
--stage {1,2,3}        选择模拟哪个阶段（必填）
--sims N               队伍概率估算的蒙特卡洛次数
--pick-sims N          每个 Pick'em 组合的估值次数
--candidates N         最多测试的 Pick'em 组合数
--no-advancers         忽略预设晋级结果，从更早阶段重新模拟
--seed N               随机种子，用于结果复现（默认 42）
```

示例：
```bash
python3 main.py --stage 2 --sims 10000 --pick-sims 5000
python3 main.py --stage 3 --no-advancers
```

## 文件结构

```
cologne-pickem/
├── config.py              # 所有可配置数据和参数
├── win_probability.py     # Elo/比值混合胜率模型
├── swiss_simulator.py     # 瑞士轮模拟引擎
├── main.py                # CLI 入口 + Pick'em 优化器
└── README.md / README_zh.md
```

## 配置文件

所有可调参数集中在 `config.py`。

### 队伍数据 (`TEAMS`)

```python
"vita": {
    "name": "Team Vitality",
    "vrs": 1,              # VRS 排名（Valve 地区排名）
    "hltv_rank": 1,        # HLTV 世界排名
    "hltv_pts": 1000,      # HLTV 积分
    "form": 0.95,          # 近期状态 [0-1]（Elo 模型中未使用）
    "rank_bias": 0,        # 可选：排名偏差
},
```

### 阶段种子 (`STAGE1`, `STAGE2`, `STAGE3`)

每个阶段是一个包含 16 个队伍代码的列表，列表索引即种子号。调换顺序即可改变种子排名。

```python
STAGE2 = [
    "fut", "spir", "astr", "g2", "lega", "pain", "monte", "9z",   # 种子 1-8
    "b8", "betb", "gl", "m80", "mibr", "tylo", "big", "fly",      # 种子 9-16
]
```

- 第一阶段：16 支队伍，按 VRS 排种子 1-16
- 第二阶段：种子 1-8（直通队）+ 种子 9-16（第一阶段晋级队）
- 第三阶段：种子 1-8（直通队）+ 种子 9-16（第二阶段晋级队，待定）

### rank_bias

调整队伍的实际实力相对于 HLTV/VRS 排名的偏差。正值表示队伍比排名更强，负值表示更弱。会同时偏移 VRS 和 HLTV 的有效排名，然后重新估算 Elo 评分。

```python
"tylo": {..., "rank_bias": 5},     # 实际比排名强 5 名
"astr": {..., "rank_bias": -3},    # 实际比排名弱 3 名
```

- `+N`：有效排名 = 实际排名 - N（更强）
- `-N`：有效排名 = 实际排名 + N（更弱）
- 默认 `0`：不调整

### 模型参数 (`MODEL`)

```python
MODEL = {
    # Elo / 比值权重
    "sigma_vrs": 89.0,       # VRS 的 Elo sigma 值
    "hltv_exp": 0.432,       # HLTV 比值指数
    "w_hltv": 0.837,         # HLTV 权重（主导）
    "w_vrs": 0.163,          # VRS 权重

    # 爆冷系数
    #   > 0  -> 胜率趋近 50%（随机性增大）
    #   = 0  -> 不调整
    #   < 0  -> 胜率远离 50%（放大强队优势）
    "upset_bo1": 0.20,       # BO1：单图变数大，压缩强队优势
    "upset_bo3": -0.10,      # BO3：多图放大实力差距

    # 交手记录调整
    "h2h_weight": 0.12,      # 极端交手记录最多 ±6% 调整
}
```

### 模拟参数 (`SIM`)

```python
SIM = {
    "team_sims": 5000,       # 队伍概率估算的模拟次数
    "pick_sims": 3000,       # 每个 Pick'em 组合的估值次数
    "candidates": 4000,      # 最多测试的 Pick'em 组合数
}
```

## 胜率模型

双组件 Elo/比值混合模型：

```
VRS 评分由排名估算：  1880 - (rank - 1) * 10.5
HLTV 评分由积分估算：  3 + pts * 0.177

p_vrs  = 1 / (1 + 10^((vrs_B - vrs_A) / sigma_vrs))
p_hltv = 1 / (1 + (hltv_B / hltv_A) ^ hltv_exp)
p_base = w_hltv * p_hltv + w_vrs * p_vrs

爆冷修正：
p_map  = 0.5 + (p_base - 0.5) * (1 - upset_factor)

BO1：  使用 upset_bo1（例如 0.20 → 80% 变为 74%）
BO3：  使用 upset_bo3 修正每图胜率后（例如 -0.10 → 80% 变为 83%），
       再通过二项分布计算 BO3 总胜率：P(2-0) + P(2-1)
```

### 爆冷系数效果示例

| upset | 效果 | p=80% 变为 |
|:-----:|------|:---------:|
| 0.35 | BO1 高随机性 | 69.5% |
| 0 | 不调整 | 80% |
| -0.10 | BO3 放大优势 | 83% → BO3 97.7% |
| -1 | 大幅放大 | ~98% |
| 1 | 完全硬币 | 50% |
| 2 | 胜率倒转 | 20% |

## 瑞士轮配对算法

严格遵循 CS Major 2026 官方规则（对照 [majors.im](https://majors.im/2026/cologne) 源码验证）：

1. **Inverted Seed 排序**（第 0 轮）：种子 1-8 正常排列；种子 9-16 取反（`1000 - seed`），使得下半区最强队与上半区最强队对阵
2. **DFS 自末尾搜索**：每个 W-L 组内，第一支队从排序列表末尾开始寻找首个未交手队伍配对，避免重赛
3. **Buchholz 破同分**：第 0 轮后按负场（升序）、胜场（降序）、Buchholz（降序）、种子号排序
4. **淘汰/晋级战 BO3**：当队伍累积 2 胜或 2 负时改为 BO3

## Pick'em 计分

每阶段 10 个选择：

| 类别 | 位置数 | 得分条件 |
|------|:-----:|----------|
| exact30 | 2 | 选择的队伍恰好 3-0 晋级 |
| advancers | 6 | 选择的队伍以 3-1 或 3-2 晋级 |
| exact03 | 2 | 选择的队伍恰好 0-3 淘汰 |

通过线：>= 5 个正确选择。

## 输出内容

模拟完成后输出：

- 队伍池及实力评分，标注 rank_bias 调整
- 第 0 轮对阵表，用于验证配对逻辑
- **前 3 名**最优 Pick'em 组合，各自包含：
  - 通过率（>=5分 / >=4分）和期望得分
  - exact30 / advancers / exact03 选择及各队概率
- 最优组合的得分分布图
- 全部队伍的晋级/3-0/0-3 概率预测

## Pick'em 过滤器

在 `config.py` 底部有一个 `pickem_filter` 函数，用于在评估前剔除不符合自定义规则的 Pick'em 组合：

```python
def pickem_filter(picks, teams):
    """
    picks = {"exact30": [...], "advancers": [...], "exact03": [...]}
    返回 True 保留该组合，False 跳过。
    """

    # 示例：不让 TYLOO/FlyQuest 出现在 0-3
    if "tylo" in picks["exact03"] or "fly" in picks["exact03"]:
        return False

    # 示例：不让巴西队出现在 3-0
    # br_teams = {"furi", "mibr", "pain", "lega", "9z"}
    # for code in picks["exact30"]:
    #     if code in br_teams:
    #         return False

    return True
```

被过滤掉的组合数会在输出中报告（例如 `(42 combination(s) rejected by pickem_filter)`）。

## 数据来源

- HLTV 排名来自 [5EPlay](https://csgo.5eplay.com) 每周排名报道（2026 年 6 月 2 日）
- VRS 排名来自官方 Major 种子分配
- 赛事结果来自 HLTV / Liquipedia / 电竞新闻
