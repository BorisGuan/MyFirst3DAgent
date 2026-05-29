# Designer Operation Library 开发计划书

## 0. 总结

当前阶段的目标不是继续优化框架，也不是优先补 E2E 或 smoke，而是建设一个面向高达/机甲/硬表面模型设计师工作流的 operation 能力库。这个能力库要把常用、通用、可组合的设计动作产品化成 operations，让用户可以用简单指令驱动 AI 拆解意图，并通过多个 operation 的组合完成模型细节设计。

这条路线的商业价值在于：系统不只是“能执行一个 Blender modifier”，而是逐步沉淀一套机甲设计操作语言。用户说“让胸甲更 RG 风、细节密一点但不要破坏轮廓”，系统最终应该能拆解成一组稳定操作，例如分件线、装甲分层、散热口、边缘处理、法线收尾等，而不是生成一次性脚本。

本计划的边界很明确：

```text
当前阶段只做 operation 扩展和设计动作库建设。
暂不做框架重构、参数系统重构、Outcome 泛化、Safety 分级、E2E 优先补齐、真实 Blender smoke 扩展或通用 sequence 架构。
```

已经完成的基础：

```text
edge_soften
weighted_normal_finish
intent-aware operation selection
TaskObject -> Planning -> Runtime -> Domain -> Core API 主链
```

下一阶段重点：围绕设计原则，把常见设计师操作拆成可实现、可组合、可逐步扩展的 operation 清单，并按优先级逐个实现。

## 1. 目标定义

### 1.1 不是框架工程，是真实设计能力工程

operation 扩展的目标不是“多注册几个函数”，而是把模型设计师的常用动作变成系统能力。

设计师常用语言通常是：

```text
增加分件线
强化装甲层次
做厚重一点
加机械细节
加散热口
加喷口
加武器挂点
做左右对称细节
让表面高光更硬朗
做 RG 风高密度细节
不要破坏整体轮廓
```

这些不是底层 Blender API，而是设计语义。operation 库要把这些语义落到可执行操作。

### 1.2 用户体验目标

用户最终不需要知道 operation 名称。用户只需要说：

```text
给胸甲做更多 RG 风格分件线，细节密一点，但不要影响轮廓。
```

系统内部应该能逐步映射为：

```text
目标部位: chest_armor
设计风格: RG / high-density mechanical detail
约束: preserve silhouette, non-destructive
候选 operation:
  panel_line_bevel_prepare
  armor_layer_plate_prepare
  vent_slot_prepare
  edge_soften
  weighted_normal_finish
```

短期内仍然可以一次只执行一个 operation；中期再基于真实组合需求引入 operation sequence。

## 2. 当前阶段边界

### 2.1 本阶段要做

```text
建立设计师 operation taxonomy
定义 operation library roadmap
优先实现常见、高价值、低风险、可组合的 operations
每个 operation 都沿用当前 Registry / Planning / Runtime / Domain / Core 扩展方式
每个 operation 都尽量对应真实设计动作
```

### 2.2 本阶段暂不做

```text
不重构 TaskObject schema
不设计通用 operation sequence 架构
不重构参数补全系统
不新增 OperationSpec 大量能力字段
不泛化 OperationOutcome 
不做 Safety policy 分级重构
不把测试或 smoke 作为当前主线目标
不为了未来能力提前改 Runtime / Domain 边界
```

这些事情可以进入后置 backlog，但不能阻塞 operation 扩展主线。

## 3. 设计原则到 Operation 的映射

### 3.1 机甲模型常见设计原则

| 设计原则 | 设计含义 | 可转化的 operation 方向 |
| --- | --- | --- |
| 分件感 | 让装甲像多个独立板件拼合 | panel line, parting line, bevel groove |
| 层次感 | 通过外甲、叠甲、边缘错落增强结构 | armor layer, plate offset, thickness preview |
| 硬表面高光 | 让机械表面反光更稳定、更硬朗 | weighted normal, bevel finish |
| 功能暗示 | 通过散热口、喷口、接口表达机械功能 | vents, thrusters, hardpoints |
| 比例适配 | 细节尺寸符合 1/144、1/100 等比例 | operation default size profiles, later scale-aware tuning |
| 轮廓保护 | 增加细节但不破坏大形 | modifier-only, inset/engrave style, non-destructive first |
| 风格一致 | 同一部位的线宽、密度、方向统一 | operation families, style presets later |
| 可组合 | 简单操作可组合成复杂设计意图 | operation library + future Planning sequence |

### 3.2 先从高达/机甲硬表面高频动作开始

优先级最高的动作不是最炫的，而是最常用、最容易被组合、最能形成设计语言的动作：

