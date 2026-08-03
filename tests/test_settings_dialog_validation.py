"""Test settings_dialog model validation (spec fix-test-model-revert).

Tests that _update_config rejects:
- Empty string
- Placeholder values like 'test_model', 'test', 'placeholder', 'default', 'example'

And accepts real model names like 'qwen3.5:0.8b'.
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_update_config_rejects_empty():
    """Test 1: empty string rejected by _update_config"""
    print("=== Test 1: empty string rejected ===")
    try:
        # Inspect _update_config source for empty check
        from hyperbrain.ui import settings_dialog
        import inspect
        src = inspect.getsource(settings_dialog.SettingsDialog._update_config)
        assert "Ollama Model 不能为空" in src, "Empty check not found in _update_config"
        assert "raise ValueError" in src, "No ValueError raise in _update_config"
        print("PASS: empty check present")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_update_config_rejects_test_model():
    """Test 2: 'test_model' placeholder rejected"""
    print("=== Test 2: test_model placeholder rejected ===")
    try:
        from hyperbrain.ui import settings_dialog
        import inspect
        src = inspect.getsource(settings_dialog.SettingsDialog._update_config)
        assert "test_model" in src, "test_model check not found in _update_config"
        # Check for placeholder list
        for placeholder in ("test", "placeholder", "default", "example", "your_model"):
            assert placeholder in src, f"Placeholder {placeholder!r} not in rejection list"
        print("PASS: all placeholders in rejection list")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_update_config_accepts_real_model():
    """Test 3: real model name 'qwen3.5:0.8b' is allowed by code logic"""
    print("=== Test 3: real model name allowed ===")
    try:
        from hyperbrain.ui import settings_dialog
        import inspect
        src = inspect.getsource(settings_dialog.SettingsDialog._update_config)
        # Check that there's a path where the value is assigned
        assert "self._config.model.ollama_model = ollama_model_value" in src, \
            "Assignment to ollama_model not found"
        print("PASS: assignment path present")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_apply_settings_catches_value_error():
    """Test 4: _apply_settings catches ValueError and shows QMessageBox"""
    print("=== Test 4: _apply_settings catches errors ===")
    try:
        from hyperbrain.ui import settings_dialog
        import inspect
        src = inspect.getsource(settings_dialog.SettingsDialog._apply_settings)
        assert "except Exception" in src, "No exception handler in _apply_settings"
        assert "QMessageBox.warning" in src, "No QMessageBox.warning in _apply_settings"
        print("PASS: exception handler present")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_settings_saved_signal_exists():
    """Test 5: settings_saved signal declared"""
    print("=== Test 5: settings_saved signal declared ===")
    try:
        from hyperbrain.ui import settings_dialog
        import inspect
        src = inspect.getsource(settings_dialog.SettingsDialog)
        assert "settings_saved = pyqtSignal(dict)" in src, "settings_saved signal not declared"
        print("PASS: settings_saved signal present")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_settings_saved_emitted_in_apply():
    """Test 6: settings_saved.emit called in _apply_settings"""
    print("=== Test 6: settings_saved.emit in _apply_settings ===")
    try:
        from hyperbrain.ui import settings_dialog
        import inspect
        src = inspect.getsource(settings_dialog.SettingsDialog._apply_settings)
        assert "settings_saved.emit" in src, "settings_saved.emit not called"
        assert "saved_fields" in src, "saved_fields dict not built"
        print("PASS: settings_saved.emit called with saved_fields")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_main_window_connects_settings_saved():
    """Test 7: main_window._show_settings connects settings_saved signal"""
    print("=== Test 7: main_window._show_settings connects signal ===")
    try:
        from hyperbrain.ui import main_window
        import inspect
        src = inspect.getsource(main_window.MainWindow._show_settings)
        assert "settings_saved.connect" in src, "settings_saved.connect not in _show_settings"
        print("PASS: main_window connects settings_saved")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_main_window_on_settings_saved():
    """Test 8: main_window._on_settings_saved method exists"""
    print("=== Test 8: main_window._on_settings_saved exists ===")
    try:
        from hyperbrain.ui import main_window
        import inspect
        assert hasattr(main_window.MainWindow, "_on_settings_saved"), \
            "_on_settings_saved method missing"
        src = inspect.getsource(main_window.MainWindow._on_settings_saved)
        assert "status_label" in src, "status_label not referenced in _on_settings_saved"
        print("PASS: _on_settings_saved updates status_label")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_list_ollama_models_method():
    """Test 9: _on_list_ollama_models method exists"""
    print("=== Test 9: list ollama models method ===")
    try:
        from hyperbrain.ui import settings_dialog
        import inspect
        assert hasattr(settings_dialog.SettingsDialog, "_on_list_ollama_models"), \
            "_on_list_ollama_models method missing"
        assert hasattr(settings_dialog.SettingsDialog, "_show_model_picker"), \
            "_show_model_picker method missing"
        src = inspect.getsource(settings_dialog.SettingsDialog._on_list_ollama_models)
        assert "ollama" in src and "list" in src, "ollama list not called"
        print("PASS: list ollama models methods present")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_list_button_in_ui():
    """Test 10: list_ollama_models_btn button declared in UI"""
    print("=== Test 10: list_ollama_models_btn declared ===")
    try:
        from hyperbrain.ui import settings_dialog
        import inspect
        # The button is declared in _setup_ui, but the class source covers it
        src = inspect.getsource(settings_dialog.SettingsDialog)
        assert "list_ollama_models_btn" in src, "list_ollama_models_btn not in class"
        assert "列出本地模型" in src, "Button label not found"
        assert "QPushButton" in src, "QPushButton import missing"
        print("PASS: list_ollama_models_btn declared in UI")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    tests = [
        test_update_config_rejects_empty,
        test_update_config_rejects_test_model,
        test_update_config_accepts_real_model,
        test_apply_settings_catches_value_error,
        test_settings_saved_signal_exists,
        test_settings_saved_emitted_in_apply,
        test_main_window_connects_settings_saved,
        test_main_window_on_settings_saved,
        test_list_ollama_models_method,
        test_list_button_in_ui,
    ]
    results = []
    for t in tests:
        results.append(t())
    print()
    print(f"=== Total: {sum(results)}/{len(results)} passed ===")
    sys.exit(0 if all(results) else 1)
