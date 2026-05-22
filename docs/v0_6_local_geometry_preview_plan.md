# V0.6 局部几何预览与安全执行计划

## 1. 阶段定位

V0.6 承接 V0.5 的真实模型对象绑定结果，目标是让 Agent 第一次进入“可视化预览”和“真实软件接口调用前安全设计”阶段，但仍不直接修改真实 mesh。

产品路径：

```text
V0.2：自然语言 -> OperationPlan V2 操作蓝图
V0.3：OperationPlan V2 -> Execution Blueprint 执行蓝图
V0.4：Execution Blueprint -> Execution Package 半自动执行包
V0.5：真实模型上下文读取 -> 部件对象绑定 -> 执行包阻塞项复核
V0.6：绑定对象 -> 局部几何预览计划 -> 安全预览脚本草案 -> 回滚契约
```

V0.6 的核心问题不是“自动把刻线布尔到模型上”，而是回答：

```text
在已经知道目标 Blender 对象是谁的前提下，如何安全地把即将发生的局部几何操作预览出来，并让用户确认？
```

V0.6 第一版应当把真实几何修改继续后置，只生成可审查、可删除、可回滚的预览层。

## 2. V0.6 目标

V0.6 完成后，系统应该能够：

- 接收 V0.4 `execution_package`、V0.5 `model_binding_context` 和 `execution_package_review`。
- 判断当前执行包是否允许进入预览阶段。
- 把执行任务转换成局部几何预览计划。
- 输出机器可读的 `Geometry Preview Plan`。
- 生成 Blender 预览脚本草案，用于创建独立的预览集合、标记线、占位体或注释对象。
- 明确哪些操作只是预览，哪些仍被几何级 blocker 阻止。
- 为后续真实软件接口调用建立安全约束、确认机制和回滚契约。

V0.6 的直接价值是让用户在 Blender 中看到“将要在哪个对象、哪个区域、以什么形式添加细节”的可视化提示，而不是只看 JSON 或文字摘要。

## 3. 不做范围

V0.6 第一版明确不做以下内容：

- 不自动修改目标 mesh 顶点、边、面。
- 不执行布尔切割、真实刻线、挤出、重拓扑或 modifier apply。
- 不删除用户已有对象。
- 不保存 `.blend` 文件。
- 不把预览结果当作最终模型结果。
- 不绕过 `execution_package_review` 中的剩余 blocker。
- 不在普通 Python CLI 中直接 `import bpy` 或运行 Blender。
- 不依赖 LLM 生成核心几何操作代码。
- 不承诺 preview element 的位置已经贴合真实拓扑表面。

V0.6 可以生成 Blender Python 脚本草案，但脚本只应创建可识别、可删除的预览对象。真实几何修改应放到 V0.7 或更后阶段，并且必须建立用户确认和回滚机制。

## 4. 为什么先做预览层

V0.5 已经知道抽象部件对应哪些真实对象，但还不知道真实表面边界、法线、厚度、碰撞和关节活动范围。如果此时直接做几何修改，风险很高：

- 刻线可能落在错误表面。
- 装甲分层可能穿透或悬空。
- 推进器占位可能覆盖连接面。
- 管线和液压杆可能影响关节活动。
- 自动脚本一旦修改 mesh，回滚成本明显变高。

因此 V0.6 先引入预览层：

```text
执行包 -> 绑定对象 -> 预览计划 -> Blender 预览草案 -> 用户确认
```

这个阶段产生的是“可视化确认材料”，不是最终几何。

## 5. 输入与输出关系

### 5.1 输入一：Execution Package

来自 V0.4，提供任务拆解、执行模式、required inputs、blocked_by 和用户检查点。

重点字段：

- `target_part`
- `execution_mode`
- `execution_tasks`
- `required_inputs`
- `blocked_by`
- `user_checkpoints`

### 5.2 输入二：Model Binding Context

来自 V0.5，提供抽象部件和真实场景对象的绑定关系。

重点字段：

- `target_part`
- `bindings`
- `binding_status`
- `confidence`
- `object_name`
- `resolved_inputs`
- `remaining_blockers`

### 5.3 输入三：Execution Package Review

来自 V0.5，用于判断执行包当前能否进入预览。

重点字段：

- `review_status`
- `bound_objects`
- `resolved_inputs`
- `unresolved_inputs`
- `remaining_blockers`
- `review_notes`

### 5.4 输出一：Geometry Preview Plan

V0.6 的核心机器可读输出。它描述预览对象、预览模式、目标绑定对象、安全状态和剩余阻塞项。

建议字段：

