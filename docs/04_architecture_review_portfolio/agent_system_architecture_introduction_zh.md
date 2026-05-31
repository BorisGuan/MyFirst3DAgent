# 3D 模型修改 Agent 系统 - 架构介绍

评审依据：本文档基于当前仓库实现编写，包括 `3d_agent/task_object`、`agent_layer`、`planning`、`domain`、`runtime`、`blender_ops`、`core_api`、`reporting`、CLI 入口、上下文 JSON 文件、测试以及已有架构文档。当实现与文档不一致时，以实际实现为准。

已检查的关键证据：

```text
3d_agent/task_object/schema.py
3d_agent/task_object/ownership.py
3d_agent/task_object/lifecycle.py
3d_agent/agent_layer/agent_service.py
3d_agent/agent_layer/legacy_intent_adapter.py
3d_agent/model/context_manager.py
3d_agent/model/scene_manifest.py
3d_agent/model/model_binding.py
3d_agent/planning/*.py
3d_agent/domain/operation_contracts.py
3d_agent/domain/operation_registry.py
3d_agent/runtime/runtime_engine.py
3d_agent/runtime/execution_context.py
3d_agent/blender_ops/domain_operations.py
3d_agent/core_api/*.py
3d_agent/reporting/*.py
3d_agent/cli.py
3d_agent/main.py
3d_agent/context/*.json
3d_agent/model_contexts/00_base_gundam.json
3d_agent/session/*.json
tests/test_*.py
docs/02_task_object_architecture/current_task_object_architecture_status.md
docs/02_task_object_architecture/step_20_real_blender_smoke.md
docs/04_architecture_review_portfolio/agent_global_architecture_design.md
docs/04_architecture_review_portfolio/agent_execution_reliability_design.md
```

## 1. 执行摘要

这个项目是一个用于修改 Blender 硬表面和机甲模型的受控执行 AI Agent 架构。它的核心设计选择是把自然语言翻译成结构化、有状态的任务数据，然后只执行已注册的、确定性的设计操作。它不是一个朴素的 LLM 到 Blender 脚本生成系统。

中心抽象是 `TaskObject`，定义在 `3d_agent/task_object/schema.py` 中。它是执行链的主要事实源：用户输入、目标、意图、规划结果、运行时路径、结果、诊断信息和产物都存在于同一个可序列化对象中。生命周期是显式的：`draft -> validated -> bound -> planned -> ready_to_execute -> executing -> completed`，或进入 `failed`。

面向 LLM 的 Agent Layer 只创建 draft task。它不执行 Blender 代码，不调用 `bpy`，不调用 Domain operations，也不决定最终的 `selected_operation`。Planning 会验证任务、绑定目标对象、从 `OperationRegistry` 中选择 operation、从 `OperationSpec` 中补全参数，并检查安全策略。Runtime 只接受 `ready_to_execute` 状态的任务，派生最小化的 `DomainOperationInput`，分发到已注册的 domain handler，协调持久化，写入报告，并将任务标记为 completed 或 failed。

Domain operations 是 `3d_agent/blender_ops/domain_operations.py` 中固定的 Python handlers。它们代表 `edge_soften`、`panel_line_bevel_prepare`、`thruster_nozzle_prepare` 等设计能力。这些 handlers 调用 Core API。Core API 是唯一导入或使用 Blender `bpy` 的层，相关模块包括 `core_api/scene_object_api.py` 和 `core_api/persistence_api.py`。

当前 Atomic Operation Library v1 包含十个 modifier-only、non-destructive operations。持久化策略会保存输出 `.blend` 副本，并拒绝覆盖源文件。这让系统比任意 LLM 生成的 Blender 脚本更安全、更容易审计，也更容易测试。

## 2. 这个系统解决的问题

LLM 生成的 Blender 脚本能力很强，但并不安全。它们可能调用任意 API、覆盖文件、删除对象、执行破坏性 mesh edit，或者以难以检查的方式失败。即使某个脚本成功运行一次，它也很少能成为可复用的建模能力。

自然语言设计意图也不等同于 Blender API 意图。设计师可能会说：“给胸甲添加机械面板细节”。这不应该直接映射成随机 Python。它应该映射成一个受约束的设计操作，并具有已知安全策略、已知参数、已知目标绑定、已知报告输出和已知失败行为。

这个架构解决了若干常见 Agent 失败模式：

```text
Planning 与 execution 混在一起
LLM 输出被当成可执行代码
工具调用隐藏在自然语言推理中
多个相互竞争的事实源
失败后没有稳定恢复点
缺少清晰的变更审计轨迹
缺少可复用的 operation 词汇表
```

3D 建模工作流需要受控修改、回滚、可解释性、可重复性和领域特定抽象。这个系统会在接触 Blender 之前，把开放式用户请求转成结构化状态转换和已注册 operations。

## 3. 核心设计哲学

### State-based agent architecture

系统围绕显式任务状态构建，而不是围绕隐式对话状态构建。任务只能在已知状态之间推进，每一层也只能写入自己拥有的字段。

