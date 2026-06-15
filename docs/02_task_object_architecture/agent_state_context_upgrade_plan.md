# Agent State / Context Upgrade Plan

## 1. 目标

本计划用于把当前 Agent 的 `TaskObject` 状态模型升级为更稳定、更可演化的状态架构。

核心目标：

1. 保持 `TaskObject` 作为主链任务事实源。
2. 增加独立的运行上下文，避免把运行时资源、临时数据、工具结果全部塞进 `TaskObject`。
3. 精确规定字段归属、可变性、迁移策略和 Schema Drift 防护。
4. 为后续 Codex 分步实现提供清晰边界。

非目标：

1. 不改变现有业务能力。
2. 不新增真实 Blender 操作。
3. 不重启旧链路。
4. 不把完整日志、完整 prompt、完整 report、完整 tool stdout 存入主状态对象。

---

## 2. 总体设计

目标状态架构分为三层：

```text
TaskObject
  持久化任务事实源，描述任务是什么、计划是什么、最终结果是什么。

AgentRunContext
  单次运行上下文，描述这次运行如何推进、当前执行到哪里、临时共享信息是什么。

RuntimeHandles
  不可持久化运行依赖，保存 handler、model client、persistence api、clock、report writer 等运行资源。
```

核心原则：

```text
TaskObject 可保存、可恢复、可审计。
AgentRunContext 可保存部分运行状态，但不能保存外部重资源。
RuntimeHandles 不可保存，只在进程内使用。
```

---

## 3. TaskObject 字段升级计划

### 3.1 TaskObject 根字段

目标字段：

```text
task_id: str
task_version: str
schema_version: str
state: TaskState
source: TaskSource
task_type: str
target: TaskTarget
intent: TaskIntent
constraints: TaskConstraints
execution_policy: ExecutionPolicy
planning: TaskPlanning
runtime: TaskRuntime
result: TaskResult
diagnostics: TaskDiagnostics
artifact_refs: ArtifactRefs
extensions: TaskExtensions
created_at: str | None
updated_at: str | None
```

### 3.2 不可更改字段

以下字段创建后不可被普通流程修改。只有 migration 过程可以修正旧数据。

```text
task_id
task_version
created_at
source.original_user_input
```

字段注释要求：

```text
task_id
  Immutable after creation. This value is the stable identity of a task across planning,
  execution, reporting, artifact references, and persisted snapshots. Mutating it would
  break traceability and make historical artifacts impossible to associate reliably.

task_version
  Immutable after creation. This records the TaskObject model generation used to create
  the task. It must not be silently overwritten because older tasks may need deterministic
  migration behavior.

created_at
  Immutable after creation. This is the audit timestamp for task creation. Later updates
  must use updated_at instead, otherwise the lifecycle history becomes misleading.

source.original_user_input
  Immutable after creation. This preserves the exact user request from which the task was
  derived. Normalized or rewritten text may exist in separate fields, but the original
  request must remain unchanged for audit, debugging, and re-planning.
```

### 3.3 schema_version 与 task_version

新增：

```text
schema_version: str = "task_object_schema_v2"
```

说明：

```text
task_version
  表示任务对象创建时代码模型的大版本，可用于产品级兼容判断。

schema_version
  表示当前序列化 schema 的具体版本，用于 migration。
```

要求：

1. 所有 `from_dict()` 必须先执行 migration，再构造对象。
2. 所有 `to_dict()` 必须输出当前 `schema_version`。
3. 未知 `schema_version` 必须显式失败，不能静默按当前版本解析。

---

## 4. 字段精确定义

### 4.1 TaskSource

目标字段：

```text
original_user_input: str
normalized_user_input: str
channel: str
metadata: dict[str, Any]
```

字段说明：

```text
original_user_input
  用户最初输入，不可更改。

normalized_user_input
  Agent Layer 可写。用于保存 trim、规范化后的输入。

channel
  Agent Layer 可写。表示来源，例如 cli、test、api、copilot。

metadata
  受控扩展区。必须只存轻量引用或来源信息。
```

Schema Drift 防护：

