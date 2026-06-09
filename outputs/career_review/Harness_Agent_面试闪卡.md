# Harness Agent 面试闪卡

使用方式：不要背全文。每题先看关键词，然后关掉文档，用自己的话说 60 秒。说不出来时再看回答骨架。

## 0. 总主线

```text
真实复杂系统经验
-> AI 辅助问题调查
-> TaskObject-centered Agent Harness
-> LLM bounded worker
-> Tools & Skills 工程化
-> Evaluation / Trace / Feedback
```

核心句：

```text
我想做的不是把 AI 包装成一个更会聊天的工具，而是把 AI 放进一个有状态、有边界、有评测、有反馈的 Harness 里，让它真正变成稳定、可交付、可持续改进的工程能力。
```

---

## 0A. 你怎么看未来 Agent 的发展方向？

关键词：

```text
IDE -> Agent Workspace
Human specifies intent
Agent Runtime executes
Human = Architect / Reviewer
Agent = Executor
```

60 秒骨架：

```text
1. 我觉得软件开发环境正在从 IDE 时代进入 Agent Workspace 时代。
2. 传统 IDE 里是 Human writes code，IDE 只是编辑器、debug、git、build 工具。
3. Copilot 第一阶段只是高级 autocomplete，人还是 runtime。
4. 现在 Cursor、Claude Code、OpenHands 这类工具开始让 AI 持续推进任务，人从指定实现细节变成指定 intent 和约束。
5. 未来软件工程会越来越像 Human = Architect / Reviewer，Agent = Executor。
```

收束句：

```text
行业真正的变化不是 AI 会写代码，而是软件工程的执行主体正在从 Human 转向 Agent Runtime。
```

---

## 0B. 为什么下一代 IDE 更像 Agent Workspace？

关键词：

```text
orchestration
planning
execution loop
context management
memory
tool routing
terminal agent
workspace / repo / shell
```

60 秒骨架：

```text
1. 过去 IDE 的核心是写代码和调试代码。
2. 现在 Agentic IDE 的核心逐渐变成 orchestration：规划任务、管理上下文、调用工具、执行测试、读日志、修 bug。
3. Agent 真正需要的不只是 GUI 编辑器，而是 filesystem、shell、git、process、logs、test runtime。
4. 所以 Terminal Agent、Claude Code、OpenHands 这类工具会变强，因为它们更接近真实工程执行环境。
5. IDE 会从主角退到 workspace，Agent Runtime 会成为任务执行主体。
```

收束句：

```text
未来 IDE 的核心竞争力不只是编辑体验，而是 Agent Runtime 的编排、记忆、工具路由和可观测性。
```

---

## 0C. 这种趋势下，工程师竞争力会怎么变化？

关键词：

```text
system thinking
runtime
workflow
constraints
evaluation
trust boundaries
agent governance
Agent Infrastructure
```

60 秒骨架：

```text
1. 如果大模型能力逐渐商品化，稀缺能力就不再只是写代码快。
2. 更重要的是谁能设计系统、设计 runtime、设计 workflow、定义约束、定义 evaluation、管理状态和风险。
3. 以后工程师更像 architect / reviewer，需要把任务目标、边界和验收标准定义清楚。
4. 我现在做的 TaskObject、Planning/Runtime separation、OperationSpec、feedback loop、evaluation，本质上是在做 Agent Infrastructure。
5. 这也是我为什么认为 Harness / Agent Runtime 是有长期价值的方向。
```

收束句：

```text
未来真正稀缺的是能让 Agent 稳定、安全、长期完成复杂任务的系统设计能力。
```

---

## 0D. 你的个人护城河是什么？

关键词：

```text
Agent Systems Engineering
Runtime Engineering
Vertical Agent Runtime
复杂任务闭环
状态治理
工具抽象
Evaluation
长期记忆
```

60 秒骨架：

```text
1. 我不想把护城河建立在某个模型、某个 prompt 技巧或某个框架 API 上，因为这些会快速商品化。
2. 我更想建立的是 Agent Systems Engineering 能力，也就是让 Agent 在复杂领域里稳定、安全、可追踪地完成任务。
3. 这包括 runtime orchestration、planning/runtime separation、stateful execution、tool schema、sandboxed harness、evaluation loop、memory layering。
4. 我的 3D Agent 项目就是在垂直领域里验证这个方向：把 3D 修改流程固化成状态、原子操作、工具契约、验证器和报告。
5. 长期来看，我更适合做复杂领域 Agent Runtime / Infrastructure，而不是泛用聊天壳子或纯 prompt 工程。
```

收束句：

```text
我的护城河不是最会调用 LLM，而是更懂如何让 Agent 可靠工作。
```

---

## 1. 请做一个自我介绍

关键词：

```text
10+ 年企业级软件
MDS / DQS
客户问题 / Release / CloudTest
AI Agent Harness
TaskObject / Planning / Runtime
LLM bounded worker
```

