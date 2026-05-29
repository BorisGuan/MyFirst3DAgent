# Agent 全局架构设计说明

## 0. 总览

当前系统已经收敛为一个以 `TaskObject` 为主事实源的 state-based Agent 架构。真实模型修改不再由 LLM 生成任意 Blender 脚本，也不再由 legacy `OperationPlan`、execution package 或 operation dict 执行，而是通过受控主链完成：

```text
Agent Layer
-> TaskObject
-> Planning Engine
-> Runtime Engine
-> DomainOperationInput
-> Domain Operation
-> Core API
-> Blender bpy
-> output .blend copy + Runtime report
```

当前 Atomic Operation Library v1 已经完成：10 个 modifier-only、non-destructive、可复用的基础 operations 全部通过这条主链执行，不改变主架构。

最新验证基线：

```text
python -m unittest discover -s tests
Ran 366 tests: OK
```

本文档的目的不是规划下一个 operation，而是完整描述当前 Agent 全局架构、上下文管理、执行边界、准确性来源和下一阶段性能/准确性提升入口。

## 1. 核心原则

### 1.1 TaskObject 是主事实源

真实修改链路中的核心事实都落在 `TaskObject` 中：

```text
source.user_input
source.metadata
task_type
target.semantic_part
target.bound_object
target.binding_candidates
intent.action
intent.detail_type
intent.desired_effect
intent.style
intent.density
intent.scale
intent.parameters
constraints
execution_policy
planning.selected_operation
planning.parameters
planning.reasoning
runtime
result
artifact_refs
diagnostics
state
```

`TaskObject` 的价值是避免多事实源回潮。以下对象不能再成为真实执行入口：

```text
OperationPlan
Execution Blueprint
Execution Package
operation dict
preview script
authoring script
implementation hint
```

### 1.2 LLM 不直接执行

LLM/Agent 可以参与：

```text
理解用户输入
生成或修正 intent
解释候选目标和候选 operation
在受控 action 集内推动状态流转
```

LLM/Agent 不允许：

```text
直接调用 bpy
生成任意 Blender Python 脚本并执行
绕过 OperationSpec
绕过 Runtime
绕过 Domain/Core 边界
覆盖源 .blend 文件
```

### 1.3 Operation 是受控能力，不是 Blender API wrapper

Atomic Operation 是设计语义上的最小可复用动作，不是底层 API 名称。

```text
panel_line_bevel_prepare 是设计动作
add_bevel_modifier 是 Core API 实现手段
BEVEL modifier 是 Blender 低层能力
```

同一个 Core helper 可以服务多个 operation：

```text
add_bevel_modifier:
  edge_soften
  panel_line_bevel_prepare
  vent_slot_prepare
  thruster_nozzle_prepare
  hardpoint_socket_prepare
  armor_edge_lip_prepare

add_solidify_modifier:
  solidify_thickness_preview
  armor_layer_plate_prepare
  surface_inset_prepare

add_weighted_normal_modifier:
  weighted_normal_finish
```

### 1.4 Copy-only 是当前回滚基础

当前不依赖 Blender undo 作为回滚机制，而是保持源文件不可变：

```text
source .blend 不覆盖
真实修改保存到 output_blend_copy
失败或不满意时丢弃 output copy
Runtime report 记录执行事实
```

## 2. 上下文管理设计

当前系统的上下文管理不是单一聊天历史，也不是把所有信息塞进 prompt。它是分层上下文体系，每类上下文服务不同阶段。

```text
Static design context        -> 帮 Agent 理解设计语言
Model context                -> 帮 Agent 理解可用部位和抽象模型信息
Session context              -> 保存项目目标、工作计划、近期交互摘要
TaskObject context           -> 真实执行主链的结构化任务事实
Scene / binding context      -> 帮 Planning 绑定 Blender object
Operation capability context -> 帮 Planning 选择可执行 operation
Runtime context              -> 注入执行依赖和 handler map
Report / feedback context    -> 记录执行结果和失败原因
```