1. `metadata` 必须使用命名空间 key。
2. 推荐 key 形式：`source.blend_file`、`source.scene_manifest_ref`。
3. 禁止在 `metadata` 中保存完整 manifest、完整 prompt、完整响应。

### 4.2 TaskTarget

目标字段：

```text
semantic_part: str
bound_object: str | None
binding_candidates: list[str]
binding_confidence: str | None
binding_reason: str
```

字段说明：

```text
semantic_part
  Agent Layer 可写。表示用户语义目标，例如 chest_armor。

bound_object
  Planning Layer 可写。表示解析后的具体对象名。

binding_candidates
  Planning Layer 可写。表示候选对象列表。

binding_confidence
  Planning Layer 可写。表示绑定置信度，建议 low / medium / high。

binding_reason
  Planning Layer 可写。简短解释为什么绑定到该对象。
```

不可变规则：

```text
semantic_part 在进入 BOUND 状态后不可再由 Agent Layer 修改。
bound_object 在进入 READY_TO_EXECUTE 后不可修改。
```

原因注释：

```text
semantic_part becomes frozen after binding because downstream planning and target binding
are derived from it. Changing it later without restarting the planning flow can make the
task internally inconsistent.

bound_object becomes frozen once the task is ready to execute because runtime execution,
artifact naming, and reports depend on the selected object identity. Changing it after
readiness would execute a plan against a different target than the one validated.
```

### 4.3 TaskIntent

目标字段：

```text
desired_effect: str
action: str
detail_type: str
style: str
density: str
scale: str
symmetry: str
placement_zones: list[str]
parameters: dict[str, Any]
```

字段说明：

```text
desired_effect
  用户想达成的高层效果。

action
  Agent Layer 从自然语言中提取的动作意图。

detail_type
  细节类型，例如 armor_layers、panel_line、edge_soften。

style / density / scale / symmetry / placement_zones
  设计语义字段。

parameters
  语义参数扩展区。
```

Schema Drift 防护：

1. `parameters` 只允许保存意图层参数，不允许保存 Planning 或 Runtime 生成的执行参数。
2. `parameters` key 必须使用稳定业务名称，不允许直接使用底层工具参数名作为事实源。
3. 如果某个参数被 Planning 转换为执行参数，应写入 `planning.parameters`，而不是覆盖 `intent.parameters`。

### 4.4 TaskConstraints

目标字段：

```text
preserve_source_file: bool
non_destructive: bool
mesh_edit_allowed: bool
notes: list[str]
safety_tags: list[str]
```

字段说明：

```text
preserve_source_file
  默认 true。用于表达源文件保护要求。

non_destructive
  默认 true。用于表达非破坏性修改要求。

mesh_edit_allowed
  默认 false。用于显式限制是否允许真实 mesh 级修改。

notes
  Agent Layer 可写。保存用户或解析器提取的轻量约束。

safety_tags
  Planning Layer 可追加。保存安全策略分类，例如 requires_copy、no_mesh_edit。
```

不可变规则：

```text
preserve_source_file 一旦为 true，不允许被后续层改为 false。
non_destructive 一旦为 true，不允许被后续层改为 false。
mesh_edit_allowed 默认 false，只有明确安全策略升级流程可以改为 true。
```

原因注释：

```text
preserve_source_file is monotonic for safety. A later layer must not weaken the user's
source preservation requirement, because runtime side effects depend on this guarantee.

non_destructive is monotonic for safety. Once a task is classified as non-destructive,
downstream layers may only preserve or strengthen this constraint, not relax it.

mesh_edit_allowed controls irreversible edit capability. It must remain false unless a
dedicated policy decision explicitly upgrades the task, otherwise planning could silently
turn a safe preview task into destructive geometry editing.
```

### 4.5 ExecutionPolicy

目标字段：

```text
mode: str
preserve_source_file: bool
output_blend_copy: str | None
report_file: str | None
allowed_side_effects: list[str]
requires_user_confirmation: bool
```

字段说明：

