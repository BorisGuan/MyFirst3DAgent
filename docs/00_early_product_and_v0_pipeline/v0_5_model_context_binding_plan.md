# V0.5 真实模型上下文读取与部件绑定计划

## 1. 阶段定位

V0.5 的目标是让 Agent 第一次接触真实建模软件中的对象上下文，但仍不直接修改真实几何。它承接 V0.4 的 Execution Package，补齐执行包里反复出现的真实模型输入缺口，例如 `real_mesh_file`、`target_part_object`、`surface_boundary_reference`、`connection_point_reference`。

产品路径：

```text
V0.2：自然语言 -> OperationPlan V2 操作蓝图
V0.3：OperationPlan V2 -> Execution Blueprint 执行蓝图
V0.4：Execution Blueprint -> Execution Package 半自动执行包
V0.5：真实模型上下文读取 -> 部件对象绑定 -> 执行包阻塞项复核
V0.6：局部几何预览、真实软件接口调用和安全回滚
```

V0.5 的核心不是“自动建模”，而是回答一个更基础的问题：

```text
抽象部件名 chest_armor / backpack / leg / shield，在真实 Blender 场景里分别对应哪些对象？
```

只有这个问题先解决，后续几何软件接口调用才有明确目标。

## 2. V0.5 目标

V0.5 完成后，系统应该能够：

- 读取真实模型对象清单的中间文件。
- 把 Blender 场景对象转换成结构化 Scene Manifest。
- 根据对象名、集合路径、自定义属性和尺寸信息，匹配抽象机甲部件。
- 输出 Model Binding Context。
- 标记哪些 V0.4 阻塞项可以解除，哪些仍然需要真实表面边界、连接点或厚度信息。
- 为后续 V0.6 的局部几何预览和接口调用提供目标对象引用。

V0.5 的直接价值是让 V0.4 的执行包从“需要真实模型”推进到“已经知道目标模型对象是谁”。

## 3. 不做范围

V0.5 明确不做以下内容：

- 不直接修改 `.blend`、`.obj`、`.fbx`、`.glb` 文件。
- 不执行布尔切割、挤出、刻线、重拓扑或 modifier apply。
- 不自动保存 Blender 文件。
- 不承诺精确识别复杂 mesh 的拓扑、法线、厚度和碰撞。
- 不做完整插件 UI。
- 不依赖 LLM 完成核心绑定判断。
- 不把低置信度绑定当作可执行目标。
- 不自动解除所有 `blocked_by`，只解除有证据支持的阻塞项。

## 4. 为什么先用 Scene Manifest

普通 Python CLI 环境通常不能直接 `import bpy` 读取 `.blend`。如果 V0.5 一开始要求 Agent 直接运行在 Blender Python 内，项目会立刻被 Blender 运行环境绑定，测试和回归都会变重。

因此 V0.5 第一版建议采用中间文件：

```text
Blender 场景 -> blender_scene_manifest.json -> Agent 读取和绑定
```

这个方案的好处：

- Agent 仍可在普通 Python 环境中运行。
- 单元测试可以直接使用固定 JSON 样例。
- 未来接 Blender 插件或命令行导出脚本时，不需要重写绑定逻辑。
- 真实几何读取和真实几何修改可以继续后置。

## 5. 输入与输出关系

### 5.1 输入一：Blender Scene Manifest

V0.5 第一版的外部输入建议是 `blender_scene_manifest.json`：

```json
{
  "manifest_version": "v0_5",
  "source_software": "blender",
  "source_file": "demo_gundam.blend",
  "unit_system": "metric",
  "objects": [
    {
      "object_name": "ChestArmor_Upper_01",
      "object_type": "MESH",
      "collection_path": ["Gundam", "Body", "Chest"],
      "dimensions": [2.4, 0.8, 1.1],
      "location": [0.0, 0.0, 3.2],
      "rotation_euler": [0.0, 0.0, 0.0],
      "vertex_count": 1240,
      "material_names": ["armor_white"],
      "custom_properties": {
        "part_role": "chest_armor"
      }
    }
  ]
}
```

### 5.2 输入二：V0.4 Execution Package

V0.5 也可以读取 V0.4 的 `execution_package`，重点使用：

- `target_part`
- `required_inputs`
- `blocked_by`
- `execution_tasks`

### 5.3 输出：Model Binding Context

V0.5 的核心输出是 Model Binding Context：

