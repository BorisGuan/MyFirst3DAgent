# AI Agent 项目面试复习与答辩手册

本文档用于复习和面试答辩，围绕当前 3D Model Modification Agent 项目说明：面试官可能问什么、系统如何处理、自研架构和流行 Agent/RAG/Memory/MCP/LangGraph 思想有哪些重合点、为什么当前选择自研 controlled execution architecture。

## 1. 30 秒总述

我做的是一个面向 Blender 硬表面/机甲建模工作流的受控执行 AI Agent 系统。它不是让 LLM 直接生成 Blender Python 脚本，而是把自然语言设计意图转换为结构化 `TaskObject`，再通过 Planning Engine 选择受控 operation，通过 Runtime Engine 分发确定性 Domain handler，最后只有 Core API 能接触 Blender `bpy`。系统采用 copy-only 非破坏性执行策略，保存输出 `.blend` 副本，并写入 Runtime report。核心价值是把 LLM 从“不受控执行者”降级为“bounded worker”，让状态、工具、执行和报告由系统 Harness 控制。

## 2. 2 分钟项目讲法

这个项目解决的问题是：LLM 直接生成 Blender 脚本虽然灵活，但风险很高。它可能调用未知 `bpy` API、覆盖源文件、修改错误对象、执行破坏性 mesh edit，也很难测试和审计。

所以我设计了一个 state-based controlled-execution Agent architecture：

```text
User Input
-> Agent Layer
-> TaskObject
-> Planning Engine
-> Runtime Engine
-> DomainOperationInput
-> Domain Operation
-> Core API
-> Blender bpy
-> output .blend copy + Runtime report
```

关键设计包括：

```text
TaskObject 是单一事实源
Planning 负责验证、绑定、选择 operation、补参数、安全检查
Runtime 只执行 ready_to_execute task，不重新规划、不补参数
OperationSpec / OperationRegistry 定义系统可执行能力边界
Domain Operation 是固定代码 handler
Core API 是唯一接触 Blender bpy 的层
输出保存为 copy，不覆盖源 .blend 文件
```

这样做的结果是：LLM 参与理解意图，但不会直接拥有执行控制权。系统可以更好地控制安全边界、测试覆盖、失败归因和后续扩展。

## 3. 最核心的一句话

```text
LLM is a bounded worker, not the control plane.
```

中文解释：

```text
LLM 只是受控 worker，不是系统控制平面。真正控制状态、工具选择、执行和报告的是 TaskObject + Planning + Runtime 组成的 Harness。
```

这句话是面试里最值得强调的架构判断。

## 4. 面试官可能问什么

## 4.1 为什么不让 LLM 直接生成 Blender 脚本？

回答要点：

```text
因为真实 3D 文件修改有副作用，不能把执行权交给不确定文本输出。
```

具体风险：

```text
可能覆盖源 .blend 文件
可能调用任意 bpy API
可能删除对象或应用 destructive mesh edit
可能修改错误对象
失败后难以恢复
难以测试和审计
不能形成可复用操作能力
```

我的系统做法：

```text
LLM 只参与 intent parsing / explanation / retry suggestion
真实执行只能通过 OperationRegistry 中注册过的 operation
Runtime 只分发 selected_operation
Domain handler 是固定代码
Core API 是唯一接触 bpy 的边界
保存 output copy，不覆盖 source file
```

可以补一句：

```text
我不是不用 LLM，而是不让 LLM 直接拥有执行权。
```

## 4.2 TaskObject 解决了什么问题？

回答要点：

`TaskObject` 解决的是 Agent 系统里的多事实源问题。

没有 TaskObject 时，事实可能分散在：

```text
聊天历史
LLM 输出
operation dict
execution package
preview script
runtime result
report file
```

这会导致：

```text
不知道哪个才是当前任务真实状态
Planning 和 Runtime 可能使用不同事实
失败后难以恢复
测试很难写
```

当前系统中，`TaskObject` 保存：

```text
source.user_input
target.semantic_part
target.bound_object
intent.action / detail_type / style / density / scale
constraints
execution_policy
planning.selected_operation
planning.parameters
runtime paths
result
artifact_refs
state
```