```text
分件线
刻线/面板线
装甲厚度感
硬表面高光收尾
装甲分层
散热口
推进器喷口
武器挂点/接口
传感器镜头
管线/线缆
```

## 4. Operation 能力目录

本计划不在 operation 模块内部重新设计一套分层架构，也不新增“语义层 parser”。用户指令到意图字段的解析仍然由 Agent Layer 完成，operation 选择仍然由 Planning Layer 根据 `TaskObject.intent` 和 `OperationSpec` 完成。

operation 模块当前只负责一件事：把常见设计师动作封装成可执行、可复用的 operations。每个 operation 都应该沿用当前扩展方式：

```text
OperationSpec
-> Planning selected_operation
-> Runtime handler dispatch
-> DomainOperationInput
-> Domain handler
-> Core API
```

### 4.1 当前优先封装的简单操作

这些 operation 是当前阶段最应该优先实现的设计动作。它们可以单独执行，也可以在未来被 Planning 组合成多步骤方案，但现在不为它们额外创建一套 operation 内部层级。

```text
edge_soften
weighted_normal_finish
solidify_thickness_preview
panel_line_bevel_prepare
surface_inset_prepare
plate_offset_prepare
vent_slot_prepare
thruster_nozzle_prepare
hardpoint_socket_prepare
sensor_lens_prepare
cable_curve_prepare
```

实现原则：

```text
输入明确
修改范围小
可复用
尽量非破坏
能用现有架构自然接入
不为了单个 operation 重构框架
```

### 4.2 设计语义如何复用原架构

“分件线”“装甲分层”“散热口”“推进器”这些设计语义不在 operation 模块里重新解析。它们应该继续进入已有链路：

```text
用户指令
-> Agent Layer 解析为 TaskObject.intent.action / detail_type / style / density
-> Planning Layer 使用 OperationSpec.intent_actions / intent_detail_types / intent_effects 选择 operation
-> Runtime 执行已选 operation
```

因此，本计划里的“设计动作”只是 operation library 的产品化分类和命名依据，不是新架构层。

### 4.3 复杂组合暂时只记录需求

复杂用户意图可能需要多个 operation，例如：

```text
RG 风胸甲细节 = panel_line_bevel_prepare + armor_layer_plate_prepare + edge_soften + weighted_normal_finish
重甲腿部 = solidify_thickness_preview + armor_layer_plate_prepare + edge_soften
高机动背包 = thruster_nozzle_prepare + vent_slot_prepare + weighted_normal_finish
```

这些组合现在只作为需求案例记录。等单个 operation 足够多、真实组合模式稳定后，再回到 Planning 层设计最小 sequence 能力。sequence 不属于当前 operation 模块的第一步工作。

## 5. Operation 设计模板

每个新增 operation 都应该先写清楚下面这些内容，再进入代码实现。

```text
operation name
用户会怎么说
解决的设计问题
目标对象类型
几何实现方式
是否改变轮廓
是否创建新对象
是否应用 mesh data
默认参数
intent action/detail/effect 标签
与其他 operation 的组合关系
短期实现版本
后续增强版本
```

示例：

```text
operation: solidify_thickness_preview
用户语言: 让装甲更厚一点 / 增加厚度感 / 更重甲
设计问题: 装甲太薄、缺少实体厚度暗示
实现方式: 添加非应用 SOLIDIFY modifier
轮廓影响: 轻微，可通过 offset 控制
mesh data: 不应用
组合关系: 常与 weighted_normal_finish、edge_soften 组合
```

## 6. 第一阶段 Operation Library

### 6.1 已完成

#### edge_soften

用途：边缘柔化、分件线 bevel 基础、硬表面细节收口。

适用用户语言：

```text
边缘柔一点
分件线不要太生硬
机械边缘处理一下
```

当前实现：BEVEL modifier。

#### weighted_normal_finish

用途：硬表面高光收尾，让模型表面阴影更干净。

适用用户语言：

```text
优化硬表面高光
让表面更干净
改善阴影和法线
```

当前实现：WEIGHTED_NORMAL modifier。

#### solidify_thickness_preview

用途：为装甲件添加非应用 Solidify modifier，用于表达装甲厚度感。

适用用户语言：

```text
让装甲更厚一点
增加厚度感
做重甲感
让外甲不要像纸片
```

当前实现：SOLIDIFY modifier。

#### panel_line_bevel_prepare

用途：为面板线/分件线准备添加语义明确的 Bevel modifier。

适用用户语言：

```text
加刻线
加面板线
加分件线
让装甲分割更明显
```

当前实现：BEVEL modifier。

#### armor_layer_plate_prepare

用途：为装甲分层/叠甲准备添加非应用 Solidify modifier，用作外甲层 preview。

适用用户语言：