```json
{
  "binding_version": "v0_5",
  "source_manifest_ref": "blender_scene_manifest.json",
  "target_part": "chest_armor",
  "bindings": [
    {
      "target_part": "chest_armor",
      "object_name": "ChestArmor_Upper_01",
      "binding_status": "bound",
      "confidence": 0.95,
      "evidence": ["custom_property:part_role", "collection_path:Body/Chest", "name:ChestArmor"],
      "object_summary": {
        "object_type": "MESH",
        "dimensions": [2.4, 0.8, 1.1],
        "vertex_count": 1240
      },
      "resolved_inputs": ["real_mesh_file", "target_part_object"],
      "remaining_blockers": ["no_surface_boundaries"]
    }
  ],
  "unbound_parts": [],
  "unmatched_objects": [],
  "binding_summary": "已将 chest_armor 绑定到 ChestArmor_Upper_01，但仍缺少表面边界信息。"
}
```

## 6. Scene Manifest 字段契约确认

Step 1 确认：Scene Manifest 是 V0.5 第一版的只读真实场景对象目录。它只描述 Blender 场景对象，不承载执行任务，也不包含 mesh 顶点、面、法线、UV 或可修改几何数据。

| 字段 | 类型 | 必填 | 默认值 | 用途 |
|---|---|---|---|---|
| `manifest_version` | `str` | 是 | `v0_5` | manifest 版本 |
| `source_software` | `str` | 是 | `blender` | 来源软件 |
| `source_file` | `str` | 是 | 无 | 来源文件名或路径 |
| `unit_system` | `str` | 否 | `unknown` | 单位系统 |
| `objects` | `list[object]` | 是 | `[]` | 场景对象清单 |

### 6.1 object 字段

| 字段 | 类型 | 必填 | 默认值 | 用途 |
|---|---|---|---|---|
| `object_name` | `str` | 是 | 无 | Blender 对象名 |
| `object_type` | `str` | 是 | `UNKNOWN` | 对象类型，例如 `MESH`、`EMPTY`、`CURVE` |
| `collection_path` | `list[str]` | 否 | `[]` | 对象所在集合路径 |
| `dimensions` | `list[float]` | 否 | `[]` | 外包围尺寸 |
| `location` | `list[float]` | 否 | `[]` | 位置 |
| `rotation_euler` | `list[float]` | 否 | `[]` | 旋转 |
| `vertex_count` | `int` | 否 | `0` | 顶点数 |
| `material_names` | `list[str]` | 否 | `[]` | 材质名 |
| `custom_properties` | `object` | 否 | `{}` | 自定义属性 |

### 6.2 Scene Manifest 枚举与边界

字段取值确认：

- `manifest_version` 固定为 `v0_5`。
- `source_software` 第一版固定支持 `blender`。
- `unit_system` 允许 `metric`、`imperial`、`blender_default`、`unknown`。
- `object_type` 允许 `MESH`、`EMPTY`、`CURVE`、`ARMATURE`、`CAMERA`、`LIGHT`、`UNKNOWN`。
- `dimensions`、`location`、`rotation_euler` 如果出现，必须是 3 个数字。
- `custom_properties.part_role` 是最强绑定证据，但不是必填字段。

边界确认：

- 第一版只把 `MESH` 对象作为可绑定真实模型对象。
- `EMPTY`、`CURVE` 可以作为辅助对象保留，但不解除 `target_part_object`。
- manifest 不保存真实几何数据，不保存顶点坐标，不保存面列表。
- manifest 只证明“场景中存在对象”，不证明对象表面边界、厚度、连接点或关节范围可用。

## 7. Model Binding Context 字段契约确认

Step 1 确认：Model Binding Context 是 V0.5 第一版的绑定结果报告。它记录抽象部件与真实场景对象的匹配关系，并复核 V0.4 执行包中哪些输入已被满足、哪些阻塞项仍然保留。

| 字段 | 类型 | 必填 | 默认值 | 用途 |
|---|---|---|---|---|
| `binding_version` | `str` | 是 | `v0_5` | 绑定上下文版本 |
| `source_manifest_ref` | `str` | 是 | 无 | 来源 manifest |
| `target_part` | `str` | 否 | `unknown_part` | 当前关注部件 |
| `bindings` | `list[object]` | 是 | `[]` | 部件与对象绑定结果 |
| `unbound_parts` | `list[str]` | 是 | `[]` | 未绑定部件 |
| `unmatched_objects` | `list[str]` | 是 | `[]` | 未匹配对象 |
| `binding_summary` | `str` | 是 | `""` | 用户可读摘要 |

### 7.1 binding 字段

