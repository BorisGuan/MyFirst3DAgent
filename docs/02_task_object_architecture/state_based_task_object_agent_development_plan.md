# State-based TaskObject Agent 开发计划

## 1. 文档目的

本文档是后续代码改造的执行级计划。目标是把当前项目改造成完整生命周期的 state-based TaskObject Agent Architecture。

后续每次开始某个 Step 前，必须先读取本文档中对应 Step 的内容，并只执行该 Step 的范围。本文档不是旧 Phase 2 计划的补充，也不是极简 TaskObject 接线方案，而是新的主架构落地路径。

## 2. 最终目标架构

主链路必须收敛为：

```text
Agent Layer
-> Task Object Layer
-> Planning Layer
-> Domain Operation Layer
-> Core API Layer
-> Runtime Layer
```

旁支系统不进入主链决策：

```text
Logging / Report / Memory / Preview
```

各层定位：

| 层 | 职责 | 禁止 |
|---|---|---|
| Agent Layer | 理解用户输入，创建 TaskObject draft | 不选择具体 Blender 操作，不调用执行层 |
| Task Object Layer | 统一语义、生命周期、状态、字段所有权 | 不执行业务动作，不保存外部副作用 |
| Planning Layer | 校验、绑定、选择操作、补全参数、安全策略 | 不调用 Domain/Core/bpy，不修改模型 |
| Domain Operation Layer | 执行业务工具动作 | 不写文件，不写 report，不理解自然语言 |
| Core API Layer | 封装 `bpy` 技术细节 | 不包含业务语义，不做规划 |
| Runtime Layer | 执行调度、副作用、保存、报告、状态落盘 | 不选择 operation，不补参数，不直接调用 `bpy` |

## 3. 当前项目基础判断

当前项目已有两条链路。

旧 AI 链路：

```text
main.py
-> command_classifier
-> intent_parser
-> planner
-> risk_checker
-> execution_blueprint
-> execution_package
-> preview / authoring
```

新执行链路：

```text
cli.py
-> operation_planner
-> modification_execution
-> domain_operations.edge_soften
-> core_geometry_api
-> bpy
-> blend copy + report
```

新的目标不是长期维护这两条链，而是保留可复用能力，废弃或迁移不符合新架构的旧语义结构。

可复用能力：

```text
command_classifier 的分类能力
intent_parser 的自然语言理解能力
domain_operations.edge_soften 的业务修改能力
core_geometry_api 的 bpy 封装能力
现有测试中的 fake / mock 工具
```

需要迁移或废弃的旧主链结构：

```text
OperationPlan 作为真实修改事实源
Execution Blueprint 作为真实修改事实源
Execution Package 作为真实修改事实源
preview/authoring 作为真实修改路径
operation dict 作为主链唯一输入
```

## 4. 全局开发约束

### 4.1 主链约束

1. 真实修改主链必须围绕 TaskObject。
2. `OperationPlan`、`Execution Blueprint`、`Execution Package` 不得作为新的真实修改入口。
3. `edge_soften` 是架构完成前唯一允许的 Domain Operation。
4. 不新增 `add_panel_line`、`add_armor_plate` 等新操作，除非计划明确进入扩展阶段。
5. 不为了兼容旧链路而引入新的旧结构 adapter 作为主链。

### 4.2 分层约束

1. Agent Layer 不调用 Domain/Core/Runtime。
2. Planning Layer 不调用 Domain/Core/Runtime，不 import `bpy`。
3. Domain Operation Layer 不写文件、不写 report、不改 TaskObject 状态。
4. Core API Layer 是唯一允许直接接触 `bpy` 的层。
5. Runtime Layer 不选择 operation，不补参数，不理解自然语言。
6. Report / Logging / Memory / Preview 只能作为旁支读取主链信息或记录 artifact。

### 4.3 TaskObject 约束

1. TaskObject 是主链唯一事实源。
2. TaskObject 必须有完整生命周期状态。
3. TaskObject 可以保存 artifact 引用和结果摘要，但不能保存完整日志、完整 preview 数据、大型 report 内容。
4. TaskObject 字段必须有 ownership 规则。
5. 已完成或失败的 TaskObject 不允许被静默覆盖成另一个成功结果。