```text
mode
  Planning Layer 可写。表示执行模式，例如 safe_non_destructive。

preserve_source_file
  Planning Layer 可写，但不得弱化 TaskConstraints。

output_blend_copy
  Planning Layer 可写。Runtime 只读。

report_file
  Planning Layer 可写。Runtime 只读或补充失败报告引用。

allowed_side_effects
  Planning Layer 可写。列出 Runtime 被允许执行的副作用。

requires_user_confirmation
  Planning Layer 可写。用于阻断 Runtime 自动执行。
```

不可变规则：

```text
READY_TO_EXECUTE 后 ExecutionPolicy 不允许修改。
```

原因注释：

```text
ExecutionPolicy is frozen after readiness because it is the contract Runtime validates
before performing side effects. Changing it after the task is ready would bypass the
planning and safety checks that produced the policy.
```

### 4.6 TaskPlanning

目标字段：

```text
selected_operation: str | None
parameters: dict[str, Any]
reasoning: list[str]
validation_summary: str
planner_version: str | None
safety_decision: str | None
```

字段说明：

```text
selected_operation
  Planning Layer 可写。选择的领域操作。

parameters
  Planning Layer 可写。执行参数事实源。

reasoning
  Planning Layer 可写。只保存简短理由，不保存完整 LLM chain。

validation_summary
  Planning Layer 可写。保存规划校验摘要。

planner_version
  Planning Layer 可写。标记规划器版本。

safety_decision
  Planning Layer 可写。记录安全检查结果。
```

Schema Drift 防护：

1. `parameters` 是执行参数事实源。
2. 不同 operation 的参数应通过 operation contract 校验。
3. `parameters` 不允许保存非执行参数，例如 report path、source file、large preview data。

不可变规则：

```text
READY_TO_EXECUTE 后 selected_operation 和 parameters 不允许修改。
```

原因注释：

```text
selected_operation and parameters are frozen after readiness because runtime execution is
validated against them. Mutating them later would make the executed action differ from the
planned and safety-checked action.
```

### 4.7 TaskRuntime

目标字段：

```text
source_blend_file: str | None
output_blend_copy: str | None
report_file: str | None
started_at: str | None
finished_at: str | None
runtime_id: str | None
attempt: int
```

字段说明：

```text
source_blend_file
  Runtime Layer 可写或从 source metadata 解析后写入。

output_blend_copy
  Runtime Layer 可写。应与 ExecutionPolicy 保持一致。

report_file
  Runtime Layer 可写。应与实际写出的 report 引用一致。

started_at / finished_at
  Runtime Layer 可写。

runtime_id
  Runtime Layer 可写。表示本次执行实例。

attempt
  Runtime Layer 可写。表示执行尝试次数。
```

不可变规则：

```text
started_at 一旦写入，同一次 attempt 中不可修改。
runtime_id 一旦写入，同一次 attempt 中不可修改。
```

原因注释：

```text
started_at is immutable within an execution attempt because it anchors runtime duration
and audit records. A retry should create a new attempt rather than rewrite history.

runtime_id is immutable within an execution attempt because reports, artifacts, and tool
observations may refer to it. Rewriting it would break correlation between runtime records.
```

### 4.8 TaskResult

目标字段：

```text
success: bool | None
summary: str
report_file: str | None
artifacts: dict[str, str]
error: TaskError | None
```

字段说明：

```text
success
  Runtime Layer 可写。

summary
  Runtime Layer 可写。简短结果摘要。

report_file
  Runtime Layer 可写。最终 report 引用。

artifacts
  Runtime Layer 可写。轻量 artifact 引用。

error
  Runtime Layer 可写。结构化错误。
```

Schema Drift 防护：

1. `artifacts` 只保存路径或 ID，不保存内容。
2. artifact key 必须稳定，例如 `output_blend_copy`、`runtime_report`、`failure_report`。
3. 所有失败必须优先写 `error`，`summary` 只是人类可读摘要。

### 4.9 TaskError

新增结构：

```text
stage: str
code: str
message: str
recoverable: bool
owner_layer: str
retry_hint: str | None
artifact_ref: str | None
```

字段说明：

```text
stage
  失败阶段，例如 validation、binding、operation_selection、runtime、reporting。

code
  稳定错误码，供测试和恢复逻辑使用。

message
  人类可读错误。

recoverable
  是否可以自动或人工恢复。

owner_layer
  哪一层产生错误。

retry_hint
  可选恢复建议。

artifact_ref
  可选错误报告引用。
```