60 秒骨架：

```text
1. 我有 10+ 年企业级软件经验，长期参与 MDS / DQS 产品维护。
2. 做过客户 ICM、release signoff、CloudTest、可访问性修复、hotfix 和安全改造。
3. 最近独立做了 3D Model Modification Agent，本质是 Controlled Agent Execution Harness。
4. 它不是 LLM demo，而是 TaskObject + Planning + Runtime + OperationSpec 的受控执行系统。
5. 我适合做把 AI 从“能回答”推进到“能稳定干活”的 Agent 工程。
```

收束句：

```text
我的优势是把真实复杂系统经验迁移到 AI Agent Harness 设计里。
```

---

## 2. 为什么你适合 Harness Agent 岗位？

关键词：

```text
不只是 demo
真实系统
规则沉淀
评测回归
Tools & Skills
MDS/DQS 经验
```

60 秒骨架：

```text
1. 我理解这个岗位不是找会调 API 的人，而是找能把 AI 做成稳定系统的人。
2. 我过去处理 MDS/DQS 的真实客户问题，知道系统会失败、会脏、会需要追踪和兜底。
3. 我的 Agent 项目也按这个思路设计：TaskObject 管状态，OperationSpec 管工具，Runtime 管执行，Report 管追踪。
4. 我关注 eval、回归、feedback，而不是只做一次性 demo。
```

收束句：

```text
我能把业务经验、工程边界和 Agent 架构结合起来。
```

---

## 3. 什么是 Agent Harness？

关键词：

```text
control plane
LLM worker
状态
工具
执行
评测
反馈
```

60 秒骨架：

```text
1. Harness 是 Agent 的控制平面，不等于 LLM 本身。
2. LLM 负责理解、生成建议、总结信息。
3. Harness 负责状态、工具权限、执行流程、错误处理、日志、评测和反馈闭环。
4. 在我的项目里，Harness 对应 TaskObject + Planning + Runtime + Reporting。
5. 这样可以避免 LLM 直接拥有执行权。
```

收束句：

```text
LLM is a bounded worker, not the control plane.
```

---

## 4. 你的项目是什么？

关键词：

```text
3D Agent
Blender
TaskObject
Planning
Runtime
OperationSpec
Core API
copy-only
```

60 秒骨架：

```text
1. 表面上是 Blender 3D 模型修改 Agent。
2. 本质上是一个 controlled Agent execution architecture。
3. 用户输入先变成 TaskObject，Planning 做验证、绑定、选工具、补参数、安全检查。
4. Runtime 只执行 ready task，分发 Domain handler。
5. Core API 是唯一接触 bpy 的层，输出 copy，不覆盖源文件。
```

收束句：

```text
这个项目验证的是有真实副作用场景下，Agent 怎么安全执行。
```

---

## 5. 为什么不让 LLM 直接生成 Blender 脚本？

关键词：

```text
副作用
bpy 风险
覆盖源文件
误改对象
不可审计
OperationSpec
Runtime
```

60 秒骨架：

```text
1. Blender 文件修改有真实副作用。
2. LLM 直接写 bpy 脚本可能覆盖源文件、删除对象、应用破坏性 mesh edit。
3. 失败后很难定位，也不能稳定复用。
4. 所以我把执行限制在 OperationRegistry 注册过的 operation。
5. Domain handler 是固定代码，Core API 才能接触 bpy。
```

收束句：

```text
我不是不用 LLM，而是不让 LLM 直接拥有执行权。
```

---

## 6. TaskObject 解决了什么问题？

关键词：

```text
单一事实源
状态机
字段 ownership
防止漂移
可序列化
可恢复
```

60 秒骨架：

```text
1. Agent 最容易出问题的是事实散落在聊天历史、dict、script、report 里。
2. TaskObject 把当前任务事实集中起来。
3. 它保存 user_input、target、intent、planning、runtime、result、artifacts。
4. 它有生命周期：draft 到 completed / failed。
5. 每一层只能写自己拥有的字段，避免跨层污染。
```

收束句：

```text
TaskObject 让 Agent 从聊天驱动变成状态驱动。
```

---

## 7. Planning 和 Runtime 为什么要分离？

关键词：

```text
decision != execution
Planning 决策
Runtime 执行
不重规划
failure stage
```

60 秒骨架：

```text
1. Planning 负责做决定：验证、绑定、选 operation、补参数、安全检查。
2. Runtime 负责执行：只接受 ready_to_execute task。
3. Runtime 不理解自然语言，不重新选工具，不补参数。
4. 如果失败，Runtime 记录 failure stage，而不是临时换另一个工具。
5. 这样失败归因清楚，系统可测试。
```

收束句：

```text
Planning 做决定，Runtime 只执行，这是稳定 Agent 的关键边界。
```

---

## 8. OperationSpec / OperationRegistry 对应什么？

