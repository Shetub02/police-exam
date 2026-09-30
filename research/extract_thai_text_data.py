import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ข้อสอบจริง' / 'ไทย' / 'ข้อสอบภาษาไทย.pdf'
TESSERACT = Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
TESSDATA = Path(tempfile.gettempdir()) / 'police-thai-tessdata'
SCRATCH = Path(tempfile.gettempdir()) / 'police-thai-actual-pages'

# Page 32 is the answer key. These are the question numbers printed on pages 1-31.
PAGE_NUMBERS = {
    1: range(1, 3), 2: range(3, 5), 3: range(5, 7), 4: range(7, 10),
    5: range(10, 12), 6: range(12, 14), 7: range(14, 17), 8: range(17, 20),
    # Printed page 37 (questions 20-21) is absent from both supplied question PDFs.
    9: range(22, 24), 10: range(24, 26), 11: range(26, 29), 12: range(29, 32),
    13: range(32, 35), 14: range(35, 38), 15: range(38, 41), 16: range(41, 44),
    17: range(44, 47), 18: range(47, 51), 19: range(51, 55), 20: range(55, 59),
    21: range(59, 63), 22: range(63, 67), 23: range(67, 71), 24: range(71, 75),
    25: range(75, 79), 26: range(79, 83), 27: range(83, 87), 28: range(87, 91),
    29: range(91, 95), 30: range(95, 99), 31: range(99, 101),
}


def ocr_page(page_number):
    image_path = SCRATCH / f'p{page_number:02}.png'
    text_path = SCRATCH / f'p{page_number:02}.txt'
    if text_path.exists():
        return page_number, text_path.read_text(encoding='utf-8')
    pdf = pdfium.PdfDocument(SOURCE)
    pdf[page_number - 1].render(scale=2).to_pil().save(image_path)
    result = subprocess.run(
        [str(TESSERACT), str(image_path), 'stdout', '-l', 'tha+eng', '--tessdata-dir', str(TESSDATA), '--psm', '4'],
        capture_output=True, text=True, encoding='utf-8', errors='replace', check=True,
    )
    text_path.write_text(result.stdout, encoding='utf-8')
    print(f'OCR Thai page {page_number}/31', flush=True)
    return page_number, result.stdout


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        pages = dict(pool.map(ocr_page, range(1, 32)))
    report = {}
    for page_number, expected in PAGE_NUMBERS.items():
        text = pages[page_number]
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        found = []
        for number in expected:
            matches = [index for index, line in enumerate(lines) if re.match(rf'^{number}\s*[.,)]?\s+', line)]
            if matches:
                found.append(number)
        report[page_number] = {'expected': list(expected), 'found': found}
    (ROOT / 'tmp' / 'thai-page-ocr.json').write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
