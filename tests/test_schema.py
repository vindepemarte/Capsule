import json

from typer.testing import CliRunner

from capsule.cli.app import app
from capsule.spec.schema import manifest_json_schema


runner = CliRunner()


def test_manifest_json_schema_contains_core_sections():
    schema = manifest_json_schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "Capsule Manifest"
    assert "name" in schema["properties"]
    assert "input_schema" in schema["properties"]
    assert "output_schema" in schema["properties"]
    assert "agents" in schema["properties"]
    assert "workflow" in schema["properties"]
    assert "name" in schema["required"]
    assert "mcp" in schema["$defs"]["ToolSpec"]["properties"]["type"]["enum"]


def test_schema_command_prints_json_schema():
    result = runner.invoke(app, ["schema"])

    assert result.exit_code == 0, result.output
    schema = json.loads(result.output)
    assert schema["title"] == "Capsule Manifest"
    assert "tools" in schema["properties"]


def test_schema_command_writes_json_schema(tmp_path):
    output = tmp_path / "capsule.schema.json"

    result = runner.invoke(app, ["schema", "--output", str(output)])

    assert result.exit_code == 0, result.output
    schema = json.loads(output.read_text(encoding="utf-8"))
    assert schema["title"] == "Capsule Manifest"