关键词：

```text
Tool Calling
Agent Skills
参数 schema
安全等级
handler
metadata
```

60 秒骨架：

```text
1. 它类似 tool calling，但比直接暴露函数更受控。
2. OperationSpec 声明 operation 名称、参数 schema、安全等级、handler、intent metadata。
3. OperationRegistry 是系统可执行能力列表。
4. LLM 不能随便调用不存在的工具。
5. 每个 skill 都可以测试、报告和复用。
```

收束句：

```text
我把工具能力从 prompt 里抽离出来，沉淀成可复用的 Agent Skills。
```

---

## 9. 你怎么理解 Tools & Skills？

关键词：

```text
不是堆代码
能力积木
OperationSpec
Domain handler
可复用
可回归
```

60 秒骨架：

```text
1. 我理解 Tools & Skills 不是把代码堆起来，而是把可复用能力产品化。
2. 在我的项目里，一个 skill 对应 OperationSpec + Domain handler + 参数 schema + report schema。
3. 这样每次不需要重新 prompt，也不需要 LLM 临时发明做法。
4. 技能稳定后可以进入评测和回归。
```

收束句：

```text
Skill 的价值在于可复用、可验证、可维护。
```

---

## 10. 你怎么做 Agent Evaluation？

关键词：

```text
Operation Selection
Parameter Accuracy
Target Binding
Runtime Reliability
不是只看 demo
```

60 秒骨架：

```text
1. 我不会只看 Agent 是否输出了内容。
2. 我会分四类评估：operation selection、parameter accuracy、target binding、runtime reliability。
3. operation 看是否选对工具。
4. parameter 看是否符合用户语义。
5. binding 看是否改对对象。
6. runtime 看 output、report、source unchanged 和 failure stage。
```

收束句：

```text
Agent 评估要看任务是否稳定正确完成，而不是只看能不能跑。
```

---

## 11. 你怎么处理上下文？

关键词：

```text
ContextManager
Context Assembly
TaskObject
不是事实源
按阶段装配
```

60 秒骨架：

```text
1. 我区分 context 和 state。
2. Context 是给 LLM 的输入，TaskObject 才是当前任务事实源。
3. 当前有 design taxonomy、model context、session context。
4. 后续会按阶段装配：classifier、intent parser、planning explanation、user response。
5. 不把所有文档都塞进 prompt，也不让 context 覆盖 TaskObject。
```

收束句：

```text
Context 是 evidence，TaskObject 是事实。
```

---

## 12. 你怎么理解 Memory？

关键词：

```text
Working
Episodic
Semantic
Procedural
不复制 OperationSpec
```

60 秒骨架：

```text
1. 我不会直接照搬四层记忆，而是映射到当前系统。
2. Working memory 是当前 TaskObject。
3. Episodic memory 是 Runtime report + 用户反馈。
4. Semantic memory 是 taxonomy 和 docs RAG。
5. Procedural memory 已经是 OperationSpec + Domain handler，不应该再复制一套。
```

收束句：

```text
Memory 只能增强 Planning，不能变成第二事实源。
```

---

## 13. 你需要 RAG 吗？

关键词：

```text
evidence provider
不是 decision maker
docs
operation
failure cases
citation
```

60 秒骨架：

```text
1. 需要，但它的位置要正确。
2. RAG 应该提供 evidence，不应该直接决定 selected_operation。
3. 可以检索 architecture docs、operation docs、failure cases、evaluation reports。
4. evidence 进入 Context Assembly，帮助解释和建议。
5. 最终决策仍由 OperationSpec 和 Planning selector 控制。
```

收束句：

```text
RAG 是证据层，不是执行控制层。
```

---

## 13A. RAG 的基本原理是什么？

关键词：

```text
Retrieval-Augmented Generation
知识库
chunk
embedding
向量检索
rerank
evidence
```

60 秒骨架：

```text
1. RAG 全称是 Retrieval-Augmented Generation，也就是检索增强生成。
2. 它的核心不是让模型凭记忆回答，而是先从知识库里检索相关证据。
3. 常见流程是：文档切 chunk，生成 embedding，存入向量索引，任务进来后检索相关片段，再放进 prompt。
4. RAG 不一定只有向量检索，也可以结合关键词检索、metadata filter、BM25、rerank。
5. 它解决的是知识库太大、prompt 放不下、模型容易胡编的问题。
```

收束句：

```text
RAG 的价值是让模型基于相关证据回答，而不是凭空生成。
```

---

## 13B. 在你的系统里，什么会成为知识库？

关键词：

```text
design taxonomy
OperationSpec
operation docs
model context
runtime reports
failure cases
feedback memory
architecture docs
```

60 秒骨架：

