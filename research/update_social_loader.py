from pathlib import Path

root = Path(__file__).resolve().parents[1]
for name in ["police_suppression_real_exam_by_subject.html", "evidence.html"]:
    path = root / name
    text = path.read_text(encoding="utf-8")
    if "police-real-general-fixes.js" not in text:
        anchor = '<script src="police-real-data.js?v=20260927-actual100"></script>'
        text = text.replace(anchor, anchor + '<script src="police-real-general-fixes.js?v=20260928-q38"></script>')
    if "police-real-social-data.js" in text:
        text = text.replace("police-real-social-data.js?v=20260928-social-pending", "police-real-social-data.js?v=20260928-social-text100")
    else:
        anchor = '<script src="police-real-thai-data.js?v=20260928-thai-text100"></script>'
        text = text.replace(anchor, anchor + '<script src="police-real-social-data.js?v=20260928-social-text100"></script>')
    text = text.replace("police-app.js?v=20260928-social-pending", "police-app.js?v=20260928-social-text100")
    path.write_text(text, encoding="utf-8")