它的生命周期是：

```text
draft
-> validated
-> bound
-> planned
-> ready_to_execute
-> executing
-> completed / failed
```

面试表达：

```text
我把 Agent 当前任务事实集中到 TaskObject，避免 OperationPlan、dict、script 等多事实源回潮。每层只能写自己拥有的字段。
```

## 4.3 你的 Agent 架构和 LangGraph 有什么相似点？

相似点：

```text
都有显式 state
都有阶段化 workflow
都强调节点之间的状态传递
都可以做 checkpoint / retry / human-in-the-loop
```

对应关系：

| LangGraph 概念 | 当前项目中的对应物 |
| --- | --- |
| State | `TaskObject` |
| Node | Agent Layer / Planning stages / Runtime stages |
| Edge | TaskObject lifecycle transition |
| Checkpoint | serialized TaskObject / task file / report |
| Tool node | Domain Operation handler |
| Human-in-the-loop | 未来的 user confirmation / binding confirmation |

为什么没有直接用 LangGraph？

```text
这个项目需要非常强的执行边界：Blender 文件不能被随意修改，source .blend 不能被覆盖，operation 必须走 OperationSpec 和 Runtime，Domain/Core 不能被 LLM 绕过。
```

回答方式：

```text
LangGraph 的 state graph 思想和我的 TaskObject lifecycle 很接近。但主项目选择自研，是因为 Blender 文件安全、OperationSpec 契约、copy-only persistence 和 Domain/Core 边界需要更强控制。我可以用 LangGraph 做 mini demo 来证明我理解主流框架，但主项目的核心价值是 domain-specific controlled runtime。
```

## 4.4 你的架构和 ReAct 有什么关系？

ReAct 常见模式是：

```text
Reason -> Act -> Observe -> Reason -> Act
```

当前项目没有完全采用自由 ReAct loop，而是更受控：

```text
Reasoning 发生在 Agent / Planning explanation
Act 只能是 selected_operation
Observe 来自 Runtime report / OperationOutcome
下一轮 Reasoning 未来可以读取 report / feedback memory
```

为什么不直接做自由 ReAct？

```text
自由 ReAct 容易让 LLM 在每轮动态选择工具，增加执行不确定性。当前系统修改真实 Blender 文件，所以选择 controlled state machine 更安全。
```

可以这样回答：

```text
我借鉴 ReAct 的 observe/feedback 思想，但不采用无限自由工具循环。我的 Act 被 OperationRegistry 约束，Observe 被 Runtime report 结构化，下一轮 Planning 可以读取 observation，但不能绕过 TaskObject 主事实源。
```

## 4.5 你的 OperationSpec / OperationRegistry 和 OpenAI tool calling 有什么关系？

相似点：

```text
都把可执行能力声明成结构化 contract
都有参数 schema
都有 tool / handler 名称
都限制模型不能随便调用任意函数
```

不同点：

```text
OpenAI tool schema 通常是面向 LLM 直接选择工具
我的 OperationSpec 是 Planning-facing capability registry
最终选择由 Planning selector + metadata scoring 完成
Runtime 只执行已选 operation
```

OperationSpec 当前包含：

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

面试表达：

```text
我不是把函数直接暴露给 LLM，而是把工具封装成 OperationSpec，包含 safety、handler、参数 schema、intent metadata。这样工具选择和执行都可测试。
```

## 4.6 你的上下文管理怎么设计？

当前上下文分层：

```text
Static design context
Model context
Session context
TaskObject context
Scene / binding context
Operation capability context
Runtime context
Report / feedback context
```

核心原则：

```text
Context 不是事实源，Context 只是给 LLM 的输入装配。
TaskObject 才是当前任务事实源。
```

当前 `ContextManager` 主要负责：

```text
加载 design taxonomy
加载 model context
加载 session context
生成 summary_for_classifier
生成 summary_for_planner
回答 context query
记录 interaction summary
```

后续 `Context Assembly v1` 可以拆成：

```text
Classifier context
Intent parser context
Planning explanation context
User response context
```