| 字段 | 类型 | 必填 | 默认值 | 用途 |
|---|---|---|---|---|
| `target_part` | `str` | 是 | 无 | 抽象部件名 |
| `object_name` | `str` | 是 | 无 | 真实场景对象名 |
| `binding_status` | `str` | 是 | `unbound` | `bound`、`candidate`、`ambiguous`、`unbound` |
| `confidence` | `float` | 是 | `0.0` | 绑定置信度 |
| `evidence` | `list[str]` | 是 | `[]` | 绑定证据 |
| `object_summary` | `object` | 是 | `{}` | 对象摘要 |
| `resolved_inputs` | `list[str]` | 是 | `[]` | 已满足的 V0.4 输入 |
| `remaining_blockers` | `list[str]` | 是 | `[]` | 仍未解决的阻塞项 |

### 7.2 Model Binding Context 枚举与边界

字段取值确认：

- `binding_version` 固定为 `v0_5`。
- `binding_status` 允许 `bound`、`candidate`、`ambiguous`、`unbound`。
- `confidence` 范围固定为 `0.0` 到 `1.0`。
- `resolved_inputs` 第一版允许 `real_mesh_file`、`target_part_object`、`scale_parameters`。
- `remaining_blockers` 沿用 V0.4 的 blocker 标签，例如 `no_surface_boundaries`、`no_part_connection_points`、`no_joint_range_data`、`no_thickness_data`、`no_mounting_surface`。

状态含义确认：

| binding_status | 含义 | 是否可作为执行目标 |
|---|---|---|
| `bound` | 证据充分，置信度高，可绑定到目标部件 | 是，但仍需检查剩余 blocker |
| `candidate` | 有一定证据，但需要用户确认 | 否 |
| `ambiguous` | 多个对象或证据冲突，无法自动选择 | 否 |
| `unbound` | 未找到可信对象 | 否 |

边界确认：

- 只有 `binding_status = bound` 且 `confidence >= 0.90` 时，才能解除 `target_part_object`。
- 绑定成功不等于可以执行几何修改。
- 绑定成功只能解除对象级输入，不能自动解除表面边界、厚度、连接点、关节范围等几何级 blocker。
- `unmatched_objects` 只作为诊断信息，不参与执行目标选择。
- 低置信度结果必须保留为 `candidate`、`ambiguous` 或 `unbound`，不能静默升级为 `bound`。

## 8. 绑定规则

V0.5 第一版建议使用规则型绑定，不依赖 LLM。

绑定证据优先级：

1. `custom_properties.part_role` 精确匹配 `target_part`。
2. 对象名包含目标部件别名，例如 `ChestArmor`、`Backpack`、`Shield`。
3. `collection_path` 包含目标部件所在层级，例如 `Body/Chest`。
4. 材质名或对象名包含辅助语义，例如 `armor`、`thruster`、`sensor`。
5. 尺寸和位置只作为辅助证据，不作为第一版强判断依据。

置信度建议：

- `0.90 - 1.00`：可绑定，证据强。
- `0.60 - 0.89`：候选绑定，需要用户确认。
- `0.30 - 0.59`：模糊匹配，不进入执行目标。
- `< 0.30`：视为未绑定。

V0.5 只能在 `binding_status` 为 `bound` 且置信度足够高时，解除 `target_part_object` 相关阻塞。

## 9. V0.4 阻塞项复核策略

V0.5 不会一次性解除所有阻塞项。建议规则如下：

| V0.4 blocker | V0.5 是否可解除 | 条件 |
|---|---|---|
| `no_real_mesh` | 可部分解除 | manifest 有来源文件且至少一个目标 mesh 绑定成功 |
| `no_surface_boundaries` | 暂不解除 | 第一版不分析真实表面边界 |
| `no_part_connection_points` | 暂不解除 | 第一版不识别连接点 |
| `no_joint_range_data` | 暂不解除 | 第一版不识别关节运动范围 |
| `no_thickness_data` | 暂不解除 | 第一版不计算厚度 |
| `no_mounting_surface` | 暂不解除 | 第一版不识别可安装面 |
| `no_scale_parameters` | 可解除 | manifest 或用户输入提供比例/单位 |

这意味着 V0.5 的第一版重点是解除：

- `real_mesh_file`
- `target_part_object`
- 部分 `scale_parameters`

但仍保留真实几何执行前必须确认的边界、厚度、连接点和关节信息。

## 10. 模块设计建议

### 10.1 Scene Manifest Loader

建议模块：

```text
3d_agent/model/scene_manifest.py
```

职责：

