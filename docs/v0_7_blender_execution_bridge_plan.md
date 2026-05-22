# V0.7 Blender 执行桥接与安全运行计划

## 1. 阶段定位

V0.7 承接 V0.6 的 `Geometry Preview Plan`、`Safe Preview Session` 和 `Blender Preview Script Draft`，目标是让 Agent 第一次把脚本真正交给 Blender 执行，并拿回可验证的执行报告。

产品路径：

```text
V0.2：自然语言 -> OperationPlan V2 操作蓝图
V0.3：OperationPlan V2 -> Execution Blueprint 执行蓝图
V0.4：Execution Blueprint -> Execution Package 半自动执行包
V0.5：真实模型上下文读取 -> 部件对象绑定 -> 执行包阻塞项复核
V0.6：绑定对象 -> 局部几何预览计划 -> 安全预览脚本草案 -> 回滚契约
V0.7：Blender 执行桥接 -> 后台运行预览脚本 -> 执行报告 -> 可选保存副本
```

V0.7 的核心不是“修改 mesh”，而是回答：

```text
Agent 能否安全、可验证地调用本机 Blender，执行 V0.6 preview-only 脚本，并确认没有修改用户目标 mesh 或覆盖原文件？
```

因此 V0.7 第一版仍是 preview-only 执行桥接，不进入真实刻线、布尔、挤出或 modifier apply。

## 2. V0.7 目标

V0.7 完成后，系统应该能够：

- 检测本机 Blender 可执行文件路径和版本。
- 接收 V0.6 生成的 `blender_preview_script_draft`。
- 将脚本写入临时或输出目录。
- 使用 Blender background 模式打开指定 `.blend` 文件并执行脚本。
- 收集 Blender 进程退出码、stdout、stderr 和报告文件。
- 输出机器可读的 `Blender Execution Report`。
- 可选将预览结果保存为新的 `.blend` 副本。
- 明确证明原始 `.blend` 未被覆盖。
- 保持 bound mesh 不被脚本修改。

V0.7 的直接价值是把 V0.6 从“脚本草案”推进到“可在本机 Blender 中真实运行并可验收的 preview-only 执行”。

## 3. 不做范围

V0.7 第一版明确不做以下内容：

- 不执行真实 mesh 顶点、边、面修改。
- 不执行真实布尔切割、刻线、挤出或重拓扑。
- 不 apply modifier。
- 不删除用户已有对象。
- 不覆盖保存原始 `.blend` 文件。
- 不导出最终生产模型。
- 不把 generated preview object 当成最终几何。
- 不在未确认 Blender 路径和测试文件的情况下执行后台命令。
- 不依赖网上复杂模型作为自动化测试前提。

真实几何修改应放到 V0.8 或更后阶段。V0.7 只验证“执行桥接、安全运行和报告闭环”。

## 4. 用户需要提前准备什么

你当前还没有安装 Blender，因此 V0.7 计划中需要把 Blender 相关执行做成可选能力。未安装 Blender 时，代码仍可生成执行请求、脚本文件和待执行命令，但不会尝试真实运行。

### 4.1 必需准备

进入真实执行前，需要准备：

- 本机安装 Blender。
- 确认 Blender 命令行可运行，或提供完整 `blender.exe` 路径。
- 准备一个测试 `.blend` 文件副本。
- 测试 `.blend` 内对象名应和 Scene Manifest 样例一致。

建议对象名：

```text
ChestArmor_Upper_01
Backpack_Block_01
LeftLeg_Armor_01
RightLeg_Armor_01
Shield_Main_01
Head_CameraSensor_01
```

### 4.2 推荐的测试文件来源

第一版最推荐自己做一个极简 `.blend` 文件，不依赖网上模型：

- 用 cube 创建 `ChestArmor_Upper_01`。
- 用 cube 创建 `Backpack_Block_01`。
- 用 cube 创建 `LeftLeg_Armor_01` 和 `RightLeg_Armor_01`。
- 用小 cube 或 sphere 创建 `Head_CameraSensor_01`。
- 可选创建 `Shield_Main_01`。

这个文件不需要漂亮，只需要对象名稳定、可重复测试、无版权风险。