### TaskObject 作为主要事实源

`TaskObject` 防止系统漂移成多个执行源。Legacy plans、blueprint objects、preview scripts 和 operation dicts 仍然可以为了兼容性或旧 preview 流程而存在，但真实修改以 TaskObject 为中心。

### 受控执行优于自由形式代码生成

LLM 不生成任意 Blender Python 来执行。真实模型修改通过 `OperationSpec`、Runtime dispatch、Domain handler 和 Core API 完成。

### 职责分离

这条链路把意图理解、规划、运行时分发、领域 operation 逻辑、底层 Blender 访问和报告分离开来。这让失败更容易定位，也更容易测试。

### Operation 是设计能力

Operation 是语义化建模能力，不是直接的 Blender API wrapper。例如，`panel_line_bevel_prepare` 是一个设计 operation。它刚好使用 Bevel modifier，但它的名称和契约用领域语言表达。

### Non-destructive copy-only output

当前安全模型不依赖 Blender undo。它保留源 `.blend`，并写入一个输出副本。

### Atomic operations first

系统有意先从 atomic operations 开始，而不是先做 composite operation sequences。这避免了在项目积累足够真实建模案例之前就设计 sequence framework。

### Delayed abstraction

Composite operations、通用 sequence planning、object creation、boolean workflows、material workflows 和 mesh edits 都会推迟，直到评估显示确实需要它们。

## 4. 高层架构

```text
用户输入
  |
  v
Agent Layer
  |
  v
TaskObject(state=draft)
  |
  v
Planning Engine
  |-- validate
  |-- bind target
  |-- select operation
  |-- complete parameters
  |-- check safety policy
  v
TaskObject(state=ready_to_execute)
  |
  v
Runtime Engine
  |
  v
DomainOperationInput
  |
  v
Domain Operation Handler
  |
  v
Core API
  |
  v
Blender bpy
  |
  v
output .blend copy + Runtime report + TaskObject result
```

### Agent Layer

输入：用户文本和 prompt-sized context summaries。

输出：`TaskObject(state=draft)`。

允许：分类 command type、解析 intent、填充 Agent-owned fields。

不允许：绑定 Blender objects、选择最终 operation、调用 Runtime、调用 Domain/Core、调用 `bpy`。

### TaskObject

输入：来自 Agent、Planning、Runtime 和 Reporting 的结构化任务字段。

输出：可序列化的任务状态和执行事实。

允许：作为数据模型和生命周期状态载体。

不允许：自行执行副作用。

### Planning Engine

输入：draft TaskObject 加 scene manifest 或 binding context。

输出：TaskObject 经过 `validated`、`bound`、`planned`，到达 `ready_to_execute`。

允许：验证、绑定、选择 operation、补全参数、批准安全策略。

不允许：执行 Domain handlers、写报告、保存文件、调用 `bpy`。

### Runtime Engine

输入：`TaskObject(state=ready_to_execute)`。

输出：completed 或 failed TaskObject；成功时还包括 report file 和 output blend copy。

允许：创建 `DomainOperationInput`、分发 handler、协调持久化和报告。

不允许：理解自然语言、选择 operation、补全参数、直接修改几何体。

### Domain Operation

输入：`DomainOperationInput`。

输出：`OperationOutcome`。

允许：验证 operation name、提取 operation parameters、调用 Core API。

不允许：保存文件、写报告、修改 TaskObject、直接 import `bpy`。

### Core API

输入：Blender object names 和底层 modifier parameters。

输出：object lookup、modifier changes、saved output copy、low-level report state。

允许：使用 Blender `bpy`。

不允许：决定 Agent 意图、规划 operations 或拥有 task state。

## 5. TaskObject-Centered State Model

