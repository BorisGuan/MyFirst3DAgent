# Agent 系统架构优化执行计划

本文档根据 `docs/3D机甲模型Agent设计指导.docx` 整理而来，用于指导下一阶段实际执行。它不是面试复习材料，而是把设计指导中的 P0 / P1 / P2 / P3 方向转换成可落地的任务计划。

核心目标不是把 RAG、MCP、四层记忆、多 Agent 等概念全部搬进当前系统，而是判断哪些能力能增强现有主链，哪些能力会破坏当前最有价值的架构边界。

当前主链是：

```text
Agent Layer
-> TaskObject
-> Planning Engine
-> Runtime Engine
-> DomainOperationInput
-> Domain Operation
-> Core API
-> Blender bpy
-> output copy + runtime report
```

当前最应该围绕这些能力优化：

```text
精度
可靠性
反馈闭环
上下文工程
可评估性
可解释性
```

## 1. 总体原则

### 1.1 必须保护的架构资产

```text
TaskObject 主事实源
Planning / Runtime 分离
OperationSpec / OperationRegistry 能力边界
Domain / Core 执行边界
copy-only 非破坏性输出策略
Runtime report 和 failure stage
modifier-only atomic operation 稳定边界
```

### 1.2 LLM 的定位

```text
LLM is a bounded worker, not the control plane.
```

也就是：

```text
LLM 可以做 intent parsing、解释、retry suggestion、report summary。
LLM 不拥有状态控制权。
LLM 不直接触发 Runtime。
LLM 不直接调用 bpy。
LLM 不覆盖 OperationSpec。
```

真正的 control plane 是：

```text
TaskObject lifecycle
Planning Engine
Runtime Engine
Safety Policy
Reporting
```

### 1.3 上下文的定位

```text
Context 不是事实源。
Context 只是给 LLM 的输入装配。
TaskObject 才是当前任务事实源。
```

后续所有 memory、RAG、feedback 都只能作为 Planning evidence，不能覆盖 TaskObject 当前事实。

## 2. 优先级总览

## 2.1 P0 - 必须做

这些对系统真实能力和面试价值都最高，应优先进入实施。

```text
P0-1 Agent Evaluation Report
P0-2 Runtime Preflight / Post-check
P0-3 Report -> Feedback Loop
P0-4 Context Assembly v1
P0-5 Harness / Control Plane 文档化
```

## 2.2 P1 - 强烈建议做

这些能补齐 AI Agent / LLM 应用岗位的通用能力短板。

```text
P1-1 RAG Evidence Layer
P1-2 LangGraph Mini Demo
P1-3 FastAPI Service Wrapper
P1-4 Binding Confidence / User Confirmation
```

## 2.3 P2 - 有价值，但后置

这些适合写进 roadmap，不建议马上大改。

```text
P2-1 MySQL / Postgres 持久化
P2-2 MCP / Blender Worker Subprocess
P2-3 四层记忆完整系统
```

## 2.4 P3 - 暂时不要做

这些现在做会过早扩大复杂度。

```text
P3-1 多 Agent / 子 Agent 隔离
P3-2 Composite Operation 真正执行框架
P3-3 Object Creation / Boolean / Mesh Edit / Material System
```

## 3. P0-1 Agent Evaluation Report

## 3.1 目标

建立一套 Agent 评估体系，回答以下问题：

```text
自然语言是否选对 operation？
operation 参数是否符合用户语义？
semantic_part 是否绑定到正确 Blender object？
Runtime 是否可靠执行并产出可验证结果？
```

这一步的价值是把项目从：

```text
我做了一个 Agent 项目
```

升级成：

```text
我知道怎么评估一个 Agent 系统是否可靠
```

## 3.2 产物

```text
docs/04_architecture_review_portfolio/agent_evaluation_report.md
docs/03_operation_library/operation_parameter_accuracy_analysis.md
docs/04_architecture_review_portfolio/operation_selection_accuracy_review.md
docs/04_architecture_review_portfolio/target_binding_accuracy_review.md
```

可选测试文件：

```text
tests/test_agent_evaluation_cases.py
```

