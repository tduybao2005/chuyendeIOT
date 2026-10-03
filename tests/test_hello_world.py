import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "hello_world.py"


def test_prints_hello_world(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=tmp_path,  # chạy từ thư mục khác để chắc chắn không phụ thuộc cwd
    )
    assert result.returncode == 0
    assert result.stdout == "hello world!\n"
    assert result.stderr == ""