这些上下文不能混为一层：

```text
LLM hidden conversation state 不是主事实源
ContextManager summary 不是执行输入
Runtime report 不是 TaskObject 主链事实本身
DomainOperationInput 不是完整 TaskObject
```

### 2.1 静态设计上下文

主要文件：

```text
3d_agent/context/design_taxonomy.json
3d_agent/context/capabilities.json
model_contexts/00_base_gundam.json
```

作用：

```text
design_taxonomy.json: detail_types / operations / actions / styles / symmetries / scales / densities
capabilities.json: Agent 能力说明和限制
model_contexts/*.json: 抽象模型部位、别名、分类
```

消费者：

```text
ContextManager
classifier
intent parser
Agent Layer
```

### 2.2 会话上下文

主要文件：

```text
3d_agent/session/design_brief.json
3d_agent/session/working_plan.json
3d_agent/session/interaction_summary.json
```

作用：

```text
design_brief: 当前项目目标、风格、约束、重点部位
working_plan: 当前工作阶段
interaction_summary: 最近交互摘要
```

当前限制：

```text
会话上下文主要进入 Agent prompt summary
还没有系统性进入 Planning 参数推导
还没有形成用户偏好 profile
```

### 2.3 ContextManager

`ContextManager` 负责加载长期/会话上下文，并生成 prompt-sized summaries。

主要接口：

```text
summary_for_classifier()
summary_for_planner()
summary_for_user()
answer_context_query()
find_part()
record_interaction()
```

自然语言入口中的上下文流：

```text
user_input
-> ContextManager.summary_for_classifier()
-> classify_command()
-> ContextManager.summary_for_planner()
-> parse_intent()
-> create_task_draft_from_legacy_intent()
-> TaskObject(state=draft)
```

ContextManager 当前做：

```text
判断命令类型
提供设计 taxonomy
提供模型部位摘要
提供最近交互摘要
帮助 intent parser 生成 target/action/detail/style/density/scale
回答用户上下文查询
```

ContextManager 当前不做：

```text
不执行 Planning
不执行 Runtime
不绑定真实 Blender object
不调用 Domain/Core
不接触 bpy
不决定最终 selected_operation
```

### 2.4 TaskObject 上下文

`TaskObject` 是真实执行上下文。Agent 创建 draft 后，主链后续依赖结构化字段，而不是 LLM 隐式上下文。

责任划分：

```text
Agent 写 source/task_type/target.semantic_part/intent/constraints
Planning 写 target.bound_object/binding_candidates/planning/execution_policy/state
Runtime 写 runtime/result/state
Reporting 写 artifact_refs
Domain 不写 TaskObject
```

这让任务可序列化、可测试、可审计、可恢复。

### 2.5 Scene / Binding 上下文

目标绑定上下文回答“改哪个 Blender 对象”。

输入：

```text
scene_manifest
binding_context
task.target.semantic_part
```

输出：

```text
task.target.bound_object
task.target.binding_candidates
```

当前不足：

```text
binding confidence 不显式
多个候选对象时缺少用户选择机制
对象命名不规范时容易误绑
object type / collection path 过滤还可加强
```

提升入口：

```text
binding candidate ranking
binding explanation
confidence score
user target confirmation
semantic_part alias table
object type filters
collection path filters
```

### 2.6 Operation capability 上下文

Operation capability context 回答“系统会做什么”。由 `OperationRegistry` 和 `OperationSpec` 提供。

`OperationSpec` 当前字段：

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

Planning 使用：

```text
TaskObject.intent
TaskObject.task_type
TaskObject.execution_policy.mode
OperationRegistry.all_specs()
```

输出：

```text
planning.selected_operation
planning.reasoning
```

关键区别：

```text
Agent prompt context 帮助理解用户语言
OperationRegistry context 决定系统实际可执行能力
```

