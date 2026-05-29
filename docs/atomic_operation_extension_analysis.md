# Atomic Operation 扩展需求分析

## 0. 总结

本分析的开发执行计划见：[Atomic Operation 开发计划书](atomic_operation_development_plan.md)。该计划采用最新收敛版 Atomic Operation List，将当前阶段目标控制在 8-10 个边界清晰、可复用、可组合的基础 operation。

当前 Designer Operation Library 已经完成第一批 modifier-only 操作：

```text
edge_soften
weighted_normal_finish
solidify_thickness_preview
panel_line_bevel_prepare
armor_layer_plate_prepare
vent_slot_prepare
```

下一步不应直接进入 Composite Operation，也不应继续凭直觉新增 operation。Composite 需求依赖真实设计工作流、设计师痛点和高频复杂指令；在这些资料不足时，先做组合需求回收容易变成拍脑袋的“设计包”。

因此下一阶段应先做 Atomic Operation 扩展需求分析：研究哪些基础设计动作值得封装成 operation，哪些可以暂时不封装，哪些可以直接复用 Blender/Core API，哪些必须等未来能力更成熟后再做。

本分析的目标是为后续 operation 扩展提供依据，而不是新增框架层或改变现有 Agent/Planning/Runtime/Domain/Core 主链。

## 1. 分析目标

Atomic Operation 在本文中指：

```text
最小、常用、可复用、可组合的基础设计操作。
```

它不是新的架构层，不取代 Agent Layer 或 Planning Layer，也不引入新的 parser。它只是 operation library 中最适合优先封装的基础能力单位。

本阶段要回答的问题：

```text
哪些设计师基础动作最常用？
哪些动作对高达/机甲细节设计商业价值最高？
哪些动作可以在现有架构里低风险实现？
哪些动作需要 Blender 直接接口但可以通过 Core API 封装？
哪些动作暂时不该做，因为需要对象创建、mesh edit、boolean 或 sequence？
下一批 operation 的优先级是什么？
```

## 2. 分析原则

### 2.1 从设计动作出发，不从 Blender API 出发

不应该因为 Blender 有某个接口就封装它。operation 必须对应真实设计动作。

例如：

```text
add_bevel_modifier 是 Blender/Core 能力
panel_line_bevel_prepare 是设计动作
```

我们封装的是后者。

### 2.2 先做高频、低风险、可组合动作

优先级高的 operation 应同时满足：

```text
设计师常用
用户容易用自然语言表达
能复用在多个部位
能和已有 operation 组合
当前架构能自然支持
非破坏或 preview 优先
```

### 2.3 暂缓需要重型能力的动作

以下类型暂时不优先实现：

```text
需要真实 boolean cut
需要直接编辑 mesh 顶点/面
需要新增复杂对象层级
需要材质系统支持
需要批量对象同步
需要通用 operation sequence
```

这些不是不重要，而是应等 operation library 和真实需求更成熟后再做。

## 3. 已有 Operation 能力基线

| Operation | 设计动作 | Core 实现 | 当前价值 |
| --- | --- | --- | --- |
| `edge_soften` | 边缘柔化/硬表面收口 | BEVEL modifier | 通用收尾动作 |
| `weighted_normal_finish` | 硬表面高光/法线收尾 | WEIGHTED_NORMAL modifier | 视觉质量提升 |
| `solidify_thickness_preview` | 装甲厚度感 preview | SOLIDIFY modifier | 重甲/实体感 |
| `panel_line_bevel_prepare` | 面板线/分件线 preparation | BEVEL modifier | 分件感基础 |
| `armor_layer_plate_prepare` | 装甲分层/叠甲 preview | SOLIDIFY modifier | 层次感基础 |
| `vent_slot_prepare` | 散热口/格栅 preparation | BEVEL modifier | 功能暗示基础 |

这些 operation 的共同特点：

```text
modifier-only
非破坏
不创建新对象
不应用 mesh data
可通过现有 Runtime 保存 output .blend copy
```

## 4. 候选 Atomic Operation 池

### 4.1 Surface / Panel 类

