# V0.2 可用全链路 MVP 开发计划

## 1. 项目定义

### 1.1 项目名称

机甲模型细节设计 Agent V0.2 自然语言到操作蓝图 MVP。

### 1.2 项目目标

在现有基础意图 Agent 上，交付一个用户可以马上使用的命令行版本。用户输入自然语言机甲模型设计需求后，系统输出：

- 机器可读的机甲设计操作蓝图。
- 设计师可读的执行摘要。
- 基础可制作性风险提示。
- 可保存、可测试、可迭代的 JSON 输出。

### 1.3 项目原则

- 不做通用 3D 生成。
- 不接入真实 mesh 操作。
- 不做 Blender 自动建模。
- 不扩展到 Web UI。
- 本版本只打通可用闭环，所有功能围绕“输入一句话，输出机器可读操作蓝图”。

## 2. V0.2 完成后用户可以做什么

V0.2 完成后，用户可以用该工具完成以下任务：

1. 输入机甲模型修改需求。
   示例：`给胸甲加一些锐利的分件线，适合 1/144 打印。`

2. 获得机器可读操作蓝图。
   输出会明确目标部件、操作类型、细节类型、设计风格、密度、比例、对称策略和制作约束。

3. 获得设计师可读执行摘要。
   输出会告诉用户下一步在 Blender、ZBrush 或 Fusion 中应该先做什么、再做什么。

4. 获得基础风险提示。
   输出会提示刻线过密、细件过薄、关节干涉、比例不适合打印等基础风险。

5. 保存操作蓝图。
   用户可以把 JSON 输出作为后续 Blender 集成、设计审查和多轮迭代的输入。

本版本不是自动建模工具。它的直接价值是把模糊自然语言需求转成稳定、可校验、可复用的操作蓝图；设计师可读摘要只是这份蓝图的展示层，用于让用户立刻指导手工建模。

## 3. 范围管理

### 3.1 本期范围

本期只包含以下内容：

- 扩展操作蓝图 schema。
- 扩展机甲细节 taxonomy。
- 更新 LLM intent prompt。
- 更新 mock parser。
- 更新 planner 校验。
- 增加 blueprint formatter。
- 增加基础 risk checker。
- 增加命令行运行入口或完善现有入口。
- 增加典型用例和基础测试。
- 更新文档。

### 3.2 明确不做

- 不读取 `.obj`、`.fbx`、`.glb`、`.blend`。
- 不分析真实 mesh。
- 不生成真实刻线几何。
- 不执行 Blender Python。
- 不做 Web、桌面 UI、插件 UI。
- 不做用户账号、项目管理、多模型资产库。
- 不做具体商业机体复刻流程。

## 4. 交付物

### 4.1 代码交付物

- 扩展后的 `OperationPlan` 操作蓝图数据结构。
- 扩展后的 taxonomy 配置。
- 更新后的 intent prompt。
- 更新后的 planner 校验逻辑。
- 更新后的 mock parser。
- 新增 blueprint formatter。
- 新增基础 risk checker。
- 命令行演示入口。
- 测试用例。

### 4.2 文档交付物

- V0.2 使用说明。
- V0.2 示例输入输出。
- V0.2 已知限制。

### 4.3 验收交付物

- 5 条标准演示用例。
- 测试通过结果。
- 一份示例操作蓝图 JSON 输出。
- 一份设计师可读摘要输出。

## 5. 功能规格

### 5.1 OperationPlan V2 字段

V0.2 的机器可读操作蓝图必须包含以下字段：

