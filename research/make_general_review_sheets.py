from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "real-general"
OUTPUT = ROOT / "tmp" / "general-review"

numbers = [2,4,7,8,9,15,16,18,21,27,28,29,34,35,43,46,47,51,52,53,56,57,58,59,60,66,69,70,71,73,74,82,83,84,85,87,90,96]
OUTPUT.mkdir(parents=True, exist_ok=True)
for sheet_no, offset in enumerate(range(0, len(numbers), 4), 1):
    group = numbers[offset:offset+4]
    cards = []
    for number in group:
        image = Image.open(SOURCE / f"q{number:03}.jpg").convert("RGB")
        image.thumbnail((1700, 950))
        card = Image.new("RGB", (1740, 1020), "white")
        card.paste(image, (20, 50))
        ImageDraw.Draw(card).text((20, 15), f"QUESTION {number}", fill="red")
        cards.append(card)
    sheet = Image.new("RGB", (1740, 1020 * len(cards)), "white")
    for index, card in enumerate(cards):
        sheet.paste(card, (0, index * 1020))
    sheet.save(OUTPUT / f"sheet-{sheet_no:02}.jpg", quality=92)
print(len(list(OUTPUT.glob('*.jpg'))))
