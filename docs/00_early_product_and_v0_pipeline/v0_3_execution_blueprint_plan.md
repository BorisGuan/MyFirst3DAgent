# V0.3 执行蓝图设计计划

## 1. 阶段定位

V0.3 的目标不是自动建模，而是把 V0.2 已完成的 OperationPlan V2 进一步整理成后续执行层可以消费的执行蓝图。它处在 V0.2 和 Blender/Fusion 自动化之间，主要解决“蓝图怎么变成可执行任务模板”的问题。

产品路径：

```text
V0.2：自然语言 -> OperationPlan V2 操作蓝图
V0.3：OperationPlan V2 -> Execution Blueprint 执行蓝图
V0.4：Execution Blueprint -> Blender/Fusion 半自动执行
V0.5：真实模型上下文读取和局部几何辅助
```

V0.3 仍然不读取真实 mesh，不执行 Blender Python，不生成真实几何。它只定义执行层需要的中间结构、操作模板、区域语义和自动化难度判断。

## 2. V0.3 目标

V0.3 完成后，系统应该能够把一份 OperationPlan V2 转换成更接近执行层的 Execution Blueprint，至少包含：

- 操作所属的工具族。
- 推荐建模方法。
- 对真实 mesh 的依赖程度。
- 手工建模第一步。
- 适合后续自动化的程度。
- 操作区域的标准化语义。
- 风险等级和阻塞原因。
- 后续 Blender/Fusion 接入所需的前置条件。

V0.3 的直接价值是让设计师、开发者和后续执行层都能理解：这条蓝图应该用什么类型的建模动作实现，哪些部分可以半自动，哪些部分必须等真实模型上下文接入后再做。

## 3. 不做范围

V0.3 明确不做以下内容：

- 不读取 `.obj`、`.fbx`、`.glb`、`.blend`。
- 不分析真实 mesh、拓扑、法线、厚度或碰撞。
- 不执行 Blender Python。
- 不生成刻线、喷口、管线、战损等真实几何。
- 不做 Web UI、桌面 UI 或插件 UI。
- 不改动 V0.2 已冻结的 OperationPlan V2 字段。
- 不新增 V0.2 的 operation/detail_type 枚举。
- 不承诺工程级可制作性判断。

## 4. 输入与输出关系

### 4.1 输入：OperationPlan V2

V0.3 的输入来自 V0.2 的完整操作蓝图，例如：

```json
{
  "target_part": "chest_armor",
  "operation": "add_parting_lines",
  "detail_type": "parting_lines",
  "style": "sharp_mechanical",
  "density": "medium",
  "symmetry": "single_target",
  "scale": "1/144",
  "placement_zones": ["upper_chest_plate", "around_cockpit_hatch"],
  "constraints": ["keep_details_printable_at_1_144"],
  "steps": ["按 1/144 比例控制细节宽度和间距，避免过密。"],
  "risk_notes": ["1/144 比例下刻线或分件线需要控制宽度和间距。"],
  "reasoning": "用户希望添加适量锐利机械分件线，并考虑 1/144 比例。",
  "designer_brief": "建议在 chest_armor 上添加中等密度锐利机械分件线。"
}
```

### 4.2 输出：Execution Blueprint

Execution Blueprint 是 V0.3 的设计目标。建议结构如下：

```json
{
  "source_plan_ref": "operation_plan_v2",
  "target_part": "chest_armor",
  "execution_intent": {
    "tool_family": "surface_detailing",
    "recommended_method": "engraved_line_layout",
    "automation_level": "manual_guided",
    "requires_mesh_access": true,
    "requires_part_boundaries": true
  },
  "operation_template": {
    "template_id": "surface_detailing.parting_lines",
    "template_goal": "lay out printable parting lines on armor surfaces",
    "manual_first_step": "mark readable line paths on the upper chest plate",
    "execution_steps": [
      "identify visible armor plates and protected edges",
      "draw line paths before cutting or engraving",
      "keep line spacing readable at the requested scale"
    ]
  },
  "zone_mapping": [
    {
      "input_zone": "upper_chest_plate",
      "zone_role": "primary_visible_surface",
      "execution_hint": "prefer broad flat armor areas"
    }
  ],
  "automation_assessment": {
    "difficulty": "medium",
    "blocked_by": ["no_real_mesh", "no_surface_boundaries"],
    "v0_4_candidate": true
  },
  "risk_review": {
    "risk_level": "medium",
    "risk_reasons": ["1/144 line spacing may become unreadable"],
    "mitigation_steps": ["reduce density or widen line spacing before execution"]
  },
  "execution_brief": "先在胸甲上缘标记清晰的分件线路径，再按 1/144 比例控制宽度和间距；当前缺少真实 mesh，暂不直接执行切线。"
}
```