```json
{
  "preview_version": "v0_6",
  "source_package_ref": "execution_package",
  "source_binding_ref": "model_binding_context",
  "source_review_ref": "execution_package_review",
  "target_part": "chest_armor",
  "preview_mode": "annotation_overlay",
  "preview_status": "preview_ready",
  "target_objects": ["ChestArmor_Upper_01"],
  "preview_elements": [],
  "required_confirmations": [],
  "blocked_by": [],
  "safety_rules": [],
  "rollback_plan": [],
  "preview_summary": ""
}
```

### 5.5 输出二：Blender Preview Script Draft

可选输出，用于在 Blender 中创建预览集合和预览对象。

脚本第一版只允许：

- 创建独立 collection，例如 `V06_chest_armor_preview`。
- 创建 empty、curve、text note、wireframe placeholder 等预览对象。
- 给生成对象写入 `v0_6_preview_session_id`、`source_task_id`、`target_object` 等自定义属性。
- 输出预览摘要。

脚本第一版禁止：

- 修改已绑定目标对象的 mesh data。
- 修改用户已有材质。
- apply modifier。
- boolean operation。
- 删除用户已有对象。
- 保存 `.blend` 文件。

## 6. Geometry Preview Plan 字段契约

### 6.1 顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `preview_version` | string | 固定为 `v0_6` |
| `source_package_ref` | string | 默认 `execution_package` |
| `source_binding_ref` | string | 默认 `model_binding_context` |
| `source_review_ref` | string | 默认 `execution_package_review` |
| `target_part` | string | 抽象目标部件 |
| `preview_mode` | string | 预览模式 |
| `preview_status` | string | 预览状态 |
| `target_objects` | list[string] | 可预览的真实对象名 |
| `preview_elements` | list[object] | 预览元素列表 |
| `required_confirmations` | list[string] | 用户必须确认的事项 |
| `blocked_by` | list[string] | 阻止进入更高等级预览或真实执行的原因 |
| `safety_rules` | list[string] | 脚本和后续执行必须遵守的安全规则 |
| `rollback_plan` | list[string] | 回滚策略 |
| `preview_summary` | string | 用户可读摘要 |

### 6.2 `preview_mode` 枚举

- `annotation_overlay`：只创建注释、empty 和区域标记。
- `bounding_box_overlay`：基于对象 bounds 创建预览线框或占位体。
- `surface_anchor_placeholder`：生成需要用户手动对齐的表面锚点。
- `risk_marker_only`：只标记风险区域，不生成操作预览。
- `blocked`：无法生成可信预览。

第一版默认优先使用 `annotation_overlay` 和 `bounding_box_overlay`。只要缺少真实表面边界，就不能升级成真实贴面几何。

### 6.3 `preview_status` 枚举

- `preview_ready`：绑定对象可信，允许生成预览对象。
- `needs_user_confirmation`：有候选绑定或重要几何信息缺失，只能生成需要确认的预览。
- `blocked`：无可信绑定对象或输入不足，不能生成预览。

### 6.4 Preview Element 字段

字段：

```json
{
  "element_id": "preview_001",
  "source_task_id": "task_001",
  "element_type": "panel_line_hint",
  "target_object": "ChestArmor_Upper_01",
  "target_zone": "upper_center",
  "reference_frame": "object_bounds",
  "placement_hint": {
    "axis": "x",
    "normalized_position": [0.0, 0.0, 0.5]
  },
  "visual_style": {
    "color": "warning_blue",
    "display": "curve_overlay"
  },
  "intent": "Preview a sharp panel line before any mesh edit.",
  "requires_user_confirmation": true
}
```

### 6.5 `element_type` 枚举

- `panel_line_hint`
- `surface_detail_hint`
- `placeholder_volume`
- `mounting_point_hint`
- `risk_marker`
- `manual_review_note`
- `symmetry_reference`

## 7. 预览生成规则

### 7.1 从 Execution Task 到 Preview Element

建议第一版规则：

| V0.4 task_type | V0.6 element_type | 默认 preview_mode |
|---|---|---|
| `create_annotation` | `manual_review_note` | `annotation_overlay` |
| `mark_risk_zone` | `risk_marker` | `risk_marker_only` |
| `place_placeholder` | `placeholder_volume` | `bounding_box_overlay` |
| `manual_review` | `manual_review_note` | `annotation_overlay` |
| surface/detail related task | `surface_detail_hint` | `annotation_overlay` |

如果任务包含 `target_zone`，则写入 preview element。若没有真实表面坐标，只能用 `object_bounds` 或 `manual_anchor` 作为 reference frame。

### 7.2 预览状态判定

- 如果没有 `bound` 且 `confidence >= 0.90` 的绑定对象，`preview_status = blocked`。
- 如果存在 `candidate` 或 `ambiguous`，`preview_status = needs_user_confirmation`。
- 如果有可信绑定对象，但仍有 `no_surface_boundaries`、`no_joint_range_data`、`no_mounting_surface` 等几何级 blocker，仍可生成注释或包围盒预览，但不能生成真实贴面预览。
- 如果 `review_status = blocked`，只能输出阻塞摘要，不生成可执行预览脚本。

