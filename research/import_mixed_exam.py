"""Import the selected questions and their source explanations from ข้อสอบรวม.pdf."""

import json
import logging
import re
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ข้อสอบจริง/ข้อสอบรวม/ข้อสอบรวม.pdf"
SOURCE_ID = "local-guru-mixed-30days"
SOURCE_NAME = "Guru Police · ข้อสอบรวม อก. พฐ. 30 วันก่อนสอบ"
ASSETS = ROOT / "assets/mixed-exam-explanations"
REPORT = ROOT / "research/mixed-exam-import-report.json"
DATE = "2026-11-25"
SUBJECT_RANGES = {
    "general": range(1, 21),
    "thai": range(21, 41),
    "it": range(41, 81),
    "law": range(110, 136),
    "english": range(136, 151),
}
THAI_GLYPHS = str.maketrans({"\uf706": "้", "\uf70a": "่", "\uf70b": "้", "\uf70e": "์", "\uf712": "็"})
LOGIC_SYMBOLS = str.maketrans({"Ù": "∧", "Ú": "∨", "®": "→", "«": "↔"})


def clean(text):
    text = re.sub(r"ํ([่้๊๋]?)า", r"\1ำ", text)
    lines = []
    for line in text.translate(THAI_GLYPHS).splitlines():
        line = line.strip()
        if line and not line.startswith(("á¨", "µÐ", "à©")) and line != "c":
            lines.append(re.sub(r"[ \t]+", " ", line))
    return "\n".join(lines)


def join_pages(pages, first, last):
    text = ""
    offsets = []
    for index in range(first - 1, last):
        offsets.append((len(text), index + 1))
        text += clean(pages[index].extract_text() or "") + "\n"
    return text, offsets


def page_at(offsets, position):
    return max(page for offset, page in offsets if offset <= position)


def subject_for(number):
    return next((subject for subject, numbers in SUBJECT_RANGES.items() if number in numbers), None)


def read_questions(pages):
    text, offsets = join_pages(pages, 7, 42)
    starts = []
    for match in re.finditer(r"(?m)^(\d{1,3})\.\s+", text):
        number = int(match.group(1))
        suffix = text[match.end():match.end() + 30]
        first_questions = (
            (number == 1 and not starts)
            or (number == 2 and suffix.startswith("ปัจจุบันแม่"))
            or (number == 3 and suffix.startswith("กำหนดให้"))
            or (number == 4 and suffix.startswith("นายสิบตำรวจ"))
        )
        if number >= 5 or first_questions:
            starts.append((number, match.start(), match.end()))
    if [number for number, _, _ in starts] != list(range(1, 151)):
        raise ValueError("Question numbering is incomplete or out of order")

    questions = []
    passage = ""
    for index, (number, start, content_start) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(text)
        block = text[content_start:end].strip()
        if number == 149:
            block, passage = block.split("Driving and Cell Phones", 1)
            passage = "Driving and Cell Phones\n" + passage.strip()
        choices = list(re.finditer(r"(?m)^([1-4])\.\s+", block))
        if [match.group(1) for match in choices] != ["1", "2", "3", "4"]:
            raise ValueError(f"Question {number}: incomplete choices")
        prompt = block[:choices[0].start()].strip()
        values = []
        for choice_index, match in enumerate(choices):
            choice_end = choices[choice_index + 1].start() if choice_index < 3 else len(block)
            values.append(clean(block[match.end():choice_end]).replace("\n", " "))
        # Stacked fractions lose their fraction bars in the PDF's text layer.
        if number == 13:
            values = ["1/10", "1/13", "3/20", "4/13"]
        if number == 17:
            prompt = prompt.translate(LOGIC_SYMBOLS)
            values = [value.translate(LOGIC_SYMBOLS) for value in values]
        if number == 34:
            prompt = (
                "อ่านข้อความจากบทกลอนต่อไปนี้ แล้วพิจารณาว่าวรรคใดมีถ้อยคำที่อาจทำให้เกิดความกำกวม\n"
                "“เขายืนชมเขาใหญ่กลางสายหมอก\n"
                "น้องหยอกเล่นกับเพื่อนอย่างสุขสันต์\n"
                "แม่จัดสำรับอาหารไว้ให้กัน\n"
                "พ่อปลูกฝันทำสวนทุกวันคืน”"
            )
        question = {
            "number": number,
            "subject": subject_for(number),
            "question_text": prompt,
            "choices": dict(zip("ABCD", values)),
            "question_page": page_at(offsets, start),
        }
        if number == 150:
            question["reading_passage"] = passage
        if question["subject"]:
            questions.append(question)
    if len(questions) != 121:
        raise ValueError("Expected 121 questions in the requested ranges")
    return questions