- 读取 `blender_scene_manifest.json`。
- 校验 manifest 顶层字段和 object 字段。
- 标准化对象名、集合路径和自定义属性。

### 10.2 Model Binder

建议模块：

```text
3d_agent/model/model_binding.py
```

职责：

- 接收 Scene Manifest、目标部件和可选 Execution Package。
- 按规则生成 Model Binding Context。
- 输出绑定置信度、证据、已解决输入和剩余阻塞项。

### 10.3 Blender Manifest Export Draft

建议模块：

```text
3d_agent/agent/blender_manifest_export_draft.py
```

职责：

- 生成 Blender Python 导出脚本草案。
- 脚本只读取场景对象并导出 JSON。
- 脚本不修改对象、不保存 `.blend` 文件。

### 10.4 CLI 接入建议

V0.5 建议新增显式参数，不改变默认 V0.4 行为：

```powershell
python 3d_agent/main.py "给胸甲加分件线" --execution-package --scene-manifest .\examples\blender_scene_manifest.json
```

行为建议：

- 默认命令仍保持 V0.3 输出。
- `--execution-package` 仍输出 V0.4 执行包。
- `--scene-manifest <path>` 时读取 manifest 并附加 `model_binding_context`。
- 如果绑定成功，可以附加 `execution_package_review`，说明哪些阻塞项已解除、哪些仍保留。
- 对非 `model_edit` 命令不附加执行包和绑定上下文，除非后续明确设计查询 manifest 的命令。

## 11. 建议开发顺序

### Step 0：V0.5 范围确认

确认 V0.5 第一版只做 manifest 读取、部件绑定和阻塞项复核，不做真实几何修改。

输出：本计划确认版。

### Step 1：确认字段契约

确认 Scene Manifest 和 Model Binding Context 字段、枚举、默认值和边界。

输出：字段契约确认表。

### Step 2：新增样例 manifest

新增一个最小 `blender_scene_manifest.json` 样例，覆盖 chest、backpack、leg、shield、sensor 等常见对象。

输出：样例文件。

### Step 3：实现 Scene Manifest Loader

实现读取、校验和标准化 manifest 的模块。

输出：`load_scene_manifest(path)`。

### Step 4：实现规则型 Model Binder

根据目标部件、对象名、集合路径和自定义属性生成绑定结果。

输出：`create_model_binding_context(scene_manifest, target_part, execution_package=None)`。

### Step 5：实现 Execution Package Review

基于绑定结果复核 V0.4 的 `required_inputs` 和 `blocked_by`。

输出：`review_execution_package_with_binding(execution_package, binding_context)`。

### Step 6：CLI 可选接入

新增 `--scene-manifest <path>`，只在显式传入时附加 V0.5 绑定上下文。

输出：CLI 可选绑定输出。

### Step 7：Blender manifest 导出脚本草案

生成一个只读 Blender Python 脚本草案，用于导出场景对象清单。

输出：`blender_manifest_export_draft`。

### Step 8：V0.5 验收

用固定样例 manifest 和 V0.4 执行包验证绑定、阻塞项复核和非破坏性边界。

输出：验收报告。

## 12. V0.5 验收用例

### 12.1 胸甲对象绑定

输入：目标部件 `chest_armor`，manifest 中存在 `ChestArmor_Upper_01`。

必须输出：

- `binding_status`: `bound`
- `confidence >= 0.90`
- `evidence` 包含对象名或自定义属性证据
- `resolved_inputs` 包含 `real_mesh_file` 和 `target_part_object`
- `remaining_blockers` 仍包含 `no_surface_boundaries`

### 12.2 背包推进器候选绑定

输入：目标部件 `backpack`，manifest 中存在 `Backpack_Block` 和 `Thruster_L/R`。

必须输出：

- 至少 1 个高置信度 backpack 绑定
- 推进器对象作为相关对象或未匹配对象保留
- 不自动解除 `no_mounting_surface`

### 12.3 腿部左右对象绑定

输入：目标部件 `leg`，manifest 中存在 `LeftLeg_Armor` 和 `RightLeg_Armor`。

必须输出：

- 支持多个对象绑定同一抽象部件
- `binding_summary` 说明左右腿对象均已识别
- 不自动解除 `no_joint_range_data`

### 12.4 低置信度对象不进入执行目标

输入：目标部件 `shield`，manifest 只有 `Panel_Unknown_03`。

必须输出：

- `binding_status` 为 `candidate` 或 `unbound`
- 不解除 `target_part_object` 相关输入
- 用户摘要提示需要手动确认