建议文件：

```text
examples/demo_gundam_scene.blend
```

### 4.3 网上 `.blend` 文件是否可用

可以使用网上模型，但第一版不建议作为主测试依赖。原因是授权、对象命名、文件复杂度和几何结构都不可控。

如果要找公开文件，优先选择：

- Blender 官方 demo files。
- 明确 CC0 或可改编 Creative Commons 授权的 Sketchfab 模型。
- Blend Swap 上授权清楚的 `.blend` 文件。
- OpenGameArt 上授权清楚的机器人、科幻或机甲资产。
- Kenney、Quaternius 等授权友好的低模资产，导入 Blender 后保存成 `.blend`。

不要使用未经授权的商业 IP 机体模型作为样例或公开演示素材。

## 5. V0.7 执行等级

为了避免一步跳到高风险 mesh 修改，V0.7 使用分级执行模型。

```text
Level 0：只生成执行请求，不调用 Blender。
Level 1：检测 Blender 路径和版本。
Level 2：后台打开测试 .blend，执行只写 report 的脚本。
Level 3：后台执行 V0.6 preview script，创建 preview collection 和 preview objects。
Level 4：保存为新的 preview .blend 副本，不覆盖原文件。
Level 5：用户确认后的真实 mesh 修改，V0.7 不做。
```

V0.7 第一版建议实现 Level 0 到 Level 4，其中 Level 4 必须是可选开关。

## 6. 输入与输出关系

### 6.1 输入一：V0.6 CLI 输出

V0.7 主要消费 V0.6 输出：

- `geometry_preview_plan`
- `safe_preview_session`
- `blender_preview_script_draft`

这些字段可通过以下命令生成：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --preview-script-draft
```

### 6.2 输入二：Blender 文件路径

V0.7 需要用户提供测试 `.blend` 文件：

```text
examples/demo_gundam_scene.blend
```

### 6.3 输入三：Blender 可执行文件路径

可以来自：

- `blender` 命令。
- 环境变量，例如 `BLENDER_EXECUTABLE`。
- CLI 参数，例如 `--blender-executable <path>`。
- 项目配置文件。

### 6.4 输出一：Blender Execution Request

V0.7 建议新增执行请求对象，作为调用 Blender 前的机器可读契约。

字段草案：

```json
{
  "request_version": "v0_7",
  "execution_mode": "preview_only",
  "target_software": "blender",
  "blender_executable": "blender",
  "source_blend_file": "examples/demo_gundam_scene.blend",
  "script_file": "outputs/v06_preview_script.py",
  "output_report_file": "outputs/preview_execution_report.json",
  "output_blend_copy": "outputs/demo_gundam_scene.preview.blend",
  "save_copy": false,
  "allowed_operations": [],
  "forbidden_operations": [],
  "preflight_checks": []
}
```

### 6.5 输出二：Blender Execution Report

V0.7 的核心输出是执行报告。

字段草案：

```json
{
  "report_version": "v0_7",
  "execution_status": "success",
  "execution_mode": "preview_only",
  "blender_version": "",
  "source_blend_file": "examples/demo_gundam_scene.blend",
  "saved_original_file": false,
  "output_blend_copy": "",
  "created_collections": [],
  "generated_objects": [],
  "modified_bound_mesh": false,
  "script_exit_code": 0,
  "stdout_excerpt": "",
  "stderr_excerpt": "",
  "report_summary": ""
}
```

## 7. 安全策略

### 7.1 原始文件保护

V0.7 默认不保存 `.blend` 文件。如果需要保存，只能保存副本：

```text
outputs/demo_gundam_scene.preview.blend
```

禁止覆盖原始文件。

### 7.2 目标 mesh 保护

V0.7 只允许创建 generated preview objects。执行报告必须声明：

```text
modified_bound_mesh = false
```

第一版可以通过脚本安全扫描和执行报告双重确认。后续版本再增加 mesh hash 或 object data checksum。

### 7.3 进程隔离

Blender 应通过 background 模式运行：

```powershell
blender --background examples/demo_gundam_scene.blend --python outputs/v06_preview_script.py
```

命令参数必须结构化构造，不拼接成危险字符串。

### 7.4 脚本限制

执行前必须检查脚本内容不包含：

- `bpy.ops.object.delete`
- `bpy.ops.object.modifier_apply`
- `bpy.ops.mesh`
- `bpy.ops.wm.save_as_mainfile`，除非 `save_copy = true` 且路径为输出副本
- `.modifiers.new`
- boolean 相关操作

## 8. CLI 接入建议

V0.7 建议新增显式参数，不改变默认输出。

建议参数：

```text
--execute-blender-preview
--blend-file <path>
--blender-executable <path>
--save-preview-copy
--output-dir <path>
```

建议行为：

- `--execute-blender-preview` 需要 `--preview-script-draft`。
- `--execute-blender-preview` 需要 `--blend-file <path>`。
- 未提供 `--blender-executable` 时先尝试使用 `blender`。
- 未安装 Blender 或找不到路径时，输出 pending report，不视为普通单元测试失败。
- 默认不保存 `.blend` 文件。
- `--save-preview-copy` 只能保存到 output dir，不允许覆盖输入文件。

示例：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --preview-script-draft --execute-blender-preview --blend-file .\examples\demo_gundam_scene.blend --output-dir .\outputs
```