### 4.4 开发节奏约束

1. 每次只做一个 Step。
2. 不跨 Step 顺手重构。
3. 不顺手删除无关旧代码。
4. 每个 Step 必须有测试或明确验证。
5. 当前 Step 测试未通过，不进入下一 Step。
6. 测试失败时，只修当前 Step 范围内的问题。

## 5. 每个 Step 的固定执行流程

```text
1. 读取本文档中当前 Step 的内容
2. 读取当前 Step 涉及的代码文件
3. 陈述本 Step 的局部实现假设
4. 做最小必要修改
5. 立刻运行本 Step 对应测试
6. 如果失败，只修当前 Step 范围
7. 通过后总结变更和验证结果
```

## 6. Step 0：现状冻结与废弃边界标记

### 目标

明确当前系统的真实调用链、语义结构和可复用边界，为后续重构建立事实基础。

### 涉及文件

```text
3d_agent/main.py
3d_agent/cli.py
3d_agent/operation_planner.py
3d_agent/modification_execution.py
3d_agent/model/schemas.py
3d_agent/blender_ops/domain_operations.py
3d_agent/blender_ops/core_geometry_api.py
tests/test_phase_2_*.py
```

### 要做

1. 画出旧 AI 链路真实调用关系。
2. 画出现有真实修改链路真实调用关系。
3. 列出所有主链语义对象：`OperationPlan`、operation dict、report dict、execution package。
4. 标记哪些模块后续可复用，哪些模块只保留为 legacy。
5. 不做代码重构，只产出现状结论。

### 禁止

1. 不新增 TaskObject。
2. 不改业务逻辑。
3. 不删除旧代码。
4. 不开始迁移 Planner 或 Runtime。

### 验收标准

1. 能明确回答当前真实修改链从哪里开始、在哪里调用 `bpy`、在哪里保存文件。
2. 能明确指出旧事实源和新结构化请求之间的重复点。
3. 后续 Step 可以基于本 Step 的结论开始改造。

### 推荐验证

```text
python -m unittest discover -s tests
```

## 7. Step 1：建立 Task Object Layer 基础模型

### 目标

新增完整生命周期 TaskObject 的基础数据模型，但暂时不接入旧流程和执行流程。

### 新增文件

```text
3d_agent/task_object/__init__.py
3d_agent/task_object/schema.py
tests/test_task_object_schema.py
```

### 必须实现

1. `TaskState`
2. `TaskObject`
3. `TaskSource`
4. `TaskTarget`
5. `TaskIntent`
6. `TaskConstraints`
7. `ExecutionPolicy`
8. `TaskPlanning`
9. `TaskRuntime`
10. `TaskResult`

### 必须支持的状态

```text
draft
validated
bound
planned
ready_to_execute
executing
completed
failed
```

### 字段要求

TaskObject 至少应包含：

```text
task_id
task_version
state
source
task_type
target
intent
constraints
execution_policy
planning
runtime
result
diagnostics 或 artifact 引用字段
```

### 禁止

1. 不把完整日志塞进 TaskObject。
2. 不把完整 preview 数据塞进 TaskObject。
3. 不接入 Blender。
4. 不接入 Agent Layer。
5. 不接入 Planning Layer。

### 验收标准

1. 可以创建 `draft` TaskObject。
2. 可以 `to_dict()` / `from_dict()`。
3. 可以 JSON 序列化和反序列化。
4. 默认值清晰且稳定。
5. 单测覆盖基本字段和默认值。

### 推荐测试

```text
python -m unittest tests.test_task_object_schema
```

## 8. Step 2：实现生命周期状态机

### 目标

让 TaskObject 的状态不能任意跳转。

### 新增文件

```text
3d_agent/task_object/lifecycle.py
tests/test_task_object_lifecycle.py
```

### 合法主路径

```text
draft -> validated -> bound -> planned -> ready_to_execute -> executing -> completed
```

### 合法失败路径

```text
validated -> failed
bound -> failed
planned -> failed
ready_to_execute -> failed
executing -> failed
```

### 禁止状态转移

```text
draft -> executing
draft -> completed
completed -> planned
completed -> failed
failed -> completed
ready_to_execute -> bound
executing -> planned
```

### 要做