### 12.5 manifest 只读导出脚本安全检查

输入：生成 Blender manifest 导出脚本草案。

必须输出：

- 脚本只读取对象信息和写 JSON。
- 不包含 mesh 修改、modifier apply、布尔、保存 `.blend` 等操作。
- 脚本中明确标注只读用途。

## 13. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 对象命名混乱导致绑定错误 | 后续执行目标错误 | 低置信度必须进入 `candidate` 或 `unbound`，不自动执行 |
| 用户误以为 V0.5 已能自动改模型 | 期望偏差 | 文档和输出持续强调只读上下文和绑定 |
| manifest 字段过多导致实现复杂 | 开发变慢 | 第一版只保留对象名、类型、集合、尺寸、自定义属性等最小字段 |
| Blender 环境耦合过重 | 测试困难 | 第一版用 JSON manifest，Blender 脚本只作为导出草案 |
| 错误解除阻塞项 | 产生危险执行假象 | 只解除有明确证据的输入，几何边界类 blocker 继续保留 |

## 14. V0.5 完成定义

V0.5 只有在同时满足以下条件时才算完成：

- 有 Scene Manifest 字段契约。
- 有 Model Binding Context 字段契约。
- 能读取固定 `blender_scene_manifest.json` 样例。
- 能把至少 5 类抽象部件绑定到场景对象或给出候选/未绑定结果。
- 能复核 V0.4 Execution Package 的 `required_inputs` 和 `blocked_by`。
- CLI 可通过显式参数读取 manifest 并附加绑定上下文。
- 不直接执行 Blender。
- 不修改真实模型文件。
- 至少 5 条 V0.5 验收用例通过。
- V0.4 默认输出不被破坏。

## 15. Step 0 范围确认结果

V0.5 第一版范围确认如下：

```text
只读真实模型上下文 -> 规则型部件绑定 -> V0.4 执行包阻塞项复核
```

本阶段确认要做：

- 读取 `blender_scene_manifest.json`。
- 校验和标准化 Scene Manifest。
- 根据对象名、集合路径、自定义属性和辅助语义绑定 `target_part`。
- 输出 Model Binding Context。
- 复核 V0.4 Execution Package 的 `required_inputs` 和 `blocked_by`。
- 通过显式 CLI 参数接入，例如 `--scene-manifest <path>`。
- 保留一个只读 Blender manifest 导出脚本草案作为后续辅助。

本阶段确认不做：

- 不直接读取 `.blend`。
- 不直接执行 Blender Python。
- 不修改真实 mesh。
- 不执行布尔、刻线、挤出、modifier apply 或保存文件。
- 不依赖 LLM 做核心绑定判断。
- 不把低置信度候选对象当作可执行目标。
- 不自动解除表面边界、厚度、连接点、关节范围等几何级阻塞项。

进入 Step 1 的条件：

- Scene Manifest 和 Model Binding Context 字段契约继续作为 V0.5 主契约。
- 第一版实现以规则型绑定为主。
- 默认 CLI 输出不改变，V0.5 只通过显式参数附加绑定结果。
- 所有真实几何修改继续后置到 V0.6 或更后阶段。

Step 0 结论：已确认，可以进入 Step 1 字段契约确认。

## 16. Step 1 字段契约确认结果

V0.5 第一版字段契约已确认，核心对象固定为：

- Scene Manifest：真实建模软件场景的只读对象目录。
- Model Binding Context：抽象部件与真实场景对象的绑定结果报告。

Scene Manifest 契约结论：

- 第一版只支持 `source_software = blender`。
- 第一版只把 `MESH` 对象作为可绑定真实模型对象。
- `custom_properties.part_role` 是最强绑定证据。
- `dimensions`、`location`、`rotation_euler` 如果存在，必须是 3 个数字。
- manifest 不包含真实 mesh 几何数据，因此不能用于直接修改模型。

Model Binding Context 契约结论：

- `binding_status` 固定为 `bound`、`candidate`、`ambiguous`、`unbound`。
- 只有 `bound` 且 `confidence >= 0.90` 才能解除 `target_part_object`。
- `candidate`、`ambiguous`、`unbound` 都不能作为执行目标。
- 第一版只能解除对象级输入，例如 `real_mesh_file`、`target_part_object`、部分 `scale_parameters`。
- 第一版不能自动解除 `no_surface_boundaries`、`no_thickness_data`、`no_part_connection_points`、`no_joint_range_data`、`no_mounting_surface`。

Step 1 结论：已确认，可以进入 Step 2 新增样例 Scene Manifest。

