import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = Path(tempfile.gettempdir()) / "police-thai-tessdata"

CONFIG = {
    "computer": (ROOT / "ข้อสอบจริง/คอม/Copy of 01. เฉลยละเอียด คอมพิวเตอร์.pdf", ROOT / "assets/real-computer-explanations"),
    "general": (ROOT / "ข้อสอบจริง/ความสามารถทั่วไป/Copy of 01. เฉลยละเอียด ความสามารถทั่วไป.pdf", ROOT / "assets/real-general-explanations"),
    "law": (ROOT / "ข้อสอบจริง/กฏหมาย/Copy of 01. เฉลยละเอียด กฎหมาย.pdf", ROOT / "assets/real-law-explanations"),
    "social": (ROOT / "ข้อสอบจริง/สังคม/Copy of 01. เฉลยละเอียด สังคม.pdf", ROOT / "assets/real-social-explanations"),
    "thai": (ROOT / "ข้อสอบจริง/ไทย/Copy of เฉลยละเอียดภาษาไทย.pdf", ROOT / "assets/real-thai-explanations"),
}


def ocr_lines(image_path):
    result = subprocess.run(
        [str(TESSERACT), str(image_path), "stdout", "-l", "tha+eng", "--tessdata-dir", str(TESSDATA), "--psm", "6", "tsv"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
    )
    grouped = defaultdict(list)
    headers = result.stdout.splitlines()[0].split("\t")
    for raw in result.stdout.splitlines()[1:]:
        fields = raw.split("\t", 11)
        if len(fields) != 12:
            continue
        row = dict(zip(headers, fields))
        text = (row.get("text") or "").strip()
        if not text:
            continue
        key = (row["block_num"], row["par_num"], row["line_num"])
        grouped[key].append(row)
    lines = []
    for words in grouped.values():
        words.sort(key=lambda row: int(row["left"]))
        lines.append({
            "text": " ".join(row["text"] for row in words),
            "top": min(int(row["top"]) for row in words),
            "bottom": max(int(row["top"]) + int(row["height"]) for row in words),
        })
    return sorted(lines, key=lambda line: (line["top"], line["text"]))


def marker_number(text):
    normalized = re.sub(r"\s+", "", text.strip())
    match = re.match(r"^(\d{1,3})[.),]?เฉลย(?:ละเอียด)?ข้?อ", normalized, re.I)
    if match:
        return int(match.group(1))
    return None


def run(subject):
    source, destination = CONFIG[subject]
    destination.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.gettempdir()) / f"police-{subject}-answer-pages"
    scratch.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(source)
    found = {}
    for page_index in range(len(pdf)):
        page_path = scratch / f"p{page_index + 1:03}.jpg"
        image = pdf[page_index].render(scale=1.55).to_pil().convert("RGB")
        image.save(page_path, quality=88)
        lines = ocr_lines(page_path)
        markers = []
        for line in lines:
            number = marker_number(line["text"])
            if number and 1 <= number <= 100:
                markers.append((number, line["top"]))
        markers = sorted(dict(markers).items(), key=lambda item: item[1])
        for offset, (number, top) in enumerate(markers):
            bottom = markers[offset + 1][1] - 8 if offset + 1 < len(markers) else image.height - 42
            top = max(0, top - 14)
            if bottom - top < 100:
                continue
            crop = image.crop((55, top, image.width - 45, bottom))
            crop.save(destination / f"q{number:03}.jpg", quality=84, optimize=True)
            found[number] = page_index + 1
        print(f"{subject}: page {page_index + 1}/{len(pdf)}, markers {','.join(str(n) for n,_ in markers) or '-'}", flush=True)
    missing = [number for number in range(1, 101) if number not in found]
    print({"subject": subject, "found": len(found), "missing": missing})
    if missing:
        raise SystemExit(2)


if __name__ == "__main__":
    for requested in sys.argv[1:]:
        run(requested)