1. 实现状态转移校验。
2. 实现明确异常类型或明确错误信息。
3. 支持成功路径和失败路径测试。

### 禁止

1. 不实现 TaskStore。
2. 不实现重试系统。
3. 不把状态机和 Runtime 绑定。

### 验收标准

1. 合法转移通过。
2. 非法转移抛出明确异常。
3. failed/completed 后不能被静默改写。

### 推荐测试

```text
python -m unittest tests.test_task_object_lifecycle
```

## 9. Step 3：实现字段 Ownership 校验

### 目标

防止各层随意修改 TaskObject 字段。

### 新增文件

```text
3d_agent/task_object/ownership.py
tests/test_task_object_ownership.py
```

### 字段归属

```text
Agent Layer:
  source
  task_type
  target.semantic_part
  intent
  initial constraints

Planning Layer:
  target.bound_object
  target.binding_candidates
  planning.selected_operation
  planning.parameters
  planning.reasoning
  execution_policy

Runtime Layer:
  runtime
  result
  final execution state transitions

Reporting / Logging / Preview:
  artifact references only, no planning/result authority
```

### 要做

1. 定义 layer name / owner name。
2. 定义字段路径允许修改规则。
3. 提供 patch 校验函数或受控更新函数。

### 禁止

1. Planner 改 `source.user_input`。
2. Runtime 改 `planning.selected_operation`。
3. Agent 写 `target.bound_object`。
4. Domain 改 TaskObject。
5. Report 改 TaskObject 主链状态。

### 验收标准

1. owner 合法修改通过。
2. 非 owner 修改被拒绝。
3. 错误信息能说明哪个字段、哪个 owner 违规。

### 推荐测试

```text
python -m unittest tests.test_task_object_ownership
```

## 10. Step 4：建立 Agent Layer 输出 TaskObject Draft

### 目标

自然语言输入进入新主链时，输出 `TaskObject(state=draft)`，不再输出 `OperationPlan` 作为真实修改主结构。

### 新增文件

```text
3d_agent/agent_layer/__init__.py
3d_agent/agent_layer/agent_service.py
3d_agent/agent_layer/legacy_intent_adapter.py
tests/test_agent_layer_task_creation.py
```

### 允许复用

```text
3d_agent/agent/command_classifier.py
3d_agent/agent/intent_parser.py
3d_agent/model/context_manager.py
```

### 输出要求

Agent Layer 输出 TaskObject draft，至少填入：

```text
source.user_input
task_type
target.semantic_part
intent.desired_effect
intent.style
intent.density
intent.scale
constraints 初始值
```

### 禁止

1. Agent Layer 不选择 `edge_soften`。
2. Agent Layer 不绑定 Blender object。
3. Agent Layer 不写 runtime path。
4. Agent Layer 不调用 Domain/Core/Runtime。
5. Agent Layer 不生成 Blender Python 脚本。

### 验收标准

1. 输入自然语言后得到 draft TaskObject。
2. 原始用户输入完整保留。
3. TaskObject 不包含执行结果。
4. 没有真实模型修改。

### 推荐测试

```text
python -m unittest tests.test_agent_layer_task_creation
```

## 11. Step 5：实现 Planning Validator

### 目标

把 `draft` TaskObject 校验为 `validated`。

### 新增文件

```text
3d_agent/planning/__init__.py
3d_agent/planning/validator.py
tests/test_planning_validator.py
```

### 检查内容

1. `source.user_input` 必须存在。
2. `task_type` 必须是支持类型。
3. `target.semantic_part` 必须存在。
4. `intent` 必须有最低必要字段。
5. 当前状态必须是 `draft`。

### 禁止

1. Validator 不做目标绑定。
2. Validator 不选择 operation。
3. Validator 不补参数。
4. Validator 不调用 Domain/Core/bpy。

### 验收标准

1. 合法 draft 进入 `validated`。
2. 缺字段时抛出明确 validation error 或进入 failed。
3. 单测覆盖缺字段场景。

### 推荐测试

```text
python -m unittest tests.test_planning_validator
```

## 12. Step 6：实现 Binding Resolver

### 目标

把语义目标绑定到真实 Blender object 名称，但不打开 Blender，不调用 `bpy`。

