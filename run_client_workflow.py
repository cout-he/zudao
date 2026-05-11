# -*- coding: utf-8 -*-
"""One-click Python entry for the client delivery workflow."""

from __future__ import annotations

import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "outputs"
MAIN_SCRIPT = ROOT_DIR / "scripts" / "main_actual_production.py"
PANEL_WIDTHS = "1000,1240,1250,1500"
DEFAULT_ERROR_LOG_NAME = "run_client_workflow_error.log"


def show_message(title: str, message: str) -> None:
    if os.environ.get("RUN_CLIENT_WORKFLOW_NO_POPUP") == "1":
        print(f"{title}\n{message}")
        return

    try:
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        print(f"{title}\n{message}")


def show_error(title: str, message: str) -> None:
    if os.environ.get("RUN_CLIENT_WORKFLOW_NO_POPUP") == "1":
        print(f"{title}\n{message}", file=sys.stderr)
        return

    try:
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:
        print(f"{title}\n{message}", file=sys.stderr)


def resolve_python_executable() -> Path:
    candidates = [
        ROOT_DIR / ".venv_ga" / "Scripts" / "python.exe",
        ROOT_DIR / ".venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("未找到可用的 Python 环境，请先准备 .venv_ga 或 .venv。")


def list_excel_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}
            and not path.name.startswith("~$")
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def sanitize_name(text: str) -> str:
    cleaned = "".join(
        char if char not in '<>:"/\\|?*' else "_"
        for char in str(text).strip()
    )
    cleaned = cleaned.replace(" ", "_")
    return cleaned or "input"


def choose_input_file() -> Path:
    explicit_input = os.environ.get("RUN_CLIENT_WORKFLOW_INPUT", "").strip()
    if explicit_input:
        input_path = Path(explicit_input)
        if input_path.exists() and input_path.is_file():
            return input_path
        raise FileNotFoundError(f"指定的输入文件不存在：{input_path}")

    if os.environ.get("RUN_CLIENT_WORKFLOW_NO_DIALOG") == "1":
        excel_files = list_excel_files(DATA_DIR)
        if not excel_files:
            raise FileNotFoundError(f"在 {DATA_DIR} 下未找到可用的 Excel 文件。")

        if len(excel_files) == 1:
            return excel_files[0]

        preferred_files = [
            path
            for path in excel_files
            if "实际生产状态表" in path.stem or "生产状态" in path.stem
        ]
        if len(preferred_files) == 1:
            return preferred_files[0]

        raise FileNotFoundError(
            "data 文件夹下存在多个 Excel 文件，无法自动判断输入文件，请手动选择。"
        )

    try:
        import tkinter
        from tkinter import filedialog

        root = tkinter.Tk()
        root.withdraw()
        selected = filedialog.askopenfilename(
            title="请选择要排版的 Excel 文件",
            initialdir=str(DATA_DIR if DATA_DIR.exists() else ROOT_DIR),
            filetypes=[
                ("Excel 文件", "*.xlsx *.xlsm *.xls"),
                ("所有文件", "*.*"),
            ],
        )
        root.destroy()
        if selected:
            return Path(selected)
    except Exception:
        pass

    excel_files = list_excel_files(DATA_DIR)
    if len(excel_files) == 1:
        return excel_files[0]

    preferred_files = [
        path
        for path in excel_files
        if "实际生产状态表" in path.stem or "生产状态" in path.stem
    ]
    if len(preferred_files) == 1:
        return preferred_files[0]

    raise FileNotFoundError(
        "未选择输入文件，且 data 文件夹下无法唯一确定默认 Excel 文件。"
    )


def build_output_paths(input_file: Path) -> tuple[Path, Path, Path, Path]:
    run_root = OUTPUT_DIR / "client_runs"
    run_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / f"{sanitize_name(input_file.stem)}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    output_file = run_dir / f"{input_file.stem}_混合宽度结果.xlsx"
    artifact_dir = run_dir / "排版图与报告"
    log_file = run_dir / "run_client_workflow.log"
    return run_dir, output_file, artifact_dir, log_file


def run_workflow() -> tuple[int, Path, Path, Path, str]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    python_exe = resolve_python_executable()
    input_file = choose_input_file()
    run_dir, output_file, artifact_dir, _ = build_output_paths(input_file)

    command = [
        str(python_exe),
        "-X",
        "utf8",
        str(MAIN_SCRIPT),
        "--decoder-mode",
        "auto",
        "--panel-widths",
        PANEL_WIDTHS,
        "--input",
        str(input_file),
        "--output",
        str(output_file),
        "--artifact-dir",
        str(artifact_dir),
    ]

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    completed = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    return (
        int(completed.returncode),
        input_file,
        run_dir,
        output_file,
        artifact_dir,
        completed.stdout or "",
    )


def main() -> None:
    error_log_file: Path | None = None
    try:
        exit_code, input_file, run_dir, output_file, artifact_dir, run_output = run_workflow()
        error_log_file = run_dir / DEFAULT_ERROR_LOG_NAME
    except Exception:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        error_text = traceback.format_exc()
        fallback_log = OUTPUT_DIR / DEFAULT_ERROR_LOG_NAME
        fallback_log.write_text(error_text, encoding="utf-8")
        show_error(
            "运行失败",
            "程序启动失败，请查看日志：\n"
            f"{fallback_log}",
        )
        raise

    if exit_code != 0:
        error_log_file.write_text(run_output, encoding="utf-8")
        show_error(
            "运行失败",
            "排版流程执行失败，请查看日志：\n"
            f"{error_log_file}",
        )
        raise SystemExit(exit_code)

    show_message(
        "运行完成",
        "排版结果已生成。\n\n"
        f"输入文件：\n{input_file}\n\n"
        f"本次输出目录：\n{run_dir}\n\n"
        f"结果 Excel：\n{output_file}\n\n"
        f"图和报告目录：\n{artifact_dir}",
    )


if __name__ == "__main__":
    main()
