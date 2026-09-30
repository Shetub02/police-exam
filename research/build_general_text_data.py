import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OCR4 = ROOT / "tmp" / "general-question-ocr-psm4.json"
OCR6 = ROOT / "tmp" / "general-question-ocr.json"
OCRE = ROOT / "tmp" / "general-question-ocr-enhanced.json"


def clean(value):
    value = re.sub(r"\s+", " ", value).strip(" |·~-_")
    fixes = {"คํา":"คำ", "จํานวน":"จำนวน", "ทํา":"ทำ", "นํ้า":"น้ำ", "ตํ่า":"ต่ำ", "ไม":"ไม่", "ได":"ได้", "เทา":"เท่า", "ลาสุด":"ล่าสุด", "เลม":"เล่ม", "รานคา":"ร้านค้า", "จงหาคา":"จงหาค่า"}
    for old, new in fixes.items():
        value = value.replace(old, new)
    return value


def parse(number, text):
    match = re.search(rf"(?m)^\s*{number}\s*[.,)]\s*", text)
    if not match:
        return {"question": "", "choices": {}}
    body = text[match.end():]
    marker = re.compile(r"(?m)(?:^|[ \t]{2,})([1-4])\s*[.,)]?\s+")
    hits = list(marker.finditer(body))
    choices = {}
    if hits:
        question = clean(body[:hits[0].start()])
        for index, hit in enumerate(hits):
            key = int(hit.group(1))
            end = hits[index + 1].start() if index + 1 < len(hits) else len(body)
            value = clean(body[hit.end():end])
            if key not in choices and value:
                choices[key] = value
    else:
        question = clean(body)
    return {"question": question, "choices": choices}


def score(value):
    if not value:
        return -1000
    bad = len(re.findall(r"[|@#¥¢]", value)) * 5 + len(re.findall(r"\b(?:Academy|GURU|Police)\b", value, re.I)) * 10
    return min(len(value), 140) - bad


def main():
    p4 = json.loads(OCR4.read_text(encoding="utf-8"))
    p6 = json.loads(OCR6.read_text(encoding="utf-8"))
    pe = json.loads(OCRE.read_text(encoding="utf-8"))
    rows = []
    for number in range(1, 101):
        variants = [parse(number, p4[str(number)]), parse(number, p6[str(number)]), parse(number, pe[str(number)])]
        question = max((v["question"] for v in variants), key=score)
        choices = {}
        for choice in range(1, 5):
            candidates = [v["choices"].get(choice, "") for v in variants]
            choices[choice] = max(candidates, key=score)
        rows.append({"number": number, "question": question, "choices": choices, "raw4": p4[str(number)], "raw6": p6[str(number)]})
    output = ROOT / "tmp" / "general-parsed-draft.json"
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    missing = [row["number"] for row in rows if not row["question"] or any(not row["choices"][str(i)] if isinstance(next(iter(row["choices"])), str) else not row["choices"][i] for i in range(1,5))]
    print("missing", missing)


if __name__ == "__main__":
    main()