### 7.3 安全规则

每个 Geometry Preview Plan 都应包含安全规则：

- `preview_only`
- `do_not_modify_bound_mesh`
- `do_not_apply_modifiers`
- `do_not_save_blend_file`
- `generated_objects_must_be_tagged`
- `generated_objects_must_be_in_preview_collection`

## 8. 安全执行会话契约草案

V0.6 可以先定义安全执行会话，不必马上接入真实运行。

建议对象：`Safe Preview Session`

字段草案：

```json
{
  "session_version": "v0_6",
  "session_id": "v06_chest_armor_preview_001",
  "execution_mode": "preview_only",
  "target_software": "blender",
  "allowed_operations": [],
  "forbidden_operations": [],
  "preflight_checks": [],
  "generated_artifacts": [],
  "rollback_strategy": []
}
```

第一版 allowed operations：

- 创建 preview collection。
- 创建 generated preview object。
- 给 generated preview object 写自定义属性。
- 写出 preview report JSON。

第一版 forbidden operations：

- 编辑 bound mesh。
- 删除用户已有对象。
- 保存 `.blend`。
- apply modifier。
- boolean operation。
- 导出最终生产模型。

## 9. CLI 接入建议

V0.6 建议继续使用显式参数，不改变默认输出。

建议参数：

```text
--geometry-preview
--preview-script-draft
```

建议行为：

- 默认命令仍保持 V0.3 输出。
- `--execution-package` 仍只输出 V0.4 `execution_package`。
- `--scene-manifest <path>` 仍输出 V0.5 `model_binding_context` 和 `execution_package_review`。
- `--geometry-preview` 需要 `--scene-manifest <path>`，否则无法确定真实目标对象。
- `--preview-script-draft` 隐含 `--geometry-preview`，并生成 Blender 预览脚本草案。
- 对 `inspect_context` 等非模型编辑命令，不附加 V0.6 字段。