## 5. Execution Blueprint 字段契约确认

V0.3 的 Execution Blueprint 字段契约确认如下。本契约用于独立规则型转换器、测试用例和 LLM 候选 prompt。V0.3 不修改 V0.2 的 OperationPlan V2 字段，只在其后生成新的执行准备蓝图。

| 字段 | 类型 | 必填 | 默认值 | 来源 | 用途 |
|---|---|---|---|---|---|
| `source_plan_ref` | `str` | 是 | `operation_plan_v2` | converter | 标记来源蓝图类型 |
| `target_part` | `str` | 是 | 无 | OperationPlan V2 | 延续 V0.2 标准部件名 |
| `execution_intent` | `object` | 是 | 无 | converter/template | 描述工具族、推荐方法和执行依赖 |
| `execution_intent.tool_family` | `str` | 是 | 无 | operation template | 执行工具族 |
| `execution_intent.recommended_method` | `str` | 是 | 无 | operation template | 推荐建模方法 |
| `execution_intent.automation_level` | `str` | 是 | `manual_guided` | operation template | 自动化等级 |
| `execution_intent.requires_mesh_access` | `bool` | 是 | `true` | operation template | 是否需要真实 mesh 才能执行 |
| `execution_intent.requires_part_boundaries` | `bool` | 是 | `true` | operation template | 是否需要部件边界或表面区域 |
| `operation_template` | `object` | 是 | 无 | operation template | 描述可复用操作模板 |
| `operation_template.template_id` | `str` | 是 | 无 | converter | 模板标识，格式为 `tool_family.operation` |
| `operation_template.template_goal` | `str` | 是 | 无 | operation template | 模板目标 |
| `operation_template.manual_first_step` | `str` | 是 | 无 | operation template | 人工建模第一步 |
| `operation_template.execution_steps` | `list[str]` | 是 | `[]` | operation template | 执行层步骤，不包含软件命令 |
| `zone_mapping` | `list[object]` | 是 | `[]` | converter | 把 placement zone 转成执行区域语义 |
| `zone_mapping[].input_zone` | `str` | 是 | 无 | OperationPlan V2 | 原始 placement zone |
| `zone_mapping[].zone_role` | `str` | 是 | `unknown_zone` | converter | 区域角色 |
| `zone_mapping[].execution_hint` | `str` | 是 | `保守处理该区域。` | converter | 区域执行提示 |
| `automation_assessment` | `object` | 是 | 无 | converter/template | 判断自动化难度和阻塞条件 |
| `automation_assessment.difficulty` | `str` | 是 | `unknown` | operation template | 自动化难度 |
| `automation_assessment.blocked_by` | `list[str]` | 是 | `[]` | converter/template | 当前阻塞原因 |
| `automation_assessment.v0_4_candidate` | `bool` | 是 | `false` | operation template | 是否适合 V0.4 优先自动化 |
| `risk_review` | `object` | 是 | 无 | converter/risk_notes | 结构化风险复核 |
| `risk_review.risk_level` | `str` | 是 | `unknown` | converter | 风险等级 |
| `risk_review.risk_reasons` | `list[str]` | 是 | `[]` | OperationPlan V2 | 风险原因，优先来自 `risk_notes` |
| `risk_review.mitigation_steps` | `list[str]` | 是 | `[]` | converter/template | 保守缓解步骤 |
| `execution_brief` | `str` | 是 | `""` | converter | 面向用户和执行层的简短说明 |

V0.3 枚举契约：

