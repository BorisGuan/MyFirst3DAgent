# V0.4 半自动执行层开发计划

## 1. 阶段定位

V0.4 的目标是把 V0.3 默认输出的 Execution Blueprint 转换成建模软件可消费的半自动执行材料。V0.4 不是完整自动建模，也不是直接生成最终可打印模型，而是建立从执行蓝图到 Blender/Fusion 辅助执行之间的第一层桥梁。

产品路径：

```text
V0.2：自然语言 -> OperationPlan V2 操作蓝图
V0.3：OperationPlan V2 -> Execution Blueprint 执行蓝图
V0.4：Execution Blueprint -> 半自动执行包
V0.5：真实模型上下文读取和局部几何辅助
```

V0.4 的重点不是“帮用户直接改模型”，而是生成可检查、可保存、可逐步执行的执行包，让用户或后续 Blender/Fusion 集成层知道下一步应该做什么、需要哪些输入、哪些操作可以先以标记或占位形式落地。

## 2. V0.4 目标

V0.4 完成后，系统应该能够基于默认输出中的 `execution_blueprint` 生成一个 Execution Package，至少包含：

- 执行目标和来源蓝图引用。
- 软件目标，例如 `blender`、`fusion` 或 `manual`。
- 执行模式，例如标记、占位对象、脚本草案或人工步骤。
- 可执行任务列表。
- 所需输入清单。
- 不能执行的阻塞项。
- 用户确认点。
- 回滚或撤销建议。
- 输出文件建议。

V0.4 的直接价值是让用户从“知道怎么做”推进到“有一份可执行准备包”，但仍然保留人工确认和软件内检查。

## 3. 不做范围

V0.4 明确不做以下内容：

- 不自动修改真实 `.blend`、`.obj`、`.fbx`、`.glb` 文件。
- 不直接执行 Blender Python。
- 不生成最终真实几何。
- 不做布尔切割、重拓扑、UV、材质节点或渲染。
- 不保证 3D 打印公差、强度或装配可行性。
- 不做 Web UI 或插件 UI。
- 不引入复杂项目管理系统。
- 不绕过用户确认直接改模型。

## 4. 输入与输出关系

### 4.1 输入：Execution Blueprint

V0.4 的输入来自 V0.3 默认输出中的 `execution_blueprint`：

```json
{
  "source_plan_ref": "operation_plan_v2",
  "target_part": "chest_armor",
  "execution_intent": {
    "tool_family": "surface_detailing",
    "recommended_method": "parting_line_planning",
    "automation_level": "semi_automatable",
    "requires_mesh_access": true,
    "requires_part_boundaries": true
  },
  "operation_template": {
    "template_id": "surface_detailing.add_parting_lines",
    "manual_first_step": "先确认分件线是否符合装甲板块逻辑。",
    "execution_steps": ["识别装甲板块的主要轮廓和可见边。"]
  },
  "zone_mapping": [
    {
      "input_zone": "upper_chest_plate",
      "zone_role": "primary_visible_surface",
      "execution_hint": "优先作为主要视觉细节区域，保持结构清晰。"
    }
  ],
  "automation_assessment": {
    "difficulty": "medium",
    "blocked_by": ["no_real_mesh", "no_surface_boundaries"],
    "v0_4_candidate": true
  },
  "risk_review": {
    "risk_level": "medium",
    "risk_reasons": ["1/144 比例下刻线或分件线需要控制宽度和间距。"],
    "mitigation_steps": ["按 1/144 比例先降低细节密度。"]
  },
  "execution_brief": "针对 chest_armor，建议采用 parting_line_planning 执行准备。"
}
```

### 4.2 输出：Execution Package

V0.4 建议输出 Execution Package：

```json
{
  "package_version": "v0_4",
  "source_blueprint_ref": "execution_blueprint",
  "target_part": "chest_armor",
  "target_software": "blender",
  "execution_mode": "annotation_package",
  "execution_tasks": [
    {
      "task_id": "task_001",
      "task_type": "create_annotation",
      "target_zone": "upper_chest_plate",
      "instruction": "在胸甲上缘标记分件线路径，不执行真实切线。",
      "requires_user_confirmation": true,
      "status": "planned"
    }
  ],
  "required_inputs": ["real_mesh_file", "target_part_object", "surface_boundary_reference"],
  "blocked_by": ["no_real_mesh", "no_surface_boundaries"],
  "user_checkpoints": ["确认目标部件对象是否正确", "确认标记路径不会穿过舱门或关节区"],
  "rollback_plan": ["删除生成的标记对象或注释集合"],
  "output_artifacts": ["execution_package.json", "blender_annotation_script.py"],
  "execution_summary": "已生成胸甲分件线的 Blender 标记执行包，当前不会修改真实几何。"
}
```

## 5. Execution Package 字段契约草案

