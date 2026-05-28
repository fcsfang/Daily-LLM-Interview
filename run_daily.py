from __future__ import annotations

import os
import sys
from pathlib import Path


def _reexec_with_venv_python() -> None:
    project_dir = Path(__file__).resolve().parent
    venv_dir = project_dir / ".venv"
    venv_python = project_dir / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return
    if Path(sys.prefix).resolve() == venv_dir.resolve():
        return
    os.execv(str(venv_python), [str(venv_python), *sys.argv])


_reexec_with_venv_python()

from daily_llm_interview_digest.cli import main  # noqa: E402


if __name__ == "__main__":
    main()