示例：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --geometry-preview --preview-script-draft
```

预期输出新增：

- `geometry_preview_plan`
- `safe_preview_session`
- `blender_preview_script_draft`

## 10. 建议模块设计

### 10.1 Geometry Preview Planner

建议模块：

```text
3d_agent/agent/geometry_preview.py
```

职责：

- 接收 `execution_package`、`model_binding_context`、`execution_package_review`。
- 生成 `geometry_preview_plan`。
- 根据绑定状态和 blocker 决定 preview status。
- 将 V0.4 task 转成 V0.6 preview element。

核心函数建议：

```text
create_geometry_preview_plan(execution_package, model_binding_context, execution_package_review)
```

### 10.2 Safe Preview Session Builder

建议模块：

```text
3d_agent/agent/safe_preview_session.py
```

职责：

- 根据 `geometry_preview_plan` 生成安全会话契约。
- 输出 allowed operations、forbidden operations、preflight checks 和 rollback strategy。

核心函数建议：

```text
create_safe_preview_session(geometry_preview_plan)
```

### 10.3 Blender Preview Script Draft

建议模块：

```text
3d_agent/agent/blender_preview_script_draft.py
```

职责：

- 根据 `geometry_preview_plan` 和 `safe_preview_session` 生成 Blender Python 预览脚本草案。
- 只创建 preview collection 和 generated preview objects。
- 保证脚本文案和测试中都明确不修改真实 mesh。

核心函数建议：

```text
create_blender_preview_script_draft(geometry_preview_plan, safe_preview_session)
```

### 10.4 CLI 接入

建议更新：

```text
3d_agent/main.py
```

职责：

- 解析 `--geometry-preview` 和 `--preview-script-draft`。
- 在存在 `--scene-manifest <path>` 且命令类型为 `model_edit` 时附加 V0.6 输出。
- 保持非模型编辑命令不附加 V0.6 字段。

## 11. 建议开发顺序

### Step 0：V0.6 范围确认

确认 V0.6 第一版只做局部几何预览计划、安全预览会话和 Blender 预览脚本草案，不做真实 mesh 修改。

输出：本计划确认版。

### Step 1：确认 Geometry Preview Plan 字段契约

固定顶层字段、preview element 字段、枚举、默认值和阻塞规则。

输出：字段契约确认表。

### Step 2：实现规则型 Geometry Preview Planner

新增 `geometry_preview.py`，将 V0.4 execution task 转成 V0.6 preview element。

输出：`create_geometry_preview_plan(...)`。

### Step 3：实现 Safe Preview Session Builder

新增 `safe_preview_session.py`，把预览计划转换成安全会话契约。

输出：`create_safe_preview_session(...)`。

### Step 4：实现 Blender Preview Script Draft

新增 `blender_preview_script_draft.py`，生成只创建预览对象的 Blender Python 脚本草案。

输出：`create_blender_preview_script_draft(...)`。

### Step 5：CLI 可选接入

新增 `--geometry-preview` 和 `--preview-script-draft`。必须显式启用，不改变默认输出。

输出：CLI 可选预览输出。

### Step 6：V0.6 验收

用固定样例 manifest、V0.4 execution package 和 V0.5 binding review 验证预览计划、安全会话、脚本草案和默认输出隔离。

输出：验收报告。

## 12. V0.6 验收用例

### 12.1 胸甲分件线预览

输入：胸甲分件线需求，manifest 中存在 `ChestArmor_Upper_01`。

必须输出：

- `preview_status = preview_ready`。
- `target_objects` 包含 `ChestArmor_Upper_01`。
- 至少 1 个 `panel_line_hint` 或 `surface_detail_hint`。
- `safety_rules` 包含 `do_not_modify_bound_mesh`。
- `blocked_by` 仍保留几何级 blocker，例如 `no_surface_boundaries`。

### 12.2 背包推进器占位预览

输入：背包推进器强化需求。

必须输出：

- `preview_mode` 可以是 `bounding_box_overlay` 或 `annotation_overlay`。
- 包含 `placeholder_volume` 或 `mounting_point_hint`。
- 不解除 `no_mounting_surface`。
- 脚本草案只创建 generated preview object。

### 12.3 腿部液压杆风险预览

输入：两条腿加管线和液压杆。

必须输出：

- 支持多个 target object。
- 包含 `risk_marker` 或 `manual_review_note`。
- 保留 `no_joint_range_data`。
- `required_confirmations` 提示用户确认关节活动范围。

### 12.4 无可信绑定时阻塞预览

输入：manifest 中没有可信目标对象。

必须输出：

- `preview_status = blocked`。
- 不生成 Blender preview script draft 或脚本只输出阻塞说明。
- 不产生可执行 preview element。

### 12.5 非模型编辑命令隔离

输入：`现在有哪些部件？ --geometry-preview`。

必须输出：

- `command_type = inspect_context`。
- 不附加 `geometry_preview_plan`。
- 不附加 `safe_preview_session`。
- 不附加 `blender_preview_script_draft`。

### 12.6 Blender 预览脚本安全检查

输入：生成 Blender preview script draft。

必须输出：

- 脚本包含只读和预览用途说明。
- 脚本只创建独立 preview collection 和 generated preview objects。
- 脚本不包含 mesh 修改、modifier apply、boolean、删除用户对象或保存 `.blend`。

## 13. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 用户误以为预览就是最终几何 | 期望偏差 | 输出中持续使用 `preview_only` 和确认提示 |
| 预览位置不贴合真实拓扑 | 误导建模判断 | 第一版只使用 `object_bounds`、注释和手动锚点，不声称精确贴面 |
| 脚本误修改用户对象 | 数据风险 | 测试禁止 mesh edit、modifier apply、delete、save 等操作 |
| 绑定错误导致预览落错对象 | 用户判断成本上升 | 只有高置信度 `bound` 才进入 `preview_ready` |
| 回滚不完整 | 清理困难 | 所有生成对象必须打 tag 并放入独立 preview collection |
| CLI 参数变复杂 | 使用门槛提升 | V0.6 参数必须显式启用，默认输出不变 |

## 14. V0.6 完成定义

V0.6 只有在同时满足以下条件时才算完成：

- 有 Geometry Preview Plan 字段契约。
- 能从 V0.4 execution package、V0.5 binding context 和 package review 生成预览计划。
- 能生成 Safe Preview Session 契约。
- 能生成 Blender preview script draft。
- 脚本草案只创建预览对象，不修改目标 mesh。
- CLI 可通过显式参数输出 V0.6 字段。
- 非模型编辑命令不附加 V0.6 字段。
- V0.4 和 V0.5 默认行为不被破坏。
- 至少 6 条 V0.6 验收用例通过。
- 全量测试通过。

## 15. V0.6 之后的方向

V0.6 完成后，可以进入 V0.7：真实软件接口调用与受控应用。

V0.7 才适合讨论：

- 用户确认后的真实 Blender command execution。
- 局部非破坏性 modifier stack。
- 可撤销操作包。
- 自动备份和恢复。
- 更精确的 surface anchor、法线和边界读取。
- 受控的真实几何修改。

## 16. Step 0 范围确认结果

V0.6 第一版范围确认如下：

```text
V0.5 绑定对象 -> V0.6 局部预览计划 -> 安全预览会话 -> Blender 预览脚本草案
```

本阶段确认要做：

- 基于 V0.4 `execution_package`、V0.5 `model_binding_context` 和 `execution_package_review` 生成 `Geometry Preview Plan`。
- 只把执行任务转换成预览元素，例如分件线提示、表面细节提示、占位体、风险标记和人工复核注释。
- 生成 `Safe Preview Session`，明确允许操作、禁止操作、预检查和回滚策略。
- 生成 Blender preview script draft，只创建独立 preview collection 和 generated preview objects。
- 通过显式 CLI 参数接入，例如 `--geometry-preview` 和 `--preview-script-draft`。
- 保持 V0.3、V0.4、V0.5 默认输出不变。

本阶段确认不做：

- 不修改目标 mesh 的顶点、边或面。
- 不执行真实布尔、刻线、挤出、重拓扑或 modifier apply。
- 不删除用户已有对象。
- 不保存 `.blend` 文件。
- 不在普通 CLI 环境中直接运行 Blender 或 `import bpy`。
- 不绕过 V0.5 `execution_package_review` 中保留的几何级 blocker。
- 不把预览对象当成最终生产模型。
- 不依赖 LLM 生成核心几何操作代码。

进入 Step 1 的条件：

- `Geometry Preview Plan` 是 V0.6 的主契约。
- `Safe Preview Session` 是脚本草案和后续真实软件接口调用的安全边界。
- Blender preview script draft 只能创建可识别、可删除、可回滚的预览对象。
- `preview_ready` 只代表可以生成预览，不代表可以真实修改 mesh。
- 真实几何修改继续后置到 V0.7 或更后阶段。

Step 0 结论：已确认，可以进入 Step 1 Geometry Preview Plan 字段契约确认。

## 17. Step 1 Geometry Preview Plan 字段契约确认结果

V0.6 第一版 `Geometry Preview Plan` 字段契约已确认。它是 V0.6 的主输出对象，用于描述“可以在哪里生成什么预览对象，以及为什么仍不能真实修改 mesh”。

顶层字段固定为：

| 字段 | 类型 | 默认值或约束 | 说明 |
|---|---|---|---|
| `preview_version` | string | 固定 `v0_6` | V0.6 预览计划版本 |
| `source_package_ref` | string | `execution_package` | V0.4 输入引用 |
| `source_binding_ref` | string | `model_binding_context` | V0.5 绑定结果引用 |
| `source_review_ref` | string | `execution_package_review` | V0.5 阻塞项复核引用 |
| `target_part` | string | 必填 | 抽象目标部件 |
| `preview_mode` | string | 枚举 | 预览模式 |
| `preview_status` | string | 枚举 | 当前是否允许生成预览 |
| `target_objects` | list[string] | 默认空列表 | 可用于预览的真实对象名 |
| `preview_elements` | list[object] | 默认空列表 | 预览元素列表 |
| `required_confirmations` | list[string] | 默认空列表 | 用户必须确认的事项 |
| `blocked_by` | list[string] | 默认空列表 | 阻止真实执行或更高等级预览的原因 |
| `safety_rules` | list[string] | 默认安全规则 | 脚本和后续执行必须遵守的规则 |
| `rollback_plan` | list[string] | 默认回滚策略 | 删除或撤销预览对象的方法 |
| `preview_summary` | string | 必填 | 用户可读摘要 |

`preview_mode` 固定枚举：

- `annotation_overlay`：注释、empty、文字说明和区域标记。
- `bounding_box_overlay`：基于对象 bounds 的线框或占位体预览。
- `surface_anchor_placeholder`：需要用户手动对齐的表面锚点。
- `risk_marker_only`：只标记风险区域。
- `blocked`：无法生成可信预览。

`preview_status` 固定枚举：

- `preview_ready`：存在可信绑定对象，允许生成预览对象。
- `needs_user_confirmation`：存在候选绑定或关键几何信息缺失，只允许生成需要确认的预览。
- `blocked`：无可信绑定对象、输入不足或 V0.5 review 已阻塞，不生成可执行预览元素。

Preview Element 字段固定为：

| 字段 | 类型 | 默认值或约束 | 说明 |
|---|---|---|---|
| `element_id` | string | 必填 | V0.6 预览元素 ID |
| `source_task_id` | string | 可为空字符串 | 对应 V0.4 execution task |
| `element_type` | string | 枚举 | 预览元素类型 |
| `target_object` | string | 可为空字符串 | 绑定的 Blender 对象名 |
| `target_zone` | string | 可为空字符串 | 来自 V0.4 task 的目标区域 |
| `reference_frame` | string | 枚举 | 预览定位参考系 |
| `placement_hint` | object | 默认空对象 | 归一化位置、方向或尺寸提示 |
| `visual_style` | object | 默认空对象 | 颜色、显示方式、线型等视觉提示 |
| `intent` | string | 必填 | 用户可读的预览意图 |
| `requires_user_confirmation` | bool | 默认 `true` | 是否必须用户确认 |

`element_type` 固定枚举：

- `panel_line_hint`
- `surface_detail_hint`
- `placeholder_volume`
- `mounting_point_hint`
- `risk_marker`
- `manual_review_note`
- `symmetry_reference`

`reference_frame` 固定枚举：

- `object_bounds`：基于绑定对象包围盒。
- `manual_anchor`：需要用户在 Blender 中手动移动到目标表面。
- `binding_origin`：使用绑定对象原点。
- `collection_center`：使用目标对象集合或对象组中心。
- `unknown`：缺少可信定位信息。

默认 `safety_rules` 固定为：

- `preview_only`
- `do_not_modify_bound_mesh`
- `do_not_apply_modifiers`
- `do_not_save_blend_file`
- `generated_objects_must_be_tagged`
- `generated_objects_must_be_in_preview_collection`

默认 `rollback_plan` 固定为：

- 删除带有 `v0_6_preview_session_id` 的 generated preview objects。
- 删除空的 V0.6 preview collection。
- 保留用户原始对象和材质不变。

状态判定规则确认：

- `review_status = blocked` 时，`preview_status = blocked`。
- 没有 `bound` 且 `confidence >= 0.90` 的绑定对象时，`preview_status = blocked`。
- 只有 `candidate` 或 `ambiguous` 绑定时，`preview_status = needs_user_confirmation`。
- 有可信绑定对象但仍有几何级 blocker 时，可以进入 `preview_ready`，但只能生成注释、包围盒或手动锚点预览。
- `preview_ready` 不代表允许真实修改 mesh，只代表可以生成预览对象。

Step 1 结论：字段契约已确认，可以进入 Step 2 规则型 Geometry Preview Planner 实现。

## 18. Step 2 规则型 Geometry Preview Planner 实现结果

V0.6 规则型 Geometry Preview Planner 已完成第一版实现。

新增模块：

```text
3d_agent/agent/geometry_preview.py
```

核心函数：

```text
create_geometry_preview_plan(execution_package, model_binding_context, execution_package_review)
```

输入对象：

- V0.4 `execution_package`
- V0.5 `model_binding_context`
- V0.5 `execution_package_review`

输出对象：

- V0.6 `geometry_preview_plan`

第一版实现规则：

- `review_status = blocked` 时输出 `preview_status = blocked`，不生成 `preview_elements`。
- 有 `bound` 且 `confidence >= 0.90` 的绑定对象时输出 `preview_status = preview_ready`。
- 只有 `candidate` 或 `ambiguous` 绑定时输出 `preview_status = needs_user_confirmation`。
- `preview_ready` 仍会保留几何级 blocker，例如 `no_surface_boundaries`、`no_mounting_surface`、`no_joint_range_data`。
- V0.4 `execution_tasks` 会转换为 V0.6 `preview_elements`。
- 多个绑定对象会生成对应的多对象预览元素。
- 所有预览元素默认 `requires_user_confirmation = true`。

V0.4 task 到 V0.6 element 的第一版映射：

| V0.4 task_type | V0.6 element_type |
|---|---|
| `create_annotation` | `surface_detail_hint` |
| `create_curve_guide` | `panel_line_hint` |
| `mark_risk_zone` | `risk_marker` |
| `place_placeholder` | `placeholder_volume` 或 `mounting_point_hint` |
| `manual_review` | `manual_review_note` |

默认安全规则：

```text
preview_only
do_not_modify_bound_mesh
do_not_apply_modifiers
do_not_save_blend_file
generated_objects_must_be_tagged
generated_objects_must_be_in_preview_collection
```

新增测试：

```text
tests/test_v0_6_geometry_preview.py
```

测试覆盖：

- 胸甲分件线需求可生成 `preview_ready` 预览计划。
- 背包推进器需求可生成占位或安装点预览。
- 腿部液压杆需求支持左右腿多个绑定对象，并保留关节确认项。
- candidate 绑定会进入 `needs_user_confirmation`。
- blocked review 不生成预览元素。

验证结果：

```text
Ran 5 tests in 0.175s
OK
```

Step 2 结论：已完成，可以进入 Step 3 Safe Preview Session Builder 实现。

## 19. Step 3 Safe Preview Session Builder 实现结果

V0.6 Safe Preview Session Builder 已完成第一版实现。

新增模块：

```text
3d_agent/agent/safe_preview_session.py
```

核心函数：

```text
create_safe_preview_session(geometry_preview_plan)
```

输入对象：

- V0.6 `geometry_preview_plan`

输出对象：

- V0.6 `safe_preview_session`

字段契约：

```text
session_version
session_id
execution_mode
target_software
allowed_operations
forbidden_operations
preflight_checks
generated_artifacts
rollback_strategy
```

第一版实现规则：

- `session_version` 固定为 `v0_6`。
- `execution_mode` 固定为 `preview_only`。
- `target_software` 固定为 `blender`。
- `session_id` 按目标部件和状态生成，例如 `v06_chest_armor_preview_001`。
- `preview_ready` 和 `needs_user_confirmation` 会允许创建 preview collection、generated preview object、tag 和 report。
- `blocked` 只允许写出 preview report JSON，不允许创建 preview collection 或 generated preview object。
- 所有会话都禁止编辑 bound mesh、删除用户对象、保存 `.blend`、apply modifier、boolean 和导出最终生产模型。
- 所有会话都生成 preflight checks，用于确认版本、preview-only 模式、只读目标 mesh、生成对象打 tag、独立 preview collection 和用户确认事项。

第一版允许操作：

```text
create_preview_collection
create_generated_preview_object
tag_generated_preview_object
write_preview_report_json
```

blocked 会话只允许：

```text
write_preview_report_json
```

第一版禁止操作：

```text
edit_bound_mesh
delete_user_objects
save_blend_file
apply_modifiers
boolean_operation
export_final_production_model
```

新增测试：

```text
tests/test_v0_6_safe_preview_session.py
```

测试覆盖：

- Safe Preview Session 输出字段契约。
- `preview_ready` 会话只允许 preview-only 操作。
- preflight checks 包含目标对象检查和用户确认检查。
- generated artifacts 包含 preview collection、generated preview object 和 preview report。
- `blocked` 会话只允许写 report，不允许创建预览对象。
- rollback strategy 只清理带 session tag 的 generated preview objects，并保留用户原始对象。

验证结果：

```text
Ran 5 tests in 0.109s
OK
```

Step 3 结论：已完成，可以进入 Step 4 Blender Preview Script Draft 实现。

## 20. Step 4 Blender Preview Script Draft 实现结果

V0.6 Blender Preview Script Draft 已完成第一版实现。

新增模块：

```text
3d_agent/agent/blender_preview_script_draft.py
```

核心函数：

```text
create_blender_preview_script_draft(geometry_preview_plan, safe_preview_session)
```

输入对象：

- V0.6 `geometry_preview_plan`
- V0.6 `safe_preview_session`

输出对象：

- Blender Python preview script draft 字符串

第一版实现规则：

- `safe_preview_session.allowed_operations` 包含 `create_generated_preview_object` 时，脚本会创建独立 preview collection。
- 脚本会为每个 `preview_element` 创建 generated preview object。
- generated preview object 会写入 `v0_6_preview_session_id`、`source_task_id`、`target_object`、`element_type`、`target_zone`、`intent` 和 `requires_user_confirmation`。
- 脚本会写出 preview report JSON，记录 session、目标对象、生成对象、确认事项、安全规则和回滚策略。
- `blocked` 会话只生成 report 脚本，不导入 `bpy`，不创建 collection 或 object。

安全边界：

- 不编辑 bound mesh data。
- 不删除用户已有对象。
- 不调用 `bpy.ops`。
- 不 apply modifier。
- 不执行 boolean 操作。
- 不保存 `.blend` 文件。

新增测试：

```text
tests/test_v0_6_blender_preview_script_draft.py
```

测试覆盖：

- 脚本包含 V0.6 preview contract 和 collection 创建逻辑。
- 脚本会给 generated preview objects 写入 session tag 和回滚相关属性。
- 脚本不包含 destructive Blender ops。
- blocked preview script 只写 report，不导入 `bpy`，不创建 collection 或 object。

验证结果：

```text
Ran 4 tests in 0.088s
OK
```

Step 4 结论：已完成，可以进入 Step 5 CLI 可选接入。

## 21. Step 5 CLI 可选接入结果

V0.6 CLI 可选接入已完成第一版实现。

更新模块：

```text
3d_agent/main.py
```

新增显式参数：

```text
--geometry-preview
--preview-script-draft
```

参数关系：

- `--geometry-preview` 生成 `geometry_preview_plan` 和 `safe_preview_session`。
- `--preview-script-draft` 隐含 `--geometry-preview`，并额外生成 `blender_preview_script_draft`。
- `--geometry-preview` 和 `--preview-script-draft` 都需要 `--scene-manifest <path>`，否则无法确定真实目标对象。
- 对非 `model_edit` 命令，不附加 V0.6 字段。

命令示例：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --geometry-preview
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --preview-script-draft
```

