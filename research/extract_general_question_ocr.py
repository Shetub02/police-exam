import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "assets" / "real-general"
SCRATCH = Path(tempfile.gettempdir()) / "police-general-question-images-enhanced"
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = Path(tempfile.gettempdir()) / "police-thai-tessdata"


def read_one(number, psm="6"):
    source = IMAGES / f"q{number:03}.jpg"
    image = SCRATCH / source.name
    if not image.exists():
        original = Image.open(source).convert("L")
        original = ImageOps.autocontrast(original, cutoff=1)
        original = ImageEnhance.Contrast(original).enhance(1.7)
        original = original.resize((original.width * 2, original.height * 2))
        original = original.filter(ImageFilter.SHARPEN)
        original.save(image)
    result = subprocess.run(
        [str(TESSERACT), str(image), "stdout", "-l", "tha+eng",
         "--tessdata-dir", str(TESSDATA), "--psm", psm],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    return number, result.stdout.strip()


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = dict(pool.map(lambda number: read_one(number, "6"), range(1, 101)))
    output = ROOT / "tmp" / "general-question-ocr-enhanced.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote general question OCR")


if __name__ == "__main__":
    main()