```text
强化装甲层次
加叠甲
胸甲更有外甲结构
腿甲更有层次
```

当前实现：SOLIDIFY modifier。

#### vent_slot_prepare

用途：为散热口/格栅类机械功能细节添加语义明确的 Bevel modifier preparation。

适用用户语言：

```text
加散热口
加格栅
做进气口
增加机械功能细节
```

当前实现：BEVEL modifier。

#### thruster_nozzle_prepare

用途：为推进器/喷口类机械功能细节添加语义明确的 Bevel modifier preparation。

适用用户语言：

```text
加喷口
加推进器
做高机动细节
背包加喷嘴
```

当前实现：BEVEL modifier。

#### hardpoint_socket_prepare

用途：为武器挂点/接口类机械功能细节添加语义明确的 Bevel modifier preparation。

适用用户语言：

```text
加武器挂点
加接口
加连接位
加可扩展装置安装点
```

当前实现：BEVEL modifier。

#### surface_inset_prepare

用途：为内嵌面/凹面类表面层级变化添加非应用 Solidify modifier preparation。

适用用户语言：

```text
做一块内嵌面
某块装甲表面压进去一点
给表面增加凹面层次
```

当前实现：SOLIDIFY modifier。

#### armor_edge_lip_prepare

用途：为装甲边缘唇边/包边类边缘结构添加语义明确的 Bevel modifier preparation。

适用用户语言：

```text
装甲边缘有包边感
边缘更有机械板件的唇边
边缘不要只是平切
```

当前实现：BEVEL modifier。

### 6.2 下一批优先实现

#### Composite Pattern 候选表

设计价值：当前 10 个 Atomic Operations 已经足够开始整理高频组合套路。

用户语言：

```text
RG 风胸甲细节
重甲腿部细节
高机动背包细节
```

短期产物：

```text
只整理候选表
不实现 sequence
不改 TaskObject schema
```

## 7. 第二阶段 Operation Library

当第一阶段 modifier/preview 类 operation 稳定后，再进入会创建对象或更改结构的 operation。

候选：

```text
hardpoint_socket_prepare
sensor_lens_prepare
cable_curve_prepare
hydraulic_rod_prepare
surface_damage_prepare
weathering_marker_prepare
```

这些更接近真实设计生产力，但对 Core API 和输出语义要求更高。当前不为了它们提前改框架。

## 8. 用户指令到 Operation 的拆解示例

### 8.1 RG 风胸甲细节

用户：

```text
把胸甲做得更 RG 风一点，细节密一点，但不要破坏轮廓。
```

目标拆解：

```text
target: chest_armor
style: sharp_mechanical / rg-like
density: high
constraints: preserve silhouette, non_destructive
operations:
  panel_line_bevel_prepare
  armor_layer_plate_prepare
  edge_soften
  weighted_normal_finish
```

短期执行：选择一个最匹配 operation。

中期执行：支持 operation sequence 后组合执行。

### 8.2 重甲腿部

用户：

```text
让腿甲看起来更厚重，有更多装甲分层。
```

目标拆解：

```text
target: leg_armor
style: heavy_armor
density: medium
operations:
  solidify_thickness_preview
  armor_layer_plate_prepare
  edge_soften
```

### 8.3 高机动背包

用户：

```text
背包加一些高机动喷口和散热口。
```

目标拆解：

```text
target: backpack
style: high_mobility
operations:
  thruster_nozzle_prepare
  vent_slot_prepare
  weighted_normal_finish
```

## 9. 开发路线

### Step DOL-1：Designer Operation Library Plan

状态：当前文档。

目标：把后续开发路线从“框架优化/E2E 优先”转向“设计师 operation 能力库”。

产物：

```text
docs/designer_operation_library_development_plan.md
```

### Step DOL-2：solidify_thickness_preview

状态：已完成。

目标：实现装甲厚度感 preview operation。

范围：

```text
OperationSpec
Core add_solidify_modifier
Domain solidify_thickness_preview
Runtime handler registration
必要的 focused tests
```

不做：

```text
scale-aware thickness
boolean/integer schema 重构
Safety 分级重构
真实 smoke 默认执行
```

### Step DOL-3：panel_line_bevel_prepare

状态：已完成。

目标：把“面板线/分件线准备”从通用 `edge_soften` 里拆出，形成更贴近设计语义的 operation。

价值：

```text
让用户的“加刻线/加分件线”有明确 operation 承接
让 selector 能区分 edge finishing 和 panel-line preparation
为后续真实 groove/cut 打基础
```

### Step DOL-4：armor_layer_plate_prepare

状态：已完成。

目标：实现第一个更接近设计语义的装甲分层 operation。

策略：