### 4.10 TaskDiagnostics

将当前 `diagnostics: list[str]` 升级为结构化对象：

```text
warnings: list[str]
notes: list[str]
validation_messages: list[str]
```

目的：

1. 避免所有诊断信息混在同一个 list。
2. 区分警告、普通说明、校验信息。
3. 为后续 UI 或 report 分区展示准备。

Schema Drift 防护：

1. 旧版本 `diagnostics: list[str]` migration 到 `diagnostics.notes`。
2. 新代码不得直接把错误写进 diagnostics；错误必须写 `result.error`。

### 4.11 ArtifactRefs

目标结构：

```text
artifact_refs: dict[str, str]
```

约束：

```text
只保存 artifact 引用。
不保存 artifact 内容。
只允许 Reporting Layer 写入全局 artifact_refs。
Runtime 产生的执行 artifact 优先写 result.artifacts。
```

推荐 key：

```text
runtime_report
failure_report
planning_trace
scene_manifest
preview_report
tool_stdout
```

### 4.12 TaskExtensions

新增：

```text
extensions: dict[str, dict[str, Any]]
```

规则：

1. 只允许命名空间一级 key。
2. 推荐命名空间：`agent`、`planning`、`runtime`、`reporting`、`migration`。
3. 不允许根级自由 key。
4. 不允许保存大对象。
5. 每个命名空间必须有 owner layer。

示例：

```text
extensions["planning"]["candidate_operation_scores"]
extensions["migration"]["source_schema_version"]
```

---

## 5. AgentRunContext 设计

新增运行级状态对象，不替代 TaskObject。

目标字段：

```text
run_id: str
run_version: str
task_id: str
status: RunStatus
current_stage: str | None
current_step_id: str | None
steps: list[RunStep]
shared: RunSharedState
response: RunResponse
created_at: str
updated_at: str | None
```

### 5.1 不可更改字段

```text
run_id
task_id
created_at
```

字段注释要求：

```text
run_id
  Immutable after creation. It identifies one execution attempt of a task. Retrying a task
  must create a new run_id instead of rewriting the previous execution history.

task_id
  Immutable after creation. A run belongs to exactly one task. Changing it would make step
  history and runtime observations refer to the wrong task.

created_at
  Immutable after creation. It records when this run attempt started tracking state.
```

### 5.2 RunStatus

建议枚举：

```text
created
running
waiting_for_user
waiting_for_tool
blocked
succeeded
failed
cancelled
```

说明：

`TaskState` 是业务生命周期；`RunStatus` 是本次运行控制状态。两者不要混在一起。

### 5.3 RunStep

目标字段：

```text
step_id: str
name: str
owner_layer: str
status: StepStatus
started_at: str | None
finished_at: str | None
input_ref: str | None
output_ref: str | None
error: TaskError | None
summary: str
```

StepStatus：

```text
pending
running
succeeded
failed
skipped
```

用途：

1. 表示状态机当前跑到哪里。
2. 支持恢复和重试。
3. 替代散落的 debug log。
4. 为 UI / CLI / report 提供进度来源。

### 5.4 RunSharedState

目标字段：

```text
scratchpad: dict[str, Any]
tool_results: dict[str, str]
observations: list[str]
pending_user_question: str | None
```

约束：

1. `scratchpad` 只保存轻量中间事实。
2. `tool_results` 保存 artifact 引用或摘要，不保存完整 stdout。
3. `observations` 保存短文本观察，不保存完整日志。
4. `pending_user_question` 用于表示等待用户输入，不写入 TaskObject。

### 5.5 RunResponse

目标字段：

```text
success: bool | None
error: TaskError | None
message: str
```

用途：

1. 描述本次 run 的整体结果。
2. 与 TaskResult 区分：RunResponse 是运行层状态，TaskResult 是任务最终结果。

---

## 6. RuntimeHandles 设计

目标字段：

```text
domain_handlers
persistence_api
report_writer
clock
model_client
tool_registry
logger
```

约束：