## 9. 建议模块设计

### 9.1 Blender Runtime Detector

建议模块：

```text
3d_agent/integration/blender_runtime.py
```

职责：

- 检测 Blender 可执行文件路径。
- 运行 `blender --version`。
- 返回 Blender runtime status。

核心函数建议：

```text
detect_blender_runtime(blender_executable="blender")
```

### 9.2 Blender Execution Request Builder

建议模块：

```text
3d_agent/integration/blender_execution_request.py
```

职责：

- 根据 V0.6 输出、blend path 和 output dir 生成执行请求。
- 写出 preview script 文件。
- 生成 report path 和可选 preview blend copy path。

核心函数建议：

```text
create_blender_execution_request(v06_result, blend_file, output_dir, blender_executable="blender", save_copy=False)
```

### 9.3 Blender Script Safety Scanner

建议模块：

```text
3d_agent/integration/blender_script_safety.py
```

职责：

- 在执行前扫描脚本草案。
- 阻止危险操作。
- 输出 safety scan report。

核心函数建议：

```text
scan_blender_script_safety(script_text, save_copy=False)
```

### 9.4 Blender Background Runner

建议模块：

```text
3d_agent/integration/blender_runner.py
```

职责：

- 使用 `subprocess.run` 调用 Blender background 模式。
- 捕获 exit code、stdout、stderr。
- 不用 shell 拼接命令。

核心函数建议：

```text
run_blender_preview_execution(execution_request)
```

### 9.5 Execution Report Normalizer

建议模块：

```text
3d_agent/integration/blender_execution_report.py
```

职责：

- 将 Blender 进程结果和脚本 report 合并成标准 `Blender Execution Report`。
- 标记 success、failed、pending_runtime、blocked_by_safety_scan。

核心函数建议：

```text
normalize_blender_execution_report(execution_request, process_result, script_report=None)
```

## 10. 建议开发顺序

### Step 0：V0.7 范围确认

确认 V0.7 第一版只做 Blender 执行桥接和 preview-only 安全运行，不做真实 mesh 修改。

输出：本计划确认版。

### Step 1：确认 Blender Execution Request 和 Report 字段契约

固定请求对象和报告对象字段、状态枚举、默认值和安全边界。

输出：字段契约确认表。

### Step 2：实现 Blender Runtime Detector

实现 Blender 路径和版本检测。未安装 Blender 时返回结构化 pending 状态。

输出：`detect_blender_runtime(...)`。

### Step 3：实现 Script Safety Scanner

扫描 V0.6 preview script draft，阻止危险 Blender 操作。

输出：`scan_blender_script_safety(...)`。

### Step 4：实现 Execution Request Builder

把 V0.6 输出写成脚本文件和执行请求，不真实运行 Blender。

输出：`create_blender_execution_request(...)`。

### Step 5：实现 Background Runner