```text
1. 我的系统里未来会有多类知识库，不只是普通文档。
2. 设计知识包括 design taxonomy、style、density、scale、机甲建模规则。
3. 能力知识包括 OperationSpec、OperationRegistry、operation docs、parameter schema。
4. 模型知识包括 model_context、scene_manifest、binding_context、part aliases。
5. 经验知识包括 runtime reports、failure cases、post-check results、user feedback。
6. 架构知识包括 architecture docs、reliability design、optimization roadmap。
```

收束句：

```text
当这些知识变大后，就需要 RAG 帮 Agent 找到和当前任务最相关的 evidence。
```

---

## 13C. RAG 在你的系统里落地到哪些模块？

关键词：

```text
Knowledge Base
RAG Evidence Layer
Context Assembly
Planning explanation
OperationSelector
Runtime 不受 RAG 控制
```

60 秒骨架：

```text
1. 我会把 RAG 放在 Knowledge Base 和 Context Assembly 之间，作为 evidence layer。
2. RAG 负责检索和当前任务相关的 operation docs、参数 guideline、失败案例、用户反馈和架构说明。
3. Context Assembly 决定这些 evidence 进入哪个阶段的 prompt，比如 intent parser、planning explanation、user response。
4. Planning 可以参考 RAG evidence 解释为什么这样选，但最终 selected_operation 仍由 OperationSpec 和 selector 控制。
5. Runtime 不读取 RAG 来决定执行，它只执行 ready_to_execute 的 TaskObject。
```

收束句：

```text
RAG 是检索层，Context Assembly 是装配层，TaskObject 是事实层，Planning 是决策层，Runtime 是执行层。
```

---

## 13D. RAG 未来怎么规划？

关键词：

```text
先轻量
keyword search
metadata filter
vector search
rerank
citation
retrieval eval
```

60 秒骨架：

```text
1. 我不会一开始就上复杂向量数据库，先做轻量 RAG Evidence Layer。
2. 第一阶段可以用关键词检索和 metadata filter，例如按 operation、target_part、style、failure_stage 找相关片段。
3. 第二阶段再引入 embedding、vector search 和 rerank，提高语义召回能力。
4. 每条 evidence 要带 source path 和 metadata，方便解释和审计。
5. 最后要做 retrieval evaluation，看召回是否真的帮助 operation selection、参数建议和 retry suggestion。
```

收束句：

```text
RAG 先服务解释和证据检索，成熟后再进入 evaluation 和 feedback loop，但始终不替代 TaskObject 和 Planning。
```

---

## 14. 为什么不用 LangGraph？

关键词：

```text
StateGraph
TaskObject
强领域约束
文件安全
自研 runtime
可做 mini demo
```

60 秒骨架：

```text
1. LangGraph 的 state graph 思想和我的 TaskObject lifecycle 很像。
2. TaskObject 对应 State，Planning/Runtime 对应 node，lifecycle transition 对应 edge。
3. 但我的主项目涉及 Blender 文件修改，需要更强的文件安全、OperationSpec contract 和 copy-only persistence。
4. 所以主项目用自研 controlled runtime。
5. 我可以做 LangGraph mini demo 证明理解框架，但不迁移主链。
```

收束句：

```text
我不是不用框架，而是根据领域风险选择更强控制边界。
```

---

## 15. 你怎么理解 ReAct？

关键词：

```text
Reason
Act
Observe
自由 loop 风险
controlled ReAct-like
```

60 秒骨架：

```text
1. ReAct 是 Reason-Act-Observe 循环。
2. 我的项目借鉴 observe/feedback 思想，但不做自由工具循环。
3. Reason 在 Agent/Planning，Act 被限制为 selected_operation。
4. Observe 是 Runtime report / OperationOutcome。
5. 下一轮 Planning 可以读取 report，但不能绕过 TaskObject。
```

收束句：

```text
这是 controlled ReAct-like workflow，而不是自由 ReAct loop。
```

---

## 16. 为什么不现在做 Multi-Agent？

关键词：

```text
事实冲突
执行权冲突
单 control plane
worker roles
后置
```

60 秒骨架：

```text
1. 多 Agent 很容易带来事实冲突和执行权冲突。
2. 谁能写 TaskObject，谁能触发 Runtime，失败算谁的，这些都要先定义。
3. 当前系统最强的是单主链、单事实源、单 Runtime。
4. 后续可以引入只读或建议型 worker roles，比如 retry suggestion、report summary。
5. 但执行权仍然归 Harness。
```

收束句：

```text
先有稳定 control plane，再谈多 Agent。
```

---

## 17. 你怎么看 Agent 输出不稳定？

关键词：

```text
不能只靠 prompt
结构化任务
工具白名单
preflight
post-check
eval
feedback
```

60 秒骨架：

```text
1. 输出不稳定不能只靠 prompt 修。
2. 要把任务结构化，用 TaskObject 固化事实。
3. 用 OperationSpec 限制工具集合。
4. 用 preflight 和 post-check 检查执行前后状态。
5. 用 evaluation cases 和 feedback memory 把错误沉淀成规则。
```