## 3.3 评估维度

### Operation Selection Accuracy

评估自然语言是否选对 operation。

示例：

```text
用户输入：给胸甲加一些 RG 风格面板线，但不要破坏轮廓
期望 operation：panel_line_bevel_prepare
```

指标：

```text
Top-1 operation accuracy
Ambiguous rate
Unsupported request rate
Mis-selection category
```

### Parameter Accuracy

评估参数是否符合用户语义。

示例：

```text
“稍微柔化边缘” -> bevel width 应该较小
“高密度 RG 风格细节” -> panel line / inset 参数应该更细、更密
```

指标：

```text
Parameter profile match rate
Default parameter overuse rate
Manual adjustment needed rate
```

### Target Binding Accuracy

评估 semantic_part 是否改对 Blender object。

示例：

```text
chest_armor -> Body_Armor01 / Chest_Armor_xxx
```

指标：

```text
Top-1 binding accuracy
Candidate recall
Ambiguous binding rate
Wrong-object risk
```

### Runtime Reliability

评估执行链路是否可靠。

指标：

```text
Preflight pass rate
Post-check pass rate
Output copy exists
Report exists
Source hash unchanged
Failure stage completeness
```

## 3.4 涉及模块

```text
planning/operation_selector.py
planning/parameter_completer.py
planning/binding_resolver.py
runtime/runtime_engine.py
domain/operation_registry.py
blender_ops/domain_operations.py
tests/
```

## 3.5 验收标准

```text
1. 至少有 30 条自然语言 evaluation cases
2. 每个 atomic operation 至少覆盖 2 条用户表达
3. 文档列出 operation selection 的正确/错误/歧义案例
4. 文档列出参数默认值过度使用的风险
5. 文档列出 target binding 的常见失败模式
6. 文档给出 Runtime reliability checklist
```

## 3.6 暂不做

```text
不搭建复杂在线评测平台
不引入数据库
不做自动大规模标注
不让 evaluation 结果自动触发 Runtime
```

## 4. P0-2 Runtime Preflight / Post-check

## 4.1 目标

让系统从“工具调用成功”升级为“执行前可确认安全，执行后可证明结果符合预期”。

核心原则：

```text
Agent 不是执行了就算成功。
Agent 必须能证明执行结果符合预期。
```

## 4.2 Preflight 检查

执行前检查：

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

如果这些不满足，就不要进入 Domain/Core。

## 4.3 Post-check 检查

执行后检查：

```text
expected modifier exists
modifier parameters match expected
changed_objects contains target
mesh_data_applied == false
output blend copy exists
report file exists
source file hash unchanged
```

## 4.4 产物

```text
docs/04_architecture_review_portfolio/runtime_preflight_postcheck_design.md
runtime/preflight.py
runtime/postcheck.py
tests/test_runtime_preflight.py
tests/test_runtime_postcheck.py
```

也可以先只做文档和测试设计，不马上拆代码模块。

## 4.5 涉及模块

```text
runtime/runtime_engine.py
runtime/execution_context.py
reporting/report_builder.py
core_api/persistence_api.py
core_api/geometry_api.py
tests/test_runtime_execution_flow.py
```

## 4.6 验收标准

```text
1. 非 ready_to_execute task 在 preflight 阶段失败
2. missing handler 在 preflight 阶段失败
3. output path 覆盖 source path 时失败
4. post-check 能确认 modifier 存在和参数正确
5. source hash unchanged 能被记录或检查
6. failure report 能体现 preflight / post-check stage
```

## 4.7 暂不做

```text
不做 Blender undo
不做 destructive rollback
不让 Runtime 重新规划
不让 Domain 写 report 或保存文件
```

## 5. P0-3 Report -> Feedback Loop

## 5.1 目标

让 Runtime report 和用户反馈成为下一轮 Planning 的 evidence，使系统从一次性执行升级为可持续优化。

## 5.2 最小实现

先使用轻量文件，不引入数据库。

```text
outputs/memory/execution_history.jsonl
outputs/memory/feedback_memory.jsonl
```

execution history 示例：