输出行为：

- 默认命令仍保持 V0.3 增强蓝图输出，不附加 V0.4、V0.5 或 V0.6 字段。
- 带 `--scene-manifest <path>` 时继续自动生成 V0.4 `execution_package`、V0.5 `model_binding_context` 和 `execution_package_review`。
- 带 `--geometry-preview` 时附加 `geometry_preview_plan` 和 `safe_preview_session`。
- 带 `--preview-script-draft` 时附加 `geometry_preview_plan`、`safe_preview_session` 和 `blender_preview_script_draft`。
- 对 `inspect_context` 等非模型编辑命令，不附加 `execution_package`、`model_binding_context`、`execution_package_review`、`geometry_preview_plan`、`safe_preview_session` 或 `blender_preview_script_draft`。

新增测试：

```text
tests/test_v0_6_cli_preview.py
```

同步更新测试：

```text
tests/test_v0_4_execution_package.py
tests/test_v0_5_cli_scene_manifest.py
```

测试覆盖：

- `--geometry-preview` 和 `--preview-script-draft` 参数会被正确解析，不进入用户输入文本。
- `--preview-script-draft` 会隐含 `--geometry-preview`。
- 缺少 `--scene-manifest <path>` 时，V0.6 预览输出会报错。
- 模型编辑命令可附加 `geometry_preview_plan` 和 `safe_preview_session`。
- `--preview-script-draft` 可附加完整 V0.6 输出。
- 非模型编辑命令不会附加 V0.6 字段。

