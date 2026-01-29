from click.testing import CliRunner
import json
import logging
from pathlib import Path
from stac_manager.cli import cli

def test_run_workflow_uses_log_context_and_json_file():
    """Test that run-workflow logs banner and creates JSON log file."""
    runner = CliRunner()
    
    with runner.isolated_filesystem():
        # Setup dummy data and workflow
        with open('items.json', 'w') as f:
            json.dump([{"type": "Feature", "id": "test-item"}], f)
            
        with open('workflow.yaml', 'w') as f:
            f.write("""
name: log-test-workflow
settings:
  logging:
    level: INFO
    file: logs/stac_manager.json
    output_format: json
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: items.json
      format: json
  - id: output
    module: OutputModule
    config:
      base_dir: ./output
      format: json
    depends_on: [ingest]
""")
            
        result = runner.invoke(cli, ['run-workflow', 'workflow.yaml'])
        
        if result.exit_code != 0:
            print(result.output)

        assert result.exit_code == 0
        
        # 1. Check Console (StreamHandler)
        # Should see banners from LogRunContext
        assert "Start-time:" in result.output
        assert "Workflow: log-test-workflow" in result.output
        assert "Runtime:" in result.output
        
        # 2. Check File (RotatingFileHandler)
        log_file = Path('logs/stac_manager.json')
        assert log_file.exists()
        
        content = log_file.read_text()
        lines = content.strip().split('\n')
        
        # Check first line is valid JSON and has expected fields
        log_record = json.loads(lines[0])
        assert "timestamp" in log_record
        assert "level" in log_record
        assert "message" in log_record
        assert "step_id" in log_record