| 字段 | 类型 | 必填 | 默认值 | 用途 |
|---|---|---|---|---|
| `package_version` | `str` | 是 | `v0_4` | 标记执行包版本 |
| `source_blueprint_ref` | `str` | 是 | `execution_blueprint` | 标记来源蓝图 |
| `target_part` | `str` | 是 | 无 | 目标部件 |
| `target_software` | `str` | 是 | `blender` | 目标软件或执行环境 |
| `execution_mode` | `str` | 是 | `annotation_package` | 执行模式 |
| `execution_tasks` | `list[object]` | 是 | `[]` | 执行任务列表 |
| `required_inputs` | `list[str]` | 是 | `[]` | 执行前需要的输入 |
| `blocked_by` | `list[str]` | 是 | `[]` | 当前阻塞项 |
| `user_checkpoints` | `list[str]` | 是 | `[]` | 用户确认点 |
| `rollback_plan` | `list[str]` | 是 | `[]` | 回滚或撤销建议 |
| `output_artifacts` | `list[str]` | 是 | `[]` | 建议产物 |
| `execution_summary` | `str` | 是 | `""` | 用户可读摘要 |

### 5.1 execution task 字段

| 字段 | 类型 | 必填 | 默认值 | 用途 |
|---|---|---|---|---|
| `task_id` | `str` | 是 | 无 | 任务编号 |
| `task_type` | `str` | 是 | 无 | 任务类型 |
| `target_zone` | `str` | 是 | `unknown_zone` | 目标区域 |
| `instruction` | `str` | 是 | 无 | 执行说明 |
| `requires_user_confirmation` | `bool` | 是 | `true` | 是否需要用户确认 |
| `status` | `str` | 是 | `planned` | 当前任务状态 |

## 6. 执行模式

V0.4 建议先支持以下执行模式：

| execution_mode | 含义 | V0.4 是否实现 |
|---|---|---|
| `manual_instruction_package` | 只输出人工执行步骤 | 是 |
| `annotation_package` | 输出可用于 Blender 标记/注释的任务包 | 是 |
| `placeholder_package` | 输出占位对象生成计划 | 可选 |
| `script_draft_package` | 输出脚本草案，不自动执行 | 可选 |
| `direct_execution` | 直接改真实模型 | 否 |

建议 V0.4 优先实现 `manual_instruction_package` 和 `annotation_package`。这两类对真实模型破坏性最低，适合从执行蓝图过渡到 Blender/Fusion 集成。

## 7. 任务类型

| task_type | 适用场景 | 说明 |
|---|---|---|
| `create_annotation` | 面板线、分件线、战损区域 | 创建注释或标记，不改几何 |
| `create_curve_guide` | 管线、液压杆、刻线路径 | 创建曲线路径指导 |
| `place_placeholder` | 喷口、传感器、武器挂点 | 放置占位模块或位置标记 |
| `mark_risk_zone` | 关节、薄件、安装区 | 标记风险区域 |
| `manual_review` | 高风险或信息不足 | 要求用户人工检查 |

## 8. 工具族到执行模式映射

| tool_family | 推荐 execution_mode | 推荐 task_type |
|---|---|---|
| `surface_detailing` | `annotation_package` | `create_annotation` 或 `create_curve_guide` |
| `armor_composition` | `annotation_package` | `create_annotation`、`mark_risk_zone` |
| `mechanical_attachment` | `annotation_package` | `create_curve_guide`、`manual_review` |
| `propulsion_detailing` | `placeholder_package` | `place_placeholder` |
| `sensor_detailing` | `placeholder_package` | `place_placeholder` |
| `damage_weathering` | `annotation_package` | `create_annotation`、`mark_risk_zone` |

## 9. V0.4 模块设计

### 9.1 Execution Package Builder

新增模块建议：

```text
3d_agent/agent/execution_package.py
```

职责：

- 接收默认输出中的 `execution_blueprint`。
- 根据 `tool_family` 和 `recommended_method` 生成 Execution Package。
- 把 `zone_mapping` 转换成任务列表。
- 汇总 `required_inputs`、`blocked_by`、`user_checkpoints` 和 `rollback_plan`。

### 9.2 Blender Script Draft Formatter

新增模块建议：

```text
3d_agent/agent/blender_script_draft.py
```

职责：

- 从 Execution Package 生成 Blender Python 脚本草案。
- 脚本只创建注释集合、空对象、曲线路径草案或占位标记。
- 脚本默认不自动执行。
- 脚本必须包含用户确认注释和安全边界说明。

### 9.3 CLI 输出策略