1. RuntimeHandles 不允许 JSON 序列化。
2. RuntimeHandles 不允许写入 TaskObject。
3. RuntimeHandles 不允许写入 AgentRunContext 的可持久字段。
4. 所有外部副作用通过 RuntimeHandles 提供的依赖发生。

目的：

```text
把可持久化状态和不可持久化运行资源彻底分开。
```

---

## 7. Ownership 升级

当前 ownership 只控制写字段。建议升级为读写契约。

### 7.1 Agent Layer

Reads：

```text
source.normalized_user_input
source.metadata
```

Writes：

```text
source.normalized_user_input
source.channel
source.metadata
task_type
target.semantic_part
intent
constraints.notes
```

Forbidden：

```text
planning
runtime
result
execution_policy.output_blend_copy
target.bound_object
```

### 7.2 Planning Layer

Reads：

```text
source
target.semantic_part
intent
constraints
```

Writes：

```text
target.bound_object
target.binding_candidates
target.binding_confidence
target.binding_reason
planning
execution_policy
constraints.safety_tags
```

Forbidden：

```text
source.original_user_input
runtime
result
```

### 7.3 Runtime Layer

Reads：

```text
target.bound_object
planning.selected_operation
planning.parameters
execution_policy
constraints
```

Writes：

```text
runtime
result
state to executing/completed/failed
```

Forbidden：

```text
source
intent
planning.selected_operation
planning.parameters
execution_policy after ready_to_execute
```

### 7.4 Reporting Layer

Reads：

```text
whole stable TaskObject snapshot
AgentRunContext steps summary
```

Writes：

```text
artifact_refs
```

Forbidden：

```text
state
planning
runtime
result.success
```

### 7.5 Domain Layer

Reads：

```text
DomainOperationInput only
```

Writes：

```text
none on TaskObject
```

Rule：

Domain Layer 不允许直接修改 TaskObject。它只返回 outcome，由 Runtime Layer 决定如何写回任务状态。

---

## 8. Schema Drift 防护机制

### 8.1 Migration Pipeline

新增 migration 入口：

```text
migrate_task_object_dict(raw: dict) -> dict
```

处理顺序：

```text
1. 读取 schema_version / task_version
2. 如果缺失，按 legacy v1 处理
3. 按版本链逐步迁移到当前版本
4. 记录 migration metadata 到 extensions["migration"]
5. 执行结构校验
6. 构造 TaskObject
```

### 8.2 Unknown Field Policy

建议策略：

```text
根级未知字段：拒绝或迁移到 extensions["migration"]["unknown_root_fields"]
已知 dataclass 内未知字段：拒绝或记录后丢弃
extensions 内未知字段：允许，但必须有命名空间
```

推荐优先级：

```text
开发期严格失败。
兼容旧数据时通过 migration 处理。
运行期不静默吞掉未知根字段。
```

### 8.3 Typed Accessors

为动态字段建立访问器，避免全项目直接索引 dict。

建议访问器：

```text
get_source_blend_file(task)
set_source_blend_file(task, value)
get_planning_parameter(task, name)
set_planning_parameter(task, name, value)
add_artifact_ref(task, key, path)
set_task_error(task, error)
append_diagnostic_note(task, note)
```

Rule：

```text
业务代码不直接写 source.metadata / intent.parameters / planning.parameters / result.artifacts / extensions。
```

### 8.4 Validation Layers

建议四类校验：

```text
schema validation
  字段类型、必填字段、未知字段策略。

lifecycle validation
  状态转换是否合法。

ownership validation
  当前层是否可以写这些字段。

readiness validation
  ready_to_execute 前所需字段是否齐全。
```

### 8.5 Golden Snapshot Tests

新增测试：

```text
test_task_object_v1_snapshot_migrates_to_current
test_unknown_root_field_is_rejected
test_extensions_require_namespace
test_ready_to_execute_freezes_planning_fields
test_runtime_cannot_weaken_execution_policy
test_original_user_input_is_immutable
test_run_context_is_serializable_without_runtime_handles
```

---

## 9. 分阶段执行计划

### Phase 1：Schema 扩展，不接入主流程

目标：