```json
{
  "target_part": "chest_armor",
  "operation": "add_parting_lines",
  "detail_type": "parting_lines",
  "style": "sharp_mechanical",
  "density": "medium",
  "symmetry": "centerline_symmetry",
  "scale": "1/144",
  "placement_zones": ["upper_chest_plate", "around_cockpit_hatch"],
  "constraints": ["avoid_joint_interference", "keep_lines_printable"],
  "steps": [
    "在胸甲上缘添加两组斜切分件线",
    "围绕驾驶舱舱门保留主体轮廓，不穿过舱门边界",
    "刻线宽度按 1/144 比例保持克制"
  ],
   "risk_notes": [
      "1/144 比例下刻线过密会降低打印清晰度",
      "胸甲下缘需要避开腰部活动区域"
   ],
   "reasoning": "用户希望胸甲增加锐利分件线，并考虑 1/144 打印可制作性。",
   "designer_brief": "建议在胸甲上缘和驾驶舱周围添加中等密度斜切分件线，保持中心对称，并避开腰部活动区域。"
}
```

字段说明：`designer_brief` 是给用户看的摘要；其他字段构成后续执行层可复用的机器蓝图。

#### 5.1.1 字段契约冻结表

V0.2 字段冻结如下。后续代码实现必须严格以此表为准，不在 V0.2 开发过程中临时新增字段。

| 字段 | 类型 | 必填 | 默认值 | 生成来源 | 用途 |
|---|---|---|---|---|---|
| `target_part` | `str` | 是 | 无 | parser | 指向模型上下文中的标准部件名 |
| `operation` | `str` | 是 | `add_panel_lines` | parser | 描述要执行的蓝图操作 |
| `detail_type` | `str` | 是 | `panel_lines` | parser | 描述要添加或调整的细节类型 |
| `style` | `str` | 是 | `default_mecha` | parser | 描述设计语言和视觉风格 |
| `density` | `str` | 是 | `medium` | parser | 描述细节密度 |
| `symmetry` | `str` | 是 | `single_target` | parser | 描述对称或成组策略 |
| `scale` | `str` | 是 | `unknown` | parser | 描述制作比例 |
| `placement_zones` | `list[str]` | 是 | `[]` | parser/planner | 建议操作区域 |
| `constraints` | `list[str]` | 是 | `[]` | parser/planner | 制作、比例、活动或装配约束 |
| `steps` | `list[str]` | 是 | `[]` | parser/planner | 面向后续执行层和设计师的步骤 |
| `risk_notes` | `list[str]` | 是 | `[]` | parser/risk checker | 可制作性和设计风险提示 |
| `reasoning` | `str` | 是 | `""` | parser | 简短解释解析依据 |
| `designer_brief` | `str` | 是 | `""` | formatter/parser | 给用户看的蓝图摘要 |

#### 5.1.2 字段边界

- `target_part` 必须来自当前模型上下文中的 `name` 字段，不能输出 display name 或 alias。
- `operation` 和 `detail_type` 可以相同含义但不能混用：`operation` 表示动作，`detail_type` 表示对象或细节类型。
- `designer_brief` 不作为执行层输入的唯一依据，执行层必须优先读取结构化字段。
- `risk_notes` 只输出保守提示，不输出精确工程结论。
- `placement_zones` 在 V0.2 只允许自然语言区域标签，不要求绑定真实 mesh 坐标。
- `constraints` 在 V0.2 只允许约束标签或短语，不要求 CAD 参数化表达。
- `steps` 在 V0.2 只表达操作顺序，不要求可直接执行 Blender Python。
- 旧字段 `action` 不进入 V0.2 主输出；如需兼容旧逻辑，只能在内部映射为 `operation`。

### 5.2 枚举值

#### 5.2.1 operation

- `add_panel_lines`
- `add_parting_lines`
- `add_armor_layers`
- `add_vents`
- `add_thrusters`
- `add_pipes`
- `add_hydraulic_rods`
- `add_sensors`
- `add_weapon_mounts`
- `add_surface_damage`
- `refine_surface`

冻结说明：V0.2 只支持以上 11 个操作。新增操作必须进入 V0.3 或之后。

#### 5.2.2 detail_type

- `panel_lines`
- `parting_lines`
- `armor_layers`
- `vents`
- `thrusters`
- `pipes`
- `hydraulic_rods`
- `sensors`
- `weapon_mounts`
- `surface_damage`
- `weathering`