def read_answers(pages):
    table = {int(number): int(key) for number, key in re.findall(r"(\d+)\.\s*ตอบ\s*([1-4])", pages[43].extract_text())}
    if len(table) != 150:
        raise ValueError("The summary answer key must contain 150 answers")
    text, offsets = join_pages(pages, 45, 96)
    starts = list(re.finditer(r"ข้อ\s*(\d{1,3})\.\s*เฉลย\s*ข้อ\s*([1-4])\.?", text))
    if [int(match.group(1)) for match in starts] != list(range(1, 151)):
        raise ValueError("Detailed explanation numbering is incomplete")
    answers = {}
    for index, match in enumerate(starts):
        number, key = int(match.group(1)), int(match.group(2))
        if key != table[number]:
            raise ValueError(f"Question {number}: answer table and explanation disagree")
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        answers[number] = {
            "key": "ABCD"[key - 1],
            "detail": clean(text[match.end():end]),
            "page": page_at(offsets, match.start()),
        }
    return answers


def answer_positions(document):
    positions = {}
    for page_index in range(44, 96):
        words = document.pages[page_index].extract_words()
        for index, word in enumerate(words[:-3]):
            if word["text"] != "ข้อ" or word["x0"] > 75:
                continue
            following = words[index + 1:index + 5]
            number = re.fullmatch(r"(\d{1,3})\.", following[0]["text"])
            if number and any("เฉลย" in item["text"] for item in following[1:]):
                positions[int(number.group(1))] = (page_index, word["top"])
    if set(positions) != set(range(1, 151)):
        raise ValueError("Cannot locate every source explanation for image cropping")
    return positions


def render_explanation(document, positions, number):
    start_page, start_y = positions[number]
    end_page, end_y = positions[number + 1]
    strips = []
    for page_index in range(start_page, end_page + 1):
        page = document[page_index]
        width, height = page.get_size()
        top = start_y - 5 if page_index == start_page else 72
        bottom = end_y - 8 if page_index == end_page else height - 45
        if bottom <= top:
            continue
        image = page.render(scale=2).to_pil().convert("RGB")
        strips.append(image.crop((124, round(top * 2), round((width - 60) * 2), round(bottom * 2))))
    if not strips:
        raise ValueError(f"Question {number}: empty explanation image")
    combined = Image.new("RGB", (max(image.width for image in strips), sum(image.height for image in strips) + 16 * (len(strips) - 1)), "white")
    top = 0
    for image in strips:
        combined.paste(image, (0, top))
        top += image.height + 16
    output = ASSETS / f"q{number:03}.jpg"
    combined.save(output, quality=91, optimize=True)
    return output.relative_to(ROOT).as_posix()