- `tool_family`: `surface_detailing`、`armor_composition`、`mechanical_attachment`、`propulsion_detailing`、`sensor_detailing`、`damage_weathering`
- `automation_level`: `manual_guided`、`semi_automatable`、`automation_candidate`、`blocked_until_mesh`、`not_recommended`
- `difficulty`: `low`、`medium`、`high`、`unknown`
- `risk_level`: `low`、`medium`、`high`、`unknown`
- `zone_role`: `primary_visible_surface`、`edge_detail_zone`、`joint_sensitive_zone`、`mounting_zone`、`damage_zone`、`sensor_orientation_zone`、`unknown_zone`

字段契约边界：

- Execution Blueprint 不替代 OperationPlan V2，只作为后续执行层准备结构。
- V0.3 不把 Execution Blueprint 接入主 CLI，先保持独立转换和独立测试。
- `execution_steps` 只能描述建模意图和步骤，不能输出 Blender Python、CAD 命令或真实几何操作。
- `blocked_by` 使用短标签，例如 `no_real_mesh`、`no_surface_boundaries`、`no_part_connection_points`、`no_joint_range_data`、`no_thickness_data`、`no_mounting_surface`、`no_scale_parameters`。
- `risk_review` 是保守复核，不输出精确工程结论。

## 6. 工具族定义

V0.3 建议先定义以下工具族：

| tool_family | 适用操作 | 说明 |
|---|---|---|
| `surface_detailing` | panel lines、parting lines、surface refine | 表面线条、浅刻线、分件线和细化 |
| `armor_composition` | armor layers、vents | 装甲层次、散热口、表面结构重组 |
| `mechanical_attachment` | pipes、hydraulic rods、weapon mounts | 外挂机械结构、连接件和承力点 |
| `propulsion_detailing` | thrusters | 喷口、推进器、背包推进结构 |
| `sensor_detailing` | sensors | 摄像头、传感器、监视器和小型设备 |
| `damage_weathering` | surface damage、weathering | 战损、旧化、磨损和浅表痕迹 |

## 7. 自动化等级

| automation_level | 含义 |
|---|---|
| `manual_guided` | 当前只能给设计师步骤建议 |
| `semi_automatable` | 后续有真实 mesh 后可半自动生成路径或辅助对象 |
| `automation_candidate` | 适合 V0.4 优先尝试脚本化 |
| `blocked_until_mesh` | 必须等待真实模型文件和表面边界 |
| `not_recommended` | 当前不建议自动化，容易破坏结构或语义 |

## 8. 自动化难度

| difficulty | 判断标准 |
|---|---|
| `low` | 主要是文本模板、标记或简单对象放置 |
| `medium` | 需要区域识别、曲线路径或简单几何依赖 |
| `high` | 需要真实 mesh、布尔、拓扑、厚度或装配判断 |
| `unknown` | 输入信息不足，无法判断 |

## 9. 风险等级

| risk_level | 含义 |
|---|---|
| `low` | 只有一般设计注意事项 |
| `medium` | 可能影响打印清晰度、装配或可读性 |
| `high` | 可能削弱结构、影响关节或明显依赖真实 mesh |
| `unknown` | 缺少判断依据 |

## 10. 11 个 operation 的执行模板

### 10.1 `add_panel_lines`

- 工具族：`surface_detailing`
- 推荐方法：`engraved_line_layout`
- 自动化难度：`medium`
- 适合 V0.4：是
- 依赖：真实表面边界、可见面方向、比例信息
- 手工第一步：在主要可见装甲面上标记线条路径
- 主要风险：刻线过密、比例下不可读、穿过关键结构

### 10.2 `add_parting_lines`

- 工具族：`surface_detailing`
- 推荐方法：`parting_line_planning`
- 自动化难度：`medium`
- 适合 V0.4：是
- 依赖：部件边界、装甲板块关系、比例信息
- 手工第一步：确定分件线是否符合装甲板块逻辑
- 主要风险：分件线破坏主体轮廓或与关节区域冲突

### 10.3 `add_armor_layers`

- 工具族：`armor_composition`
- 推荐方法：`layered_plate_blockout`
- 自动化难度：`high`
- 适合 V0.4：部分适合
- 依赖：轮廓边界、厚度、遮挡关系
- 手工第一步：先确定主装甲层和副装甲层的覆盖关系
- 主要风险：叠甲过厚、比例失衡、遮挡关节

