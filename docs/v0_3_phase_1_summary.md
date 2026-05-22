# V0.3 Phase 1 收口记录

## 1. 阶段结论

V0.3 Phase 1 已完成。当前阶段目标是把 V0.2 的 OperationPlan V2 转换成后续执行层可消费的 Execution Blueprint，并保持该能力独立于 V0.2 主 CLI 链路。

当前完成状态：

- Execution Blueprint 设计计划已完成。
- Execution Blueprint 字段契约已确认。
- 独立规则型转换器已实现。
- V0.3 LLM 候选 prompt 草案已保留。
- V0.3 测试已新增并通过。
- V0.2 主流程未被破坏。

## 2. 已完成产物

- `docs/v0_3_execution_blueprint_plan.md`
- `3d_agent/agent/execution_blueprint.py`
- `3d_agent/prompts/v0_3_execution_blueprint_prompt_draft.txt`
- `tests/test_v0_3_execution_blueprint.py`

## 3. 当前能力边界

当前 V0.3 能力可以独立完成：

```text
OperationPlan V2 -> Execution Blueprint
```

Phase 1 时普通 CLI 仍保持 V0.2 输出：

```text
用户输入 -> OperationPlan V2 -> risk/formatter -> CLI 输出
```

Phase 1 未默认接入：

```text
用户输入 -> OperationPlan V2 -> Execution Blueprint -> CLI 输出
```

这是刻意设计，不是遗漏。原因是先保护 V0.2 已稳定的命令行输出，避免用户每次运行时突然多出执行层蓝图。

## 4. 验证结果

最近一次全量测试命令：

```powershell
python -m unittest discover -s tests -v
```

结果：

```text
Ran 14 tests

OK
```

测试覆盖：

- V0.2 OperationPlan V2 主链路。
- V0.3 Execution Blueprint 字段契约。
- 典型 operation 到 tool family 的映射。
- V0.3 prompt 草案渲染。
- `run_agent()` 默认不输出 Execution Blueprint。

## 5. 故意未做

Phase 1 故意未做以下内容：

- 不默认接入主 CLI。
- 不执行 Blender Python。
- 不读取真实 mesh。
- 不生成真实几何。
- 不让 LLM prompt 成为验收路径。
- 不修改 V0.2 OperationPlan V2 字段。

## 6. 下一步实现选择

V0.3 Phase 2 最终采用默认接入方式。由于后续马上进入 V0.4，默认输出直接升级为 V0.3 增强蓝图，不再保留 V0.2 轻量默认模式。

当前命令形式：

```powershell
python 3d_agent/main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。"
```

预期行为：

- `model_edit` 默认输出 OperationPlan V2 顶层字段，并额外包含 `execution_blueprint`。
- `inspect_context` 和 `explain_capability` 不附加 `execution_blueprint`。
- 该接入仍不执行 Blender，不读取 mesh，只输出执行准备蓝图。

当前实现状态：已完成。

## 8. Phase 2 接入结果

Phase 2 已将 `execution_blueprint` 接入默认 `model_edit` 输出。非模型编辑命令不会附加 `execution_blueprint`。

## 7. 收口判断

V0.3 Phase 1 可以作为稳定基线。V0.3 Phase 2 已把默认输出升级为 V0.3 增强蓝图，为 V0.4 执行层开发提供默认输入。