```json
{
  "task_id": "xxx",
  "user_input": "给胸甲加 RG 风格面板线",
  "target": "chest_armor",
  "selected_operation": "panel_line_bevel_prepare",
  "parameters": {
    "width": 0.006,
    "segments": 1
  },
  "result": "success",
  "failure_stage": null,
  "user_feedback": "线条太密",
  "future_adjustment": "reduce panel line density"
}
```

下一轮 Planning 可以读取摘要：

```text
Recent feedback:
- User prefers lower panel line density on chest armor.
- Previous high-density setting caused visual clutter.
```

## 5.3 与四层记忆的关系

这里对应的是：

```text
Episodic memory = 历史执行结果 + 用户反馈 + 失败案例
```

但必须保持边界：

```text
Memory 只能作为 Planning evidence
Memory 不能替代 TaskObject 主事实源
```

## 5.4 产物

```text
docs/04_architecture_review_portfolio/report_feedback_loop_design.md
model/feedback_memory.py
model/execution_history.py
tests/test_feedback_memory.py
```

## 5.5 验收标准

```text
1. Runtime report 可被追加到 execution_history.jsonl
2. 用户反馈可写入 feedback_memory.jsonl
3. Context Assembly 能读取最近反馈摘要
4. feedback 不直接覆盖 selected_operation
5. feedback 不直接触发 Runtime
```

## 5.6 暂不做

```text
不引入 MySQL/Postgres
不做复杂 memory ranking
不让 memory 自动改 TaskObject
不让 feedback 自动执行 retry
```

## 6. P0-4 Context Assembly v1

## 6.1 目标

把 ContextManager 从“提供 summary”升级为“按阶段装配不同 context bundle”。

## 6.2 7 段上下文装配

建议结构：

```text
1. System safety / execution boundary
2. User request
3. Current TaskObject summary
4. Model / scene / binding context
5. Design taxonomy context
6. Operation capability context
7. Recent report / feedback memory
```

## 6.3 不同阶段的 context bundle

### Classifier context

```text
user request
supported task types
design taxonomy summary
```

### Intent parser context

```text
user request
model part aliases
style / density / scale taxonomy
```

### Planning explanation context

```text
TaskObject intent
OperationSpec summary
binding candidates
recent failure / feedback evidence
```

### User response context

```text
Runtime result
changed_objects
report summary
next-step suggestion
```

## 6.4 产物

```text
docs/04_architecture_review_portfolio/context_assembly_v1_design.md
model/context_assembly.py
model/context_bundle.py
tests/test_context_assembly.py
```

## 6.5 涉及模块

```text
model/context_manager.py
agent_layer/agent_service.py
agent/command_classifier.py
agent/intent_parser.py
planning/planning_engine.py
domain/operation_registry.py
```

## 6.6 验收标准

```text
1. classifier / intent parser / planning explanation 使用不同 context bundle
2. context bundle 不包含无关全文
3. OperationRegistry 能提供 capability summary
4. Context Assembly 不修改 TaskObject
5. 文档明确 ContextManager / Context Assembly / TaskObject 的边界
```

## 6.7 暂不做

```text
不把所有文档塞进 prompt
不让 context 覆盖 TaskObject 字段
不做复杂向量库
不做完整长期记忆系统
```

## 7. P0-5 Harness / Control Plane 文档化

## 7.1 目标

把现有系统明确表达为：

```text
Controlled Agent Execution Harness
```

## 7.2 映射关系

```text
LLM Worker:
- intent parsing
- explanation
- retry suggestion
- report summary

Control Plane:
- TaskObject lifecycle
- Planning Engine
- Runtime Engine
- Safety Policy
- Reporting

Execution Boundary:
- Domain Operation
- Core API
- Blender bpy
```

## 7.3 产物

```text
docs/04_architecture_review_portfolio/agent_execution_harness_design.md
```

## 7.4 验收标准

```text
1. 文档能解释为什么 LLM 不拥有执行权
2. 文档能映射当前模块到 worker / control plane / execution boundary
3. 文档能用于面试 2 分钟讲解
4. 不要求改代码
```