冻结说明：V0.2 只支持以上 11 个细节类型。`mechanical_greeble` 作为旧输入概念保留在 parser 兼容逻辑中，但不作为 V0.2 主输出枚举。

#### 5.2.3 style

- `default_mecha`
- `sharp_mechanical`
- `heavy_armor`
- `military_realistic`
- `clean_anime`
- `high_mobility`
- `exposed_inner_frame`

冻结说明：V0.2 只支持以上 7 种风格。未识别风格统一输出 `default_mecha`。

#### 5.2.4 symmetry

- `single_target`
- `left_right_mirror`
- `centerline_symmetry`
- `group_sync`

冻结说明：V0.2 只识别对称策略，不做完整目标展开；完整成组目标展开放到 V0.3。

#### 5.2.5 density

- `low`
- `medium`
- `high`

冻结说明：沿用 V0.1 的三档密度，不增加更细粒度数值。

#### 5.2.6 scale

- `unknown`
- `non_scale`
- `1/144`
- `1/100`
- `1/60`

冻结说明：V0.2 只支持常见模型比例和未知比例，不处理任意比例换算。

### 5.3 Step 1 冻结结论

V0.2 的字段和枚举以第 5.1、5.2 节为准。后续 Step 2 到 Step 12 均不得在未变更本节的情况下新增输出字段或新增枚举值。

## 6. 模块设计

### 6.1 Schema 模块

目标：定义 OperationPlan V2，并提供 `to_dict()` 输出。

修改文件：

- `3d_agent/model/schemas.py`

工作项：

- 增加枚举集合。
- 更新 `OperationPlan` dataclass。
- 保留向后兼容字段映射，不再使用旧 `action` 作为主字段。

完成标准：

- 新字段可实例化。
- 非法枚举可被 planner 拦截。

### 6.2 Taxonomy 模块

目标：让 parser 能识别更多机甲细节类型。

修改文件：

- `3d_agent/context/design_taxonomy.json`

工作项：

- 增加 V0.2 细节类型关键词。
- 增加 style 关键词。
- 增加 scale 关键词。
- 增加 symmetry 关键词。

完成标准：

- 中文输入能匹配常见细节、风格、比例、对称表达。

### 6.3 Intent Parser 模块

目标：从用户输入中提取 OperationPlan V2 所需字段。

修改文件：

- `3d_agent/agent/intent_parser.py`
- `3d_agent/prompts/intent_prompt.txt`

工作项：

- 更新 prompt 输出格式。
- 更新 mock parser 检测逻辑。
- 增加默认值策略。
- 保持 copilot-api 和 openai 路径可用。

完成标准：

- mock 模式下能输出完整 V2 plan。
- LLM 模式 prompt 明确要求完整 JSON。

### 6.4 Planner 模块

目标：校验 OperationPlan V2 并补齐派生字段。

修改文件：

- `3d_agent/agent/planner.py`

工作项：

- 更新 required fields。
- 增加枚举校验。
- 增加 list 字段类型校验。
- 对空 `placement_zones`、`steps`、`risk_notes` 做默认补齐。

完成标准：

- 非法目标部件报错。
- 非法 operation、detail_type、style、density、symmetry、scale 报错。
- 合法输入返回稳定 JSON。

### 6.5 Risk Checker 模块

目标：提供基础可制作性风险提示。

新增文件：

- `3d_agent/agent/risk_checker.py`

工作项：

- 根据部件、细节类型、密度、比例生成风险提示。
- 重点覆盖 `antenna`、`camera_sensor`、`thruster`、`joint-like` 部件和 `1/144` 比例。
- 输出 `risk_notes` 补充项。

完成标准：

- `antenna + high + panel_lines + 1/144` 输出高风险提示。
- `chest_armor + medium + parting_lines + 1/144` 输出中等风险提示。

### 6.6 Formatter 模块

目标：把机器可读操作蓝图转成设计师可读摘要。

新增文件：

- `3d_agent/agent/formatter.py`