面试表达：

```text
我不是把所有上下文塞进 prompt，而是按阶段装配不同 context bundle，并且上下文只作为 LLM 的输入，不替代 TaskObject 主事实源。
```

## 4.7 你的系统有没有 Memory？和四层记忆怎么对应？

当前系统已经有一些 memory-like 结构，但没有完整四层记忆系统。

合理映射：

| 常见记忆类型 | 当前项目对应 |
| --- | --- |
| Working memory | 当前 `TaskObject` |
| Episodic memory | Runtime reports + future feedback memory |
| Semantic memory | design taxonomy + docs RAG + model context |
| Procedural memory | `OperationSpec` + Domain handlers |

关键边界：

```text
不要新建 procedural memory 去复制 OperationSpec。
```

原因：

```text
OperationSpec 已经是系统可执行能力事实源。
如果 procedural memory 也描述系统能做什么，就会产生第二事实源。
```

当前最应该补的是：

```text
Episodic memory = execution_history.jsonl + feedback_memory.jsonl
Semantic memory = docs / taxonomy / operation docs RAG
```

面试表达：

```text
我会把 Runtime report 和用户反馈沉淀成 episodic memory，作为下一轮 Planning 的 evidence，但不会让 memory 覆盖 TaskObject 当前事实。
```

## 4.8 你的系统需要 RAG 吗？RAG 放在哪一层？

需要，但不是放在 Runtime，也不是直接决定操作。

正确定位：

```text
RAG = evidence provider
```

不是：

```text
RAG = decision maker
```

RAG 可以检索：

```text
architecture docs
operation docs
OperationSpec summaries
design taxonomy
parameter guidelines
runtime reports
failure cases
evaluation reports
```

架构位置：

```text
RAG evidence
-> Context Assembly
-> Agent / Planning explanation
-> OperationSelector 仍然基于 OperationSpec 做最终选择
-> Runtime 仍然只执行 selected_operation
```

禁止：

```text
RAG 直接输出“执行这个 operation”
RAG 直接生成 bpy 调用
RAG 覆盖 selected_operation
RAG 覆盖 OperationSpec
```

面试表达：

```text
我会把 RAG 作为证据层，用于解释、参数建议和相似失败案例检索，但不会让 RAG 取代 Planning selector 或 Runtime 控制权。
```

## 4.9 你的系统为什么暂时不做 Multi-Agent？

因为当前系统最强资产是：

```text
单主链
单事实源
单 Runtime
单执行入口
```

如果现在引入多个 Agent：

```text
Planner Agent
Binding Agent
Critic Agent
Executor Agent
Memory Agent
```

马上会出现问题：

```text
谁能写 TaskObject？
谁能触发 Runtime？
多个 Agent 输出冲突怎么办？
失败归因在哪里？
谁拥有最终事实？
```

什么时候再考虑 Multi-Agent？

```text
composite planning
visual critique
parameter optimization
multi-step design review
```

当前更合理的是：

```text
LLM worker roles
```

例如：

```text
intent parsing worker
retry suggestion worker
report summary worker
```

它们只能给建议，不能拥有执行权。

面试表达：

```text
我不是反对 multi-agent，而是认为当前阶段不应该让多个 Agent 共同拥有执行状态。先保持单控制平面，等进入 composite planning 或 visual critique 时，再引入只读或建议型 worker roles。
```

## 4.10 为什么暂时不做 Composite Operation？

Composite 很有价值，但现在不应该直接做自动执行框架。

原因是 sequence 会拉动：

```text
TaskObject schema
operation_steps
Runtime recovery
per-step report
failure policy
rollback strategy
user confirmation
```

当前更适合做：

```text
Composite Pattern Documentation
LLM-generated explicit plan proposal
manual review / confirmation
```

而不是自动执行多步 sequence。

面试表达：

```text
我先完成 atomic operation 的准确率、可靠性和验证矩阵，再进入 composite execution。否则 sequence 只会把单步不稳定放大。
```

## 4.11 为什么暂时不做 Boolean / Mesh Edit / Material System？