## 8. P1-1 RAG Evidence Layer

## 8.1 目标

补齐 AI Agent / LLM 应用岗位常见 RAG 能力，同时增强 Planning explanation 和 retry suggestion。

## 8.2 边界

```text
RAG = evidence provider
RAG != decision maker
```

RAG 可以检索：

```text
architecture docs
operation specs
operation docs
design taxonomy
parameter guidelines
runtime reports
evaluation reports
failure cases
```

RAG 用途：

```text
解释 operation 选择原因
查找设计原则
查找参数建议
查找相似失败案例
辅助 retry suggestion
```

RAG 不允许：

```text
直接输出“执行这个 operation”
直接调用 bpy
覆盖 selected_operation
覆盖 OperationSpec
覆盖 TaskObject 当前事实
```

## 8.3 架构位置

```text
RAG evidence
-> Context Assembly
-> Agent / Planning explanation
-> OperationSelector 仍然基于 OperationSpec 做最终选择
-> Runtime 仍然只执行 selected_operation
```

## 8.4 产物

```text
docs/04_architecture_review_portfolio/rag_evidence_layer_design.md
rag/index_builder.py
rag/retriever.py
tests/test_rag_retriever.py
```

## 8.5 验收标准

```text
1. 能按 operation / intent 查询相关文档片段
2. 返回 evidence 带来源路径
3. evidence 进入 Context Assembly
4. selected_operation 仍由 OperationSelector 决定
```

## 9. P1-2 LangGraph Mini Demo

## 9.1 目标

不用 LangGraph 重写主项目，只做 mini demo 来证明理解主流 state graph 框架。

## 9.2 Mini workflow

```text
parse_intent
-> select_operation
-> execute_tool
-> verify_result
-> retry_or_finish
```

## 9.3 State 设计

```text
AgentState:
- user_input
- task_object_summary
- selected_operation
- execution_result
- retry_count
```

## 9.4 产物

```text
examples/langgraph_mini_demo/
examples/langgraph_mini_demo/README.md
```

## 9.5 验收标准

```text
1. demo 能跑通一个简单 state graph
2. README 解释它和 TaskObject lifecycle 的关系
3. 明确说明主项目不迁移到 LangGraph
```

## 10. P1-3 FastAPI Service Wrapper

## 10.1 目标

让项目从本地 CLI 工具更接近可交付服务。

## 10.2 最小 API

```text
POST /tasks
GET /tasks/{task_id}
POST /tasks/{task_id}/plan
POST /tasks/{task_id}/execute
GET /tasks/{task_id}/report
```

## 10.3 产物

```text
service/app.py
service/schemas.py
tests/test_service_api.py
```

## 10.4 验收标准

```text
1. 能创建 TaskObject
2. 能查询 TaskObject
3. 能触发 Planning
4. 能执行 ready task
5. API 不绕过 Runtime
```

## 11. P1-4 Binding Confidence / User Confirmation

## 11.1 目标

降低改错 Blender object 的风险。

## 11.2 建议新增信息

```text
binding_confidence
binding_evidence
candidate_ranking
requires_user_confirmation
confirmed_by_user
```

## 11.3 短期做法

先记录在 Planning diagnostics / report，不急着改 TaskObject schema。

示例：

```json
{
  "binding_confidence": 0.72,
  "binding_evidence": [
    "alias matched chest_armor",
    "object type mesh",
    "collection path Armor"
  ],
  "requires_user_confirmation": true,
  "candidates": [
    "Body_Armor01",
    "Chest_Plate_L",
    "Torso_Front"
  ]
}
```

## 11.4 产物

```text
docs/04_architecture_review_portfolio/binding_confidence_design.md
tests/test_binding_confidence.py
```

## 11.5 验收标准

```text
1. binding result 能输出 confidence 和 evidence
2. 多候选对象时能标记 requires_user_confirmation
3. 低 confidence 不直接进入 ready_to_execute
4. 不破坏现有 binding_resolver 行为
```

## 12. P2-1 MySQL / Postgres 持久化

## 12.1 当前建议

现在不建议马上做数据库持久化。

