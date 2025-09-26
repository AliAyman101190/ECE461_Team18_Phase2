import os
import sys
import pytest
from types import SimpleNamespace
from types import SimpleNamespace
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

from app.cli_controller import CLIController


def test_parse_arguments_monkeypatch(monkeypatch):
    with patch.object(CLIController, 'check_github_token_validity', return_value=True):
        controller = CLIController()
    # Simulate command line args
    monkeypatch.setattr(sys, 'argv', ['run', 'install'])
    args = controller.parse_arguments()
    assert args.command == 'install'


# def test_install_dependencies_success(monkeypatch):
#     with patch.object(CLIController, 'check_github_token_validity', return_value=True):
#         controller = CLIController()

#     # Mock subprocess.run to return success
#     mock_proc = MagicMock()
#     mock_proc.returncode = 0

#     with patch('app.cli_controller.subprocess.run', return_value=mock_proc) as mock_run:
#         rc = controller.install_dependencies()
#         assert rc == 0
#         mock_run.assert_called()


# def test_install_dependencies_failure(monkeypatch):
#     with patch.object(CLIController, 'check_github_token_validity', return_value=True):
#         controller = CLIController()

#     # Mock subprocess.run to return non-zero
#     mock_proc = MagicMock()
#     mock_proc.returncode = 1
#     mock_proc.stderr = 'error'

#     with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
#         rc = controller.install_dependencies()
#         assert rc == 1


# def test_run_tests_parsing(monkeypatch):
#     with patch.object(CLIController, 'check_github_token_validity', return_value=True):
#         controller = CLIController()

#     # Simulate pytest stdout with passed/failed and TOTAL line
#     fake_stdout = '20 passed in 1.23s\nTOTAL 100 90%'

#     mock_proc = MagicMock()
#     mock_proc.returncode = 0
#     mock_proc.stdout = fake_stdout

#     with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
#         rc = controller.run_tests()
#         # When subprocess returns 0, should return 0
#         assert rc == 0


# def test_run_tests_timeout(monkeypatch):
#     with patch.object(CLIController, 'check_github_token_validity', return_value=True):
#         controller = CLIController()
#     # Make subprocess.run raise TimeoutExpired
#     with patch('app.cli_controller.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='pytest', timeout=1)):
#         rc = controller.run_tests()
#         assert rc == 1


# def test_run_requires_valid_github_token(monkeypatch):
#     # Ensure that when the GitHub token is valid at construction, run() proceeds
#     with patch.object(CLIController, 'check_github_token_validity', return_value=True):
#         c = CLIController()
#         # Simulate CLI arguments for a file-processing command
#         monkeypatch.setattr(c, 'parse_arguments', lambda: SimpleNamespace(command='somefile.txt'))
#         called = {}
#         def fake_process(p):
#             called['ok'] = True
#             return 0
#         monkeypatch.setattr(c, 'process_urls', fake_process)
#         rc = c.run()
#         assert rc == 0
#         assert called.get('ok', False) is True


# def test_instantiation_raises_on_invalid_token():
#     # If the token check fails during __init__, CLIController should exit
#     with patch.object(CLIController, 'check_github_token_validity', return_value=False):
#         with pytest.raises(SystemExit) as exc:
#             CLIController()
#         assert exc.value.code == 1