输出格式：

- 目标部件。
- 设计意图。
- 推荐操作。
- 建模步骤。
- 风险提示。
- 下一步建议。

完成标准：

- `run_agent()` 的 `model_edit` 结果中包含 `designer_brief` 和 `user_message`。
- `designer_brief` 能直接指导用户手工建模。
- `user_message` 包含对操作蓝图的简短说明。

### 6.7 CLI 演示链路

目标：用户可以在命令行输入一句话并看到完整结果。

修改或确认文件：

- `3d_agent/main.py`

工作项：

- 确认 CLI 能接收用户输入。
- 打印 JSON。
- 打印设计师可读摘要。

完成标准：

- 执行命令后能完成一次完整链路演示。

## 7. 任务拆解 WBS

### 7.1 阶段 A：需求冻结

任务：确认 V0.2 范围、字段、枚举、验收用例。


输出：本开发计划冻结版本。


完成标准：不再新增 V0.2 范围外功能。

### 7.2 阶段 B：Schema 和 Taxonomy

任务 B1：更新 `schemas.py`。


任务 B2：更新 `design_taxonomy.json`。


任务 B3：更新 planner required fields。


完成标准：基础 plan 可通过校验。

### 7.3 阶段 C：Parser 和 Prompt

任务 C1：更新 `intent_prompt.txt`。


任务 C2：更新 mock parser。


任务 C3：补齐默认值策略。


完成标准：mock 模式能解析 5 条标准输入。

### 7.4 阶段 D：Risk 和 Formatter

任务 D1：新增 `risk_checker.py`。


任务 D2：新增 `formatter.py`。


任务 D3：在 `loop.py` 的 model_edit 链路接入 risk 和 formatter。


完成标准：输出包含 `risk_notes` 和 `user_message`。

### 7.5 阶段 E：CLI 和示例

任务 E1：确认或更新 `main.py`。


任务 E2：新增示例输入输出文档。


任务 E3：跑通 5 条验收用例。


完成标准：用户可以通过命令行使用完整闭环。

### 7.6 阶段 F：测试和收尾

任务 F1：增加单元测试。


任务 F2：运行测试。


任务 F3：修复 V0.2 范围内缺陷。


任务 F4：更新使用说明。


完成标准：测试通过，文档可指导用户运行。

## 8. 里程碑

| 里程碑 | 内容 | 完成标准 |
|---|---|---|
| M1 | 需求冻结 | 本计划确认，范围不再扩散 |
| M2 | Plan V2 校验完成 | 新 schema、taxonomy、planner 可用 |
| M3 | Parser 完成 | mock 和 prompt 都输出 V2 JSON |
| M4 | 蓝图展示层完成 | 结果包含 `designer_brief`、建模步骤和风险提示 |
| M5 | CLI 闭环完成 | 命令行可完成一次端到端使用 |
| M6 | V0.2 验收完成 | 5 条验收用例通过 |

## 9. 验收用例

### 9.1 用例 1：胸甲分件线

输入：

```text
给胸甲加一些锐利的分件线，适合 1/144 打印。
```

必须输出：

- `target_part`: `chest_armor`
- `operation`: `add_parting_lines`
- `style`: `sharp_mechanical`
- `density`: `medium`
- `scale`: `1/144`
- 至少 3 条 `steps`
- 至少 1 条 `risk_notes`

### 9.2 用例 2：背包推进器

输入：

```text
把背包的推进器做得更高机动一点，加喷口和机械细节。
```

必须输出：

- 目标部件为 `backpack`、`booster` 或 `thruster` 中合理目标。
- `style`: `high_mobility`
- `detail_type`: `thrusters`
- 输出喷口相关步骤。

### 9.3 用例 3：V 字天线风险

输入：

```text
给 V 字天线加大量刻线，比例 1/144。
```

必须输出：

- `target_part`: `antenna`
- `density`: `high`
- `scale`: `1/144`
- 风险提示必须包含结构过细或打印风险。

