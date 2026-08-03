"""Test config save verification (spec fix-test-model-revert).

Tests:
1. save_config writes to yaml correctly
2. save_config verifies write by reading back
3. save_config raises IOError if readback mismatches
4. Config class has hermes field
5. Project config.yaml has correct ollama_model (not test_model)
"""
import os
import sys
import tempfile
import yaml
import traceback

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hyperbrain.core.config import Config, save_config, get_config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_save_and_verify_normal():
    """Test 1: save_config + verification normal path"""
    print("=== Test 1: save_config + verification normal path ===")
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    tmp.close()
    try:
        cfg = Config()
        cfg.model.ollama_model = "qwen3.5:0.8b"
        save_config(cfg, tmp.name)

        with open(tmp.name, "r", encoding="utf-8") as f:
            saved = yaml.safe_load(f)
        assert saved["model"]["ollama_model"] == "qwen3.5:0.8b", \
            f"Expected qwen3.5:0.8b, got {saved['model']['ollama_model']}"
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise
    finally:
        os.unlink(tmp.name)


def test_save_and_verify_mismatch_raises():
    """Test 2: save_config with readback mismatch raises IOError"""
    print("=== Test 2: save_config IOError on mismatch ===")
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    tmp.close()
    try:
        cfg = Config()
        cfg.model.ollama_model = "qwen3.5:0.8b"

        # Monkey-patch _verify_saved_config to simulate mismatch
        from hyperbrain.core import config as cfg_mod
        original = cfg_mod.ConfigManager._verify_saved_config

        def bad_verify(self, path_obj, config):
            raise IOError("simulated mismatch")

        cfg_mod.ConfigManager._verify_saved_config = bad_verify
        try:
            try:
                save_config(cfg, tmp.name)
                print("FAIL: expected IOError not raised")
                assert False, "expected IOError not raised"
            except IOError as e:
                assert "mismatch" in str(e) or "simulated" in str(e)
                print(f"PASS: IOError raised as expected ({e})")
        finally:
            cfg_mod.ConfigManager._verify_saved_config = original
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def test_config_has_hermes_field():
    """Test 3: Config class has hermes field"""
    print("=== Test 3: Config class has hermes field ===")
    try:
        cfg = Config()
        assert hasattr(cfg, "hermes"), "Config missing hermes field"
        assert cfg.hermes is not None
        print(f"PASS: hermes type = {type(cfg.hermes).__name__}")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_project_config_no_test_model():
    """Test 4: Project config.yaml does not contain test_model"""
    print("=== Test 4: Project config.yaml ollama_model != test_model ===")
    try:
        cfg = get_config()
        actual = cfg.model.ollama_model
        assert actual != "test_model", f"ollama_model is still test_model!"
        assert actual == cfg.model.default_model, \
            f"ollama_model ({actual}) != default_model ({cfg.model.default_model})"
        print(f"PASS: ollama_model = {actual}")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_yaml_file_directly():
    """Test 5: config.yaml on disk has correct ollama_model"""
    print("=== Test 5: config.yaml disk content ===")
    try:
        yaml_path = os.path.join(PROJECT_ROOT, "config.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        ollama_model = data.get("model", {}).get("ollama_model")
        assert ollama_model != "test_model", "config.yaml still has test_model!"
        print(f"PASS: config.yaml ollama_model = {ollama_model}")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


def test_default_model_matches_ollama():
    """Test 6: default_model == ollama_model"""
    print("=== Test 6: default_model == ollama_model ===")
    try:
        cfg = get_config()
        assert cfg.model.default_model == cfg.model.ollama_model, \
            f"default_model ({cfg.model.default_model}) != ollama_model ({cfg.model.ollama_model})"
        print(f"PASS: both = {cfg.model.default_model}")
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    tests = [
        test_save_and_verify_normal,
        test_save_and_verify_mismatch_raises,
        test_config_has_hermes_field,
        test_project_config_no_test_model,
        test_yaml_file_directly,
        test_default_model_matches_ollama,
    ]
    results = []
    for t in tests:
        try:
            t()
            results.append(True)
        except Exception:
            results.append(False)
    print()
    print(f"=== Total: {sum(results)}/{len(results)} passed ===")
    sys.exit(0 if all(results) else 1)
