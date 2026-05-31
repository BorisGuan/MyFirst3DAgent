# Atomic Operation 开发计划书

## 0. 总结

本计划基于最新整理的 Atomic Operation List，目标是把 Designer Operation Library 从“继续随意新增 operation”收敛为一套边界清晰、数量克制、可组合、可逐步增强的基础操作库。

当前阶段不做 Composite Operation，不做 sequence，不做框架重构，也不让 LLM 直接调用 Blender API。本阶段目标是把高达/机甲/硬表面设计中最常用、最小、最可复用的基础设计动作封装成受控 operation。

当前阶段原计划收敛到 10 个 Atomic Operations，现已完成 10/10。Atomic Operation Library v1 在本阶段收口。

当前已实现的 10 个 operation：

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

这 10 个 operation 覆盖四类基础设计能力：

```text
Surface / Panel: 表面结构、分件、凹凸细节载体
Form / Mass: 厚度、体块、层次、边缘结构
Functional Detail: 喷口、接口、功能性机械暗示
Finish: 硬表面高光、边缘收口、最终观感
```

核心原则：

```text
Atomic Operation 不是 Blender API wrapper。
Atomic Operation 是设计语义上的最小可复用动作。
Blender API 只能作为 Core API 实现手段，不能直接暴露给 LLM 或用户。
```

## 1. 开发边界

### 1.1 本阶段要做

```text
继续封装基础 Atomic Operations
每个 operation 对应明确设计语义
每个 operation 沿用 OperationSpec -> Planning -> Runtime -> Domain -> Core API 路径
优先 modifier-only / preview / non-destructive
保持 operation 数量克制，避免重复语义
```

### 1.2 本阶段不做

```text
不做 Composite Operation 实现
不做 operation sequence
不做对象创建体系
不做 mesh edit / boolean cut
不做材质系统
不重构 TaskObject
不重构 ParameterCompleter
不泛化 OperationOutcome
不让 LLM 直接调用 Blender API
```

### 1.3 如何判断是否值得封装

一个候选 operation 进入当前阶段，必须尽量满足：

```text
设计师会把它作为独立动作表达
它能独立产生明确的小设计价值
它能被多个部位复用
它能被未来 composite 组合复用
它能通过当前 Core API 或小型 Core helper 安全实现
它不需要重型几何能力
```

## 2. Atomic Operation 分类

## 2.1 Surface / Panel 类

Surface / Panel 类负责表面结构、分件、面板感和凹凸细节载体。

### 2.1.1 `panel_line_bevel_prepare`

状态：已完成。

设计语义：

```text
加刻线
加面板线
加分件线
让装甲分割更明显
```

为什么它是 atomic：

```text
只负责 panel line / parting line 的 bevel-based preparation
不是完整分件设计
可复用于胸甲、腿甲、肩甲、背包等多个部位
```

当前实现：

```text
Core: add_bevel_modifier
Domain: panel_line_bevel_prepare
Blender: BEVEL modifier
```

边界：

```text
不做真实 mesh 刻槽
不做 boolean cut
不 apply modifier
不创建对象
```

### 2.1.2 `surface_inset_prepare`

状态：已完成。

设计语义：

```text
做一块内嵌面
某块装甲表面压进去一点
给表面增加凹面层次
```

为什么值得做：

```text
panel_line 是线性分割感
surface_inset 是面层级变化
它能成为 panel line 与 armor layer 之间的过渡能力
```

当前最小实现方向：

```text
Core: add_solidify_modifier
Domain: surface_inset_prepare
Blender: SOLIDIFY modifier
```

风险：

```text
容易和 panel_line_bevel_prepare、armor_layer_plate_prepare 语义重叠
实现前需要明确它只表达 inset-like surface preparation
```

### 2.1.3 `vent_slot_prepare`

状态：已完成。

设计语义：

```text
加散热口
加格栅
做进气口
增加机械功能细节
```

为什么它是 atomic：

```text
只表达 vent / grille preparation
当前先作为表面功能细节入口
不承担完整散热结构设计
```

当前实现：

```text
Core: add_bevel_modifier
Domain: vent_slot_prepare
Blender: BEVEL modifier
```

边界：

```text
不做真实 cut
不做 boolean
不创建格栅对象
```

## 2.2 Form / Mass 类

Form / Mass 类负责厚度、体块、层次、边缘结构。

### 2.2.1 `solidify_thickness_preview`