### 2.7 Runtime context

Runtime context 回答“如何执行”。由 `ExecutionContext` 注入。

```text
domain_handlers
persistence_api
report_writer
clock
```

当前默认 handler map 注册 10 个 operation handlers：

```text
edge_soften
weighted_normal_finish
solidify_thickness_preview
panel_line_bevel_prepare
armor_layer_plate_prepare
vent_slot_prepare
thruster_nozzle_prepare
hardpoint_socket_prepare
surface_inset_prepare
armor_edge_lip_prepare
```

Runtime context 原则：

```text
不理解自然语言
不选择 operation
不补参数
只根据 selected_operation 派发 handler
缺 handler 时失败，不 fallback
```

### 2.8 Report / feedback context

执行结果上下文包括：

```text
Runtime report JSON
OperationOutcome
TaskObject.result
TaskObject.artifact_refs
Core API modified_objects / removed_modifiers
```

当前用途：

```text
记录 success / failed
记录 operation / target_object
记录 changed_objects
记录 modifier_info
记录 output_blend_copy artifact
记录 failure stage / error message
```

当前不足：

```text
Runtime report 还没有系统性反馈给下一轮 Planning
失败 report 还没有自动形成 retry suggestion
operation-level post-check 还不完整
用户偏好还没有从反馈中沉淀
```

提升入口：

```text
report -> next planning context
failure report -> retry guidance
user feedback -> preference profile
post-check facts -> operation quality signal
```

## 3. 全局架构分层

## 3.1 Agent Layer

职责：

```text
接收自然语言
调用 classifier / intent parser
创建 TaskObject(state=draft)
填充 Agent-owned 字段
```

拥有字段：

```text
source
task_type
target.semantic_part
intent
constraints
```

禁止：

```text
不调用 Planning
不调用 Runtime
不调用 Domain/Core
不接触 Blender
不决定最终 selected_operation
```

当前准确性风险：

```text
intent.action/detail_type 可能不够细
style/density/scale 对参数影响还没有被系统化使用
legacy parser taxonomy 可能不足以覆盖新增 operation 语义
```

提升入口：

```text
intent taxonomy 标准化
中文同义表达映射
设计语义同义词表
style/density/scale 结构化稳定性
```

## 3.2 TaskObject Lifecycle / Ownership

职责：

```text
定义任务状态
约束状态转换
约束各层字段所有权
提供序列化 / 反序列化
```

当前状态流：

```text
draft
-> validated
-> bound
-> planned
-> ready_to_execute
-> executing
-> completed / failed
```

当前价值：

```text
让 Agent / Planning / Runtime / Domain 边界可检查
防止 Domain 修改 TaskObject
防止 Runtime 重新规划
防止旧执行入口回流
```

后续可能扩展：

```text
operation_steps
waiting_for_confirmation
attempt / previous_failure
```

当前建议：暂不改 TaskObject schema。先做参数准确性、选择准确性和真实验证分析。

## 3.3 Planning Layer

职责：

```text
validate draft task
resolve target binding
select operation
complete parameters
check safety policy
推进 TaskObject 到 ready_to_execute
```

关键模块：

```text
planning.validator
planning.binding_resolver
planning.operation_selector
planning.parameter_completer
planning.safety_policy_checker
planning.planning_engine
```

### 3.3.1 Operation Selection

当前能力：

```text
按 task_type / state / safety 过滤 OperationSpec
支持 explicit operation 参数
按 intent.action / detail_type / desired_effect 打分
按 priority 做稳定 tie-break
ambiguous 时 fail fast
```

提升入口：

```text
operation selection confidence
intent label normalization
同义词和中文表达扩展
候选 operation 解释
ambiguous 时用户确认机制
OperationSpec metadata 质量复核
```

### 3.3.2 Parameter Completion

当前能力：