### 10.4 `add_vents`

- 工具族：`armor_composition`
- 推荐方法：`recessed_vent_layout`
- 自动化难度：`medium`
- 适合 V0.4：是
- 依赖：平面区域、开孔方向、打印尺度
- 手工第一步：选择不削弱主承力区域的位置
- 主要风险：小比例开槽不清晰或削弱薄壁

### 10.5 `add_thrusters`

- 工具族：`propulsion_detailing`
- 推荐方法：`thruster_component_placement`
- 自动化难度：`high`
- 适合 V0.4：部分适合
- 依赖：安装空间、推进方向、部件连接面
- 手工第一步：确认喷口方向和背包/腿部结构逻辑
- 主要风险：喷口方向不合理、与现有结构穿插

### 10.6 `add_pipes`

- 工具族：`mechanical_attachment`
- 推荐方法：`curve_pipe_routing`
- 自动化难度：`medium`
- 适合 V0.4：是
- 依赖：起止点、避障区域、管径比例
- 手工第一步：先标记管线起点和终点
- 主要风险：管线悬空、穿过关节或装甲边界

### 10.7 `add_hydraulic_rods`

- 工具族：`mechanical_attachment`
- 推荐方法：`piston_pair_layout`
- 自动化难度：`medium`
- 适合 V0.4：是
- 依赖：关节轴线、伸缩方向、连接点
- 手工第一步：确认液压杆的上下连接端点
- 主要风险：影响可动范围、方向不符合结构逻辑

### 10.8 `add_sensors`

- 工具族：`sensor_detailing`
- 推荐方法：`sensor_module_placement`
- 自动化难度：`low`
- 适合 V0.4：是
- 依赖：可见面、朝向、尺寸比例
- 手工第一步：确认传感器朝向和观察用途
- 主要风险：小件过薄或比例不协调

### 10.9 `add_weapon_mounts`

- 工具族：`mechanical_attachment`
- 推荐方法：`hardpoint_mount_layout`
- 自动化难度：`high`
- 适合 V0.4：谨慎
- 依赖：承力面、连接标准、武器尺寸
- 手工第一步：确认挂点是否位于合理承力结构上
- 主要风险：挂点无支撑、影响姿态或装配

### 10.10 `add_surface_damage`

- 工具族：`damage_weathering`
- 推荐方法：`shallow_damage_marking`
- 自动化难度：`high`
- 适合 V0.4：谨慎
- 依赖：表面厚度、法线、局部结构强度
- 手工第一步：先标记浅表损伤区域，不直接切深缺口
- 主要风险：削弱薄件、破坏风格统一

### 10.11 `refine_surface`

- 工具族：`surface_detailing`
- 推荐方法：`surface_cleanup_pass`
- 自动化难度：`medium`
- 适合 V0.4：部分适合
- 依赖：已有细节分布、表面噪声、风格目标
- 手工第一步：区分需要保留的结构线和需要弱化的杂线
- 主要风险：过度清理导致机械层次变弱

## 11. 常见部件区域模板

### 11.1 `chest_armor`

- `upper_chest_plate`：胸甲上缘主要可见面
- `center_front_panel`：胸口中心面板
- `around_cockpit_hatch`：驾驶舱舱门周边
- `lower_chest_edge`：胸甲下缘，需注意腰部活动区

### 11.2 `backpack`

- `rear_equipment_block`：背包主设备块
- `thruster_surrounds`：喷口周边
- `side_mount_points`：侧向挂载点
- `top_accessory_area`：顶部附属结构区

### 11.3 `leg`

- `outer_armor_surface`：腿部外侧装甲面
- `inner_frame_exposure`：可见内构区域
- `joint_surrounds`：膝、踝等关节周边
- `calf_side_panel`：小腿侧装甲面

### 11.4 `shield`

- `front_plate`：盾牌正面板
- `outer_edges`：盾牌外缘
- `mounting_back`：背面连接区
- `damage_safe_zone`：适合浅表战损的非承力区域

### 11.5 `antenna`