| 候选 | 设计价值 | 当前可实现性 | 建议 |
| --- | --- | --- | --- |
| `surface_inset_prepare` | 凹面/内嵌面准备，支撑刻线和装甲层次 | 中等，可用 bevel/solidify preview 近似 | 可做，但语义容易和 panel line/armor layer 重叠 |
| `parting_line_prepare` | 分件线和装甲分割 | 高，当前 `panel_line_bevel_prepare` 已部分覆盖 | 暂不单独做，等 panel line 不够用再拆 |
| `groove_cut_preview` | 刻槽/凹槽 preview | 高，但真实 cut 需要更强 mesh/boolean 能力 | 暂缓 |
| `surface_damage_prepare` | 战损划痕/缺口 preview | 中高，但真实 damage 需要 mesh edit 或纹理系统 | 暂缓 |

判断：Surface / Panel 类已有基础覆盖，短期不必继续堆相近 operation。

### 4.2 Armor / Form 类

| 候选 | 设计价值 | 当前可实现性 | 建议 |
| --- | --- | --- | --- |
| `plate_offset_prepare` | 外甲错层、板件抬升/偏移 preview | 中等，当前 `armor_layer_plate_prepare` 已覆盖一部分 | 暂缓，避免重复 |
| `armor_edge_lip_prepare` | 装甲边缘唇边/包边 | 高，可用 bevel/solidify 近似 | 可作为后续候选 |
| `thickness_balance_preview` | 多部位厚度一致性 | 高，但需要批量/scale-aware 能力 | 暂缓 |
| `silhouette_guard_marker` | 轮廓保护标记 | 中等，更像规划/约束，不是几何 operation | 不做 operation |

判断：Armor 类当前已有 `solidify_thickness_preview` 和 `armor_layer_plate_prepare`，下一步不急于继续扩。

### 4.3 Functional Detail 类

| 候选 | 设计价值 | 当前可实现性 | 建议 |
| --- | --- | --- | --- |
| `thruster_nozzle_prepare` | 推进器/喷口基础准备 | 高，但真实喷口通常需要新增对象 | 建议优先做 preview 版 |
| `hardpoint_socket_prepare` | 武器挂点/接口 | 高，可先做 socket marker/preparation | 建议优先级第二 |
| `sensor_lens_prepare` | 传感器/镜头 | 高，但真实镜头需要对象/材质 | 建议后置到第二批 |
| `cable_curve_prepare` | 管线/线缆路径准备 | 高，但需要 curve/object 创建 | 暂缓到对象创建能力更明确后 |
| `hydraulic_rod_prepare` | 液压杆/活塞 | 中高，但需要 cylinder/object 创建 | 暂缓 |

判断：Functional Detail 类是下一阶段最值得扩展的方向，因为它补足了当前 operation library 的功能暗示能力。

### 4.4 Finish / Cleanup 类

| 候选 | 设计价值 | 当前可实现性 | 建议 |
| --- | --- | --- | --- |
| `hard_surface_finish` | 综合收尾，高光/边缘一致性 | 已由 `edge_soften` + `weighted_normal_finish` 覆盖 | 不单独做 |
| `modifier_cleanup_prepare` | 替换/清理同名 AI modifier | Core 已有替换逻辑 | 不作为用户 operation |
| `style_consistency_prepare` | 统一风格/线宽/密度 | 需要批量/sequence/parameter policy | 暂缓 |

判断：Finish 类当前够用，不是下一批重点。

## 5. 下一批推荐优先级

### Priority 1: `thruster_nozzle_prepare`

理由：

```text
推进器/喷口是高达和机甲模型最高频功能细节之一。
用户自然语言表达非常稳定：加喷口、加推进器、做高机动细节。
它能服务背包、腿部、小臂、肩部等多个部位。
它与高机动风格、高密度机械细节高度相关。
```

当前最小实现版本：

```text
不创建真实 nozzle geometry
不做 cylinder/cone mesh
先做 modifier-based preparation 或 named detail marker
沿用当前 OperationSpec -> Domain -> Core 方式
必要时先使用 BEVEL modifier 表达喷口边缘准备
```