### 9.4 用例 4：腿部对称机械细节

输入：

```text
给两条腿加同样的管线和液压杆，密度中等。
```

V0.2 最低要求：

- 可以识别目标为 `leg` 或合理腿部目标。
- `detail_type` 为 `pipes` 或 `hydraulic_rods`。
- `symmetry` 为 `left_right_mirror` 或 `group_sync`。

说明：完整目标展开放到 V0.3。

### 9.5 用例 5：盾牌战损

输入：

```text
给盾牌加少量战损和旧化，不要太脏。
```

必须输出：

- `target_part`: `shield`
- `operation`: `add_surface_damage`
- `detail_type`: `surface_damage` 或 `weathering`
- `density`: `low`
- `designer_brief` 强调克制处理。

## 10. 质量管理

### 10.1 代码质量要求

- 不引入无关框架。
- 不改变现有 provider 配置方式。
- 不破坏 `inspect_context` 和 `explain_capability`。
- 所有新增枚举必须集中定义。
- 所有 LLM 输出必须经过 planner 校验。

### 10.2 测试要求

必须覆盖：

- 合法 V2 plan 校验。
- 非法枚举报错。
- mock parser 输出完整字段。
- risk checker 对高风险场景输出提示。
- formatter 输出非空 `designer_brief` 和 `user_message`。

### 10.3 文档要求

- README 或独立文档必须说明如何运行 V0.2。
- 示例输入输出必须与验收用例一致。
- 已知限制必须明确写出。

## 11. 风险管理

| 风险 | 影响 | 应对 |
|---|---|---|
| schema 一次扩展过多 | 实现拖延 | V0.2 只保留本计划列出的字段 |
| LLM 输出缺字段 | 链路失败 | planner 校验并报错，mock 用默认值补齐 |
| 风险提示不准确 | 用户误解 | V0.2 只输出保守提示，不给精确工程结论 |
| 成组编辑复杂 | 范围扩大 | V0.2 只识别 symmetry，不做完整目标展开 |
| Blender 集成诱惑过早 | 偏离 MVP | V0.2 不执行 Blender，只输出操作蓝图和设计师摘要 |

## 12. 变更控制

V0.2 开发期间，新增需求按以下规则处理：

- 影响端到端闭环的缺失功能，可以进入 V0.2。
- UI、Blender 执行、真实 mesh 分析，一律进入 V0.3 或之后。
- 新增字段必须同时满足：能被 parser 解析、能被 planner 校验、能被 formatter 用于生成设计师摘要。
- 任何不能被验收用例覆盖的新功能，不进入 V0.2。

## 13. 开发顺序

严格按以下顺序执行：

1. 冻结 schema 字段和枚举。
2. 修改 `schemas.py`。
3. 修改 `design_taxonomy.json`。
4. 修改 `planner.py`。
5. 修改 `intent_prompt.txt`。
6. 修改 `intent_parser.py`。
7. 新增 `risk_checker.py`。
8. 新增 `formatter.py`。
9. 修改 `loop.py` 接入 risk 和 formatter。
10. 确认或修改 `main.py`。
11. 增加测试。
12. 增加示例文档。
13. 跑验收用例。

## 14. V0.2 完成定义

V0.2 只有在同时满足以下条件时才算完成：

- 5 条验收用例全部通过。
- `run_agent()` 返回完整 OperationPlan V2 操作蓝图。
- `run_agent()` 返回设计师可读 `designer_brief`。
- `run_agent()` 返回简短 `user_message`。
- 高风险输入能输出基础风险提示。
- 命令行可以完成一次端到端演示。
- 文档说明如何运行和如何理解输出。
- 未引入 V0.2 范围外功能。

## 15. 逐步实施计划

本节用于指导实际开发执行。开发期间严格按步骤推进，每一步完成后先验收，再进入下一步。除非发现阻塞问题，否则不调整顺序。

### 15.1 Step 0：开发前基线确认

目标：确认当前项目状态，避免在不清楚现状的情况下修改代码。

