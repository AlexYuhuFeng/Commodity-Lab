# Replay Pack Authoring / 历史复盘内容包规范

Commodity Lab replay packs train decisions using only information available at each historical checkpoint. A pack is release-ready only when `review_replay_event()` returns `reviewed`.

Commodity Lab 的历史复盘只允许使用每个决策时点已经公开的信息。只有 `review_replay_event()` 返回 `reviewed` 的内容包才能进入正式版本。

## Required Event Fields / 事件字段

- Stable `id`, supported `commodity`, bilingual `title` and `summary`.
- Commercial `exposure`, curriculum `skills`, reviewed `source_notes`, and at least two chronological `checkpoints`.
- 稳定的 `id`、受支持的商品、双语标题与摘要。
- 商业敞口、课程技能、已审查来源，以及至少两个按时间排序的决策节点。

## Source Review / 来源审查

Every source note must include publisher, title, publication date, first-available date, URL, and its precise use in the pack. Licensed prices must not be copied into the repository. Calibrated training curves must stay explicitly labelled as simulations.

每条来源必须记录发布机构、标题、发布日期、首次可用日期、链接和在案例中的具体用途。仓库不得保存受许可限制的价格数据；校准后的训练曲线必须明确标记为模拟数据。

## Checkpoint Contract / 决策节点契约

Each checkpoint contains bilingual known facts, one decision prompt, target actions, a hidden outcome, market regime, base price, and deterministic seed. Every target action includes leg type, market, side, quantity, and tenor.

每个节点包含双语已知事实、一个决策任务、目标动作、提交前隐藏的结果、市场结构、基准价格和确定性随机种子。每个目标动作必须包含工具类型、市场、方向、数量和期限。

## Information Boundary / 信息边界

`build_replay_session()` exposes only checkpoints up to the requested index. Outcomes, model strategy, and plausible alternatives appear only after `evaluate_replay_decision()` scores the submitted decision locally. Source notes are filtered by `available_from`.

`build_replay_session()` 只展示请求节点及以前的信息。结果、参考策略和可行替代方案只能在 `evaluate_replay_decision()` 本地评分后出现；来源按 `available_from` 过滤。

## Release Checklist / 发布检查

1. Run the full test suite and confirm every pack reports `reviewed`.
2. Verify chronological dates and point-in-time source availability.
3. Exercise every checkpoint in the installed client without future-information leakage.
4. Confirm bilingual labels, deterministic scoring, and at least two plausible strategy alternatives.

1. 运行完整测试，确认所有内容包均为 `reviewed`。
2. 核对时间顺序和来源在当时是否可得。
3. 在安装后的客户端逐节点操作，确认没有未来信息泄露。
4. 核对双语文案、确定性评分和至少两种可行替代策略。
