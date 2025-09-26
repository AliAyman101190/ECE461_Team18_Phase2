import warnings
import sys
import os
import argparse
from pathlib import Path

# Suppress noisy RequestsDependencyWarning emitted by system-installed requests
# when urllib3/chardet versions are different than expected. Do this before
# importing any module that may import `requests`.
warnings.filterwarnings("ignore", module=r"requests.*")

# NOTE: We intentionally do NOT import CLIController at module import time.
# Tests patch `app.main.CLIController`, so we keep a module attribute that can
# be patched while avoiding side effects before env validation.
CLIController = None  # type: ignore


def _validate_log_path_from_env() -> None:
    """
    If a log file path is provided via environment variables, validate it is
    writable (create parent directories if possible). Exit with code 1 on error.
    Recognized env vars: LOG_FILE, LOG_PATH.
    """
    # Support multiple common env var names. Treat empty strings as INVALID.
    file_keys = ['LOG_FILE', 'LOG_PATH', 'LOGFILE', 'LOGFILE_PATH']
    dir_keys = ['LOG_DIR', 'LOG_DIRECTORY']
    env_path = None
    env_dir = None

    # Capture the first explicitly provided file path env var (even if empty)
    for key in file_keys:
        if key in os.environ:
            env_path = os.environ.get(key)
            break

    # Capture the first explicitly provided directory env var (even if empty)
    for key in dir_keys:
        if key in os.environ:
            env_dir = os.environ.get(key)
            break

    # If a directory is specified, ensure it exists and is writable
    if env_dir is not None:
        try:
            if not str(env_dir).strip():
                raise RuntimeError("log directory path is empty")
            dir_path = Path(env_dir)
            if not dir_path.exists() or not dir_path.is_dir():
                raise RuntimeError("log directory does not exist or is not a directory")
            if not os.access(str(dir_path), os.W_OK):
                raise RuntimeError("log directory is not writable")
        except Exception as e:
            print(f"Error: Invalid log directory in environment: {env_dir} ({e})", file=sys.stderr)
            sys.exit(1)

    # If a file path is specified, ensure parent exists and is writable, and file is creatable/appended
    if env_path is not None:
        try:
            if not str(env_path).strip():
                raise RuntimeError("log file path is empty")
            path_obj = Path(env_path)
            parent = path_obj.parent
            if not parent.exists() or not parent.is_dir():
                raise RuntimeError("log file parent directory does not exist")
            if not os.access(str(parent), os.W_OK):
                raise RuntimeError("log file parent directory is not writable")
            # Try opening the file for append to validate writability without creating parents
            with open(path_obj, 'a', encoding='utf-8'):
                pass
        except Exception as e:
            print(f"Error: Invalid log file path in environment: {env_path} ({e})", file=sys.stderr)
            sys.exit(1)


def _parse_commandline_for_preflight(argv: list[str]) -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('command', nargs='?')
    try:
        args, _ = parser.parse_known_args(argv[1:])
        return args.command or ''
    except SystemExit:
        # If parsing fails (e.g., unknown args), skip token validation
        return ''


def _validate_github_token_if_required(command: str) -> None:
    """
    For commands other than 'install' and 'test', require a non-empty GITHUB_TOKEN.
    Exit 1 if invalid or missing.
    """
    # Only enforce when a concrete command is provided and it's not install/test
    if command in ('', 'install', 'test'):
        return
    token = os.environ.get('GITHUB_TOKEN')
    if not token or not token.strip():
        print("Error: Invalid or missing GITHUB_TOKEN in environment.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    # Preflight env validation before importing the rest of the application
    _validate_log_path_from_env()
    command = _parse_commandline_for_preflight(sys.argv)
    _validate_github_token_if_required(command)

    global CLIController  # patched by tests
    if CLIController is None:
        # Import lazily after preflight checks
        from cli_controller import CLIController as _RealCLIController
        CLIController = _RealCLIController

    controller = CLIController()
    exit_code = controller.run()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()