收束句：

```text
稳定性来自系统约束，不是来自更长的 prompt。
```

---

## 18. 你怎么用 AI 辅助工作？

关键词：

```text
Copilot
Codex
Claude Code
DeepSeek
信息压缩
假设生成
人工验证
```

60 秒骨架：

```text
1. 我高频使用 AI，但不把它当最终裁判。
2. Copilot 适合工作文件分析和文档处理，但要防幻觉。
3. Codex 适合长上下文工程任务。
4. Claude Code 长文本能力强，但也要观察稳定性。
5. DeepSeek 适合短问题和情感类反馈。
6. 我的原则是：AI 给阶段性参考，人做最终证据判断。
```

收束句：

```text
信息越准确，AI 越可靠；边界越清楚，AI 越能干活。
```

---

## 19. AI 辅助 MDS/DQS ICM 的例子怎么讲？

关键词：

```text
日志
错误栈
trace
DB backup
假设
收敛
root cause
人工确认
```

60 秒骨架：

```text
1. 我会先收集客户描述、日志、trace、DB backup、环境信息。
2. 用 AI 辅助总结已知事实和缺失信息。
3. 让 AI 列可能原因和调查路径。
4. 我再基于代码、数据库、配置和复现场景确认哪些成立。
5. 逐步缩小范围直到 root cause。
6. 最后沉淀到知识库，减少下次调查成本。
```

收束句：

```text
AI 是调查中的临时 analyst，不是最终裁判。
```

---

## 20. 你的个人工作方式是什么？

关键词：

```text
第一性原理
边界条件
变量拆解
证据
目标驱动
闭环
```

60 秒骨架：

```text
1. 我习惯从第一性原理理解系统，不满足于只会用表层 API。
2. 面对不确定性，我会先澄清边界条件和变量。
3. 对长期重复问题，我会归档、总结规律、沉淀知识。
4. 我偏好目标驱动，有目标后会拆解计划并推进闭环。
5. 这也是我喜欢 Agent Harness 的原因：它把混乱输出变成可控系统。
```

收束句：

```text
我倾向于让混乱问题按照可解释、可复用的规则运转。
```

---

## 21. 你的项目短板是什么？

关键词：

```text
eval 未完整
feedback loop 未落地
RAG 未实现
服务化不足
real smoke 覆盖有限
```

60 秒骨架：

```text
1. 我不会说项目已经完美。
2. 当前已经有 366 tests、fake E2E、edge_soften real smoke。
3. 但系统化 evaluation、feedback loop、RAG evidence、FastAPI service 还在 roadmap。
4. 下一步计划是 Agent Evaluation Report -> Runtime Preflight/Post-check -> Context Assembly -> Feedback Loop。
```

收束句：

```text
我清楚当前边界，也有明确的工程化下一步。
```

---

## 21A. 你的 Agent 有 Runtime Loop 吗？

关键词：

```text
Runtime Engine
single-pass runtime
future controlled runtime loop
真实副作用
real side effects
preflight
observe
post-check
retry suggestion
```

60 秒骨架：

```text
1. 当前版本有 Runtime Engine，但还不是完整 Runtime Loop。
2. 现在更准确地说是 controlled single-pass runtime：Planning 把 TaskObject 推到 ready_to_execute，Runtime 执行一次 selected_operation，写 report，然后 completed 或 failed。
3. Runtime Loop 是执行、观察、检查、决定下一步的循环，适合长任务、多步骤、失败恢复和 human-in-the-loop。
4. 我的系统会修改真实 Blender 文件，这属于 real side effects，也就是执行后会改变外部世界的状态，比如添加 modifier、生成 output blend copy、写 report。
5. 所以我不会一开始做自由 ReAct loop，而是先保证单步安全，再基于 preflight、post-check、failure stage、feedback memory 做 controlled runtime loop。
```

收束句：

```text
当前是 controlled single-pass runtime，下一阶段目标是 controlled runtime loop；先保证单步安全，再做受控循环。
```

---

## 22. 为什么不直接做更复杂功能？

关键词：

```text
Composite
MCP
mesh edit
boolean
安全边界
先稳定单步
```

60 秒骨架：

```text
1. Composite、MCP、mesh edit 都有价值。
2. 但它们会扩大安全边界和恢复复杂度。
3. 当前系统先保持 modifier-only、copy-only、non-destructive。
4. 先把单步 operation 的准确率、可靠性、post-check 做稳。
5. 再做重型能力。
```

收束句：

```text
复杂能力要建立在稳定边界之上。
```

---

## 23. 如果问“你没有医疗经验怎么办？”

关键词：

```text
业务可学
工程方法可迁移
专家标准
规则沉淀
真实系统
```

60 秒骨架：