涉及文件：

- `3d_agent/model/schemas.py`
- `3d_agent/agent/planner.py`
- `3d_agent/agent/intent_parser.py`
- `3d_agent/agent/loop.py`
- `3d_agent/context/design_taxonomy.json`
- `3d_agent/prompts/intent_prompt.txt`
- `3d_agent/main.py`

执行内容：

1. 阅读当前基础链路。
2. 确认 `run_agent()` 的现有返回结构。
3. 确认 mock 模式是否可运行。
4. 确认是否已有测试目录和测试框架。

输出物：

- 一份开发前状态摘要。
- 当前可运行命令记录。
- 当前缺失项记录。

验收标准：

- 能清楚说明当前链路从输入到输出经过哪些模块。
- 能确认 V0.2 需要修改和新增的文件列表。

停下确认点：

- 向用户确认基线状态，再开始 Step 1。

### 15.2 Step 1：冻结 OperationPlan V2 字段和枚举

目标：先确定机器可读操作蓝图的数据契约，后续所有模块都围绕该契约实现。

涉及文件：

- `docs/v0_2_mvp_development_plan.md`

执行内容：

1. 确认 `OperationPlan V2` 必填字段。
2. 确认 `operation` 枚举。
3. 确认 `detail_type` 枚举。
4. 确认 `style` 枚举。
5. 确认 `symmetry` 枚举。
6. 确认 `scale` 枚举。
7. 确认 `designer_brief` 是否作为 plan 输出字段。

输出物：

- 冻结后的字段表。
- 冻结后的枚举表。

验收标准：

- 字段和枚举不再在 V0.2 开发过程中随意新增。
- 每个字段都有明确用途。
- 每个枚举值都能被至少一个验收用例使用或解释。

停下确认点：

- 用户确认字段和枚举后，才能进入 Step 2。

### 15.3 Step 2：实现 Schema 层

目标：把冻结后的操作蓝图契约落到代码数据结构中。

涉及文件：

- `3d_agent/model/schemas.py`

执行内容：

1. 增加 V0.2 枚举集合。
2. 更新 `OperationPlan` dataclass。
3. 增加 list 字段：`placement_zones`、`constraints`、`steps`、`risk_notes`。
4. 增加文本字段：`operation`、`style`、`symmetry`、`scale`、`designer_brief`。
5. 保留 `reasoning`。
6. 确认 `to_dict()` 输出完整字段。

输入：

- Step 1 冻结的数据契约。

输出：

- 可实例化的 `OperationPlan V2`。

验收标准：

- `OperationPlan` 能输出完整字典。
- 所有 V0.2 字段都存在。
- 旧的 `action` 不再作为主输出字段。

停下确认点：

- 展示 `schemas.py` 修改摘要和一个 plan 示例。

### 15.4 Step 3：扩展 Taxonomy 配置

目标：让系统具备识别 V0.2 关键词的基础词典。

涉及文件：

- `3d_agent/context/design_taxonomy.json`

执行内容：

1. 扩展 `detail_types`。
2. 增加 `operations` 或更新现有 `actions` 到 V0.2 命名。
3. 增加 `styles`。
4. 增加 `symmetries`。
5. 增加 `scales`。
6. 保留旧关键词兼容，例如“刻线”“机械细节”“战损”。

输入：

- Step 1 冻结的枚举。

输出：

- V0.2 taxonomy JSON。

验收标准：

- 验收用例中的关键词都能在 taxonomy 中找到对应项。
- JSON 格式合法。
- 不删除当前已支持的基础关键词。

停下确认点：

- 展示 taxonomy 分类摘要。

### 15.5 Step 4：更新 Planner 校验层

目标：确保所有蓝图输出都经过严格校验，避免不稳定 LLM 输出直接进入后续链路。

涉及文件：

- `3d_agent/agent/planner.py`

执行内容：