## 17. Step 2 样例 Scene Manifest 结果

V0.5 第一版样例 manifest 已新增：

```text
examples/blender_scene_manifest.json
```

该样例用于后续 Scene Manifest Loader、Model Binder 和 CLI 接入测试。它符合 Step 1 字段契约，使用 `source_software = blender`，且不包含真实 mesh 顶点、面、法线或可修改几何数据。

样例覆盖的对象类型：

- `MESH`：作为可绑定真实模型对象。
- `CURVE`：作为辅助指导对象保留，不解除 `target_part_object`。

样例覆盖的抽象部件：

- `chest_armor` -> `ChestArmor_Upper_01`
- `backpack` -> `Backpack_Block_01`
- `leg` -> `LeftLeg_Armor_01`、`RightLeg_Armor_01`
- `shield` -> `Shield_Main_01`
- `camera_sensor` -> `Head_CameraSensor_01`
- `thruster` -> `Backpack_Thruster_L`、`Backpack_Thruster_R`

样例还包含：

- `Panel_Unknown_03`：用于测试未匹配对象。
- `Chest_SurfaceGuide_Curve`：用于测试非 `MESH` 辅助对象不会被当作可执行目标。

Step 2 结论：已完成，可以进入 Step 3 实现 Scene Manifest Loader。

## 18. Step 3 Scene Manifest Loader 实现结果

V0.5 Scene Manifest Loader 已完成第一版实现。

新增模块：

```text
3d_agent/model/scene_manifest.py
```

核心函数：

```text
load_scene_manifest(path)
normalize_scene_manifest(manifest)
```

当前能力：

- 读取 `blender_scene_manifest.json`。
- 校验 `manifest_version = v0_5`。
- 校验 `source_software = blender`。
- 校验 `unit_system` 枚举。
- 校验并标准化 `objects` 列表。
- 校验 `object_type` 枚举。
- 校验 `dimensions`、`location`、`rotation_euler` 必须为空列表或 3 个数字。
- 为可选字段补默认值，例如 `collection_path`、`material_names`、`custom_properties`。

新增测试：

```text
tests/test_v0_5_scene_manifest.py
```

测试覆盖：

- 样例 manifest 可正常读取。
- 样例覆盖 V0.5 需要的主要抽象部件。
- 可选 object 字段会被标准化。
- `CURVE` 辅助对象会被保留，但不作为绑定逻辑处理。
- 不支持的软件来源会被拒绝。
- 非 3 维向量字段会被拒绝。
- 不支持的 object type 会被拒绝。

验证结果：

```text
Ran 7 tests in 0.005s
OK
```

Step 3 结论：已完成，可以进入 Step 4 实现规则型 Model Binder。

## 19. Step 4 规则型 Model Binder 实现结果

V0.5 规则型 Model Binder 已完成第一版实现。

新增模块：

```text
3d_agent/model/model_binding.py
```

核心函数：

```text
create_model_binding_context(scene_manifest, target_part, execution_package=None, source_manifest_ref="scene_manifest")
```

当前能力：

- 根据 Scene Manifest 和 `target_part` 生成 Model Binding Context。
- 支持 `chest_armor`、`backpack`、`leg`、`shield`、`camera_sensor`、`thruster` 的第一版规则匹配。
- 使用 `custom_properties.part_role` 作为最强绑定证据。
- 使用对象名、集合路径和材质名作为辅助证据。
- 只把 `MESH` 对象作为可绑定真实模型对象。
- 对 `bound`、`candidate`、`ambiguous`、`unbound` 输出明确状态。
- 只有 `bound` 且 `confidence >= 0.90` 时才输出对象级 `resolved_inputs`。
- 能保留 `no_surface_boundaries` 等几何级 blocker，不因对象绑定成功而误解除。

关键安全规则：

- 如果对象已有 `custom_properties.part_role`，但它不等于当前 `target_part`，不会被误绑定。
- 因此 `Backpack_Thruster_L/R` 不会在绑定 `backpack` 时被当成背包主对象。
- `CURVE` 等辅助对象会保留在 `unmatched_objects`，不作为执行目标。
- 低置信度对象不会被静默升级成 `bound`。

新增测试：

```text
tests/test_v0_5_model_binding.py
```

测试覆盖：

- `chest_armor` 高置信度绑定到 `ChestArmor_Upper_01`。
- `backpack` 不会误绑其下的 `thruster` 子对象。
- `leg` 支持左右腿两个对象绑定同一抽象部件。
- `camera_sensor` 可以绑定到头部传感器对象。
- 没有 `part_role` 的名称/集合候选只能进入 `candidate`。
- 非 `MESH` 辅助对象不会被绑定。
- 无可信对象时输出 `unbound_parts`。