```text
1. 我没有医疗业务经验，这是事实。
2. 但这个岗位核心不是医学知识本身，而是把专家标准沉淀成可复用 Agent 能力。
3. 我过去在 MDS/DQS 中处理过复杂业务规则、客户问题、发布和回归。
4. 我擅长把混乱问题拆成规则、变量、证据和流程。
5. 医疗业务可以跟专家学习，工程化沉淀方法是可迁移的。
```

收束句：

```text
我擅长把专家知识变成可执行、可验证、可维护的系统能力。
```

---

## 24. 如果问“为什么你年资高但 AI 经验不久？”

关键词：

```text
工程底座
真实系统
AI 加速
边界判断
不是玩具 demo
```

60 秒骨架：

```text
1. 我的 AI 项目时间不算长，但我有长期企业级工程底座。
2. Agent 真正难点不是会调 API，而是状态、边界、错误、评测、交付。
3. 这些能力来自多年真实系统经验。
4. AI 加速了我的实现，但我负责判断、约束和验收。
5. 所以我更适合做工程化 Agent，而不是纯 prompt demo。
```

收束句：

```text
我的优势是用成熟工程经验驾驭 AI，而不是只追新工具。
```

---

## 25. 最后反问面试官

关键词：

```text
control plane
eval
feedback
skills
trace
human review
```

可问问题：

```text
1. 你们现在的 Agent 是 LLM 直接 tool calling，还是有独立 control plane？
2. 你们如何评估 Agent 输出是否对齐业务专家标准？
3. 你们的 Tools & Skills 是如何版本化和回归测试的？
4. 你们如何处理 Agent 输出错误后的反馈闭环？
5. 哪些环节必须 human review，哪些可以自动化？
6. 你们更需要我先补哪块：evaluation、workflow、tooling，还是工程基建？
```

收束句：

```text
这些问题展示的是你关心生产级 Agent，而不只是 demo。
```

---

## 25A. 和招聘方打招呼怎么说？

关键词：

```text
Harness Agent
企业级系统经验
MDS / DQS
TaskObject
Planning / Runtime
OperationSpec
评测回归
稳定输出
```

通用短版：

```text
你好，我对这个 Harness Agent / AI Agent 工程化岗位很感兴趣。

我有 10 年左右企业级软件开发和复杂系统维护经验，长期参与 Microsoft SQL Server MDS / DQS 产品维护、客户问题诊断、CloudTest / Release Signoff、Hotfix、可访问性修复和安全改造。

最近我独立做了一个 3D Model Modification Agent 项目，重点是 Agent 架构而不是 demo：用 TaskObject 管理任务状态和事实，用 Planning / Runtime 分离决策与执行，用 OperationSpec / OperationRegistry 沉淀 Agent Skills，并通过 Runtime report、copy-only 策略和测试体系保证可追踪、可回归。

我比较关注 Agent 的状态管理、工具调用边界、Runtime 可靠性、上下文管理、评测和反馈闭环，感觉和岗位方向比较匹配，想和您进一步沟通一下。
```

偏 Harness 岗位版：

```text
你好，我看到岗位在做 Agent Harness / Tools & Skills / 评测回归 / 工程基建方向，感觉和我最近做的事情比较匹配。

我过去主要做企业级软件和复杂系统维护，长期参与 Microsoft SQL Server MDS / DQS 项目，处理过客户 ICM、可访问性修复、CloudTest / Release Signoff、Hotfix、BinaryFormat 安全改造和知识库沉淀。

最近我独立做了一个 3D Model Modification Agent 项目。它不是让 LLM 直接生成 Blender 脚本，而是做了一套受控执行架构：TaskObject 做主事实源，Planning 和 Runtime 分离，OperationSpec / OperationRegistry 沉淀 Agent Skills，Domain/Core 控制真实执行边界，Runtime report 记录执行结果。我的核心思路是：LLM 是 bounded worker，不是 control plane。

我觉得自己比较适合做 Agent Harness / Agent Workflow / AI 工程化这类方向，想进一步了解下这个岗位。
```

偏技术负责人版：

```text
你好，我对岗位里的 Agent Harness、Tools & Skills、评测回归和工程基建方向很感兴趣。

我最近独立实现了一个 TaskObject-centered Controlled Agent Execution Harness，用于 3D 模型修改场景。这个系统中，LLM 不直接拥有执行权，而是通过 TaskObject 记录任务事实，通过 Planning Engine 完成 validation、binding、operation selection 和 parameter completion，再由 Runtime Engine 确定性分发 Domain handler。工具能力通过 OperationSpec / OperationRegistry 管理，Core API 是唯一接触 Blender bpy 的边界，执行结果通过 Runtime report 记录。

除了这个 Agent 项目，我也有较长时间的企业级软件经验，主要在 Microsoft SQL Server MDS / DQS 相关产品中处理客户问题、Hotfix、Release Signoff、CloudTest、可访问性修复、安全改造和复杂问题定位。我比较擅长把混乱问题拆成状态、规则、工具、评测和反馈闭环。

如果这个岗位需要的是能把 Agent 从 demo 推进到可交付系统的人，我觉得我会比较匹配，想进一步沟通。
```

