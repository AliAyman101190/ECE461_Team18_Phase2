import os
import sys
import tempfile
import json
import shutil
import subprocess
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from cli_controller import CLIController


def test_parse_arguments_monkeypatch(monkeypatch):
    controller = CLIController()
    # Simulate command line args
    monkeypatch.setattr(sys, 'argv', ['run', 'install'])
    args = controller.parse_arguments()
    assert args.command == 'install'


def test_install_dependencies_success(monkeypatch):
    controller = CLIController()

    # Mock subprocess.run to return success
    mock_proc = MagicMock()
    mock_proc.returncode = 0

    with patch('app.cli_controller.subprocess.run', return_value=mock_proc) as mock_run:
        rc = controller.install_dependencies()
        assert rc == 0
        mock_run.assert_called()


def test_install_dependencies_failure(monkeypatch):
    controller = CLIController()

    # Mock subprocess.run to return non-zero
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = 'error'

    with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
        rc = controller.install_dependencies()
        assert rc == 1


def test_run_tests_parsing(monkeypatch):
    controller = CLIController()

    # Simulate pytest stdout with passed/failed and TOTAL line
    fake_stdout = '20 passed in 1.23s\nTOTAL 100 90%'

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = fake_stdout

    with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
        rc = controller.run_tests()
        # When subprocess returns 0, should return 0
        assert rc == 0


def test_run_tests_timeout(monkeypatch):
    controller = CLIController()
    # Make subprocess.run raise TimeoutExpired
    with patch('app.cli_controller.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='pytest', timeout=1)):
        rc = controller.run_tests()
        assert rc == 1