验证结果：

```text
Ran 14 tests in 0.013s
OK
```

Step 4 结论：已完成，可以进入 Step 5 实现 Execution Package Review。

## 20. Step 5 Execution Package Review 实现结果

V0.5 Execution Package Review 已完成第一版实现。

更新模块：

```text
3d_agent/model/model_binding.py
```

新增核心函数：

```text
review_execution_package_with_binding(execution_package, binding_context)
```

输出对象：

```text
execution_package_review
```

当前能力：

- 读取 V0.4 Execution Package 的 `required_inputs` 和 `blocked_by`。
- 读取 V0.5 Model Binding Context 的 `bindings` 和 `resolved_inputs`。
- 汇总已绑定对象。
- 输出已解决输入 `resolved_inputs`。
- 输出未解决输入 `unresolved_inputs`。
- 输出已解除阻塞项 `resolved_blockers`。
- 输出仍保留阻塞项 `remaining_blockers`。
- 输出复核状态 `review_status`。
- 输出用户可读复核摘要 `review_summary`。

复核状态：

| review_status | 含义 |
|---|---|
| `resolved` | 执行包所需输入和 blocker 均已被当前绑定结果满足 |
| `partially_resolved` | 对象级输入已部分解决，但仍有未解决输入或 blocker |
| `needs_user_confirmation` | 只有候选或模糊绑定，需要用户确认 |
| `blocked` | 没有可信绑定对象，执行包仍被阻塞 |

当前安全边界：

- 只复核执行包，不改写原始 Execution Package。
- 只解除对象级 blocker，例如 `no_real_mesh`。
- `no_surface_boundaries`、`no_thickness_data`、`no_part_connection_points`、`no_joint_range_data`、`no_mounting_surface` 继续保留。
- 即使 `target_part_object` 已绑定，也不代表可以执行真实几何修改。

新增测试覆盖：

- 胸甲执行包可以解除 `no_real_mesh`，但保留 `no_surface_boundaries`。
- 传感器执行包可以解除 blocker，但仍保留未满足的 `orientation_reference` 输入。
- 候选绑定只进入 `needs_user_confirmation`。
- 无可信绑定时进入 `blocked`。

验证结果：

```text
Ran 18 tests in 0.018s
OK
```

Step 5 结论：已完成，可以进入 Step 6 CLI 可选接入。

## 21. Step 6 CLI 可选接入结果

V0.5 CLI 可选接入已完成第一版实现。

更新模块：

```text
3d_agent/main.py
```

新增显式参数：

```text
--scene-manifest <path>
```

命令示例：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --execution-package --scene-manifest .\examples\blender_scene_manifest.json
```

输出行为：

- 默认命令仍保持 V0.3 增强蓝图输出，不附加 V0.5 字段。
- 带 `--execution-package` 时继续输出 V0.4 `execution_package`。
- 带 `--scene-manifest <path>` 时读取 Scene Manifest。
- 带 `--scene-manifest <path>` 时会附加 `model_binding_context`。
- 带 `--scene-manifest <path>` 时会附加 `execution_package_review`。
- 如果只传 `--scene-manifest <path>`，系统会自动生成 `execution_package`，用于完成绑定复核。
- 对 `inspect_context` 等非模型编辑命令，不附加 `execution_package`、`model_binding_context` 或 `execution_package_review`。

新增测试：

```text
tests/test_v0_5_cli_scene_manifest.py
```

测试覆盖：

- `--scene-manifest <path>` 参数会被正确解析，不进入用户输入文本。
- 缺少 manifest 路径时会报错。
- 模型编辑命令可附加 `model_binding_context` 和 `execution_package_review`。
- `--scene-manifest <path>` 会自动补充 `execution_package`。
- 非模型编辑命令不会附加 V0.5 字段。

验证结果：

```text
Ran 34 tests in 0.282s
OK
```

Step 6 结论：已完成，可以进入 Step 7 Blender manifest 导出脚本草案。

## 22. Step 7 Blender manifest 导出脚本草案结果

V0.5 Blender manifest 导出脚本草案已完成第一版实现。

新增模块：

```text
3d_agent/agent/blender_manifest_export_draft.py
```

核心函数：

```text
create_blender_manifest_export_draft(output_path="blender_scene_manifest.json")
```

脚本草案职责：

- 在 Blender Python 环境中读取 `bpy.context.scene.objects`。
- 导出 V0.5 Scene Manifest JSON。
- 记录对象名、对象类型、集合路径、尺寸、位置、旋转、顶点数、材质名和自定义属性。
- 支持指定导出路径。

安全边界：

- 不创建 Blender 对象。
- 不编辑 mesh geometry。
- 不执行 boolean 或 mesh 操作。
- 不 apply modifier。
- 不保存 `.blend` 文件。

新增测试：

```text
tests/test_v0_5_blender_manifest_export_draft.py
```

测试覆盖：

- 脚本包含 V0.5 Scene Manifest 契约字段。
- 脚本使用指定输出路径写出 JSON。
- 脚本读取场景对象、材质槽和自定义属性。
- 脚本不包含破坏性 Blender 操作。

验证结果：

```text
Ran 4 tests in 0.001s
OK
```

Step 7 结论：已完成，可以进入 Step 8 V0.5 验收。

## 23. Step 8 V0.5 验收报告

V0.5 验收已完成。验收范围覆盖固定 Scene Manifest 样例、规则型部件绑定、V0.4 执行包阻塞项复核、CLI 显式接入和只读 Blender manifest 导出脚本草案。

CLI 端到端验收命令：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json
python 3d_agent/main.py "把背包的推进器做得更高机动一点，加喷口和机械细节。" --scene-manifest .\examples\blender_scene_manifest.json
python 3d_agent/main.py "给两条腿加同样的管线和液压杆，密度中等。" --scene-manifest .\examples\blender_scene_manifest.json
python 3d_agent/main.py "现在有哪些部件？" --scene-manifest .\examples\blender_scene_manifest.json
```

