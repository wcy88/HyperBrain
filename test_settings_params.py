"""设置对话框参数优化测试

测试：
1. Max Tokens 范围 1-262144（256K，匹配 Pydantic 验证）
2. 最大思维链长度 范围 1-20
3. 学习率 step=0.001
4. 缺省值正确（Temperature=0.7, Max Tokens=4096 等）
5. 所有参数都有 tooltip
6. API Key 占位符正确
7. config.py 缺省值与 UI 一致
8. config.py 验证规则
9. Pydantic ModelConfig 验证（models/base.py）

使用方式：py test_settings_params.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestRunner:
    def __init__(self):
        self.results = []

    def run(self, name, func):
        print(f'\n=== {name} ===')
        try:
            func()
            print(f'  PASSED')
            self.results.append((name, True, None))
        except Exception as e:
            import traceback
            print(f'  FAILED: {e}')
            traceback.print_exc()
            self.results.append((name, False, str(e)))


def test_max_tokens_range():
    """测试 Max Tokens 范围是 1-262144（256K）"""
    from hyperbrain.ui.settings_dialog import SettingsDialog
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog()
    assert dialog.max_tokens_spin.minimum() == 1, \
        f"Max Tokens min 应该是 1, 实际 {dialog.max_tokens_spin.minimum()}"
    assert dialog.max_tokens_spin.maximum() == 262144, \
        f"Max Tokens max 应该是 262144, 实际 {dialog.max_tokens_spin.maximum()}"
    assert dialog.max_tokens_spin.singleStep() == 1024, \
        f"Max Tokens step 应该是 1024, 实际 {dialog.max_tokens_spin.singleStep()}"
    print(f'  Max Tokens 范围: {dialog.max_tokens_spin.minimum()} - {dialog.max_tokens_spin.maximum()} (step={dialog.max_tokens_spin.singleStep()}) ✓')


def test_max_chain_range():
    """测试 最大思维链长度 范围是 1-20"""
    from hyperbrain.ui.settings_dialog import SettingsDialog
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog()
    assert dialog.max_chain_spin.minimum() == 1, \
        f"最大思维链长度 min 应该是 1, 实际 {dialog.max_chain_spin.minimum()}"
    assert dialog.max_chain_spin.maximum() == 20, \
        f"最大思维链长度 max 应该是 20, 实际 {dialog.max_chain_spin.maximum()}"
    print(f'  最大思维链长度 范围: {dialog.max_chain_spin.minimum()} - {dialog.max_chain_spin.maximum()} ✓')


def test_learning_rate_step():
    """测试 学习率 step 是 0.001"""
    from hyperbrain.ui.settings_dialog import SettingsDialog
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog()
    step = dialog.learning_rate_spin.singleStep()
    # 注意：PyQt6 在浮点数 setSingleStep 时可能有精度问题
    assert abs(step - 0.001) < 1e-6, f"学习率 step 应该是 0.001, 实际 {step}"
    print(f'  学习率 step: {step} ✓')


def test_default_values():
    """测试缺省值（测试 spin box 的 setValue 调用，而 _load_settings 之前的初始值）"""
    from hyperbrain.ui.settings_dialog import SettingsDialog
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    # 创建一个空配置场景的 mock - 用 monkeypatch 替换 load_settings
    # 因为 _load_settings 会在 __init__ 中用 config 覆盖 spin box 初始值
    # 这里我们直接创建 spin box 并测试代码

    # 通过导入模块检查源码中的 setValue 调用
    import inspect
    from hyperbrain.ui import settings_dialog
    source = inspect.getsource(settings_dialog)

    # 检查显式 setValue 调用
    assert "self.temperature_spin.setValue(0.7)" in source, "Temperature 应有 setValue(0.7)"
    assert "self.max_tokens_spin.setValue(4096)" in source, "Max Tokens 应有 setValue(4096)"
    assert "self.timeout_spin.setValue(90)" in source, "Timeout 应有 setValue(90)"
    assert "self.reasoning_depth_spin.setValue(3)" in source, "推理深度 应有 setValue(3)"
    assert "self.max_chain_spin.setValue(5)" in source, "最大思维链 应有 setValue(5)"
    assert "self.confidence_threshold_spin.setValue(0.7)" in source, "置信度阈值 应有 setValue(0.7)"
    assert "self.max_exec_time_spin.setValue(30)" in source, "最大执行时间 应有 setValue(30)"
    assert "self.retry_spin.setValue(3)" in source, "重试次数 应有 setValue(3)"
    assert "self.learning_rate_spin.setValue(0.001)" in source, "学习率 应有 setValue(0.001)"
    print(f'  所有 9 个参数都有显式 setValue 调用 ✓')


def test_tooltips():
    """测试所有参数都有 tooltip"""
    from hyperbrain.ui.settings_dialog import SettingsDialog
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog()

    widgets_with_tooltip = [
        dialog.temperature_spin,
        dialog.max_tokens_spin,
        dialog.timeout_spin,
        dialog.reasoning_depth_spin,
        dialog.max_chain_spin,
        dialog.reflection_check,
        dialog.confidence_threshold_spin,
        dialog.max_exec_time_spin,
        dialog.retry_spin,
        dialog.parallel_check,
        dialog.learning_rate_spin,
        dialog.online_learning_check,
    ]
    for widget in widgets_with_tooltip:
        tooltip = widget.toolTip()
        assert tooltip and len(tooltip) > 0, \
            f"{widget.__class__.__name__} 应该有 tooltip"
    print(f'  所有 12 个关键参数都有 tooltip ✓')


def test_api_key_placeholder():
    """测试 API Key 占位符"""
    from hyperbrain.ui.settings_dialog import SettingsDialog
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    dialog = SettingsDialog()

    expected_placeholder = "（可选，未填则不启用）"
    for key_edit in [dialog.openai_key_edit, dialog.anthropic_key_edit, dialog.google_key_edit]:
        placeholder = key_edit.placeholderText()
        assert placeholder == expected_placeholder, \
            f"API Key 占位符应该是 '{expected_placeholder}', 实际 '{placeholder}'"
    print(f'  3 个 API Key 占位符均为 "{expected_placeholder}" ✓')


def test_config_defaults():
    """测试 config.py dataclass 缺省值（独立测试，不依赖 config.json）"""
    from hyperbrain.core.config import ModelConfig, CognitiveConfig
    # 直接实例化，使用 dataclass 默认值
    m = ModelConfig()
    assert m.max_tokens == 4096, \
        f"ModelConfig() max_tokens 默认 4096, 实际 {m.max_tokens}"
    assert m.temperature == 0.7, \
        f"ModelConfig() temperature 默认 0.7, 实际 {m.temperature}"
    assert m.timeout == 90.0, \
        f"ModelConfig() timeout 默认 90.0, 实际 {m.timeout}"

    c = CognitiveConfig()
    assert c.reasoning_depth == 3, \
        f"CognitiveConfig() reasoning_depth 默认 3, 实际 {c.reasoning_depth}"
    assert c.max_chain_length == 5, \
        f"CognitiveConfig() max_chain_length 默认 5, 实际 {c.max_chain_length}"
    assert abs(c.confidence_threshold - 0.7) < 1e-6, \
        f"CognitiveConfig() confidence_threshold 默认 0.7, 实际 {c.confidence_threshold}"
    print(f'  config.py dataclass 缺省值正确 ✓')


def test_config_validation():
    """测试 config.py 验证规则（dataclass ModelConfig）"""
    from hyperbrain.core.config import ModelConfig, CognitiveConfig, ConfigValidationError

    # Max Tokens 超出新上限 262144
    try:
        c = ModelConfig(max_tokens=300000)
        c.validate()
        assert False, "max_tokens=300000 应该抛异常"
    except ConfigValidationError as exc:
        assert "max_tokens" in str(exc), f"异常消息应提到 max_tokens: {exc}"
        print(f'  max_tokens=300000 正确抛异常: {exc}')

    # Max Tokens 上限 262144 合法
    c = ModelConfig(max_tokens=262144)
    c.validate()
    print('  max_tokens=262144 验证通过 ✓')

    # Max Tokens 100000 合法（之前 Pydantic le=8192 会拒）
    c = ModelConfig(max_tokens=100000)
    c.validate()
    print('  max_tokens=100000 验证通过（之前 Pydantic 8K 限制解除）✓')

    # Max Tokens 32768 合法（用户报错的值）
    c = ModelConfig(max_tokens=32768)
    c.validate()
    print('  max_tokens=32768 验证通过（用户报错的值已修复）✓')

    # reasoning_depth 超出范围
    try:
        c = CognitiveConfig(reasoning_depth=20)
        c.validate()
        assert False, "reasoning_depth=20 应该抛异常"
    except ConfigValidationError as e:
        assert "reasoning_depth" in str(e)
    print(f'  reasoning_depth=20 正确抛异常 ✓')

    # max_chain_length 超出范围
    try:
        c = CognitiveConfig(max_chain_length=50)
        c.validate()
        assert False, "max_chain_length=50 应该抛异常"
    except ConfigValidationError as e:
        assert "max_chain_length" in str(e)
    print(f'  max_chain_length=50 正确抛异常 ✓')


def test_pydantic_model_config():
    """测试 Pydantic ModelConfig（models/base.py）验证规则"""
    from pydantic import ValidationError
    from hyperbrain.models.base import ModelConfig as PydModelConfig, ModelProvider

    # max_tokens=100000 合法（之前 le=8192 会拒）
    c = PydModelConfig(
        model_name="gpt-4",
        provider=ModelProvider.OPENAI,
        max_tokens=100000
    )
    assert c.max_tokens == 100000
    print('  Pydantic max_tokens=100000 验证通过 ✓')

    # max_tokens=262144 上限合法
    c = PydModelConfig(
        model_name="claude-3",
        provider=ModelProvider.ANTHROPIC,
        max_tokens=262144
    )
    assert c.max_tokens == 262144
    print('  Pydantic max_tokens=262144 验证通过 ✓')

    # max_tokens=262145 超出上限，应抛 ValidationError
    try:
        c = PydModelConfig(
            model_name="gpt-4",
            provider=ModelProvider.OPENAI,
            max_tokens=262145
        )
        assert False, "Pydantic max_tokens=262145 应该抛 ValidationError"
    except ValidationError as exc:
        assert "max_tokens" in str(exc)
        print(f'  Pydantic max_tokens=262145 正确抛 ValidationError ✓')

    # max_tokens 缺省值应为 4096（不是 2048）
    c = PydModelConfig(model_name="gpt-4", provider=ModelProvider.OPENAI)
    assert c.max_tokens == 4096, \
        f"Pydantic ModelConfig 缺省 max_tokens 应为 4096, 实际 {c.max_tokens}"
    print(f'  Pydantic ModelConfig 缺省 max_tokens=4096 ✓')


def main():
    runner = TestRunner()

    runner.run('Max Tokens 范围测试', test_max_tokens_range)
    runner.run('最大思维链长度 范围测试', test_max_chain_range)
    runner.run('学习率 step 测试', test_learning_rate_step)
    runner.run('缺省值测试', test_default_values)
    runner.run('Tooltip 测试', test_tooltips)
    runner.run('API Key 占位符测试', test_api_key_placeholder)
    runner.run('config.py 缺省值测试', test_config_defaults)
    runner.run('config.py 验证规则测试', test_config_validation)
    runner.run('Pydantic ModelConfig 验证测试', test_pydantic_model_config)

    print('\n' + '=' * 50)
    passed = sum(1 for _, ok, _ in runner.results if ok)
    failed = sum(1 for _, ok, _ in runner.results if not ok)
    print(f'总计: {passed} 通过, {failed} 失败')
    if failed > 0:
        print('\n失败项:')
        for name, ok, err in runner.results:
            if not ok:
                print(f'  - {name}: {err}')
    print('=' * 50)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
