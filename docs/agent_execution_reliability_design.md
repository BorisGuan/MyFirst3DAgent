# Agent Execution Reliability Design

## 0. 总结

本文件说明 3D Agent 系统如何保证操作准确性，以及在出错时如何保护源文件、记录原因、停止或继续推进。核心结论是：Agent 的准确性不能靠 LLM 一次性判断正确，而要靠 `TaskObject` 状态机、Planning 校验、OperationSpec 契约、Runtime 边界、Domain/Core 白名单、copy-only 保存策略、报告和后续 validation 共同保证。

当前系统的执行主链是：

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

LLM/Agent 只负责理解用户意图，不直接调用 Blender API。真实执行只允许通过已注册 operation 进入 Domain/Core，再由 Core API 调用 `bpy`。

## 1. 准确性来源

准确性不是单点能力，而是分布在整个链路中。

| 层 | 准确性职责 |
| --- | --- |
| Agent Layer | 理解用户输入，生成 `TaskObject.intent` |
| TaskObject | 保存任务事实、状态、目标、规划和结果 |
| Planning Layer | 验证任务、绑定目标、选择 operation、补全参数、检查安全策略 |
| Runtime Layer | 只执行 ready task，派发已选 operation，协调保存和报告 |
| Domain Operation | 只执行单个领域 operation，不保存文件、不写 report、不改 TaskObject |
| Core API | 唯一触碰 Blender `bpy` 的层，执行低层 modifier/object 操作 |
| Reporting / Validation | 记录执行结果、错误阶段、变更对象和 artifact |

因此系统不是：

```text
LLM 判断正确 -> 直接执行 Blender 脚本
```

而是：

```text
LLM 只提供意图
-> 系统逐层约束、校验、执行、记录
```

## 2. 操作前保护：Preflight

在真正调用 Blender 前，系统应该确认任务满足执行条件。当前已有一部分 preflight 能力，后续可以整理成更明确的 Runtime preflight 阶段。

应检查：

```text
TaskObject state 是否 ready_to_execute
source_blend_file 是否存在
output_blend_copy 是否不会覆盖源文件
scene target 是否已经绑定到 bound_object
selected_operation 是否存在
selected_operation 是否已注册 Domain handler
parameters 是否通过 OperationSpec.parameter_schema
execution_policy 是否为 safe_non_destructive
DomainOperationInput 是否不携带 report/output artifact path
operation 是否不会 apply mesh data
```

当前已经具备的基础：

```text
TaskObject lifecycle state check
Planning validation
operation registry lookup
parameter completion and schema validation
safety policy check
Runtime ready_to_execute check
DomainOperationInput artifact path rejection
save_as_copy_only source overwrite protection
```

## 3. 操作中保护：边界和白名单

当前系统最重要的执行中保护是分层边界。

```text
Planning 不调用 Runtime / Domain / Core / bpy
Runtime 不选择 operation，不补参数
Domain 不写文件、不写 report、不改 TaskObject
Core API 独占 bpy
CLI 不直接调用 Domain/Core
```

每个 operation 的 Blender 执行逻辑是固定代码，不由 LLM 动态生成。

示例：

```text
edge_soften
-> Domain edge_soften()
-> Core add_bevel_modifier()
-> Blender object.modifiers.new(type="BEVEL")
```

```text
solidify_thickness_preview
-> Domain solidify_thickness_preview()
-> Core add_solidify_modifier()
-> Blender object.modifiers.new(type="SOLIDIFY")
```

固定代码的作用是限制行为边界：

```text
不会删除对象
不会应用 mesh data
不会覆盖源文件
不会临时调用未知 bpy API
不会绕过 Runtime report
```

参数控制设计效果，固定 handler 控制安全范围。

## 4. 操作后验证：Post-check

执行成功不等于设计效果完全正确。Post-check 可以分成技术验证和设计验证。

技术验证可以自动化：

```text
output_blend_copy exists
source_blend unchanged
target object exists
expected modifier exists
modifier type correct
modifier parameters correct
mesh_data_applied == false
Runtime report exists
TaskObject result.success == true
TaskObject result.artifacts points to output copy
```

设计验证更难自动化：

```text
是否更像 RG 风
厚度是否合适
刻线是否太密
是否破坏轮廓
是否符合目标比例
```

短期策略：

```text
Runtime report + preview/smoke artifact + 用户确认
```

长期策略可以考虑：

```text
几何分析
截图/视图检查
视觉模型辅助评估
用户反馈闭环
```

## 5. 错误分类和处理

错误必须按阶段记录，而不是统一吞掉。

| 错误阶段 | 处理方式 |
| --- | --- |
| Agent parse error | 不执行，请用户补充说明 |
| Planning validation error | 停在 draft/validated，不执行 |
| Binding error | 请求用户选择或修正目标对象 |
| Operation selection error | 请求用户明确设计动作或补充意图 |
| Parameter completion error | 请求参数、修正参数或回到默认值策略 |
| Safety policy error | 阻止执行并说明风险 |
| Runtime handler missing | 停止，不自动 fallback 到其他 operation |
| Domain operation error | 标记 failed，写 failure report |
| Core API error | 标记 failed，不保存成功结果 |
| Persistence error | 标记 failed，提示输出路径或保存问题 |

