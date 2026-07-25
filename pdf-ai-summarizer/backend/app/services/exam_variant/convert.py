from pathlib import Path

from app.core.config import settings

import subprocess

def convert_doc_to_docx(path: Path) -> Path:
    if path.suffix.lower() == ".docx":
        return path
    out_dir = Path(settings.exam_variant_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
    ["soffice", "--headless", "--convert-to", "docx", "--outdir", str(out_dir), str(path)],
    capture_output=True,   # bắt lại stdout/stderr thay vì in thẳng ra terminal
    timeout=60,             # giây — nếu soffice treo quá lâu thì tự raise TimeoutExpired
    )
    output_path = out_dir / f"{path.stem}.docx"
    
    if not output_path.exists():
        raise RuntimeError(f"Convert thất bại: {result.stderr.decode()}")
    return output_path

        