CLI 验收结果：

```text
chest_status=bound, chest_object=ChestArmor_Upper_01, chest_confidence=1.0, chest_resolved=real_mesh_file,target_part_object, chest_remaining=no_surface_boundaries, chest_review=partially_resolved
backpack_status=bound, backpack_object=Backpack_Block_01, backpack_remaining=no_mounting_surface,no_part_connection_points,no_surface_boundaries, backpack_review=partially_resolved
leg_binding_count=2, leg_objects=LeftLeg_Armor_01,RightLeg_Armor_01, leg_remaining_review=no_part_connection_points,no_joint_range_data,no_surface_boundaries, leg_review=partially_resolved
context_command=inspect_context, context_has_package=False, context_has_binding=False, context_has_review=False
```

验收用例结论：

- 胸甲对象绑定通过：`chest_armor` 绑定到 `ChestArmor_Upper_01`，置信度为 `1.0`，对象级输入已解除，`no_surface_boundaries` 保留。
- 背包对象绑定通过：`backpack` 绑定到 `Backpack_Block_01`，推进器子对象不会误作为背包主对象，安装面和连接点等几何级阻塞项保留。
- 腿部左右对象绑定通过：`leg` 同时识别 `LeftLeg_Armor_01` 和 `RightLeg_Armor_01`，`no_joint_range_data` 保留。
- 低置信度和未绑定路径通过测试覆盖：`candidate`、`unbound` 不会解除 `target_part_object`，复核状态会进入 `needs_user_confirmation` 或 `blocked`。
- manifest 只读导出脚本安全检查通过：脚本只读取对象信息并写 JSON，不包含 mesh 修改、modifier apply、布尔或保存 `.blend` 操作。
- 非 `model_edit` 命令隔离通过：`inspect_context` 不附加 `execution_package`、`model_binding_context` 或 `execution_package_review`。

V0.5 子集测试：

```text
Ran 27 tests in 0.082s
OK
```

全量回归测试：

```text
Ran 54 tests in 0.424s
OK
```

完成定义复核：

- Scene Manifest 字段契约已确认并实现。
- Model Binding Context 字段契约已确认并实现。
- 固定 `blender_scene_manifest.json` 样例可读取、校验和标准化。
- 已覆盖 chest、backpack、leg、shield、camera_sensor、thruster 等抽象部件。
- 已能复核 V0.4 Execution Package 的 `required_inputs` 和 `blocked_by`。
- CLI 已通过 `--scene-manifest <path>` 显式读取 manifest 并附加绑定上下文。
- 不直接执行 Blender。
- 不修改真实模型文件。
- V0.4 默认输出未被破坏。

Step 8 结论：V0.5 已完成并通过验收。下一阶段可以进入 V0.6 局部几何预览、真实软件接口调用前的安全设计，或先补一份 V0.6 计划书。