风险：

```text
如果语义太接近 vent_slot_prepare，需要明确区分：vent 是散热/格栅，thruster 是推进/喷口。
真实 nozzle geometry 后续会需要对象创建能力。
```

### Priority 2: `hardpoint_socket_prepare`

理由：

```text
武器挂点/接口是模型玩法和装备扩展的核心设计点。
用户表达稳定：加武器挂点、加接口、加连接点。
可以服务肩部、背包、手臂、腰部、腿部。
```

当前最小实现版本：

```text
先做 socket preparation，不创建复杂连接件。
可用 bevel/solidify preview 表达接口区域准备。
```

### Priority 3: `sensor_lens_prepare`

理由：

```text
传感器/镜头是头部、胸部、肩部、武器上的常见细节。
商业表现力强，但真实 lens 通常涉及对象和材质。
```

当前建议：

```text
暂不立即实现，等对象/材质策略更明确。
```

### Priority 4: `cable_curve_prepare`

理由：

```text
管线/线缆是机械细节高频元素。
但真实实现通常需要 curve 创建和路径控制。
```

当前建议：

```text
暂缓到 Core API 对 curve/object 创建有明确边界之后。
```

## 6. 不建议立即封装的操作

### 6.1 与已有 operation 语义重叠过高

```text
parting_line_prepare
plate_offset_prepare
hard_surface_finish
```

原因：当前已有 operation 可以覆盖大部分短期需求，继续拆会让 selector 选择变模糊。

### 6.2 需要重型几何能力

```text
groove_cut_preview
boolean_panel_cut
real_vent_cut
real_thruster_nozzle_create
hydraulic_rod_create
cable_curve_create
```

原因：这些最终有价值，但现在实现会拉动 Core API、Outcome、Safety 和可能的对象创建策略。

### 6.3 更像约束或规划策略，不像 operation

```text
silhouette_guard_marker
style_consistency_prepare
symmetry_policy_prepare
```

原因：这些更应该进入 Planning constraints 或未来 sequence/style policy，而不是 Domain operation。

## 7. Blender/Core API 可直接复用判断

| Blender/Core 能力 | 是否直接封装成 operation | 原因 |
| --- | --- | --- |
| BEVEL modifier | 否，需包装成设计语义 operation | 用户不会说“加 BEVEL”，会说分件线/边缘/喷口边缘 |
| SOLIDIFY modifier | 否，需包装成厚度/装甲层/接口语义 | 同一 Core helper 可服务多个设计动作 |
| WEIGHTED_NORMAL modifier | 已封装为 `weighted_normal_finish` | 设计语义明确 |
| Boolean cut | 暂不封装 | 当前风险高，后续再设计 |
| Mesh edit | 暂不封装 | 需要更强 Safety/Outcome 约束 |
| Curve create | 暂不封装 | 需要对象创建边界 |
| Material create | 暂不封装 | 当前 operation library 主线是几何/结构细节 |

原则：

```text
Blender API 是实现手段，不是用户级 operation。
只有当它能稳定映射到设计师动作时，才封装成 operation。
```

## 8. 建议路线调整

将原计划的 DOL-6 从 Composite Operation 需求回收改为：

```text
Step DOL-6: Atomic Operation Extension Analysis
```

然后继续：

```text
Step DOL-7: thruster_nozzle_prepare [done]
Step DOL-8: hardpoint_socket_prepare [done]
Step AO-3: surface_inset_prepare [done]
Step AO-4: armor_edge_lip_prepare [done]
Step AO-5: Composite Pattern Candidate Table [next]
Step DOL-9: sensor_lens_prepare feasibility review
Step DOL-10: Composite Operation demand review
```

Composite 回收不取消，只后移。它应该在基础 operation 足够丰富、且有真实用户组合需求之后再做。

## 9. 立即下一步

建议下一步做：

```text
Step AO-5: Composite Pattern 候选表
```

边界：

```text
只整理候选表
不实现 sequence
不改 TaskObject schema
不做 Runtime/Planning 架构改造
```

这样可以继续丰富基础 operation library，同时保持实现风险可控。