这些功能扩展很诱人，但会显著扩大安全边界。

当前系统优势是：

```text
modifier-only
non-destructive
copy-only
mesh_data_applied = false
```

如果太早进入 boolean / mesh edit，会增加：

```text
几何破坏风险
回滚复杂度
post-check 难度
Blender crash 风险
测试矩阵复杂度
```

前置条件：

```text
preflight / post-check
worker isolation
safety policy
smoke matrix
failure recovery
```

面试表达：

```text
我刻意把第一版 operation library 限制在 modifier-only 和 non-destructive 范围内，是为了先建立可控、安全、可测试的执行链。更强的 mesh edit 能力会在 worker isolation 和 post-check 成熟后再进入。
```

## 4.12 你的系统怎么评估 Agent 是否可靠？

建议回答四类指标。

### Operation Selection Accuracy

看自然语言是否选对 operation。

指标：

```text
Top-1 operation accuracy
Ambiguous rate
Unsupported request rate
Mis-selection category
```

### Parameter Accuracy

看参数是否符合用户语义。

指标：

```text
Parameter profile match rate
Default parameter overuse rate
Manual adjustment needed rate
```

### Target Binding Accuracy

看是否改对 Blender object。

指标：

```text
Top-1 binding accuracy
Candidate recall
Ambiguous binding rate
Wrong-object risk
```

### Runtime Reliability

看执行链路是否可靠。

指标：

```text
Preflight pass rate
Post-check pass rate
Output copy exists
Report exists
Source hash unchanged
Failure stage completeness
```

面试表达：

```text
我会从 operation selection、parameter accuracy、target binding、runtime reliability 四个维度评估 Agent，而不是只看 demo 是否能跑。
```

## 4.13 你的 Runtime 怎么保证安全？

当前已经有：

```text
只接受 ready_to_execute TaskObject
DomainOperationInput.from_task_object 校验 ready state
execution_policy 防止覆盖源文件
DomainOperationInput 拒绝 artifact paths
缺 handler 直接失败，不 fallback
save_as_copy_only 拒绝覆盖 source .blend
Runtime failure report 记录 error_stage
```

后续 Preflight 检查：

```text
TaskObject.state == ready_to_execute
selected_operation exists
domain handler exists
bound_object exists
source_blend_file exists
output_blend_copy != source_blend_file
parameters schema valid
safety policy passed
```

后续 Post-check 检查：

```text
expected modifier exists
modifier parameters match expected
changed_objects contains target
mesh_data_applied == false
output blend copy exists
report file exists
source file hash unchanged
```

面试表达：

```text
执行成功不等于业务成功，所以我会做 preflight 和 post-check：执行前确认 handler、target、policy、parameters；执行后确认 modifier、output copy、report、source unchanged。
```

## 4.14 你的 Binding 怎么处理？未来怎么增强？

当前 binding 做法：

```text
scene_manifest / binding_context
-> semantic_part
-> binding candidates
-> confirmed bound object
-> task.target.bound_object
```

当前风险：

```text
operation 选对了，参数也对，但改错对象
多个候选对象时没有足够用户确认
binding confidence 没有成为 TaskObject first-class field
```

未来增强：

```text
binding_confidence
binding_evidence
candidate_ranking
requires_user_confirmation
confirmed_by_user
```

短期做法：

```text
先记录在 Planning diagnostics / report
暂不急着改 TaskObject schema
```

面试表达：

```text
我会先把 binding confidence 和 evidence 作为 Planning 可解释信息记录下来，在真实多候选场景验证后，再决定是否升级为 TaskObject 的一等字段。
```

## 5. 自研架构与流行框架/概念对照表