### 新增文件

```text
3d_agent/planning/binding_resolver.py
tests/test_planning_binding_resolver.py
```

### 输入

```text
TaskObject(state=validated)
scene manifest / model binding context
```

### 输出

```text
TaskObject(state=bound)
target.bound_object = real object name
target.binding_candidates = optional candidates
```

### 允许复用

```text
3d_agent/model/model_binding.py
3d_agent/model/scene_manifest.py
examples/blender_scene_manifest.json
```

### 禁止

1. 不打开 `.blend`。
2. 不调用 `bpy`。
3. 不修改模型。
4. 不选择 operation。
5. 不补参数。

### 验收标准

1. 已知语义部位能绑定到 object name 或候选列表。
2. 无法绑定时错误明确。
3. 测试使用 fake manifest，不依赖 Blender。

### 推荐测试

```text
python -m unittest tests.test_planning_binding_resolver
```

## 13. Step 7：建立 Operation Registry

### 目标

让支持的 Domain Operation 有统一注册表，避免 Planning 硬编码散落。

### 新增文件

```text
3d_agent/domain/__init__.py
3d_agent/domain/operation_registry.py
3d_agent/domain/operation_contracts.py
tests/test_operation_registry.py
```

### 当前只注册

```text
edge_soften
```

### OperationSpec 字段

```text
name
supported_task_types
required_target_state
default_parameters
parameter_schema
safety_level
handler_name
report_schema
```

### 禁止

1. 不新增其他 operation。
2. 不做复杂插件系统。
3. Registry 不 import `bpy`。
4. Registry 不调用 Domain handler。

### 验收标准

1. 可以查询 `edge_soften`。
2. 不支持的 operation 报错。
3. Operation Selector 后续只能通过 registry 查询能力。

### 推荐测试

```text
python -m unittest tests.test_operation_registry
```

## 14. Step 8：实现 Operation Selector

### 目标

从 bound TaskObject 选择 Domain Operation。

### 新增文件

```text
3d_agent/planning/operation_selector.py
tests/test_planning_operation_selector.py
```

### 当前选择规则

```text
task_type = surface_detail_enhancement
execution_policy.mode = safe_non_destructive
-> planning.selected_operation = edge_soften
```

### 要写入

```text
planning.selected_operation
planning.reasoning
```

### 禁止

1. 不调用 Domain Operation。
2. 不产生 Blender modifier 名称作为主操作。
3. 不补完整执行参数。
4. 不直接读取 CLI 参数。
5. 不调用 Core/bpy。

### 验收标准

1. 支持任务选择 `edge_soften`。
2. 不支持任务被拒绝。
3. 选择原因写入 `planning.reasoning`。

### 推荐测试

```text
python -m unittest tests.test_planning_operation_selector
```

## 15. Step 9：实现 Parameter Completer

### 目标

从 intent / constraints / operation spec 补全执行参数。

### 新增文件

```text
3d_agent/planning/parameter_completer.py
tests/test_planning_parameter_completer.py
```

### 当前参数

```text
strength
style
```

### 当前规则

1. 默认 `strength = 0.01`。
2. 默认 `style = mechanical`。
3. 用户明确参数可以覆盖默认值，但必须校验。
4. `density/style/scale` 可影响默认值，但第一版保持保守。

### 禁止

1. 不调用 Domain/Core/bpy。
2. 不写 report。
3. 不写 runtime path。
4. 不做 mesh 级直接决策。

### 验收标准

1. `edge_soften` 参数完整。
2. 非法 `strength` / `style` 报错。
3. TaskObject 进入 `planned`。

### 推荐测试

```text
python -m unittest tests.test_planning_parameter_completer
```

## 16. Step 10：实现 Safety Policy Checker

### 目标

把约束转换成执行策略，并决定是否可以进入 `ready_to_execute`。

### 新增文件

```text
3d_agent/planning/safety_policy_checker.py
tests/test_planning_safety_policy_checker.py
```

### 当前允许策略

```text
safe_non_destructive
preserve_source_file = true
non_destructive = true
mesh_edit_allowed = false
```

### 禁止

1. 不支持破坏性 mesh edit。
2. 不允许覆盖源 `.blend`。
3. 不允许没有 output copy 的真实执行。
4. 不绕过 report artifact。