```text
OperationSpec.default_parameters + intent.parameters
支持 number / string
支持 enum
支持 exclusive_minimum
过滤 planning-only 参数 operation
```

当前不足：

```text
没有 boolean/integer/min/max 完整 schema
没有 scale/style/density 参数 profile
没有程度词映射：稍微/明显/高密度/重甲
缺少每个 operation 的参数推荐表
```

这是下一阶段最重要的提升入口之一。

建议下一步文档：

```text
docs/operation_parameter_accuracy_analysis.md
```

### 3.3.3 Target Binding

当前能力：

```text
从 scene_manifest 或 binding_context 绑定 semantic_part 到 object_name
记录 bound_object 和 binding_candidates
```

当前不足：

```text
绑定置信度不显式
多个候选时用户选择机制还不完善
模型命名不规范时容易误绑
目标对象类型过滤仍可加强
```

提升入口：

```text
binding confidence
binding explanation
candidate ranking
user target confirmation
semantic_part alias table
```

## 3.4 Operation Registry / OperationSpec

职责：

```text
声明系统支持哪些 operation
声明 task_type/state/safety 兼容性
声明默认参数和参数 schema
声明 intent selection metadata
声明 handler_name
声明 report_schema
```

当前已注册 10 个 operations：

```text
edge_soften
weighted_normal_finish
solidify_thickness_preview
panel_line_bevel_prepare
armor_layer_plate_prepare
vent_slot_prepare
thruster_nozzle_prepare
hardpoint_socket_prepare
surface_inset_prepare
armor_edge_lip_prepare
```

提升入口：

```text
OperationSpec 文件拆分或分组
参数 schema 能力增强
selection metadata 质量审查
operation category 作为维护文档，不急于进 schema
```

## 3.5 Runtime Layer

职责：

```text
只接受 ready_to_execute task
构造 DomainOperationInput
按 selected_operation 派发 handler
协调 persistence
协调 report writer
推进 executing/completed/failed
```

关键保护：

```text
Runtime 不选择 operation
Runtime 不补参数
Runtime 不理解自然语言
缺 handler 时失败，不 fallback
失败记录 RuntimeExecutionError.stage
```

提升入口：

```text
Runtime preflight report
handler map 维护方式
operation-level post-check
失败后 retry policy
用户确认 checkpoint
```

## 3.6 Domain Operation Layer

职责：

```text
接收 DomainOperationInput
检查 operation 名是否匹配
从 parameters 取执行参数
调用 Core API
返回 OperationOutcome
```

禁止：

```text
不写文件
不写 report
不保存 .blend
不改 TaskObject
不理解自然语言
不直接 import bpy
```

当前特点：

```text
每个 operation 是固定代码
LLM 不决定底层 Blender API
多个 operation 可以复用同一个 Core helper
```

提升入口：

```text
重复参数解析 helper 清理
Domain handlers 分组
operation-specific post-check facts
handler table 自动化注册是否值得做
```

当前建议：暂不做 handler 自动注册。

## 3.7 Core API Layer

职责：

```text
唯一触碰 bpy
解析 Blender object
添加/替换 modifier
保存 output copy
记录低层 modified_objects
```

当前 Core helpers：

```text
require_object
object_snapshot
modifier_snapshot
add_bevel_modifier
add_solidify_modifier
add_weighted_normal_modifier
remove_or_replace_named_modifier
save_as_copy_only
write_modification_report
build_modification_report
```

当前保护：

```text
同名 modifier 替换
参数基础校验
记录 mesh_data_applied=false
拒绝覆盖源文件
```

提升入口：

```text
modifier existence verification
operation post-check helper
curve/object creation 边界设计
boolean / mesh edit 安全策略
Core API 分组维护
```

当前建议：在进入 object creation / boolean 之前，不扩大型 Core API。

## 3.8 Reporting / Diagnostics

职责：

```text
记录 execution_status
记录 task_id / operation / target_object
记录 changed_objects
记录 modifier_info
记录 error_stage / error_message
记录 artifact refs
```