1. 更新 required fields。
2. 校验 `target_part` 是否存在。
3. 校验 `operation` 枚举。
4. 校验 `detail_type` 枚举。
5. 校验 `style` 枚举。
6. 校验 `density` 枚举。
7. 校验 `symmetry` 枚举。
8. 校验 `scale` 枚举。
9. 校验 list 字段类型。
10. 对空 list 字段补默认值。
11. 构造并返回 `OperationPlan V2`。

输入：

- parser 输出的 intent dict。
- model context。

输出：

- 通过校验的操作蓝图 dict。

验收标准：

- 合法 intent 能返回完整 plan。
- 非法枚举能抛出明确错误。
- 缺字段能抛出明确错误。
- list 字段不是 list 时能抛出明确错误。

停下确认点：

- 展示合法和非法样例的校验结果。

### 15.6 Step 5：更新 Intent Prompt

目标：让 LLM 路径输出 OperationPlan V2 格式。

涉及文件：

- `3d_agent/prompts/intent_prompt.txt`

执行内容：

1. 更新输出 JSON 模板。
2. 明确所有字段必须返回。
3. 明确枚举值只能从 V0.2 列表选择。
4. 明确 `designer_brief` 是用户可读摘要。
5. 明确不得输出 markdown。
6. 明确不生成真实 Blender 或 mesh 操作。

输入：

- OperationPlan V2 字段和枚举。

输出：

- V0.2 intent prompt。

验收标准：

- prompt 中包含完整 JSON shape。
- prompt 中包含字段规则。
- prompt 中包含边界限制。

停下确认点：

- 展示新 prompt 的输出格式段落。

### 15.7 Step 6：更新 Mock Parser

目标：保证在不依赖外部 LLM 的情况下，也能稳定跑通 V0.2 全链路。

涉及文件：

- `3d_agent/agent/intent_parser.py`

执行内容：

1. 增加 `operation` 检测。
2. 扩展 `detail_type` 检测。
3. 增加 `style` 检测。
4. 增加 `symmetry` 检测。
5. 增加 `scale` 检测。
6. 生成默认 `placement_zones`。
7. 生成默认 `constraints`。
8. 生成默认 `steps`。
9. 生成默认 `risk_notes` 空列表或基础提示。
10. 生成 `designer_brief`。

输入：

- 用户自然语言。
- planner context。

输出：

- 完整 intent dict。

验收标准：

- 5 条验收用例在 mock 模式下都能输出完整字段。
- 不识别的字段有稳定默认值。
- 不引入外部依赖。

停下确认点：

- 展示 5 条验收输入的 mock parser 原始输出。

### 15.8 Step 7：新增 Risk Checker

目标：为操作蓝图补充基础可制作性风险提示。

涉及文件：

- `3d_agent/agent/risk_checker.py`
- `3d_agent/agent/loop.py`

执行内容：

1. 新增 `evaluate_risks(plan, model_context)`。
2. 按比例判断风险。
3. 按部件判断风险。
4. 按细节类型和密度判断风险。
5. 合并已有 `risk_notes`，避免重复。
6. 在 model_edit 链路中接入。

输入：

- 已校验 OperationPlan V2。
- model context。

输出：

- 带补充 `risk_notes` 的 plan。

验收标准：

- `antenna + high + panel_lines + 1/144` 输出结构过细或打印风险。
- `chest_armor + medium + parting_lines + 1/144` 输出刻线密度或活动区域提示。
- 低风险场景不输出夸张警告。

停下确认点：

- 展示风险规则表和 2 个风险输出样例。

### 15.9 Step 8：新增 Blueprint Formatter

目标：把机器蓝图转换成用户能读懂的展示层，但不改变机器蓝图本身。

涉及文件：

- `3d_agent/agent/formatter.py`
- `3d_agent/agent/loop.py`

执行内容：

1. 新增 `format_designer_brief(plan)`。
2. 新增 `format_user_message(plan)`。
3. 输出目标部件、推荐操作、步骤、风险和下一步建议。
4. 确保 `designer_brief` 非空。
5. 确保 `user_message` 简短。
6. 在 model_edit 链路中接入。