### 验收标准

1. 合法策略进入 `ready_to_execute`。
2. 不安全策略被拒绝。
3. 单测覆盖覆盖源文件风险。

### 推荐测试

```text
python -m unittest tests.test_planning_safety_policy_checker
```

## 17. Step 11：实现 Planning Engine 串联

### 目标

把 Validator、Binding Resolver、Operation Selector、Parameter Completer、Safety Policy Checker 串成正式 Planning Layer。

### 新增文件

```text
3d_agent/planning/planning_engine.py
tests/test_planning_engine_flow.py
```

### 流程

```text
draft
-> validate
-> bind
-> select operation
-> complete parameters
-> check safety
-> ready_to_execute
```

### 禁止

1. Planning Engine 不调用 Runtime。
2. Planning Engine 不调用 Domain。
3. Planning Engine 不调用 Core。
4. Planning Engine 不调用 `bpy`。
5. Planning Engine 不写 report。

### 验收标准

1. 一次调用能把 draft TaskObject 推到 `ready_to_execute`。
2. 每个阶段失败能停止并返回明确错误。
3. 测试使用 fake manifest / fake registry。

### 推荐测试

```text
python -m unittest tests.test_planning_engine_flow
```

## 18. Step 12：定义 DomainOperationInput / OperationOutcome

### 目标

Domain 层不直接依赖完整 TaskObject，只接受最小执行输入。

### 修改文件

```text
3d_agent/domain/operation_contracts.py
tests/test_domain_operation_contracts.py
```

### DomainOperationInput 字段

```text
task_id
operation
target_object
parameters
execution_policy
```

### OperationOutcome 字段

```text
operation
target_object
success
changed_objects
modifier_info
mesh_data_applied
diagnostics
```

### 禁止

1. DomainOperationInput 不包含自然语言。
2. DomainOperationInput 不包含 report path。
3. DomainOperationInput 不包含 output blend path。
4. DomainOperationInput 不包含 preview/logs。
5. OperationOutcome 不写文件。

### 验收标准

1. 可以从 ready_to_execute TaskObject 派生 DomainOperationInput。
2. 输入缺 `target_object` 时失败。
3. OperationOutcome 可 JSON 序列化。

### 推荐测试

```text
python -m unittest tests.test_domain_operation_contracts
```

## 19. Step 13：重构 Domain Operation Layer

### 目标

`edge_soften` 只做业务动作，返回 OperationOutcome。

### 修改文件

```text
3d_agent/blender_ops/domain_operations.py
tests/test_phase_2_domain_operations.py
```

### 要移除

```text
save_as_copy_only
write_modification_report
implementation_hint 中的 report/output 逻辑
```

### 要保留

```text
require_object
add_bevel_modifier
style -> width 计算
modifier outcome 生成
```

### 禁止

1. Domain 不写文件。
2. Domain 不写 report。
3. Domain 不改 TaskObject。
4. Domain 不 import Runtime。
5. Domain 不理解自然语言。

### 验收标准

1. `edge_soften(DomainOperationInput) -> OperationOutcome`。
2. 单元测试确认没有保存副本行为。
3. 旧 Domain 测试按新契约更新后通过。

### 推荐测试

```text
python -m unittest tests.test_phase_2_domain_operations tests.test_domain_operation_contracts
```

## 20. Step 14：整理 Core API Layer

### 目标

`bpy` 只在 Core API 出现，职责更清晰。

### 新增/修改建议

```text
3d_agent/core_api/__init__.py
3d_agent/core_api/scene_object_api.py
3d_agent/core_api/geometry_api.py
3d_agent/core_api/persistence_api.py
```

可以暂时保留：

```text
3d_agent/blender_ops/core_geometry_api.py
```

作为兼容 wrapper，但新代码应走 `core_api/*`。

### 迁移建议

```text
require_object -> scene_object_api
object_snapshot -> scene_object_api
add_bevel_modifier -> geometry_api
remove_or_replace_named_modifier -> geometry_api
save_as_copy_only -> persistence_api
```

### 禁止

1. 不把 report builder 放 Core Geometry。
2. 不让 Agent/Planning/Domain 直接 import `bpy`。
3. 不顺手新增 mesh edit 功能。
4. 不改变现有 bevel 行为。

