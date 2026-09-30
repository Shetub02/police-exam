import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ข้อสอบจริง" / "สังคม" / "ข้อสอบสังคม Extract.pdf"
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = Path(tempfile.gettempdir()) / "police-thai-tessdata"
SCRATCH = Path(tempfile.gettempdir()) / "police-social-actual-pages"


def ocr_page(page_number):
    image_path = SCRATCH / f"p{page_number:02}.png"
    text_path = SCRATCH / f"p{page_number:02}.txt"
    if text_path.exists():
        return page_number, text_path.read_text(encoding="utf-8")
    pdf = pdfium.PdfDocument(SOURCE)
    pdf[page_number - 1].render(scale=2.4).to_pil().save(image_path)
    result = subprocess.run(
        [str(TESSERACT), str(image_path), "stdout", "-l", "tha+eng",
         "--tessdata-dir", str(TESSDATA), "--psm", "4"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    text_path.write_text(result.stdout, encoding="utf-8")
    print(f"OCR social page {page_number}/26", flush=True)
    return page_number, result.stdout


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        pages = dict(pool.map(ocr_page, range(1, 27)))
    output = ROOT / "tmp" / "social-page-ocr.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
