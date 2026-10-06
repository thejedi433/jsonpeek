"""Tests for jsonpeek CLI tool."""
import json
import sys
from pathlib import Path
import pytest
from jsonpeek import main, get_type_name, resolve_path, describe, show_keys, count_types


def test_get_type_name():
    """Test type name detection."""
    assert get_type_name(None) == "null"
    assert get_type_name(True) == "bool"
    assert get_type_name(False) == "bool"
    assert get_type_name(42) == "int"
    assert get_type_name(3.14) == "float"
    assert get_type_name("hello") == "str"
    assert get_type_name([1, 2]) == "list"
    assert get_type_name({"a": 1}) == "dict"


def test_resolve_path_empty():
    """Test empty path returns root."""
    data = {"a": 1}
    assert resolve_path(data, "") == data
    assert resolve_path(data, None) == data


def test_resolve_path_dict():
    """Test dot-separated dict navigation."""
    data = {"a": {"b": {"c": 42}}}
    assert resolve_path(data, "a") == {"b": {"c": 42}}
    assert resolve_path(data, "a.b") == {"c": 42}
    assert resolve_path(data, "a.b.c") == 42


def test_resolve_path_list_index():
    """Test list indexing with [N]."""
    data = {"items": [10, 20, 30]}
    assert resolve_path(data, "items[0]") == 10
    assert resolve_path(data, "items[1]") == 20
    assert resolve_path(data, "items[2]") == 30


def test_resolve_path_nested_list():
    """Test nested dict + list navigation."""
    data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
    assert resolve_path(data, "users[0]") == {"name": "Alice"}
    assert resolve_path(data, "users[1].name") == "Bob"


def test_resolve_path_error_key():
    """Test KeyError on missing key."""
    data = {"a": 1}
    with pytest.raises(KeyError):
        resolve_path(data, "missing")


def test_resolve_path_error_index():
    """Test IndexError on out of bounds."""
    data = {"items": [1, 2]}
    with pytest.raises(IndexError):
        resolve_path(data, "items[5]")


def test_resolve_path_error_type():
    """Test TypeError when indexing non-dict/list."""
    data = {"a": 42}
    with pytest.raises(TypeError):
        resolve_path(data, "a.b")


def test_describe_empty_dict():
    """Test describe empty dict."""
    assert describe({}) == "{}"


def test_describe_empty_list():
    """Test describe empty list."""
    assert describe([]) == "[]"


def test_describe_primitives():
    """Test describe primitives."""
    assert describe(None) == "null: None"
    assert describe(42) == "int: 42"
    assert describe(3.14) == "float: 3.14"
    assert describe("hi") == "str: 'hi'"


def test_describe_long_string():
    """Test describe truncates long strings."""
    long_str = "x" * 50
    result = describe(long_str)
    assert "..." in result
    assert len(result) < 60


def test_describe_dict():
    """Test describe dict with keys."""
    data = {"a": 1, "b": "hi"}
    result = describe(data, max_depth=2)
    assert "dict(2 keys)" in result
    assert "a: int: 1" in result
    assert "b: str: 'hi'" in result


def test_describe_dict_truncated():
    """Test describe truncates dict with max_items."""
    data = {"a": 1, "b": 2, "c": 3, "d": 4}
    result = describe(data, max_depth=2, max_items=2)
    assert "... (2 more)" in result


def test_describe_list():
    """Test describe list with sample."""
    data = [1, 2, 3]
    result = describe(data)
    assert "list[3] of int: 1" == result


def test_describe_depth_limit():
    """Test describe respects max_depth."""
    data = {"a": {"b": {"c": 1}}}
    result = describe(data, max_depth=1)
    assert "..." in result


def test_show_keys_dict(capsys):
    """Test show_keys for dict."""
    data = {"name": "Alice", "age": 30}
    show_keys(data, "")
    captured = capsys.readouterr()
    assert "name: str" in captured.out
    assert "age: int" in captured.out


def test_show_keys_list(capsys):
    """Test show_keys for list of dicts."""
    data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    show_keys(data, "")
    captured = capsys.readouterr()
    assert "list with 2 items" in captured.out
    assert "First item type: dict" in captured.out
    assert "id: int" in captured.out
    assert "name: str" in captured.out


