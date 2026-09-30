import json
import subprocess
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "assets" / "real-social-explanations"
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = Path(tempfile.gettempdir()) / "police-thai-tessdata"
SCRATCH = Path(tempfile.gettempdir()) / "police-social-explanation-images"


def read_one(number):
    path = IMAGES / f"q{number:03}.jpg"
    scratch_path = SCRATCH / path.name
    if not scratch_path.exists():
        shutil.copyfile(path, scratch_path)
    result = subprocess.run(
        [str(TESSERACT), str(scratch_path), "stdout", "-l", "tha+eng",
         "--tessdata-dir", str(TESSDATA), "--psm", "6"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    return number, result.stdout.strip()


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = dict(pool.map(read_one, range(1, 101)))
    output = ROOT / "tmp" / "social-explanation-ocr.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote social explanation OCR")


if __name__ == "__main__":
    main()