### 验收标准

1. `bpy` 搜索结果只在 Core API 和测试 fake 中出现。
2. 现有 Core 能力测试通过。
3. Domain 通过 Core API 调用能力，不直接 import `bpy`。

### 推荐测试

```text
python -m unittest tests.test_phase_2_core_geometry_api
```

## 21. Step 15：建立 Runtime Layer

### 目标

Runtime 负责执行调度和副作用。

### 新增/修改文件

```text
3d_agent/runtime/__init__.py
3d_agent/runtime/runtime_engine.py
3d_agent/runtime/execution_context.py
tests/test_runtime_execution_flow.py
```

### Runtime 流程

```text
load ready_to_execute TaskObject
-> build DomainOperationInput
-> call Domain Operation
-> call persistence_api.save_as_copy_only
-> call report writer
-> update TaskObject.result
-> state completed / failed
```

### 禁止

1. Runtime 不选择 operation。
2. Runtime 不补参数。
3. Runtime 不直接调用 `bpy`。
4. Runtime 不绕过 Domain 修改模型。
5. Runtime 不理解自然语言。

### 验收标准

1. 成功执行后 TaskObject `state=completed`。
2. 失败后 TaskObject `state=failed`。
3. report 文件由 Runtime 协调生成。
4. source `.blend` 不被覆盖。

### 推荐测试

```text
python -m unittest tests.test_runtime_execution_flow
```

## 22. Step 16：建立 Report 旁支系统

### 目标

报告不属于 Domain，也不塞爆 TaskObject。

### 新增文件

```text
3d_agent/reporting/__init__.py
3d_agent/reporting/report_builder.py
3d_agent/reporting/report_writer.py
tests/test_reporting.py
```

### 输入

```text
TaskObject
OperationOutcome
PersistenceResult
```

### 输出

```text
report JSON file
```

### TaskObject 中只记录

```text
result.report_file
result.summary
artifact reference
```

### 禁止

1. Report 不改 planning。
2. Report 不调用 `bpy`。
3. Report 不决定操作成功失败。
4. Report 不成为 Domain 执行依赖。

### 验收标准

1. report 内容包含 task_id、operation、target、parameters、changed_objects。
2. report 文件可写。
3. TaskObject 不保存完整 report 大对象。

### 推荐测试

```text
python -m unittest tests.test_reporting
```

## 23. Step 17：统一 CLI / main 入口

### 目标

新入口统一走 TaskObject 主链。

### 修改文件

```text
3d_agent/main.py
3d_agent/cli.py
tests/test_task_object_cli_flow.py
```

### 支持入口

```text
--input "给胸甲做机械风格边缘软化"
--task-file path/to/task.json
```

### 新流程

```text
input
-> Agent Layer
-> TaskObject draft
-> Planning Engine
-> Runtime Engine
```

### 旧入口处理

1. V0.x preview / execution package flags 不再作为真实修改主链。
2. 可以临时保留为 legacy 子命令。
3. 真实修改必须走 TaskObject。
4. 旧结构化 `--operation edge_soften` 如保留，必须先转换为 TaskObject。

### 禁止

1. CLI 不直接构造 operation dict 执行。
2. CLI 不直接调用 Domain。
3. CLI 不直接调用 Core。
4. CLI 不绕过 Planning Engine。

### 验收标准

1. 自然语言入口可生成 TaskObject。
2. task-file 入口可执行 ready_to_execute TaskObject。
3. 真实修改入口只走 TaskObject 主链。

### 推荐测试

```text
python -m unittest tests.test_task_object_cli_flow
```

## 24. Step 18：清理旧主链事实源

### 目标

移除或降级旧语义结构在真实修改链中的地位。

### 处理对象

```text
OperationPlan
Execution Blueprint
Execution Package
preview/authoring script path
```

### 策略

1. `OperationPlan` 可保留给 legacy preview，但不能进入 Runtime。
2. `Execution Blueprint` 只能作为派生说明。
3. `Execution Package` 不再作为执行入口。
4. Preview 只能读 TaskObject，不写主链结果。

### 禁止