偏同频版：

```text
你好，我看到这个岗位在讲 Agent Harness、评测、回归、Tools & Skills 和真实场景落地，感觉比较符合我想做的方向。

我不太想做只是“调 API / 写 prompt”的 AI 应用，更关注怎么把 AI 放进一个有状态、有边界、有工具契约、有评测和反馈机制的工程系统里。最近我独立做了一个 3D Model Modification Agent 项目，核心就是验证这套思路：LLM 只是 bounded worker，真正的 control plane 是 TaskObject + Planning + Runtime。

我过去长期做 Microsoft SQL Server MDS / DQS 这类企业级产品维护，处理过客户 ICM、发布、CloudTest、Hotfix、可访问性、安全改造和问题沉淀，对真实系统的稳定性、回归和可维护性比较敏感。希望有机会聊聊这个岗位。
```

使用建议：

```text
Boss 直聘：用通用短版。
技术负责人：用技术负责人版。
Harness 文案很有个性的岗位：用同频版。
对方明显强调 Tools & Skills / Eval：用偏 Harness 岗位版。
```

收束句：

```text
打招呼的核心不是堆技术词，而是让对方立刻知道：我有真实系统经验，也做过 Agent Harness 项目，并且关注稳定输出和工程化落地。
```

---

## 25B. LLM 基础概念怎么讲？

关键词：

```text
token
context window
temperature / top-p
system / user instruction
structured output
hallucination
```

60 秒骨架：

```text
1. LLM 本质上是基于上下文预测下一个 token 的模型，所以 token 和 context window 是最基础的限制。
2. context window 决定一次能看多少输入，但不等于长期记忆，也不保证模型会正确使用所有信息。
3. temperature / top-p 控制输出随机性，工程场景里通常会降低随机性，并配合结构化输出。
4. system / developer / user instruction 决定约束层级，但真实系统不能只依赖 prompt 约束。
5. hallucination 是模型在缺少证据或约束时生成看似合理但不可靠内容，所以要靠 evidence、schema、tool result 和 validation 收敛。
```

收束句：

```text
我理解 LLM 是强推理和生成组件，但生产级 Agent 需要用上下文、工具、校验和执行边界把它约束起来。
```

---

## 25C. Tool / Function Calling 怎么讲？

关键词：

```text
tool schema
parameter validation
tool selection
tool execution
side effect
idempotency
permission boundary
```

60 秒骨架：

```text
1. Function calling / tool calling 是让模型用结构化参数请求外部能力，而不是只输出自然语言。
2. 关键不只是把 API 暴露给模型，而是定义 tool schema、参数类型、必填字段、权限和副作用。
3. tool selection 是模型或 planner 判断该用哪个工具，tool execution 应该由受控 runtime 执行。
4. 对有副作用的工具，要考虑参数校验、幂等性、审批、日志和失败回滚。
5. 在我的项目里，OperationSpec / OperationRegistry 就是工具能力契约，Runtime 才是真正执行者。
```

收束句：

```text
Tool calling 的核心是把模型意图变成可校验、可审计、可控制的外部动作。
```

---

## 25D. Agent Loop 怎么讲？

关键词：

```text
plan
act
observe
state
checkpoint
retry
bounded autonomy
```

60 秒骨架：

```text
1. Agent loop 可以理解为 plan -> act -> observe -> update state 的循环。
2. plan 是决定下一步，act 是调用工具或执行动作，observe 是读取结果、错误和环境反馈。
3. 生产系统里不能让这个 loop 完全自由，否则容易出现错误工具调用、状态漂移和无限 retry。
4. 所以要有状态机、checkpoint、failure stage、retry policy 和 human approval。
5. 我的系统当前不是自由 ReAct loop，而是 controlled execution：Planning 先把任务变成 ready task，Runtime 只执行确定动作，再把 report 作为下一轮 evidence。
```

收束句：

```text
Agent loop 的价值是持续推进任务，但工程重点是让循环有边界、有状态、有停止条件。
```

---

## 25E. RAG 和 Memory 的区别怎么讲？

关键词：

```text
RAG = evidence retrieval
Memory = experience / state
embedding
chunk
episodic memory
semantic memory
not source of truth
```

60 秒骨架：

```text
1. RAG 主要解决从外部知识库检索相关证据的问题，典型流程是 chunk、embedding、retrieve、rerank、assemble context。
2. Memory 更偏长期经验和状态沉淀，例如用户偏好、历史任务、失败案例和反馈。
3. 两者都不应该直接变成执行事实源，否则会和当前任务状态冲突。
4. 在我的项目里，RAG 可以检索 operation docs、failure cases、architecture docs；Memory 可以保存 runtime report 和用户反馈。
5. 但当前任务事实仍然由 TaskObject 管，Planning 可以参考 evidence，Runtime 不能被 RAG 或 Memory 直接驱动。
```