验证结果：

```text
Ran 22 tests in 0.411s
OK
```

Step 5 结论：已完成，可以进入 Step 6 V0.6 验收。

## 22. Step 6 V0.6 验收报告

V0.6 验收已完成。验收范围覆盖固定 Scene Manifest 样例、V0.4 execution package、V0.5 binding review、V0.6 geometry preview plan、safe preview session、Blender preview script draft、CLI 显式接入和默认输出隔离。

CLI 端到端验收命令：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --preview-script-draft
python 3d_agent/main.py "把背包的推进器做得更高机动一点，加喷口和机械细节。" --scene-manifest .\examples\blender_scene_manifest.json --preview-script-draft
python 3d_agent/main.py "给两条腿加同样的管线和液压杆，密度中等。" --scene-manifest .\examples\blender_scene_manifest.json --geometry-preview
python 3d_agent/main.py "现在有哪些部件？" --scene-manifest .\examples\blender_scene_manifest.json --geometry-preview --preview-script-draft
```

CLI 验收结果：

```text
chest_status=preview_ready, chest_target=ChestArmor_Upper_01, chest_elements=surface_detail_hint,surface_detail_hint, chest_blockers=no_surface_boundaries, chest_has_script=True, chest_script_has_ops=False
backpack_mode=bounding_box_overlay, backpack_elements=mounting_point_hint,manual_review_note,manual_review_note, backpack_blockers=no_mounting_surface,no_part_connection_points,no_surface_boundaries, backpack_has_script=True
leg_targets=LeftLeg_Armor_01,RightLeg_Armor_01, leg_elements=panel_line_hint,panel_line_hint,manual_review_note,manual_review_note,manual_review_note,manual_review_note, leg_blockers=no_part_connection_points,no_joint_range_data,no_surface_boundaries
context_command=inspect_context, has_preview=False, has_session=False, has_script=False
```

验收用例结论：

- 胸甲分件线预览通过：`preview_status = preview_ready`，目标对象为 `ChestArmor_Upper_01`，保留 `no_surface_boundaries`，脚本草案不包含 `bpy.ops`。
- 背包推进器占位预览通过：`preview_mode = bounding_box_overlay`，包含 `mounting_point_hint` 和人工复核注释，保留安装面和连接点等几何级 blocker。
- 腿部液压杆风险预览通过：同时识别 `LeftLeg_Armor_01` 和 `RightLeg_Armor_01`，保留 `no_joint_range_data`，确认事项包含关节活动范围。
- 无可信绑定阻塞路径通过测试覆盖：`preview_status = blocked`，不生成可执行 `preview_elements`，blocked script 只写 report。
- 非模型编辑命令隔离通过：`inspect_context` 不附加 `geometry_preview_plan`、`safe_preview_session` 或 `blender_preview_script_draft`。
- Blender 预览脚本安全检查通过：脚本只创建 preview collection 和 generated preview objects，不包含 mesh 修改、modifier apply、boolean、删除用户对象或保存 `.blend` 操作。

V0.6 子集测试：

```text
Ran 20 tests in 0.372s
OK
```

全量回归测试：

```text
Ran 74 tests in 0.832s
OK
```

完成定义复核：

- Geometry Preview Plan 字段契约已确认并实现。
- 已能从 V0.4 execution package、V0.5 binding context 和 package review 生成预览计划。
- 已能生成 Safe Preview Session 契约。
- 已能生成 Blender preview script draft。
- 脚本草案只创建预览对象，不修改目标 mesh。
- CLI 已通过 `--geometry-preview` 和 `--preview-script-draft` 显式输出 V0.6 字段。
- 非模型编辑命令不附加 V0.6 字段。
- V0.4 和 V0.5 默认行为未被破坏。
- 6 条 V0.6 验收用例均有测试或 CLI 验证覆盖。
- 全量测试通过。

Step 6 结论：V0.6 已完成并通过验收。下一阶段可以进入 V0.7 真实软件接口调用与受控应用计划，重点设计用户确认、备份、可撤销操作和非破坏性 modifier 路径。