1. 不为了兼容旧链继续新增 adapter 到 Runtime。
2. 不让旧 planner 重新成为 source of truth。
3. 不让 preview/authoring 成为真实修改路径。

### 验收标准

1. 搜索真实执行路径，不再依赖 `OperationPlan`。
2. Runtime 输入只接受 TaskObject / task-file。
3. 文档和测试都反映新主链。

### 推荐测试

```text
python -m unittest discover -s tests
```

## 25. Step 19：端到端 TaskObject Flow 测试

### 目标

验证新架构闭环，但不依赖真实 Blender。

### 新增文件

```text
tests/test_end_to_end_task_object_flow.py
```

### 测试链

```text
自然语言
-> Agent Layer
-> TaskObject draft
-> Planning Engine
-> Runtime with fake Domain/Core
-> completed TaskObject
```

### 禁止

1. E2E 单元测试不依赖真实 Blender。
2. 不使用真实 `.blend` 做常规单元测试。
3. 不绕过 TaskObject 注入 operation dict。
4. 不直接调用 Domain 模拟成功。

### 验收标准

1. E2E fake 测试通过。
2. 旧 Phase 2 相关测试更新后通过。
3. `python -m unittest discover -s tests` 通过。

### 推荐测试

```text
python -m unittest tests.test_end_to_end_task_object_flow
python -m unittest discover -s tests
```

## 26. Step 20：真实 Blender Smoke 测试

### 目标

验证真实 `.blend` 修改仍可运行。

### 输入

```text
自然语言或 task-file
source .blend
output .blend copy
report path
```

### 推荐 Blender

```text
D:\tools\blender-5.1\blender.exe
```

### 推荐资产

```text
examples/BlendFile/RZ-01/RZ-01.blend
examples/BlendFile/Gundam/GF-Gundam.blend
```

### 禁止

1. 不覆盖源 `.blend`。
2. 不把 smoke 测试变成默认单元测试。
3. 不在失败时静默成功。
4. 不为了 smoke 通过绕过 TaskObject 主链。

### 验收标准

1. 输出 `.blend` copy 存在。
2. report JSON 存在。
3. source `.blend` 未被覆盖。
4. TaskObject result 指向 artifacts。
5. Runtime 记录 completed 或 failed。

## 27. 分阶段推荐执行顺序

第一批：建立语义地基。

```text
Step 0: 现状冻结
Step 1: TaskObject schema
Step 2: Lifecycle
Step 3: Ownership
Step 4: Agent Layer 输出 draft
Step 5: Planning Validator
```

第二批：建立规划主链。

```text
Step 6: Binding Resolver
Step 7: Operation Registry
Step 8: Operation Selector
Step 9: Parameter Completer
Step 10: Safety Policy Checker
Step 11: Planning Engine
```

第三批：收敛执行层。

```text
Step 12: DomainOperationInput / OperationOutcome
Step 13: Domain Operation Layer 重构
Step 14: Core API Layer 整理
Step 15: Runtime Layer
Step 16: Report 旁支系统
```

第四批：统一入口和清理旧链。

```text
Step 17: CLI / main 统一入口
Step 18: 清理旧主链事实源
Step 19: E2E TaskObject Flow 测试
Step 20: 真实 Blender Smoke 测试
```

## 28. 每一步完成后的固定汇报格式

每个 Step 完成后，应输出：

```text
已完成：
- 修改了哪些文件
- 新增了哪些文件

保持不变：
- 哪些旧功能未触碰

验证：
- 跑了哪些测试
- 结果如何

下一步：
- 下一 Step 名称
- 下一 Step 开始前需要读取哪些文件
```

## 29. 总体验收标准

最终完成后必须满足：

```text
没有 OperationPlan / ExecutionPackage 双事实源
没有 AI 直接输出 Blender 操作
没有 Domain 写文件/写 report
没有 Runtime 选择 operation
没有 Core API 之外的 bpy
TaskObject 是唯一主链事实源
自然语言可以进入 TaskObject 主链
结构化 task-file 可以进入 Runtime 执行
Report / Logging / Memory / Preview 是旁支系统
```

最终验证命令：

```text
python -m unittest discover -s tests
```

真实 Blender smoke 单独执行，不作为普通单元测试依赖。
