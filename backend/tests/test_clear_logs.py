import os
import sys
import io
import tempfile
import shutil
import logging

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app import clear_logs


def test_clear_logs_deletes_files(tmp_path, capsys):
    # Create a temporary logs directory sibling to app/
    app_dir = os.path.join(project_root, 'app')
    # create a source logs directory separate from the destination
    src_logs = tmp_path / 'src_logs'
    src_logs.mkdir()

    # Create fake log files in source
    file1 = src_logs / 'a.log'
    file2 = src_logs / 'b.log'
    file1.write_text('one')
    file2.write_text('two')

    # Monkeypatch the Path resolution so clear_logs looks at our tmp logs dir
    original_file = clear_logs.__file__ if hasattr(clear_logs, '__file__') else None

    try:
        # Temporarily replace __file__ for module to point inside a dummy app folder
        clear_logs_path = os.path.join(str(tmp_path), 'app')
        os.makedirs(clear_logs_path, exist_ok=True)
        # Create a dummy file so Path(__file__).resolve().parent.parent works
        fake_file = os.path.join(clear_logs_path, 'clear_logs.py')
        with open(fake_file, 'w', encoding='utf-8') as f:
            f.write('# dummy')

        # Now run clear_logs by temporarily setting __file__ on the module
        old_file = getattr(clear_logs, '__file__', None)
        setattr(clear_logs, '__file__', fake_file)

        # Also create logs dir at expected parent
        parent_logs = os.path.join(os.path.dirname(fake_file), '..', 'logs')
        parent_logs = os.path.abspath(parent_logs)
        # Move our src_logs into that location (ensure destination cleaned first)
        if os.path.exists(parent_logs):
            shutil.rmtree(parent_logs)
        shutil.copytree(str(src_logs), parent_logs)

        # Run
        clear_logs.clear_logs()

        captured = capsys.readouterr()
        assert 'Deleted' in captured.out
        # Verify files removed
        remaining = os.listdir(parent_logs) if os.path.exists(parent_logs) else []
        assert remaining == []

    finally:
        # cleanup
        if old_file is not None:
            setattr(clear_logs, '__file__', old_file)
        if os.path.exists(parent_logs):
            shutil.rmtree(parent_logs)


def test_clear_logs_no_logs_dir(tmp_path, capsys):
    # Create fake app dir elsewhere and ensure no logs dir exists
    clear_logs_path = tmp_path / 'app'
    clear_logs_path.mkdir()
    fake_file = clear_logs_path / 'clear_logs.py'
    fake_file.write_text('# dummy')

    old_file = getattr(clear_logs, '__file__', None)
    try:
        setattr(clear_logs, '__file__', str(fake_file))
        clear_logs.clear_logs()
        captured = capsys.readouterr()
        assert 'No logs directory found' in captured.out
    finally:
        if old_file is not None:
            setattr(clear_logs, '__file__', old_file)