`TaskObject` 定义在 `3d_agent/task_object/schema.py` 中。它包含：

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
diagnostics
artifact_refs
```

重要的嵌套结构包括：

```text
TaskSource: user_input, channel, metadata
TaskTarget: semantic_part, bound_object, binding_candidates
TaskIntent: desired_effect, action, detail_type, style, density, scale, symmetry, placement_zones, parameters
TaskConstraints: preserve_source_file, non_destructive, mesh_edit_allowed, notes
ExecutionPolicy: mode, preserve_source_file, output_blend_copy, report_file
TaskPlanning: selected_operation, parameters, reasoning
TaskRuntime: source_blend_file, output_blend_copy, report_file, started_at, finished_at
TaskResult: success, summary, report_file, artifacts
```

`3d_agent/task_object/lifecycle.py` 中的生命周期允许：

```text
draft -> validated
validated -> bound | failed
bound -> planned | failed
planned -> ready_to_execute | failed
ready_to_execute -> executing | failed
executing -> completed | failed
completed -> terminal
failed -> terminal
```

`3d_agent/task_object/ownership.py` 中的字段所有权是显式的：

| 层 | 拥有字段 |
| --- | --- |
| Agent | `source`, `task_type`, `target.semantic_part`, `intent`, `constraints` |
| Planning | `target.bound_object`, `target.binding_candidates`, `planning`, `execution_policy` |
| Runtime | `runtime`, `result` |
| Reporting | `artifact_refs` |
| Domain | none |

状态所有权也受到约束。例如，Planning 可以把任务移动到 `validated`、`bound`、`planned`、`ready_to_execute` 或 `failed`，而 Runtime 可以把任务移动到 `executing`、`completed` 或 `failed`。

这个模型能防止多个事实源，因为 selected operation、bound object、parameters、runtime paths 和 result 都是同一个可序列化对象的一部分。它也提升了可测试性和恢复能力：单元测试可以在特定状态构造 TaskObject，运行某个阶段，并断言精确的字段变化。序列化后的 task file 可以通过 CLI 的 `--task-file` 进入系统，并从已知状态恢复。

## 6. Agent Layer

Agent Layer 实现在 `3d_agent/agent_layer/agent_service.py` 和 `3d_agent/agent_layer/legacy_intent_adapter.py` 中。

`create_draft_task()` 接收自然语言输入，创建或使用 `ContextManager`，调用 `classify_command()`，然后调用 `parse_intent()`。如果 command type 不是 `model_edit`，它会拒绝请求。对于 model edit，它会把 legacy parser output 适配成 draft TaskObject。

Agent Layer 消耗：

```text
ContextManager.summary_for_classifier()
ContextManager.summary_for_planner()
command_classifier
intent_parser
design taxonomy
model context
session summaries
```

它只写 Agent-owned fields：

```text
source
task_type
target.semantic_part
intent
constraints
```

它不决定最终的 `planning.selected_operation`。Parser 可能生成 action 或类似 legacy operation 的 label，但真正的 operation selection 发生在 Planning 中，通过 `OperationRegistry` 和 `OperationSpec` metadata 完成。

## 7. Context Management System

上下文系统是分层的，不是单一 prompt blob。

### Static design context

文件：

```text
3d_agent/context/design_taxonomy.json
3d_agent/context/capabilities.json
3d_agent/context/mecha_design_rules.json
```

`design_taxonomy.json` 定义 panel lines、parting lines、armor layers、vents、thrusters、pipes、sensors、weapon mounts、damage 和 weathering 等 detail types。它还定义 operation phrases、actions、styles、symmetries、scales 和 densities。

### Model context

文件：

```text
3d_agent/model_contexts/00_base_gundam.json
3d_agent/model/model_context.py
```

Model context 是抽象 metadata，不是 mesh data。它列出可作为目标的部位，例如 head、body、chest armor、skirt armor、backpack、thruster、shield、beam rifle、camera sensor 和 cockpit hatch，并包含 aliases 与 categories。

### Session context

文件：

```text
3d_agent/session/design_brief.json
3d_agent/session/working_plan.json
3d_agent/session/interaction_summary.json
```

这些文件保存当前 project/session facts 和 recent interactions。当前实现主要在 `ContextManager` summaries 中使用它们。

### ContextManager

`3d_agent/model/context_manager.py` 加载 static、model 和 session context。它按 name、alias、category 和 detail level 建立索引。它提供：

```text
summary_for_classifier()
summary_for_planner()
summary_for_user()
answer_context_query()
find_part()
record_interaction()
```

### TaskObject context

TaskObject 是 execution context。Draft 创建之后，主链依赖 TaskObject fields，而不是隐藏的 LLM memory。

### Scene / binding context

`scene_manifest.py` 验证从 Blender 导出的只读 scene manifests。`model_binding.py` 根据 semantic targets 对 scene objects 打分，并生成包含 binding status 和 confidence 的 binding contexts。Planning 当前消费已确认的 `bound` entries，并存储 `bound_object` 和 `binding_candidates`。

### Operation capability context

`OperationRegistry` 和 `OperationSpec` 描述可执行能力。这不同于 prompt context：prompt context 帮助语言理解；registry context 控制实际可以执行什么。

### Runtime context

`ExecutionContext` 注入 domain handlers、persistence API、report writer 和 clock。它是 Runtime 的依赖边界。

### Report / feedback context

Runtime reports 和 `OperationOutcome` 描述执行后发生了什么。当前 reports 对审计有用。完整的 report-to-planning feedback loop 尚未实现。

### Implementation/document difference

已确认差异：`capabilities.json` 和部分 session constraints 仍然描述早期的 abstract-planning-only agent。当前代码和 README 已经支持通过 TaskObject、Runtime、Domain 和 Core API 进行受控真实 Blender 修改。未来 cleanup 应更新这些 context files，避免 prompt context 低估当前能力。

## 8. Planning Layer

Planning 实现在 `3d_agent/planning` 中。

`plan_task()` 组合五个阶段：

```text
validate_draft_task()
resolve_task_binding()
select_operation()
complete_parameters()
check_safety_policy()
```

### Validation

`validator.py` 要求：

```text
state == draft
source.user_input
task_type == surface_detail_enhancement
target.semantic_part
intent.desired_effect
intent.style
intent.density
intent.scale
```

它会把 task 推进到 `validated`。

### Target binding

`binding_resolver.py` 要求任务处于 validated 状态，并且提供 scene manifest 或现有 binding context。当传入 scene manifest 时，它使用 `model_binding.create_model_binding_context()`。它只接受已确认的 `bound` bindings 进入执行，并把第一个 bound object 存为 `target.bound_object`。

当前限制：binding confidence 存在于 model binding output 中，但 TaskObject target 只存储 `bound_object` 和 `binding_candidates`；它没有存储 confidence score 或 user confirmation status。

### Operation selection

`operation_selector.py` 按以下条件过滤 specs：

```text
task_type
required_target_state
execution_policy.mode / safety_level
```

它支持通过 `task.intent.parameters["operation"]` 显式选择 operation。如果没有显式指定，它会给 compatible specs 打分：

```text
intent.action match: +40
intent.detail_type match: +30
intent.desired_effect match: +20
```

它使用 priority 和 name 作为确定性 tie-breakers，但如果多个 best specs 具有相同 score 和 priority，则失败。如果没有 compatible spec 获得 intent match，也会以 ambiguous 失败。

### Parameter completion

`parameter_completer.py` 会合并 `OperationSpec.default_parameters` 和显式 `TaskIntent.parameters`。它会在 Domain execution 之前去掉 planning-only 的 `operation` 参数。

当前支持的 schema types：

```text
number
string
string enum
exclusive_minimum for numbers
```

当前限制：boolean、integer、完整 min/max、style profiles、density profiles、scale profiles 和 degree-word mapping 尚未完整建模。例如，用户表达中的 “slightly”、“dense”、“heavy armor” 或 scale-specific values 还没有系统地转换为 parameter profiles。

### Safety policy

`safety_policy_checker.py` 要求：

```text
safe_non_destructive mode
preserve_source_file == true
non_destructive == true
mesh_edit_allowed == false
output_blend_copy present
report_file present
output copy does not equal source file
```

它会把 task 推进到 `ready_to_execute`。

## 9. Operation Registry and OperationSpec

`OperationSpec` 定义在 `3d_agent/domain/operation_contracts.py` 中。它代表受控 operation contract，而不是 Blender API 调用。

字段包括：

```text
name
supported_task_types
required_target_state
default_parameters
parameter_schema
safety_level
handler_name
report_schema
intent_actions
intent_detail_types
intent_effects
priority
```

`3d_agent/domain/operation_registry.py` 中的 `OperationRegistry` 存储 static specs，并暴露 `register()`、`get()`、`has()`、`all_specs()` 和 `supported_for_task_type()`。

从代码中确认已实现 operations：

| Operation | 设计目的 | Core 机制 | Non-destructive | 设计原则 |
| --- | --- | --- | --- | --- |
| `edge_soften` | 软化机械边缘和基础表面细节 | `add_bevel_modifier` | yes, modifier-only | 受控边缘细化 |
| `weighted_normal_finish` | 改善硬表面高光/着色流动 | `add_weighted_normal_modifier` | yes, modifier-only | 不做 mesh edit 的 finish pass |
| `solidify_thickness_preview` | 预览装甲厚度 | `add_solidify_modifier` | yes, modifier-only | Copy-safe mass/thickness preview |
| `panel_line_bevel_prepare` | 准备 panel 或 parting line 基础 | `add_bevel_modifier` | yes, modifier-only | Surface/panel vocabulary |
| `armor_layer_plate_prepare` | 预览分层装甲板深度 | `add_solidify_modifier` | yes, modifier-only | Armor layering capability |
| `vent_slot_prepare` | 准备 vent 或 grille 细节 | `add_bevel_modifier` | yes, modifier-only | Functional mechanical detail |
| `thruster_nozzle_prepare` | 准备 thruster/nozzle 细节 | `add_bevel_modifier` | yes, modifier-only | Propulsion design detail |
| `hardpoint_socket_prepare` | 准备 weapon/equipment mount socket | `add_bevel_modifier` | yes, modifier-only | Functional interface detail |
| `surface_inset_prepare` | 准备 recessed/inset surface | `add_solidify_modifier` | yes, modifier-only | Recessed surface detail |
| `armor_edge_lip_prepare` | 准备 armor edge lip/trim | `add_bevel_modifier` | yes, modifier-only | Mechanical edge trim |

## 10. Atomic Operation Library v1

系统从 atomic operations 开始，是因为每个 operation 都必须在组合成更大流程之前先做到安全、可测试、可解释、可复用。Composite system 会在基础词汇表被验证之前放大失败场景。

当前 operation set 可以这样分类：

| Category | Operations |
| --- | --- |
| Surface / Panel | `edge_soften`, `panel_line_bevel_prepare`, `surface_inset_prepare`, `armor_edge_lip_prepare` |
| Form / Mass | `solidify_thickness_preview`, `armor_layer_plate_prepare` |
| Functional Detail | `vent_slot_prepare`, `thruster_nozzle_prepare`, `hardpoint_socket_prepare` |
| Finish | `weighted_normal_finish` |

这形成了一套用于机甲和硬表面建模的小型领域特定 operation language。它覆盖 panelization、layered armor、vents、thrusters、mount sockets、insets、armor trims、thickness preview 和 hard-surface shading finish。

这些 operations 的共同属性是：

```text
modifier-only
non-destructive
reusable
composable later
controlled by OperationSpec
executed by Runtime + Domain + Core pipeline
reported through structured Runtime reports
```

## 11. Runtime Layer

Runtime 实现在 `3d_agent/runtime/runtime_engine.py` 和 `runtime/execution_context.py` 中。

`execute_ready_task()` 只接受 `TaskObject(state=ready_to_execute)`。它会在任何副作用之前拒绝其他状态。然后它会：

```text
builds DomainOperationInput.from_task_object(task)
resolves source_blend_file
validates output_blend_copy path
marks task executing
looks up domain handler from ExecutionContext.domain_handlers
calls handler
saves output blend copy through persistence API
writes success report
marks task completed
```

失败处理是 stage-based。Runtime 会把失败包装成 `RuntimeExecutionError(stage, original_error)`；如果 task 仍处在可执行状态，则将其标记为 failed，并尝试写入 failure report。已知 stages 包括 `state`、`domain_input`、`persistence_policy`、`domain_operation`、`persistence`、`report_writer` 和通用 `execution`。

Runtime 不理解自然语言，不选择 operation，不补全参数，也不直接调用 Core geometry helpers。如果 handler 缺失，它会失败，而不是 fallback 到另一个 operation。

`default_execution_context()` 静态地把十个 operation names 映射到对应 domain handlers，并注入 `core_api` 作为 persistence API，同时注入 `report_writer`。

## 12. Domain Operation Layer

Domain contracts 定义在 `3d_agent/domain/operation_contracts.py` 中。

`DomainOperationInput` 是最小化输入：

```text
task_id
operation
target_object
parameters
execution_policy
```

`DomainOperationInput.from_task_object()` 要求任务处于 `ready_to_execute` 状态，并拒绝 domain execution policy 中的 artifact paths。这可以防止 Domain 接收 report/output paths。

Domain handlers 位于 `3d_agent/blender_ops/domain_operations.py`。每个 handler：

```text
checks operation_input.operation
extracts and validates operation-specific parameters
calls core_geometry_api.require_object()
calls a Core API modifier helper
returns OperationOutcome
```

代表性复用关系：

```text
Bevel helper: edge_soften, panel_line_bevel_prepare, vent_slot_prepare, thruster_nozzle_prepare, hardpoint_socket_prepare, armor_edge_lip_prepare
Solidify helper: solidify_thickness_preview, armor_layer_plate_prepare, surface_inset_prepare
Weighted normal helper: weighted_normal_finish
```

测试确认 Domain handlers 不保存副本、不写报告，并且 outcomes 中不包含 output/report artifacts。Domain 会 `import core_api as core_geometry_api`，但它不直接 import `bpy`；实际 `bpy` 访问藏在 Core API 后面。

## 13. Core API Layer

Core API 实现在 `3d_agent/core_api` 下。

关键 helpers：

```text
require_object()
object_snapshot()
modifier_snapshot()
add_bevel_modifier()
add_solidify_modifier()
add_weighted_normal_modifier()
remove_or_replace_named_modifier()
record_modified_object()
record_removed_modifier()
reset_modification_report_state()
save_as_copy_only()
build_modification_report()
write_modification_report()
```

`scene_object_api.py` 导入 Blender `bpy` 来解析对象。`persistence_api.py` 导入 `bpy` 来保存副本，并构建 low-level reports。`geometry_api.py` 操作 object/modifier collections，并记录 low-level modification facts。

安全属性：

```text
same-named modifier is removed/replaced before adding a new one
source overwrite is rejected
current opened file overwrite is rejected
mesh_data_applied is recorded as false for current operations
output directories are created as needed
```

这个边界很重要，因为 Blender API access 被隔离了。Planning、Runtime、Domain contracts 和 tests 都可以在不 import `bpy` 的情况下被推理和测试。它也让测试中注入 fake Core APIs 变得容易。

## 14. Reporting and Diagnostics

Reporting 位于 `3d_agent/reporting` 下。

`build_operation_report()` 生成：

```text
report_version
execution_status
task_id
operation
target_object
parameters
changed_objects
operation_outcome
source_blend_file
output_blend_copy
saved_original_file
```

`build_failure_report()` 会额外添加：

```text
error_stage
error_type
error_message
```

`OperationOutcome` 包括：

```text
operation
target_object
success
changed_objects
modifier_info
mesh_data_applied
diagnostics
```

优势：

```text
reports are structured JSON
success and failure are stage-aware
changed objects and modifier info are captured
TaskObject.result points to artifacts
source file preservation is explicit
```

当前缺口：

```text
post-check facts are not yet systematically modeled
reports do not yet feed back into future Planning
failure reports do not yet generate retry guidance
user preference profiles are future work
```

## 15. Testing and Validation

测试位于 `tests/` 下。完整测试套件当前通过以下命令报告 366 个测试通过：

```text
python -m unittest discover -s tests
```

从测试文件中确认的覆盖范围：

| Area | Representative tests |
| --- | --- |
| Agent Layer | `test_agent_layer_task_creation.py` |
| TaskObject schema/lifecycle/ownership | `test_task_object_schema.py`, `test_task_object_lifecycle.py`, `test_task_object_ownership.py` |
| Legacy fact-source cleanup | `test_task_object_legacy_fact_sources.py` |
| Planning validation/binding/selection/parameters/safety | `test_planning_*.py`, `test_planning_engine_flow.py` |
| Operation registry/contracts | `test_operation_registry.py`, `test_domain_operation_contracts.py` |
| Runtime | `test_runtime_execution_flow.py` |
| Domain operations | `test_phase_2_domain_operations.py` |
| Core API | `test_phase_2_core_geometry_api.py` |
| CLI and fake E2E | `test_phase_2_cli_execution_flow.py`, `test_end_to_end_task_object_flow.py` |
| Reporting | `test_reporting.py` |
| Legacy preview/authoring modules | `test_v0_*` files |

Fake E2E test 会从自然语言创建 draft task，使用 fake scene manifest 进行 planning，用 fake persistence/reporting 执行，并验证 TaskObject 在不使用真实 Blender 的情况下完成。

手动 real Blender smoke test 位于 `scripts/run_step20_blender_smoke.py`。它通过 `3d_agent/cli.py --task-file` 进入，使用 `examples/BlendFile/Gundam/GF-Gundam.blend`，对 `Body_Armor01` 应用 `edge_soften`，验证输出 `.blend` 副本，验证 Runtime report，并检查源文件 hash 未变化。

当前验证限制：

```text
real Blender smoke covers edge_soften only
full natural-language-to-real-Blender smoke is not confirmed from code
multi-operation real smoke matrix is not yet implemented
TaskPlanning supports one selected_operation, not a sequence
```

## 16. Architectural Strengths

对于面试场景，最强的架构点包括：

```text
clear separation of concerns
explicit state-based execution model
TaskObject as single source of truth
field ownership guard by architecture layer
controlled OperationRegistry instead of arbitrary tool calls
LLM-safe execution boundary
Core API isolation for Blender bpy
non-destructive copy-only persistence
reusable atomic operation library
structured Runtime reports
stage-aware failure handling
testability through fake handlers and fake persistence
extension through OperationSpec + Domain handler without changing the main chain
avoidance of premature composite/sequence abstraction
```

这是 production-minded agent design，因为该架构把执行视为受治理的生命周期，而不是 chat completion 的副作用。

## 17. Unique Design Highlights

与朴素的 LLM tool-calling agent 相比，这个系统有几个值得注意的设计选择：

1. LLM 不是执行者。
2. 自然语言被翻译成结构化 task state。
3. Operation selection 是 metadata-driven，并且确定性足够支持测试。
4. Blender APIs 被隐藏在 Core API 后面。
5. Atomic operations 是语义化设计能力。
6. Domain handlers 是固定代码，不是生成脚本。
7. Runtime 在 handler 缺失时拒绝执行，而不是临场发挥。
8. 创建输出副本，而不是覆盖源文件。
9. Reports 保留执行证据。
10. 项目把机甲建模动作视为一种领域特定 operation language。

结果不是一个通用 scripting chatbot，而是一个用于真实 3D 建模工作流的受控执行架构。

## 18. Current Limitations

代码/文档确认或强烈支持的限制：

```text
Parameter accuracy still needs improvement.
style / density / scale are captured in TaskIntent but not fully connected to parameter profiles.
Parameter schema currently supports number/string patterns, not a full schema language.
Target binding confidence exists in binding context but is not stored as a first-class TaskObject field.
User confirmation for ambiguous binding is not fully modeled in the TaskObject lifecycle.
Runtime preflight/post-check could be expanded into explicit reportable stages.
Runtime reports do not yet feed back into future Planning.
Real Blender smoke coverage is incomplete and currently centered on edge_soften.
Composite operation / sequence is intentionally postponed.
Object creation, boolean workflows, mesh edit workflows, and material systems are not current Core capabilities.
Some context JSON capability text is older than the current implementation.
```

代码中尚未确认：

```text
A complete natural-language-to-real-Blender smoke covering ContextManager, Agent Layer, Planning, Runtime, Domain, and Core in one real Blender run.
A persistent TaskObject store beyond CLI stdout, task files, and generated artifacts.
An automatic user preference profile derived from feedback.
```

## 19. Next-Phase Optimization Roadmap

### 19.1 Architecture / Accuracy Improvements

1. Operation parameter accuracy analysis

   为每个 operation 定义 parameter profiles。把 `style`、`density`、`scale` 和 degree words 映射到 parameters。例如：panel line width 和 segment count 应响应比例和视觉密度。

2. Operation selection accuracy review

   审查 `intent_actions`、`intent_detail_types`、`intent_effects`、priority，以及 specs 之间的 overlap。为中文自然语言表达和 ambiguous requests 添加更多测试用例。

3. Target binding accuracy review

   在需要时，将 binding confidence、binding evidence 和 user confirmation 提升到主 TaskObject flow 中。

4. Runtime preflight and post-check

   增加显式检查：source path existence、expected modifier existence、modifier parameters、output existence、report existence 和 source hash unchanged。

5. Report-to-planning feedback loop

   将 prior failures 和 user feedback 作为 Planning context 使用，但不要把 reports 变成第二个事实源。

6. Real Blender smoke matrix

   将手动 smoke coverage 从 `edge_soften` 扩展到完整 Atomic Operation Library v1。

7. Maintenance/refactor review

   在 operation set 稳定后，考虑按 category 拆分 OperationSpec definitions。只有在当前文件变得难以维护时，才考虑 handler grouping。

### 19.2 Functional Improvements

```text
Composite operation planning after enough real use cases
Object creation boundary design
Boolean / mesh edit safety strategy
Material system strategy
More real modeling operations after evaluation
```

推荐顺序是先做 architecture 和 accuracy，再扩展 broader functionality。

## 20. Interview Presentation Version

### 20.1 30-second version

我构建了一个用于硬表面机甲建模的受控 Blender 修改 Agent。它不是让 LLM 生成任意 Blender 脚本，而是把自然语言转成有状态的 `TaskObject`，根据安全设计 operations 的 registry 进行规划，分发到确定性的 Runtime handlers，并把 Blender `bpy` 隔离在 Core API 后面。系统写入输出 `.blend` 副本和结构化报告，因此源文件受到保护，执行过程也可审计。

### 20.2 2-minute version

这个架构围绕 TaskObject-centered lifecycle 构建。Agent Layer 只理解用户请求并创建 draft task。Planning 随后验证任务、根据 scene manifest 把 semantic target 绑定到 Blender object、从 `OperationRegistry` 选择 operation、从 `OperationSpec` 补全参数，并检查安全策略。Runtime 只接受 `ready_to_execute` tasks。它派生一个最小化的 `DomainOperationInput`，分发到已注册的 Domain handler，保存输出副本，写入报告，并把任务标记为 completed 或 failed。

重要设计决策是：LLM 永远不直接调用 Blender，也不为真实修改写可执行脚本。Domain operations 是固定代码，例如 `edge_soften`、`panel_line_bevel_prepare` 和 `weighted_normal_finish`。它们调用 Core API helpers，例如 `add_bevel_modifier`、`add_solidify_modifier` 和 `add_weighted_normal_modifier`。Core API 是唯一接触 `bpy` 的层。

这为项目带来了清晰的安全边界、可测试的状态转换、结构化报告，以及用于机甲建模的可复用 atomic operation library。

### 20.3 Deep-dive version

从 TaskObject 开始。它是 single source of truth，包含 source input、target、intent、constraints、execution policy、planning、runtime、result、diagnostics 和 artifacts。Lifecycle module 控制有效状态转换。Ownership module 控制哪一层可以修改哪些字段。

然后解释 Planning。Planning 不执行。它通过 validation、binding、operation selection、parameter completion 和 safety policy，把 draft 变成 ready task。

然后解释 Runtime。Runtime 不做 planning。它只执行 ready tasks、分发 selected operation、协调 persistence/reporting，并标记 success 或 failure。

然后解释 Domain 和 Core。Domain handlers 是 design operations。Core helpers 是 Blender API boundaries。这种拆分防止自由形式 LLM 行为泄漏到执行中。

最后解释 evaluation。系统对 TaskObject、Planning、Runtime、Domain、Core、reporting 和 fake E2E 都有单元测试，并有一个手动 real Blender smoke test。

### 20.4 What to emphasize to an interviewer

```text
Production-minded agent design
Safety and control over model execution
State modeling and field ownership
Separation of natural language, planning, execution, and low-level API access
Evaluation-driven growth
Domain-specific operation library design
Trade-off: atomic operations first, composite operations later
```

## 21. Teaching Version

一个朴素 Agent 可能接收这个请求：

```text
Add mechanical details to the chest armor.
```

然后要求 LLM 生成 Blender Python。这会带来若干风险：未知 APIs、文件覆盖、破坏性 edits、较差的可重复性，以及缺少可复用能力。

这个架构通过拆分流程来解决问题：

```text
Language understanding -> structured TaskObject
Planning -> controlled operation choice
Runtime -> deterministic dispatch
Domain -> fixed operation handler
Core -> bounded Blender API call
Report -> audit trail
```

如何理解 agent state：

```text
State is not chat history.
State is the structured contract between layers.
A task should be inspectable before and after every stage.
```

如何设计 controlled tools：

```text
Expose domain operations, not raw API access.
Make operations small enough to test.
Make parameters explicit.
Make unsafe behavior impossible by construction.
```

如何分离 semantic intent 和 execution：

```text
"Make this look more mechanical" is intent.
"Select panel_line_bevel_prepare" is planning.
"Call add_bevel_modifier" is implementation.
```

如何在不过度工程化的前提下成长：

```text
Start with atomic operations.
Collect real usage patterns.
Only then introduce composite operations or sequence planning.
```

## 22. Appendix

### Repository structure summary

```text
3d_agent/
  agent/                 legacy classifier/parser and older preview/blueprint helpers
  agent_layer/           TaskObject draft creation boundary
  blender_ops/           Domain operation handlers and compatibility wrappers
  context/               static design/capability JSON
  core_api/              Blender object, geometry, persistence helpers
  domain/                OperationSpec, OperationRegistry, DomainOperationInput, OperationOutcome
  integration/           older Blender script execution bridge
  model/                 model context, scene manifest, model binding, ContextManager
  model_contexts/        abstract Gundam model context JSON
  planning/              validator, binding, selector, parameter completer, safety policy, planning engine
  reporting/             Runtime report builders/writer
  runtime/               Runtime engine and execution context
  session/               design brief, working plan, interaction summary