| 外部概念 | 当前项目对应 | 相同点 | 为什么当前这样做 |
| --- | --- | --- | --- |
| LangGraph State | `TaskObject` | 显式状态传递 | 需要更强领域约束和字段 ownership |
| LangGraph Node | Planning stages / Runtime stages | 阶段化 workflow | 当前阶段用 Python 模块更直接可控 |
| Tool Calling | `OperationSpec` / `OperationRegistry` | 工具 schema / handler | 不直接暴露函数给 LLM，Planning 统一选择 |
| ReAct Observe | Runtime report / OperationOutcome | 执行后观察 | 观察进入 report，不让 LLM 自由循环执行 |
| Memory | TaskObject / reports / taxonomy | 保存状态和经验 | 防止 memory 覆盖 TaskObject 当前事实 |
| RAG | Future evidence layer | 检索相关知识 | 只做 evidence，不做 decision maker |
| MCP | Future Blender worker protocol | 标准化工具通信 | 等 object creation / mesh edit 时再引入隔离 |
| Multi-Agent | Future worker roles | 专门角色分工 | 当前保持单 control plane，避免事实冲突 |
| Workflow Engine | Planning + Runtime | 状态推进和执行 | 与 Blender 安全策略深度绑定 |
| Event Sourcing | Future execution_history.jsonl | 记录历史事件 | 轻量实现，不急于上数据库 |

## 6. 面试时如何解释“为什么自研”

可以这样说：

```text
我不是为了重复造轮子而自研，而是因为这个项目的核心问题不是普通聊天流程，而是真实 Blender 文件修改。它需要强约束的状态模型、可审计的任务事实、非破坏性文件策略、固定 Domain handler、明确 Runtime 边界和 failure report。这些约束比普通 demo 型 Agent 更强，所以我先实现了一个 domain-specific controlled execution harness。
```

再补一句：

```text
我理解 LangGraph、RAG、Memory、MCP 这些外部概念，也能把它们映射进当前系统。但我不会盲目引入，因为它们必须服务主链，不能破坏 TaskObject 主事实源和 Runtime 执行边界。
```

## 7. 高频面试问题与回答模板

### Q1：这个项目和普通 ChatGPT 插件/工具调用有什么区别？

回答：

普通工具调用往往让 LLM 直接决定调用哪个函数。我这里把工具调用拆成受控链路：LLM 只生成 intent，Planning 根据 OperationSpec metadata 选择 operation，Runtime 只执行 ready task，Domain handler 是固定代码，Core API 才能接触 Blender。这样可以测试、审计和控制副作用。

### Q2：如果 LLM 解析错了怎么办？

回答：

解析错不会直接执行，因为 draft TaskObject 还要经过 Planning validation、target binding、operation selection、parameter completion 和 safety policy。后续还会加入 evaluation cases、ambiguous confirmation 和 report-to-planning feedback，让错误可发现、可分类、可修正。

### Q3：如果选错 operation 怎么办？

回答：

当前 selector 会基于 intent.action、intent.detail_type、intent.desired_effect 和 OperationSpec metadata 打分，无法确定时 fail fast。下一步会做 Operation Selection Accuracy Report，统计误选类型，并在歧义场景引入用户确认。

### Q4：如果改错 Blender 对象怎么办？

回答：

这是 3D Agent 的高风险点。当前通过 scene_manifest / binding_context 绑定 semantic_part 到 bound_object。下一步会加入 binding confidence、binding evidence、candidate ranking 和 requires_user_confirmation，低置信度时不直接执行。

### Q5：为什么 Runtime 不 fallback 到其他 operation？

回答：

Runtime 的职责是执行，不是规划。如果 handler missing 或 Domain failed，Runtime 应该失败并写 report，而不是临时选择另一个 operation。否则会破坏 Planning / Runtime 分离，也会让失败归因变得混乱。

### Q6：为什么 DomainOperationInput 不带 output path 和 report path？

回答：

因为 Domain 只负责 operation 本身，不应该拥有 persistence/report 权限。输出路径和 report 文件由 Runtime / persistence layer 控制。这样可以防止 Domain handler 越权保存文件或绕过 Runtime report。

### Q7：怎么证明执行没有破坏源文件？

回答：

当前采用 copy-only 策略，`save_as_copy_only` 拒绝覆盖 source `.blend`。真实 smoke test 里会比较 source hash before/after，验证 source unchanged，同时检查 output copy 和 runtime report。

### Q8：项目现在最大的不足是什么？

回答：

