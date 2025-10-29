import sys
import os
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def test_main_calls_cli_controller_run(monkeypatch):
    # Patch CLIController to avoid running real logic
    from app import main as main_mod

    fake_controller = MagicMock()
    fake_controller.run.return_value = 0
    # Ensure environment has a github token and mock validation call
    monkeypatch.setenv('GITHUB_TOKEN', 'fake-token')
    # Patch requests.get used during token validation to simulate a 200 OK
    with patch('app.main.requests.get', return_value=MagicMock(status_code=200)):
        with patch('app.main.CLIController', return_value=fake_controller):
            # call main
            try:
                main_mod.main()
            except SystemExit:
                # main calls sys.exit; ignore in test
                pass

    fake_controller.run.assert_called()