```text
增加新字段和新 dataclass，但不改变主流程行为。
```

任务：

1. 新增 `schema_version`。
2. 新增 `created_at`、`updated_at`。
3. 将 `diagnostics` 升级为结构化对象。
4. 新增 `TaskError`。
5. 新增 `extensions`。
6. 保持 `from_dict()` 对旧数据兼容。

验证：

```text
python -m unittest tests.test_task_object_schema
python -m unittest tests.test_task_object_legacy_fact_sources
```

### Phase 2：不可变字段与生命周期冻结规则

目标：

```text
实现不可更改字段保护和 ready_to_execute 后冻结规则。
```

任务：

1. 在 ownership 层加入 immutable field 检查。
2. 禁止普通 patch 修改 `task_id`、`task_version`、`created_at`、`source.original_user_input`。
3. 禁止 `READY_TO_EXECUTE` 后修改 target、planning、execution_policy。
4. 禁止 Runtime 修改 planning 和 execution_policy。

验证：

```text
python -m unittest tests.test_task_object_ownership
```

### Phase 3：AgentRunContext 独立化

目标：

```text
引入 run-level context，承载运行控制状态、步骤进度和临时共享信息。
```

任务：

1. 新增 `AgentRunContext`。
2. 新增 `RunStatus`、`RunStep`、`StepStatus`、`RunSharedState`、`RunResponse`。
3. Runtime 开始记录 run step，但暂不改变 TaskObject 主链结果。
4. 增加 run context 序列化测试。

验证：

```text
python -m unittest tests.test_runtime_execution_flow
python -m unittest tests.test_end_to_end_task_object_flow
```

### Phase 4：RuntimeHandles 分离

目标：

```text
把运行依赖从可持久状态中彻底分离。
```

任务：

1. 将当前 `ExecutionContext` 定位为 `RuntimeHandles` 或等价概念。
2. 明确 RuntimeHandles 不可序列化。
3. `execute_ready_task` 接收 TaskObject + AgentRunContext + RuntimeHandles。
4. 保持旧参数兼容时只做薄适配。

验证：

```text
python -m unittest tests.test_runtime_execution_flow
```

### Phase 5：Schema Migration Pipeline

目标：

```text
让 task_version/schema_version 真正参与状态演化。
```

任务：

1. 新增 migration 模块。
2. `TaskObject.from_dict()` 先 migrate 后 parse。
3. 处理旧字段：`target.candidates -> target.binding_candidates`。
4. 处理旧 `diagnostics: list[str] -> diagnostics.notes`。
5. 处理缺失 `schema_version` 的旧对象。

验证：

```text
python -m unittest tests.test_task_object_schema
```

### Phase 6：Typed Accessors 与 Dict 收敛

目标：

```text
减少直接访问动态 dict 的代码。
```

任务：

1. 新增 metadata / parameter / artifact / extension 访问器。
2. 替换主链中直接 dict 写入。
3. 允许 tests/fakes 仍使用简单 dict，但主链代码走访问器。

验证：

```text
python -m unittest discover -s tests
```

---

## 10. Codex 执行规则

后续 Codex 执行本计划时必须遵守：

1. 每次只执行一个 Phase。
2. 每个 Phase 开始前先读取本文件对应部分。
3. 每个 Phase 只能改涉及文件，不顺手重构旧链路。
4. 每个 Phase 必须补测试。
5. 如果测试失败，只修当前 Phase 范围。
6. 不允许删除旧字段，必须通过 migration 过渡。
7. 不允许把完整日志、完整 report、完整 prompt、完整 stdout 写入 TaskObject。
8. 不允许绕过 ownership patch 直接修改受保护字段。

---

## 11. 最重要的架构判断

当前系统不要继续把 `TaskObject` 扩大成完整 context。

更好的方向是：

```text
TaskObject = 可持久化任务事实源
AgentRunContext = 单次运行状态和进度
RuntimeHandles = 不可持久化运行依赖
Artifacts = 大对象和详细报告的外部引用
```

这样既保留状态机 Agent 的可解释性，也能控制 Schema Drift，并为未来恢复、重试、审计、可视化和多 Agent 协作留下空间。