当前系统已有：

```text
PlanningEngineError(stage, original_error)
RuntimeExecutionError(stage, original_error)
TaskObject.state = failed
TaskResult.success = false
failure report
```

## 6. 回滚策略

当前推荐的 rollback 不是依赖 Blender undo，而是 copy-only 策略。

原则：

```text
source .blend 永远不覆盖
所有真实修改保存到 output_blend_copy
失败或不满意时丢弃 output copy
report 记录发生了什么
```

这种策略比尝试在 Blender background mode 里做 undo 更稳定。

当前保护点：

```text
save_as_copy_only refuses source overwrite
ExecutionPolicy.preserve_source_file = true
Runtime owns persistence
Domain 不保存文件
Core report records modified_objects and removed_modifiers
```

## 7. 继续推进策略

当前系统仍是 single selected operation，不是 multi-step sequence。因此当前 resume 策略是：

```text
单 operation 失败
-> TaskObject failed
-> report 记录 error_stage
-> 用户或 Planning 修正输入/参数/目标
-> 生成新的 TaskObject 或重新规划
```

未来如果引入 `operation_steps`，再考虑 step-level resume：

```text
stop_on_first_failure
skip_failed_step
continue_if_noncritical
ask_user_before_continue
retry_step_with_adjusted_parameters
```

但这应当服务真实组合需求，不应提前做通用复杂框架。

## 8. ReAct 如何接入

这里的 ReAct 指 Reason + Act 的 agent 思路，不是前端 React 框架。

本系统可以吸收 ReAct 的思想，但不能让 LLM 直接自由调用 Blender API。安全版本的 ReAct 应该运行在 `TaskObject` 状态机和 operation 白名单之内。

### 8.1 不采用的方式

不允许：

```text
LLM observes user input
-> LLM writes arbitrary bpy script
-> LLM runs Blender command directly
```

原因：

```text
绕过 OperationSpec
绕过 ParameterCompleter
绕过 Runtime dispatch
绕过 DomainOperationInput
绕过 Core API boundary
绕过 save-copy policy
绕过 reporting
风险不可控，难以测试和复现
```

### 8.2 采用的方式

采用受控 ReAct：

```text
Observe: 读取用户输入、TaskObject、scene manifest、operation registry、上次 report
Reason: 生成或修正 TaskObject.intent，解释目标/约束/候选 operation
Act: 只能调用白名单动作，例如 validate、bind、select_operation、complete_parameters、execute_ready_task
Observe: 读取 TaskObject state、Runtime report、错误阶段、artifact
Reason: 决定是否停止、询问用户、修正参数或重新规划
```

ReAct 的 action 必须是系统允许的动作，不是任意工具调用。

允许的 action 类型：

```text
create_draft_task
validate_draft_task
resolve_task_binding
select_operation
complete_parameters
check_safety_policy
execute_ready_task
ask_user_to_choose_target
ask_user_to_confirm_risk
```

不允许的 action 类型：

```text
direct_bpy_call
arbitrary_python_script
overwrite_source_blend
apply_modifier_without_policy
modify_task_from_domain
write_report_from_domain
```

## 9. ReAct 与 TaskObject 的关系

ReAct 的状态不能只存在于 LLM 隐式上下文里。关键事实必须落到 `TaskObject` 或 report 中。

推荐映射：

| ReAct 概念 | 系统承载位置 |
| --- | --- |
| Observation | scene manifest, TaskObject, Runtime report |
| Reasoning | `task.planning.reasoning`, diagnostics, report summary |
| Action | Planning stage function or Runtime execution |
| Action Result | TaskObject state change, OperationOutcome, Runtime report |
| Stop condition | TaskState completed/failed or user confirmation required |

这可以避免 ReAct 变成不可审计的“模型自言自语”。

## 10. 当前能力与后续增强

当前已有可靠性基础：

```text
TaskObject lifecycle
Planning validation
operation registry
intent-aware operation selection
parameter completion
safe_non_destructive policy
Runtime ready state check
DomainOperationInput artifact path rejection
RuntimeExecutionError.stage
failure report
source copy preservation
Domain/Core boundary
modifier-only operations
```

后续可增强项：

```text
明确 Runtime preflight report
operation-level post-check
modifier existence verification
target binding confidence
user confirmation gates
retry policy
step-level rollback/resume for future operation_steps
preview screenshot or viewport validation
parameter profile by style/scale/density
```

这些增强应该按真实需求逐步引入，不应阻塞当前 Atomic Operation library 扩展。

## 11. 结论

Agent 操作准确性来自多层约束，而不是 LLM 自由发挥。

```text
固定 operation handler 保证行为边界
受控参数决定设计效果
TaskObject 保证事实可追踪
Planning 保证选择和校验
Runtime 保证只执行 ready task
Domain/Core 保证 Blender 调用可控
copy-only 策略保证源文件安全
report 保证失败可追溯
```

ReAct 可以作为交互和修正策略，但必须被限制在 TaskObject 状态机、operation registry、Runtime dispatch 和 Core API 边界之内。
