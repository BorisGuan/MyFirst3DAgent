# V0.2 使用说明

本文档说明如何使用机甲模型细节设计 Agent V0.2。V0.2 的目标是把一句自然语言设计需求转换成机器可读的机甲设计操作蓝图，并同时输出设计师可读摘要和基础风险提示。

V0.2 不会生成真实 3D 模型，不会读取 mesh，也不会执行 Blender。它输出的是后续手工建模、设计审查或自动化建模层可以继续使用的中间蓝图。

当前默认 CLI 已升级到 V0.3 增强输出：OperationPlan V2 顶层字段仍然保留，同时会额外包含 `execution_blueprint`，用于后续 V0.4 执行层开发。

## 1. 运行方式

在项目根目录运行：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。"
```

命令行会显示三类内容：

- `user_message`：一句很短的状态说明。
- `designer_brief`：给设计师看的执行摘要。
- JSON：完整 OperationPlan V2 操作蓝图，以及默认附加的 V0.3 `execution_blueprint`。

如果要保存完整 JSON：

```powershell
python 3d_agent/main.py "给盾牌加少量战损和旧化，不要太脏。" > shield_plan.json
```

摘要会显示在终端里，保存到文件中的内容仍是干净 JSON。

## 2. 示例输入

### 2.1 胸甲分件线

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。"
```

预期重点：

- `target_part`: `chest_armor`
- `operation`: `add_parting_lines`
- `detail_type`: `parting_lines`
- `style`: `sharp_mechanical`
- `scale`: `1/144`
- 包含至少 1 条风险提示

### 2.2 背包推进器

```powershell
python 3d_agent/main.py "把背包的推进器做得更高机动一点，加喷口和机械细节。"
```

预期重点：

- `target_part`: `backpack`
- `detail_type`: `thrusters`
- `style`: `high_mobility`
- `steps` 中包含喷口或推进器相关步骤

### 2.3 V 字天线风险

```powershell
python 3d_agent/main.py "给 V 字天线加大量刻线，比例 1/144。"
```

预期重点：

- `target_part`: `antenna`
- `density`: `high`
- `scale`: `1/144`
- `risk_notes` 包含打印清晰度或结构强度风险

### 2.4 腿部对称机械细节

```powershell
python 3d_agent/main.py "给两条腿加同样的管线和液压杆，密度中等。"
```

预期重点：

- `target_part`: `leg`
- `detail_type`: `pipes` 或 `hydraulic_rods`
- `symmetry`: `group_sync` 或 `left_right_mirror`
- `risk_notes` 包含关节活动或连接端点相关提示

### 2.5 盾牌战损

```powershell
python 3d_agent/main.py "给盾牌加少量战损和旧化，不要太脏。"
```

预期重点：

- `target_part`: `shield`
- `operation`: `add_surface_damage`
- `density`: `low`
- `designer_brief` 强调克制处理

## 3. 输出示例

输入：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。"
```

终端摘要示例：

```text
已生成 chest_armor 操作蓝图：添加中等密度分件线，包含 1 条风险提示。
建议在 chest_armor 上添加中等密度锐利机械分件线，按 1/144 比例控制细节，需注意 1/144 比例下刻线或分件线需要控制宽度和间距。
```

完整 JSON 示例：

```json
{
	"command_type": "model_edit",
	"confidence": "medium",
	"target_part": "chest_armor",
	"operation": "add_parting_lines",
	"detail_type": "parting_lines",
	"style": "sharp_mechanical",
	"density": "medium",
	"symmetry": "single_target",
	"scale": "1/144",
	"placement_zones": [
		"upper_chest_plate",
		"around_cockpit_hatch"
	],
	"constraints": [
		"keep_details_printable_at_1_144",
		"keep_line_density_readable"
	],
	"steps": [
		"确认 chest_armor 的主要可见面和边界。",
		"以锐利机械风格添加中等密度分件线。",
		"保留原有轮廓和关键结构，不穿过关节或连接区域。",
		"按 1/144 比例控制细节宽度和间距，避免过密。"
	],
	"risk_notes": [
		"1/144 比例下刻线或分件线需要控制宽度和间距。"
	],
	"reasoning": "用户希望添加适量锐利机械分件线，并考虑 1/144 比例。",
	"designer_brief": "建议在 chest_armor 上添加中等密度锐利机械分件线，按 1/144 比例控制细节，需注意 1/144 比例下刻线或分件线需要控制宽度和间距。",
	"user_message": "已生成 chest_armor 操作蓝图：添加中等密度分件线，包含 1 条风险提示。"
}
```

## 4. OperationPlan V2 字段说明

| 字段 | 含义 |
|---|---|
| `command_type` | 命令类型，模型编辑请求为 `model_edit` |
| `confidence` | 命令分类置信度 |
| `target_part` | 标准目标部件名，来自模型上下文 |
| `operation` | 蓝图操作类型，例如 `add_parting_lines` |
| `detail_type` | 细节对象类型，例如 `parting_lines` |
| `style` | 设计风格，例如 `sharp_mechanical` |
| `density` | 细节密度，支持 `low`、`medium`、`high` |
| `symmetry` | 对称或成组策略 |
| `scale` | 模型比例，例如 `1/144` |
| `placement_zones` | 建议操作区域标签 |
| `constraints` | 制作、比例、活动或装配约束 |
| `steps` | 面向执行层和设计师的操作步骤 |
| `risk_notes` | 基础可制作性风险提示 |
| `reasoning` | 解析依据摘要 |
| `designer_brief` | 给用户看的设计师摘要 |
| `user_message` | 简短状态说明 |

执行层或后续自动化工具应优先读取结构化字段，不应只依赖 `designer_brief`。

## 5. 其他命令

查询当前模型上下文：

```powershell
python 3d_agent/main.py "现在有哪些部件？"
```

查看当前能力说明：

```powershell
python 3d_agent/main.py "你能做什么？"
```

## 6. 已知限制

- 不读取 `.obj`、`.fbx`、`.glb`、`.blend` 文件。
- 不分析真实 mesh、厚度、布线、碰撞或装配公差。
- 不生成真实刻线、喷口、管线或战损几何。
- 不执行 Blender、Fusion、ZBrush 或其他建模软件。
- 不做完整左右部件展开，V0.2 只输出 `symmetry` 策略。
- 风险提示是保守建议，不是精确工程结论。
- 当前 mock parser 是关键词驱动，复杂长句可能需要后续 LLM 路径或 V0.3 继续增强。

## 7. 测试命令

运行 V0.2 回归测试：

```powershell
python -m unittest discover -s tests -v
```

当前测试覆盖 OperationPlan V2、planner 校验、mock parser、risk checker、formatter 和 `run_agent()` 主链路。