V0.4 不建议一开始默认输出完整脚本草案。建议采用参数控制：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --execution-package
```

V0.4 CLI 行为建议：

- 默认输出 V0.3 增强蓝图。
- 带 `--execution-package` 时附加 Execution Package。
- 带 `--script-draft` 时附加脚本草案。
- 脚本草案只输出文本，不自动执行。

## 10. 建议开发顺序

### Step 0：V0.4 范围确认

确认 V0.4 只做半自动执行包，不直接执行 Blender。

输出：本计划确认版。

### Step 1：确认 Execution Package 字段契约

把第 5 节字段草案转成正式契约，确认字段、枚举、默认值和边界。

输出：字段契约确认表。

### Step 2：实现规则型 Execution Package Builder

新增 `execution_package.py`，根据 `execution_blueprint` 生成执行包。

输出：`create_execution_package(execution_blueprint)`。

### Step 3：新增 V0.4 测试

覆盖字段契约、工具族映射、任务生成、阻塞项和默认不执行真实软件。

输出：V0.4 测试文件。

### Step 4：接入 CLI 可选参数

新增 `--execution-package`，只在显式请求时输出执行包。

输出：CLI 可选执行包输出。

### Step 5：生成 Blender 脚本草案

基于 Execution Package 生成只读脚本草案，不自动运行。

输出：`blender_script_draft` 字段或独立文件内容。

### Step 6：新增安全检查

确保所有脚本草案包含不自动执行、不修改真实几何、需要用户确认的说明。

输出：安全检查测试。

### Step 7：V0.4 验收

用固定用例验证执行包和脚本草案。

输出：验收报告。

## 11. V0.4 验收用例

### 11.1 胸甲分件线执行包

输入：胸甲分件线 OperationPlan，默认生成 Execution Blueprint，再生成 Execution Package。

必须输出：

- `target_software`: `blender`
- `execution_mode`: `annotation_package`
- 至少 1 个 `create_annotation` 或 `create_curve_guide` 任务
- `blocked_by` 包含 `no_real_mesh` 或 `no_surface_boundaries`
- `rollback_plan` 非空

### 11.2 背包推进器占位包

输入：背包推进器 Execution Blueprint。

必须输出：

- 推荐 `placeholder_package`
- 至少 1 个 `place_placeholder` 任务
- `required_inputs` 包含安装面或部件对象信息
- 明确不直接生成真实喷口几何

### 11.3 腿部液压杆曲线指导包

输入：腿部液压杆 Execution Blueprint。

必须输出：

- 至少 1 个 `create_curve_guide` 任务
- `user_checkpoints` 包含关节活动范围确认
- `blocked_by` 包含 `no_joint_range_data`

### 11.4 盾牌战损注释包

输入：盾牌战损 Execution Blueprint。

必须输出：

- 至少 1 个 `create_annotation` 或 `mark_risk_zone` 任务
- `execution_summary` 强调浅表、克制和不直接深切
- `rollback_plan` 非空

### 11.5 传感器占位包

输入：传感器 Execution Blueprint。

必须输出：

- 至少 1 个 `place_placeholder` 任务
- `user_checkpoints` 包含朝向确认
- 脚本草案只创建占位标记，不生成最终模型

## 12. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 用户误以为 V0.4 会自动建模 | 期望偏差 | 文档和输出明确写“半自动执行包，不直接改模型” |
| Blender 脚本误执行 | 破坏模型 | V0.4 只输出脚本草案，不自动运行 |
| Execution Package 字段膨胀 | 实现复杂 | 先冻结最小字段，脚本草案作为可选输出 |
| 没有真实 mesh 导致任务不可落地 | 输出价值下降 | 先输出 annotation 和 placeholder，不做真实几何 |
| 后续 V0.5 接真实模型时重构 | 开发成本 | 保持 Execution Package 与真实软件解耦 |

## 13. V0.4 完成定义

V0.4 只有在同时满足以下条件时才算完成：

- 默认 V0.3 输出可作为 V0.4 输入。
- 能生成 Execution Package。
- Execution Package 包含任务、输入、阻塞项、确认点、回滚建议和摘要。
- CLI 可通过显式参数输出 Execution Package。
- 不默认执行 Blender。
- 不修改真实模型文件。
- 至少 5 条验收用例通过。
- 测试证明 V0.3 默认输出不被破坏。

## 14. 当前实现状态

V0.4 已完成第一版实现。当前实现采用规则型转换器，不依赖 LLM，也不直接执行 Blender。

已新增模块：

- `3d_agent/agent/execution_package.py`：把 `execution_blueprint` 转换成 V0.4 Execution Package。
- `3d_agent/agent/blender_script_draft.py`：根据 Execution Package 生成 Blender Python 脚本草案。

CLI 已支持显式参数：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --execution-package
```

输出行为：

- 默认命令仍输出 V0.3 增强蓝图，不附加 Execution Package。
- 带 `--execution-package` 时，在 `model_edit` 输出中附加 `execution_package`。
- 带 `--script-draft` 时，同时附加 `execution_package` 和 `blender_script_draft`。
- 对 `inspect_context` 等非模型编辑命令，不附加 V0.4 字段。
- 脚本草案只创建标记或占位对象，不修改真实 mesh，不保存文件，不执行布尔或 modifier apply。

验证结果：

```text
Ran 27 tests in 0.411s
OK
```