在本机存在 Blender 和测试 `.blend` 时，使用 background 模式执行 preview script。

输出：`run_blender_preview_execution(...)`。

### Step 6：实现 Execution Report Normalizer

整合进程结果、脚本 report 和安全扫描结果，输出标准执行报告。

输出：`normalize_blender_execution_report(...)`。

### Step 7：CLI 可选接入

新增 `--execute-blender-preview`、`--blend-file`、`--blender-executable`、`--save-preview-copy` 和 `--output-dir`。

输出：CLI 可选真实 Blender preview 执行。

### Step 8：V0.7 验收

在有 Blender 环境时跑真实执行验收；无 Blender 环境时跑 pending runtime 和安全扫描验收。

输出：验收报告。

## 11. V0.7 验收用例

### 11.1 无 Blender 环境时返回 pending

输入：未安装 Blender 或路径不可用。

必须输出：

- runtime status 为 `not_found` 或 `pending_runtime`。
- 不尝试执行后台 Blender。
- 不影响普通单元测试。

### 11.2 脚本安全扫描通过

输入：V0.6 preview script draft。

必须输出：

- safety status 为 `passed`。
- 不包含 mesh edit、modifier apply、delete、boolean 或覆盖保存。

### 11.3 危险脚本被阻止

输入：含 `bpy.ops.object.delete` 或 `bpy.ops.object.modifier_apply` 的脚本。

必须输出：

- safety status 为 `blocked`。
- 不调用 Blender。
- 报告列出命中的危险规则。

### 11.4 Execution Request 可生成

输入：V0.6 输出、blend file path 和 output dir。

必须输出：

- script file path。
- report file path。
- 结构化 Blender command args。
- 默认 `save_copy = false`。

### 11.5 真实 Blender preview 执行成功

前提：本机安装 Blender 且存在测试 `.blend`。

必须输出：

- Blender exit code 为 `0`。
- 生成 preview report JSON。
- 报告中有 created collection 和 generated objects。
- `modified_bound_mesh = false`。
- `saved_original_file = false`。

### 11.6 保存副本不覆盖原文件

输入：启用 `--save-preview-copy`。

必须输出：

- 输出 `.preview.blend` 副本。
- 原始 `.blend` 路径不变。
- 报告中 `saved_original_file = false`。

## 12. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 用户未安装 Blender | 无法真实执行 | 返回 pending runtime，仍可测试请求生成和安全扫描 |
| 覆盖原始 `.blend` | 数据损失 | 默认不保存，保存时只允许输出副本 |
| 脚本包含危险操作 | 数据风险 | 执行前 safety scan，命中即阻止 |
| Blender 路径包含空格 | 命令失败 | 使用 subprocess args list，不拼接 shell 字符串 |
| 网上模型授权不清 | 法务和演示风险 | 第一版使用自建极简 `.blend` 测试文件 |
| 复杂模型对象命名不一致 | 绑定失败 | 要求对象名或 custom property 匹配 Scene Manifest |

## 13. V0.7 完成定义

V0.7 只有在同时满足以下条件时才算完成：

- 有 Blender Execution Request 字段契约。
- 有 Blender Execution Report 字段契约。
- 能检测 Blender runtime。
- 未安装 Blender 时能结构化返回 pending 状态。
- 能扫描并阻止危险 Blender 脚本。
- 能把 V0.6 preview script draft 写成脚本文件。
- 能生成结构化 Blender background command args。
- 有 Blender 环境时能执行 preview script 并生成执行报告。
- 默认不保存 `.blend`。
- 启用保存时只保存副本，不覆盖原文件。
- 不修改 bound mesh。
- 全量测试通过。

## 14. V0.7 之后的方向

V0.7 完成后，可以进入 V0.8：非破坏性几何预览与受控 modifier。

V0.8 才适合讨论：

- duplicate mesh 上的非破坏性 modifier。
- curve bevel 形式的刻线预览。
- shrinkwrap 或 surface anchor 读取。
- preview object 到真实辅助几何的转换。
- 用户确认后的 apply path。

真实修改原始目标 mesh 应继续后置，至少等执行桥接、备份、副本、报告和回滚策略稳定后再做。