def test_show_keys_list_non_dict(capsys):
    """Test show_keys for list of primitives."""
    data = [1, 2, 3]
    show_keys(data, "")
    captured = capsys.readouterr()
    assert "list with 3 items" in captured.out
    assert "First item type: int" in captured.out


def test_show_keys_primitive(capsys):
    """Test show_keys for primitive value."""
    show_keys(42, "")
    captured = capsys.readouterr()
    assert "int: 42" in captured.out


def test_count_types():
    """Test recursive type counting."""
    data = {"a": 1, "b": [2, "x", None], "c": {"d": 3.14}}
    counts = count_types(data)
    assert counts["dict"] == 2
    assert counts["list"] == 1
    assert counts["int"] == 2
    assert counts["str"] == 1
    assert counts["null"] == 1
    assert counts["float"] == 1


def test_main_stdin_keys(capsys, monkeypatch):
    """Test main with stdin and --keys."""
    import io
    json_data = '{"name": "test", "value": 42}'
    monkeypatch.setattr('sys.stdin', io.StringIO(json_data))
    ret = main(["--keys"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "name: str" in captured.out


def test_main_file_describe(tmp_path):
    """Test main with file and --describe."""
    json_file = tmp_path / "data.json"
    json_file.write_text('{"users": [{"id": 1}, {"id": 2}]}')
    ret = main([str(json_file), "--describe"])
    assert ret == 0


def test_main_file_types(tmp_path, capsys):
    """Test main with --types."""
    json_file = tmp_path / "data.json"
    json_file.write_text('{"a": 1, "b": 2, "c": [3, 4]}')
    ret = main([str(json_file), "--types"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "int: 4" in captured.out
    assert "list: 1" in captured.out


def test_main_with_path(tmp_path, capsys):
    """Test main with --path navigation."""
    json_file = tmp_path / "data.json"
    json_file.write_text('{"data": {"items": [10, 20, 30]}}')
    ret = main([str(json_file), "--path", "data.items[1]"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "int: 20" in captured.out


def test_main_path_error(tmp_path, capsys):
    """Test main with invalid path returns error."""
    json_file = tmp_path / "data.json"
    json_file.write_text('{"a": 1}')
    ret = main([str(json_file), "--path", "missing"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_main_path_error_types(tmp_path, capsys):
    """Test main with invalid path in --types returns error."""
    json_file = tmp_path / "data.json"
    json_file.write_text('{"a": 1}')
    ret = main([str(json_file), "--types", "--path", "missing"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_main_depth_option(tmp_path, capsys):
    """Test main with --depth option."""
    json_file = tmp_path / "data.json"
    json_file.write_text('{"a": {"b": {"c": 1}}}')
    ret = main([str(json_file), "--depth", "1"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "..." in captured.out


def test_main_show_keys_with_path(tmp_path, capsys):
    """Test main --keys with --path."""
    json_file = tmp_path / "data.json"
    json_file.write_text('{"data": {"name": "test", "value": 42}}')
    ret = main([str(json_file), "--keys", "--path", "data"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "name: str" in captured.out
    assert "value: int" in captured.out


def test_get_type_name_unknown():
    """Test get_type_name with unknown type."""
    from decimal import Decimal
    assert get_type_name(Decimal("1.5")) == "Decimal"


def test_resolve_path_empty_part():
    """Test resolve_path with empty parts (double dots)."""
    data = {"a": 1}
    assert resolve_path(data, ".a") == 1
    assert resolve_path(data, "a.") == 1


def test_resolve_path_key_on_non_dict():
    """Test resolve_path raises KeyError when using key on non-dict before index."""
    data = [1, 2, 3]
    with pytest.raises(KeyError):
        resolve_path(data, "items[0]")


def test_resolve_path_key_error_non_dict():
    """Test resolve_path raises TypeError when indexing non-dict with key."""
    data = {"items": [1, 2, 3]}
    with pytest.raises(TypeError):
        resolve_path(data, "items[0].missing")


def test_main_list_output(tmp_path, capsys):
    """Test main default output for list shows Length."""
    json_file = tmp_path / "data.json"
    json_file.write_text('[1, 2, 3, 4, 5]')
    ret = main([str(json_file)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Length: 5" in captured.out


def test_main_as_module():
    """Test running as __main__."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "jsonpeek", "--help"],
        cwd=str(Path(__file__).parent),
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Inspect JSON structure" in result.stdout