def main():
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = PdfReader(SOURCE)
    if len(reader.pages) != 96:
        raise ValueError("This importer expects the reviewed 96-page source document")
    questions = read_questions(reader.pages)
    answers = read_answers(reader.pages)
    duplicate_map = json.loads((ROOT / "research/mixed-exam-duplicates.json").read_text(encoding="utf-8"))
    selected_numbers = {question["number"] for question in questions}
    if not set(map(int, duplicate_map)).issubset(selected_numbers):
        raise ValueError("A duplicate mapping refers to an excluded question")

    ASSETS.mkdir(parents=True, exist_ok=True)
    with pdfplumber.open(SOURCE) as layout:
        positions = answer_positions(layout)
    images = pdfium.PdfDocument(SOURCE)
    imported = []
    duplicates = []
    for question in questions:
        number = question["number"]
        if str(number) in duplicate_map:
            duplicates.append({"question_number": number, "subject": question["subject"], "existing_id": duplicate_map[str(number)]})
            continue
        answer = answers[number]
        row = {
            "id": f"mixed-guru-30days-{number:03}",
            "subject": question["subject"],
            "question_number": number,
            "question_text": question["question_text"],
            "choices": question["choices"],
            "correct_answer": answer["key"],
            "source_answer": f'{answer["key"]}. {question["choices"][answer["key"]]}',
            "explanation_th": [answer["detail"]],
            "explanation_author": "source",
            "answer_key_type": "document_answer_key",
            "answer_verified": True,
            "official_answer_verified": False,
            "choices_verified": True,
            "year": None,
            "exam_track": "อก./พฐ.",
            "provider": "guru-police",
            "source_id": SOURCE_ID,
            "source_name": SOURCE_NAME,
            "source_locator": f'ข้อ {number} · โจทย์หน้า PDF {question["question_page"]} · เฉลยหน้า PDF {answer["page"]}',
            "source_url": f'ข้อสอบจริง/ข้อสอบรวม/ข้อสอบรวม.pdf#page={question["question_page"]}',
            "explanation_source_id": SOURCE_ID,
            "evidence_level": "A",
            "representation": "mock",
            "exact_wording": True,
            "reviewed_at": DATE,
            "eligible": True,
            "collection": "ข้อสอบรวม",
            "note": "ชุดข้อสอบรวม อก. พฐ. 30 วันก่อนสอบ · เลขตัวเลือก 1–4 ในเอกสารตรงกับ A–D ในเว็บ",
            "verification_scope": "เทียบโจทย์และตัวเลือกกับไฟล์ต้นฉบับ จับคู่เฉลยรวมกับเฉลยละเอียดตามเลขข้อ และตรวจข้อซ้ำกับคลังเดิม",
        }
        if question.get("reading_passage"):
            row["reading_passage"] = question["reading_passage"]
        if question["subject"] == "general":
            row["explanation_image"] = render_explanation(images, positions, number)
            row["explanation_th"] = ["วิธีทำจากเฉลยต้นฉบับตามภาพด้านล่าง โดยตรวจตรงกับตารางเฉลยท้ายไฟล์แล้ว"]
        imported.append(row)

    summary = {}
    for subject, numbers in SUBJECT_RANGES.items():
        summary[subject] = {
            "selected": len(numbers),
            "added": sum(question["subject"] == subject for question in imported),
            "duplicates": sum(question["subject"] == subject for question in duplicates),
        }
    report = {
        "source_id": SOURCE_ID,
        "source_pdf": SOURCE.relative_to(ROOT).as_posix(),
        "representation": "mock",
        "reviewed_at": DATE,
        "selected_count": len(questions),
        "added_count": len(imported),
        "duplicate_count": len(duplicates),
        "excluded_numbers": list(range(81, 110)),
        "duplicate_rule": "ข้ามโจทย์ที่มีสถานการณ์ เงื่อนไข และคำถามเดียวกับข้อเดิม แม้สลับหรือปรับตัวเลือก; เก็บข้อที่เปลี่ยนเงื่อนไข ตัวเลข บทอ่าน หรือถามคนละประเด็น",
        "subjects": summary,
        "added_question_numbers": [question["question_number"] for question in imported],
        "duplicates": duplicates,
    }
    payload = {
        "sources": [{"id": SOURCE_ID, "name": SOURCE_NAME, "platform": "local-pdf", "url": SOURCE.relative_to(ROOT).as_posix(), "local": True, "status": "reviewed", "provider": "guru-police", "note": f'แนวข้อสอบตามชื่อหน้าปก คัดเฉพาะช่วงที่กำหนด 121 ข้อ เพิ่ม {len(imported)} ข้อ และข้ามข้อซ้ำ {len(duplicates)} ข้อ พร้อมเฉลยท้ายเอกสาร'}],
        "questions": imported,
        "import_summary": summary,
    }
    loader = """
(function () {
  const incoming = window.POLICE_MIXED_EXAM_DATA;
  const data = window.POLICE_DATA;
  if (!incoming || !data) return;
  const sourceIds = new Set(data.sources.map(source => source.id));
  for (const source of incoming.sources) {
    if (!sourceIds.has(source.id)) {
      data.sources.push(source);
      sourceIds.add(source.id);
    }
  }
  const questionIds = new Set(data.questions.map(question => question.id));
  for (const question of incoming.questions) {
    if (!questionIds.has(question.id)) {
      data.questions.push(question);
      questionIds.add(question.id);
    }
  }
})();
"""
    (ROOT / "police-mixed-exam-data.js").write_text("window.POLICE_MIXED_EXAM_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n" + loader, encoding="utf-8")
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added": len(imported), "duplicates": len(duplicates), "subjects": summary}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