收束句：

```text
RAG 提供证据，Memory 提供经验，TaskObject 才是当前任务事实源。
```

---

## 25F. Agent Evaluation 基础怎么讲？

关键词：

```text
golden tasks
rubric
trajectory eval
tool-call accuracy
regression
failure taxonomy
```

60 秒骨架：

```text
1. Agent evaluation 不能只看最终回答像不像，而要看任务路径是否正确。
2. 可以准备 golden tasks，定义 rubric，评估 intent parsing、tool selection、parameter accuracy、target binding 和 final outcome。
3. 对 Agent 来说，trajectory eval 很重要，因为中间工具调用错了，最终结果即使看起来合理也不可靠。
4. 还要记录 failure taxonomy，例如 instruction miss、wrong tool、bad parameter、runtime failure、unsafe action。
5. 我的项目里已经把 Runtime report、failure stage、source unchanged、output artifact 作为后续 eval 和 regression 的基础。
```

收束句：

```text
Agent Evaluation 要评估完成任务的全过程，而不是只评估一句回答。
```

---

## 25G. Safety / Governance 怎么讲？

关键词：

```text
prompt injection
tool injection
secret handling
sandbox
approval gate
audit log
least privilege
```

60 秒骨架：

```text
1. Agent 安全的核心风险是模型会被输入影响，又能调用真实工具，所以必须控制权限和副作用。
2. prompt injection 是外部内容试图覆盖系统指令，tool injection 是诱导 Agent 调用不该调用的工具或传入危险参数。
3. 处理方式包括 tool allowlist、schema validation、least privilege、sandbox、approval gate、secret redaction 和 audit log。
4. 对文件、数据库、生产环境这类高风险操作，要区分 read-only、preview、write、delete 等安全等级。
5. 我的项目用 copy-only、Domain/Core 分层、Runtime report 和 OperationSpec safety level 来降低执行风险。
```

收束句：

```text
Agent 安全不是一句 prompt，而是权限、工具、状态、审计和人审边界的系统设计。
```

---

## 25H. MCP 基础怎么讲？

关键词：

```text
Model Context Protocol
client / server
tools
resources
prompts
standard interface
```

60 秒骨架：

```text
1. MCP 是 Model Context Protocol，可以理解为给模型应用接入外部工具和上下文的一套标准协议。
2. MCP 里通常有 client 和 server：client 在 IDE 或 Agent 应用里，server 暴露 tools、resources、prompts 等能力。
3. tools 是可调用动作，resources 是可读取上下文或数据，prompts 是可复用提示模板。
4. 它和普通 function calling 的区别是，MCP 更像生态层的标准连接方式，便于不同工具以统一接口接入 Agent。
5. 如果映射到我的项目，OperationSpec / OperationRegistry 是内部工具契约，未来可以考虑把部分能力包装成 MCP server，让外部 Agent 以标准方式调用。
```

收束句：

```text
MCP 的价值是把 Agent 和外部工具/上下文的连接标准化，但执行边界和权限仍然要由 Harness 管。
```

---

## 25I. 如果被问“你基础是不是不系统”怎么答？

关键词：

```text
不是模型训练方向
工程化切入
runtime / harness
正在补齐基础概念
可迁移系统经验
```

60 秒骨架：

```text
1. 我会承认自己不是从模型训练或论文路线切入的，而是从工程化和复杂系统交付切入 Agent。
2. 我的优势不是训练模型，而是把 LLM 放进可控 runtime，让它能通过工具、状态、评估和反馈稳定完成任务。
3. 这和我过去做 MDS / DQS 客户问题、release、CloudTest、hotfix 的经验是连续的：都要求状态清楚、边界明确、结果可验证。
4. LLM、RAG、tool calling、MCP、Agent eval 这些基础概念我正在系统补齐，而且会用自己的项目把概念落到架构里。
5. 所以我的定位更接近 Agent Runtime / Harness / Infrastructure Engineer，而不是纯算法研究或 prompt operator。
```

收束句：

```text
我不是按传统 AI 学习路线起步，但我能把 Agent 做成可交付、可治理、可验证的工程系统。
```

---

## 26. 每天复习方法

```text
1. 每天只练 5 张卡片
2. 每题只说 60 秒
3. 录音回听
4. 每次只修一个问题
5. 不背全文，只背关键词顺序
```

第一天：

```text
1-5
```

第二天：

```text
6-10
```

第三天：

```text
11-13D
```

第四天：

```text
14-18
```

第五天：

```text
19-21A
```

第六天：

```text
22-25A
```

第七天：

```text
25B-25I 基础补课速查
```

第八天：

```text
随机抽 10 题
```

第九天：

```text
只练 30 秒、2 分钟、自我介绍和反问
```