输入：

- 带风险提示的 OperationPlan V2。

输出：

- `designer_brief`。
- `user_message`。

验收标准：

- `designer_brief` 能指导手工建模。
- `user_message` 不替代蓝图，只说明蓝图已生成。
- JSON 输出中同时包含机器字段和展示层字段。

停下确认点：

- 展示 1 条完整 JSON 输出和对应摘要。

### 15.10 Step 9：确认 CLI 端到端链路

目标：用户可以通过命令行直接使用 V0.2。

涉及文件：

- `3d_agent/main.py`

执行内容：

1. 确认命令行输入方式。
2. 确认调用 `run_agent()`。
3. 打印完整 JSON。
4. 打印 `designer_brief`。
5. 保持 inspect 和 capability 命令不被破坏。

输入：

- 用户自然语言命令。

输出：

- 终端展示的操作蓝图 JSON。
- 终端展示的设计师摘要。

验收标准：

- 用例 1 可通过 CLI 跑通。
- 输出可读且 JSON 完整。
- 没有异常堆栈。

停下确认点：

- 展示 CLI 运行输出。

### 15.11 Step 10：新增测试

目标：保证 V0.2 的关键链路可回归验证。

涉及文件：

- 测试目录，按当前项目结构确定。

测试项：

1. `OperationPlan V2` dataclass 输出完整字段。
2. planner 接受合法 plan。
3. planner 拒绝非法枚举。
4. mock parser 输出完整字段。
5. risk checker 输出高风险提示。
6. formatter 输出非空 `designer_brief`。
7. `run_agent()` model_edit 链路输出完整蓝图。

输出：

- 自动化测试用例。
- 测试运行结果。

验收标准：

- V0.2 相关测试全部通过。
- 不要求补齐 V0.2 范围外测试。

停下确认点：

- 展示测试命令和结果摘要。

### 15.12 Step 11：新增示例文档

目标：让用户知道如何使用 V0.2，以及如何理解输出。

涉及文件：

- `docs/v0_2_usage.md`

执行内容：

1. 写运行命令。
2. 写 5 条验收用例。
3. 写一份完整输出示例。
4. 解释 `OperationPlan V2` 字段。
5. 说明 V0.2 不自动建模。

输出：

- V0.2 使用说明文档。

验收标准：

- 用户能按文档运行一次命令。
- 用户能理解 `designer_brief` 和机器蓝图的区别。

停下确认点：

- 展示文档摘要。

### 15.13 Step 12：执行 V0.2 验收

目标：按固定用例确认全链路完成。

执行内容：

1. 运行用例 1：胸甲分件线。
2. 运行用例 2：背包推进器。
3. 运行用例 3：V 字天线风险。
4. 运行用例 4：腿部对称机械细节。
5. 运行用例 5：盾牌战损。
6. 记录每条输出是否满足验收要求。

输出：

- 验收结果摘要。
- 未通过项列表。
- 修复建议列表。

验收标准：

- 5 条用例全部满足第 9 节要求。
- 如果有失败项，只修 V0.2 范围内问题。

停下确认点：

- 用户确认 V0.2 是否进入完成状态。

## 16. 每一步执行汇报格式

后续开发时，每完成一个步骤，使用以下格式汇报：

```text
完成步骤：Step X - 步骤名称
修改文件：文件列表
完成内容：3 到 5 条要点
验证结果：命令或检查结果
风险/遗留：如果没有则写“无”
下一步：Step X+1 - 步骤名称
```

该格式用于保证开发过程可追踪、可暂停、可回滚到计划层面重新确认。

## 17. 当前下一步

当前已完成 Step 12：执行 V0.2 验收。下一步应执行：

> 确认 V0.2 是否进入完成状态，并整理后续 V0.3 方向。

V0.2 已完成自然语言到操作蓝图的命令行闭环，后续可以围绕真实模型文件、Blender/Fusion 执行层或更强的多轮编辑上下文进入 V0.3 规划。