短期优先：

```text
JSONL
SQLite
local artifact folder
```

持久化内容：

```text
TaskObject snapshots
Runtime reports
feedback memory
evaluation cases
```

## 12.2 什么时候上 MySQL / Postgres

当出现以下需求时再做：

```text
多用户
Web 服务
任务列表
权限审计
历史查询
dashboard
团队协作
```

## 13. P2-2 MCP / Blender Worker Subprocess

## 13.1 当前建议

先写入 roadmap，不马上实现。

## 13.2 适用场景

未来进入这些能力时再做：

```text
object creation
boolean
mesh edit
material system
long-running Blender process
```

## 13.3 价值

```text
隔离 Blender crash
支持 timeout / kill
进程级 sandbox
工具协议白名单
Runtime 与 Blender worker 解耦
```

## 14. P2-3 四层记忆完整系统

## 14.1 映射关系

```text
Working memory = current TaskObject
Episodic memory = Runtime reports + user feedback
Semantic memory = design taxonomy + docs RAG
Procedural memory = OperationSpec + Domain handlers
```

## 14.2 关键边界

不要新建 procedural memory 去复制 OperationSpec。

否则会出现：

```text
OperationSpec 说系统支持 A
Procedural memory 也说系统支持 A
两边不一致
```

这就是第二事实源。

## 14.3 当前最该补

```text
Episodic memory
Semantic RAG
```

不是完整四层记忆系统。

## 15. P3-1 多 Agent / 子 Agent 隔离

## 15.1 当前建议

现在不要做多 Agent。

当前系统最大优势：

```text
单主链
单事实源
单 Runtime
单执行入口
```

多 Agent 会带来：

```text
谁能写 TaskObject？
谁能触发 Runtime？
多个 Agent 输出冲突怎么办？
失败归因在哪里？
谁拥有最终事实？
```

## 15.2 什么时候再考虑

等进入：

```text
composite planning
visual critique
parameter optimization
multi-step design review
```

现在最多做：

```text
intent parsing worker
retry suggestion worker
report summary worker
```

这些 worker 只能给建议，不能拥有执行权。

## 16. P3-2 Composite Operation 执行框架

## 16.1 当前建议

暂缓。

真正做 sequence 会拉动：

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

不自动执行多步 sequence。

## 17. P3-3 Object Creation / Boolean / Mesh Edit / Material System

## 17.1 当前建议

暂缓。

当前系统优势：

```text
modifier-only
non-destructive
copy-only
no mesh data applied
```

太早进入 boolean / mesh edit 会破坏当前稳定边界。

前置条件：

```text
preflight/post-check
worker isolation
safety policy
smoke matrix
failure recovery
```

## 18. 总体验收标准

完成 P0 后，系统应该能回答：

```text
Agent 怎么评估？
执行前怎么确认安全？
执行后怎么证明正确？
report 和 feedback 怎么进入下一轮 Planning？
不同阶段怎么装配 context？
LLM 为什么不是 control plane？
```

完成 P1 后，系统还应具备：

```text
RAG evidence 能力
LangGraph 对照 demo
FastAPI 服务入口
binding confidence / user confirmation 设计
```

## 19. 建议执行顺序

```text
1. Agent Evaluation Report
2. Runtime Preflight / Post-check
3. Report -> Feedback Loop
4. Context Assembly v1
5. Harness / Control Plane 文档化
6. Binding Confidence / User Confirmation
7. RAG Evidence Layer
8. LangGraph Mini Demo
9. FastAPI Service Wrapper
10. Real Blender Smoke Matrix
```

## 20. 最终建议

下一阶段不要被“功能很多的 Agent”带偏。

真正应该做的是：

```text
把现有 TaskObject 主链升级成 Controlled Agent Execution Harness。
```

这个 Harness 应该具备：

```text
可评估
可反馈
可解释
可服务化
可逐步扩展
```

最重要的是：

```text
不破坏 TaskObject 主事实源
不破坏 Runtime 执行边界
不让 LLM 直接拥有执行权
不让 RAG / Memory / Multi-Agent 变成第二事实源
```