状态：已完成。

设计语义：

```text
让装甲更厚一点
增加厚度感
做重甲感
外甲不要像纸片
```

为什么它是 atomic：

```text
只表达厚度 preview
不是完整重甲风格设计
复用性极高
```

当前实现：

```text
Core: add_solidify_modifier
Domain: solidify_thickness_preview
Blender: SOLIDIFY modifier
```

边界：

```text
不 apply modifier
不做 scale-aware 厚度策略
不做批量厚度平衡
```

### 2.2.2 `armor_layer_plate_prepare`

状态：已完成，但必须克制使用。

设计语义：

```text
强化装甲层次
加叠甲
胸甲更有外甲结构
腿甲更有层次
```

工程判断：

```text
可以保留，但必须明确它只是 plate/layer preview
不是“装甲层次设计总入口”
```

当前实现：

```text
Core: add_solidify_modifier
Domain: armor_layer_plate_prepare
Blender: SOLIDIFY modifier
```

边界：

```text
不拆真实外甲
不创建新 armor plate 对象
不做复杂轮廓控制
不做 mesh edit
```

### 2.2.3 `armor_edge_lip_prepare`

状态：已完成。

设计语义：

```text
装甲边缘有包边感
边缘更有机械板件的唇边
边缘不要只是平切
```

为什么值得做：

```text
比 armor_layer_plate_prepare 更纯
表达的是边缘结构，不是整体装甲层次
很适合机甲/硬表面外甲设计
```

当前最小实现方向：

```text
Core: add_bevel_modifier
Domain: armor_edge_lip_prepare
Blender: BEVEL modifier
```

边界：

```text
不做复杂 mesh 包边
不创建新对象
不 apply modifier
```

## 2.3 Functional Detail 类

Functional Detail 类负责机械功能暗示。当前库已有表面、厚度、收尾能力，下一批最应该补的是功能细节。

### 2.3.1 `thruster_nozzle_prepare`

状态：已完成。

设计语义：

```text
加喷口
加推进器
做高机动细节
背包 / 腿部 / 小臂增加喷嘴
```

为什么优先：

```text
用户语言稳定
机甲识别度高
可服务背包、腿部、小臂、肩部
适合未来 high_mobility composite
```

当前最小实现方向：

```text
Core: add_bevel_modifier
Domain: thruster_nozzle_prepare
Blender: BEVEL modifier
```

需要区分：

```text
vent_slot_prepare = 散热 / 格栅
thruster_nozzle_prepare = 推进 / 喷口
```

### 2.3.2 `hardpoint_socket_prepare`

状态：已完成。

设计语义：

```text
加武器挂点
加接口
加连接位
加可扩展装置安装点
```

为什么值得做：

```text
强化玩法感和装备扩展感
肩部、背包、手臂、腰部、腿部都能复用
用户表达稳定
```

当前最小实现方向：

```text
Core: add_bevel_modifier
Domain: hardpoint_socket_prepare
Blender: BEVEL modifier
```

边界：

```text
不做真实 mechanical connector
不创建独立 socket 对象
不做 boolean 孔洞
```

### 2.3.3 `sensor_lens_prepare`

状态：候选后置。

设计语义：

```text
加传感器
加镜头
头部 / 胸部 / 武器增加光学细节
```

价值：

```text
商业表现力强
能明显增强机械设备感
```

暂缓原因：

```text
真实 lens 通常涉及对象创建和材质
当前阶段不做对象/材质系统重构
```

### 2.3.4 `cable_curve_prepare`

状态：暂缓。

设计语义：

```text
加线缆
加机械管线
预留走线结构
```

暂缓原因：

```text
真实实现通常需要 curve 创建和路径控制
当前 Core API 对 curve/object 创建边界还未明确
```

## 2.4 Finish 类

Finish 类当前不要继续扩太多。

### 2.4.1 `edge_soften`

状态：已完成，核心收尾 atomic。

设计语义：

```text
边缘柔一点
边缘不要太生硬
做硬表面细节收口
```

当前实现：

```text
Core: add_bevel_modifier
Domain: edge_soften
Blender: BEVEL modifier
```

### 2.4.2 `weighted_normal_finish`

状态：已完成，核心 finish atomic。

设计语义：

```text
优化高光
表面更干净
改善阴影与法线质量
```

当前实现：