当前主要不足是 evaluation 和 feedback 还不够完整。已经有 366 个单元测试和 real Blender smoke，但还需要针对 operation selection、parameter accuracy、target binding、runtime reliability 建立系统化 evaluation report。另外 report-to-planning feedback loop 和 context assembly 也需要增强。

### Q9：你会怎么继续优化？

回答：

我会按这个顺序做：先做 Agent Evaluation Report，再做 Runtime Preflight/Post-check，然后做 Context Assembly v1 和轻量 feedback memory。之后补 RAG evidence layer、FastAPI wrapper、LangGraph mini demo。更重的 MCP、multi-agent、composite execution、mesh edit 会放后面。

### Q10：为什么不马上做 RAG？

回答：

RAG 有价值，但它应该先作为 evidence layer，而不是执行决策层。当前系统更核心的问题是 controlled execution 和 runtime reliability。等评估和上下文装配明确后，再引入 docs/operation/failure cases RAG，可以更稳。

### Q11：为什么不马上做多 Agent？

回答：

因为当前阶段多 Agent 会引入事实冲突和执行权冲突。我的系统现在最强的是单主链、单事实源、单 Runtime。未来如果进入 composite planning、visual critique 或 parameter optimization，可以引入只读或建议型 worker roles，但不让多个 Agent 共同拥有执行权。

### Q12：这个项目有什么生产级思维？

回答：

生产级思维体现在：状态机、字段 ownership、OperationSpec contract、Runtime/Planning 分离、Domain/Core 边界、copy-only persistence、failure stage report、测试覆盖和真实 Blender smoke。它不是能跑一次的 demo，而是在设计可控、可审计、可扩展的执行体系。

## 8. 项目优势怎么讲

可以归纳成 8 个点：

```text
1. TaskObject single source of truth
2. LLM as bounded worker
3. Planning / Runtime separation
4. OperationSpec-controlled tool surface
5. Domain/Core execution boundary
6. Non-destructive copy-only persistence
7. Runtime report and failure stage
8. Evaluation-first roadmap
```

## 9. 项目短板怎么讲

不要回避短板，但要说明下一步：

```text
1. 参数准确率还需要 profile 和 evaluation
2. target binding confidence 还不是一等字段
3. Runtime post-check 还需要系统化
4. report-to-planning feedback loop 还没完整实现
5. real Blender smoke 目前主要覆盖 edge_soften
6. 还没有服务化 API 和标准 Agent 框架 demo
```

对应补救路线：

```text
Agent Evaluation Report
Runtime Preflight/Post-check
Context Assembly v1
Feedback Memory
RAG Evidence Layer
FastAPI Wrapper
LangGraph Mini Demo
Smoke Matrix
```

## 10. 面试最后反问可以问什么

可以问：

```text
你们的 Agent 系统现在是 LLM 直接 tool calling，还是有独立 control plane？
你们如何评估 tool selection accuracy 和 task success rate？
你们的 memory 会不会覆盖当前 task state？
你们是否有 preflight / post-check / failure taxonomy？
你们如何处理用户确认和高风险工具调用？
你们更看重快速 demo，还是长期可维护的 Agent runtime？
```

这些问题能反向展示你对生产级 Agent 架构的理解。

## 11. 推荐复习顺序

面试前按这个顺序复习：

```text
1. 30 秒和 2 分钟项目讲法
2. TaskObject single source of truth
3. Planning / Runtime / Domain / Core 分层
4. OperationSpec / OperationRegistry
5. LLM as worker, Harness as control plane
6. Context Assembly 和 Memory 边界
7. Evaluation metrics
8. Runtime preflight / post-check
9. RAG / LangGraph / MCP / Multi-Agent 对照关系
10. 项目短板和下一步 roadmap
```

## 12. 一句话结尾

面试最后可以这样收束：

```text
这个项目最重要的不是 Blender，而是我用一个真实有副作用的 3D 修改场景，设计了一套 TaskObject-centered controlled Agent execution architecture。它体现的是我对 Agent 状态、工具边界、执行安全、评估和可扩展性的理解。
```