docs/                    architecture and development documents
scripts/                 manual Blender smoke runner
tests/                   unittest suite
examples/                sample Blender/manifest assets
outputs/                 generated artifacts
```

### Key modules and files

| Area | Files |
| --- | --- |
| Task model | `3d_agent/task_object/schema.py`, `lifecycle.py`, `ownership.py` |
| Agent Layer | `3d_agent/agent_layer/agent_service.py`, `legacy_intent_adapter.py` |
| Context | `3d_agent/model/context_manager.py`, context/session/model JSON files |
| Planning | `3d_agent/planning/*.py` |
| Operation contracts | `3d_agent/domain/operation_contracts.py`, `operation_registry.py` |
| Runtime | `3d_agent/runtime/runtime_engine.py`, `execution_context.py` |
| Domain operations | `3d_agent/blender_ops/domain_operations.py` |
| Core API | `3d_agent/core_api/*.py` |
| Reporting | `3d_agent/reporting/*.py` |
| Entry points | `3d_agent/cli.py`, `3d_agent/main.py`, `start-agent-copilot.bat` |
| Smoke | `scripts/run_step20_blender_smoke.py` |

### Main data structures

```text
TaskObject
TaskSource
TaskTarget
TaskIntent
TaskConstraints
ExecutionPolicy
TaskPlanning
TaskRuntime
TaskResult
OperationSpec
OperationRegistry
DomainOperationInput
OperationOutcome
ExecutionContext
PersistenceResult
```

### Main execution flow

```text
create_draft_task()
-> plan_task()
   -> validate_draft_task()
   -> resolve_task_binding()
   -> select_operation()
   -> complete_parameters()
   -> check_safety_policy()
-> execute_ready_task()
   -> DomainOperationInput.from_task_object()
   -> domain handler
   -> core_api helper
   -> save_as_copy_only()
   -> build_operation_report()
   -> write_report()
```

### Implemented operations table

| Operation | Category | Core helper |
| --- | --- | --- |
| `edge_soften` | Surface / Panel | `add_bevel_modifier` |
| `weighted_normal_finish` | Finish | `add_weighted_normal_modifier` |
| `solidify_thickness_preview` | Form / Mass | `add_solidify_modifier` |
| `panel_line_bevel_prepare` | Surface / Panel | `add_bevel_modifier` |
| `armor_layer_plate_prepare` | Form / Mass | `add_solidify_modifier` |
| `vent_slot_prepare` | Functional Detail | `add_bevel_modifier` |
| `thruster_nozzle_prepare` | Functional Detail | `add_bevel_modifier` |
| `hardpoint_socket_prepare` | Functional Detail | `add_bevel_modifier` |
| `surface_inset_prepare` | Surface / Panel | `add_solidify_modifier` |
| `armor_edge_lip_prepare` | Surface / Panel | `add_bevel_modifier` |

### Test coverage summary

```text
Full unittest suite: 366 tests passing
TaskObject lifecycle and ownership: covered
Agent draft creation: covered
Planning stages: covered
OperationRegistry and OperationSpec: covered
DomainOperationInput and OperationOutcome: covered
Runtime success/failure flow: covered
Domain handlers: covered with fake Core API
Core API helpers: covered with fake bpy-style objects
Fake E2E TaskObject flow: covered
Manual real Blender smoke: edge_soften only
```

### Suggested diagrams

1. Layered execution diagram: Agent -> TaskObject -> Planning -> Runtime -> Domain -> Core -> Blender.
2. TaskObject lifecycle diagram: draft through completed/failed.
3. Field ownership matrix: Agent, Planning, Runtime, Reporting, Domain.
4. Operation capability diagram: OperationSpec -> selector -> handler -> Core helper.
5. Safety boundary diagram: LLM outside execution, `bpy` inside Core only.