提升入口：

```text
operation-specific report detail
preflight report
post-check report
用户确认所需 summary
可视化 preview metadata
```

## 4. 当前能力完成度

### 4.1 Atomic Operation Library v1

状态：完成。

```text
10 / 10 operations completed
modifier-only
non-destructive
single-operation execution
```

### 4.2 Composite / Sequence

状态：暂缓。

原因：

```text
真实组合需求还需要进一步验证
TaskPlanning 当前只有 selected_operation
sequence 会拉动 schema/runtime/report/recovery
```

### 4.3 Real Blender Smoke

状态：已有 edge_soften smoke，未覆盖全部 operation。

提升入口：

```text
operation smoke profile map
ready task fixture per operation
modifier existence check
source hash unchanged check
```

## 5. 下一阶段性能/准确性提升角度

## 5.1 参数准确性

目标：让同一个 operation 在不同 scale/style/density 下得到更合理的参数。

需要分析：

```text
每个 operation 参数含义
当前默认值是否合理
哪些参数对效果最敏感
scale 对参数的影响
style 对参数的影响
density 对参数的影响
用户程度词如何映射参数档位
```

产物建议：

```text
docs/operation_parameter_accuracy_analysis.md
```

## 5.2 Operation 选择准确性

目标：让用户自然语言更稳定地映射到正确 operation。

需要分析：

```text
intent.action/detail_type/desired_effect 规范
中文同义表达
operation metadata overlap
selector tie-break 是否合理
ambiguous 时是否需要问用户
```

## 5.3 目标绑定准确性

目标：确保操作改的是正确对象。

需要分析：

```text
semantic_part alias
scene_manifest object naming
binding confidence
多个候选对象选择
target object type filtering
用户确认目标对象机制
```

## 5.4 执行可靠性

参考文档：

```text
docs/agent_execution_reliability_design.md
```

需要分析：

```text
Runtime preflight
post-check
failure report completeness
retry/user confirmation
source unchanged verification
```

## 5.5 真实 Blender 验证覆盖

需要分析：

```text
smoke runner operation profile map
每个 operation 的 ready task template
输出 copy / report / modifier existence 验证
是否仍保持手动 smoke，不进默认 unittest
```

## 5.6 性能与维护性

需要分析：

```text
OperationSpec 是否拆文件
Domain handler 是否分组
重复参数 helper 是否整理
测试是否 table-driven
Runtime handler map 是否继续静态维护
```

## 6. 建议评估顺序

建议先从准确性最高收益处开始：

```text
1. Operation Parameter Accuracy Analysis
2. Operation Selection Accuracy Review
3. Target Binding Accuracy Review
4. Runtime Preflight / Post-check Design
5. Real Blender Smoke Matrix
6. Maintenance / Refactor Review
```

理由：

```text
参数准确性直接影响设计效果
选择准确性决定是否调用对的 operation
绑定准确性决定是否改对对象
可靠性和 smoke 决定是否能安全交付
维护性优化应在问题明确后再做
```

## 7. 当前不建议马上做的事

```text
Composite Operation implementation
operation sequence
object creation
boolean / mesh edit
material system
full NL-to-Blender smoke
large refactor of Runtime / Planning / TaskObject
```

原因：这些都会扩大架构面，当前更应该先把已完成的 Atomic Operation Library v1 做准、做稳、做可验证。

## 8. 结论

当前系统已经具备一个可运行、可扩展、边界清晰的 Atomic Operation Agent 主链。

下一阶段不应继续盲目增加 operation，也不应直接进入 Composite。更合理的入口是：

```text
Operation Parameter Accuracy Analysis
```

也就是先回答：

```text
这些固定 operation 在不同用户指令、比例、风格、密度下，参数应该如何更准确？
```

这会直接提升用户感知到的“Agent 操作准确性”。