```text
先寻找当前架构下最小可实现版本
如果需要新增对象或 mesh edit，先降级为 preview/marker operation
不为了它重构框架
```

### Step DOL-5：vent_slot_prepare
状态：已完成。

目标：实现散热口/格栅类设计操作的第一版。

策略：

```text
先做非破坏 preview 或 placeholder
后续再进入真实 cut/boolean 版本
```

### Step DOL-6：Atomic Operation 扩展需求分析

状态：已完成。

目标：研究哪些基础设计动作值得继续封装为 operation，哪些应暂缓，哪些只是 Blender/Core API 实现手段而不应直接暴露为用户级 operation。

产物：

```text
docs/atomic_operation_extension_analysis.md
docs/atomic_operation_development_plan.md
```

结论：Composite Operation 需求回收后移；当前阶段 10 个 Atomic Operations 已完成，下一步按照 [Atomic Operation 开发计划书](atomic_operation_development_plan.md) 整理 Composite Pattern 候选表，不实现 sequence。

### Step DOL-7：thruster_nozzle_prepare

状态：已完成。

目标：实现推进器/喷口类设计操作的第一版。

策略：

```text
先做当前架构可自然容纳的 preparation version
不创建真实 nozzle object
不做 mesh edit / boolean
不做 sequence
不重构参数系统
```

对应 Atomic Operation 计划步骤：

```text
Step AO-1: thruster_nozzle_prepare
```

### Step DOL-8：hardpoint_socket_prepare

状态：已完成。

目标：实现武器挂点/接口类设计操作的第一版。

策略：

```text
先做 socket preparation
不创建复杂连接件
继续沿用 OperationSpec -> Domain -> Core 扩展方式
```

对应 Atomic Operation 计划步骤：

```text
Step AO-2: hardpoint_socket_prepare
```

### Step AO-3：surface_inset_prepare

状态：已完成。

目标：实现内嵌面 / 凹面 preparation operation。

策略：

```text
先确认与 panel_line_bevel_prepare / armor_layer_plate_prepare 的语义边界
只做 modifier-based preview
不做真实 mesh inset
不做 boolean
不重构参数系统
```

### Step DOL-9：sensor_lens_prepare 可行性评估

目标：评估传感器/镜头类 operation 是否能在不引入对象/材质系统重构的情况下做出有价值的 preparation version。

### Step AO-4：armor_edge_lip_prepare

状态：已完成。

目标：实现装甲边缘唇边 / 包边 preparation operation。

策略：

```text
复用 bevel / solidify helper
不做复杂 mesh 包边
不创建新对象
不重构参数系统
```

### Step DOL-10：Composite Operation 需求回收

目标：在基础 operation 更丰富之后，再基于真实设计指令回收组合需求。

原则：

```text
只记录真实高频组合
不先做抽象 sequence 架构
如果需要 sequence，后续只做服务明确组合场景的最小 Planning sequence
```

### Step AO-5：Composite Pattern 候选表

状态：下一步。

目标：当 10 个 atomic operation 稳定后，基于它们整理 composite patterns。

注意：

```text
不是实现 sequence
只是列出 RG 胸甲、重甲腿、高机动背包等组合套路
```

## 10. 优先级原则

新增 operation 的优先级按以下顺序判断：

```text
1. 是否是高达/机甲设计师高频动作
2. 是否能被很多用户指令复用
3. 是否能和已有 operation 组合
4. 是否能在当前架构内实现
5. 是否非破坏、低风险
6. 是否能形成清晰的设计语义
```

不优先做：

```text
非常炫但不常用的操作
需要大规模框架重构的操作
需要复杂 mesh edit 才有意义的操作
一次性脚本式操作
无法稳定复用的操作
```

## 11. 后置 Backlog

这些事情重要，但不属于当前 operation 扩展主线：

```text
parameter schema boolean/integer/minimum/maximum
scale-aware parameter normalization
OperationSpec capability metadata 扩展
Safety policy 分级和 capability gating
OperationOutcome 泛化
通用 operation sequence 架构
真实 Blender smoke operation profile map
full natural-language-to-Blender smoke
```

处理原则：当某个真实 design operation 明确需要它们时，再最小化引入。

## 12. 立即下一步

下一步建议直接做：

```text
Step AO-5: Composite Pattern 候选表
```

原因：

```text
Atomic Operation 扩展需求分析已经完成
Atomic Operation 开发计划已经收敛出当前阶段 8-10 个目标 operation
当前阶段 10 个 Atomic Operations 已经收敛完成
需要开始整理常见设计组合套路
只做候选表，不实现 sequence
为后续是否做最小 Planning sequence 提供依据
继续丰富基础 operation library，而不是过早进入 Composite/sequence
```

实现时只做 operation 扩展，不做参数系统和框架层优化。