```text
Core: add_weighted_normal_modifier
Domain: weighted_normal_finish
Blender: WEIGHTED_NORMAL modifier
```

不建议新增：

```text
hard_surface_finish
```

原因：

```text
过于宽泛
已由 edge_soften + weighted_normal_finish 覆盖
容易变成 composite 或 style preset，不适合作为 atomic operation
```

## 3. 当前阶段最终 Atomic Operation 总表

## 3.1 已实现 / 保留

```text
Surface / Panel
- panel_line_bevel_prepare
- vent_slot_prepare

Form / Mass
- solidify_thickness_preview
- armor_layer_plate_prepare

Finish
- edge_soften
- weighted_normal_finish
```

## 3.2 下一批新增

```text
Functional Detail
- thruster_nozzle_prepare
- hardpoint_socket_prepare

Surface / Panel
- surface_inset_prepare

Form / Mass
- armor_edge_lip_prepare
```

推荐实现顺序：

```text
1. thruster_nozzle_prepare
2. hardpoint_socket_prepare
3. surface_inset_prepare
4. armor_edge_lip_prepare
```

理由：

```text
前两个补功能细节能力缺口
后两个补表面/体块语言丰富度
避免继续在已有 Surface / Armor 语义上重复打转
```

## 3.3 候选后置

```text
sensor_lens_prepare
cable_curve_prepare
hydraulic_rod_prepare
groove_cut_preview
boolean_panel_cut
real_vent_cut
real_thruster_nozzle_create
```

后置原因：

```text
对象创建
curve
mesh edit
boolean
材质
更复杂 Outcome / Safety 边界
```

## 4. 推荐开发路线

## Step AO-1：`thruster_nozzle_prepare`

状态：已完成。

目标：实现推进器/喷口 preparation operation。

范围：

```text
OperationSpec
Domain thruster_nozzle_prepare
Runtime handler registration
必要 focused tests
```

实现边界：

```text
不创建真实 nozzle object
不做 mesh edit / boolean
不做 sequence
不重构参数系统
优先复用现有 Core helper
```

## Step AO-2：`hardpoint_socket_prepare`

状态：已完成。

目标：实现武器挂点/接口 preparation operation。

范围：

```text
OperationSpec
Domain hardpoint_socket_prepare
Runtime handler registration
必要 focused tests
```

实现边界：

```text
不创建复杂连接件
不做 boolean 孔洞
不做对象创建系统
```

## Step AO-3：`surface_inset_prepare`

状态：已完成。

目标：实现内嵌面 / 凹面 preparation operation。

范围：

```text
先评估是否能与 panel_line_bevel_prepare / armor_layer_plate_prepare 明确区分
若边界清晰，再实现 modifier-based preview
```

## Step AO-4：`armor_edge_lip_prepare`

状态：已完成。

目标：实现装甲边缘唇边 / 包边 preparation operation。

范围：

```text
复用 bevel / solidify helper
不做复杂 mesh 包边
不创建新对象
```

## Step AO-5：Composite Pattern 候选表

状态：暂缓。

目标：当 8-10 个 atomic operation 稳定后，再基于它们整理 composite patterns。

注意：

```text
不是实现 sequence
只是列出 RG 胸甲、重甲腿、高机动背包等组合套路
```

## 5. 不做事项

当前阶段明确不做：

```text
不继续无边界新增 operation
不暴露 Blender API 给 LLM
不做真实 object creation
不做真实 mesh cut / boolean
不做材质/镜头系统
不做通用 operation sequence
不做 composite implementation
```

## 6. 结论

当前最稳的策略不是追求更多 operation，而是收敛出刚刚好的 8-10 个 atomic operation。

这批 operation 应该满足：

```text
边界清晰
互不重复
覆盖高达/机甲高频设计语言
能通过现有架构安全执行
后续能自然组合成 composite patterns
```

当前阶段收口状态：

```text
Atomic Operation Library v1: 10/10 completed
Composite Pattern: 暂缓
Operation sequence: 暂缓
```

建议下一阶段先做架构/性能/准确性分析：

```text
Step NEXT-1: Operation Parameter Accuracy Analysis
```

说明：当前 Atomic Operation Library v1 已经收敛完成，Composite Pattern 和 sequence 暂缓。下一阶段先从全局 Agent 架构出发，分析参数准确性、operation 选择准确性、目标绑定准确性、执行可靠性和真实 Blender 验证，再决定是否进入组合能力。