- `main_fin_surface`：天线主翼面
- `root_connection`：根部连接区
- `tip_area`：尖端区域，通常不建议添加高密度细节

## 12. V0.3 验收用例

### 12.1 胸甲分件线执行蓝图

输入 OperationPlan：`chest_armor + add_parting_lines + 1/144`

必须输出：

- `tool_family`: `surface_detailing`
- `recommended_method`: `parting_line_planning`
- `difficulty`: `medium`
- `requires_mesh_access`: `true`
- `risk_level`: `medium` 或 `high`

### 12.2 背包推进器执行蓝图

输入 OperationPlan：`backpack + add_thrusters + high_mobility`

必须输出：

- `tool_family`: `propulsion_detailing`
- 推荐方法与喷口组件或推进器放置有关
- 阻塞原因包含安装空间或真实连接面缺失

### 12.3 腿部管线执行蓝图

输入 OperationPlan：`leg + add_pipes/add_hydraulic_rods + group_sync`

必须输出：

- `tool_family`: `mechanical_attachment`
- 推荐方法与曲线路径或液压杆连接端点有关
- 风险包含关节活动范围

### 12.4 盾牌战损执行蓝图

输入 OperationPlan：`shield + add_surface_damage + low`

必须输出：

- `tool_family`: `damage_weathering`
- 自动化难度为 `high`
- `execution_brief` 强调浅表、克制、不直接深切

### 12.5 传感器执行蓝图

输入 OperationPlan：`head/camera_sensor + add_sensors`

必须输出：

- `tool_family`: `sensor_detailing`
- 自动化难度为 `low` 或 `medium`
- 输出朝向和可见面相关提示

## 13. V0.4 前置条件

V0.3 完成后，如果要进入 V0.4 Blender/Fusion 半自动执行，需要先准备：

- 真实模型文件加载方式。
- 部件与 mesh 对象的绑定关系。
- placement zone 与 mesh 区域的映射方式。
- 曲线路径、连接点、朝向和尺寸的参数表达。
- 操作失败时的回滚或预览机制。
- 用户确认机制，避免自动破坏模型。

## 14. 建议开发顺序

V0.3 开发不应一开始就改动 V0.2 主链路。建议顺序如下：

1. 冻结 Execution Blueprint 字段。
2. 为 11 个 operation 建立模板表。
3. 为常见部件建立 placement zone 语义表。
4. 新增 execution blueprint prompt。
5. 实现独立转换器，不接入主 CLI。
6. 用 5 条 V0.3 验收用例验证转换结果。
7. 再决定是否接入 `run_agent()` 输出。

## 15. LLM 候选路径

V0.3 当前保留一个 LLM 候选 prompt：

```text
3d_agent/prompts/v0_3_execution_blueprint_prompt_draft.txt
```

该 prompt 与本文件第 5 节字段契约保持一致，用于后续探索 LLM 型转换器。V0.3 初期不把该 prompt 接入主流程，也不依赖 LLM 完成验收。当前优先实现规则型转换器，确保输出稳定、可测试、可回归。

## 16. 默认 CLI 接入

V0.3 Phase 2 已将 Execution Blueprint 接入默认 `model_edit` 输出。V0.2 的 OperationPlan V2 字段仍然保留在顶层，Execution Blueprint 作为额外字段附加在同一份 JSON 中，为 V0.4 执行层开发提供默认输入。

命令形式：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。"
```

行为约定：

- 对 `model_edit` 命令，默认 JSON 会包含 OperationPlan V2 顶层字段和 `execution_blueprint`。
- 对 `inspect_context` 和 `explain_capability` 等非模型编辑命令，不附加 Execution Blueprint。
- 该接入只输出执行准备蓝图，不执行 Blender、不读取 mesh、不生成真实几何。

## 17. 完成定义

V0.3 只有在同时满足以下条件时才算完成：

- 每个 V0.2 operation 都能映射到执行模板。
- 输出包含工具族、推荐方法、自动化等级、难度、风险和执行摘要。
- 高风险或缺少 mesh 的操作能明确说明阻塞原因。
- OperationPlan V2 顶层字段仍然保留，Execution Blueprint 作为默认附加层输出。
- 不引入真实建模执行。
- 有独立 prompt 和验收用例。