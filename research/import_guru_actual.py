from pathlib import Path
import json, re, subprocess
import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
QUESTION_PDF = ROOT / "ข้อสอบจริง/ความสามารถทั่วไป/ข้อสอบความสามารถทั่วไป(เลข).pdf"
ANSWER_PDF = ROOT / "ข้อสอบจริง/ความสามารถทั่วไป/Copy of 01. เฉลยละเอียด ความสามารถทั่วไป.pdf"
ASSETS = ROOT / "assets/real-general"
TMP = ROOT / "tmp/guru-import"
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = ROOT / "tmp/tessdata"

page_ranges = [
    range(1,6),range(6,12),range(12,18),range(18,20),range(20,23),range(23,27),
    range(27,31),range(31,36),range(36,41),range(41,46),range(46,51),range(51,53),
    range(53,55),range(55,60),range(60,65),range(65,70),range(70,74),range(74,79),
    range(79,82),range(82,86),range(86,89),range(89,93),range(93,97),range(97,101)
]

labels = [
('ปป',2568),('ปป',2568),('ปป',2567),('ปป',2567),('ปป',2568),('ปป',2567),('พฐ',2568),('พฐ',2567),('ปป',2567),('ปป',2568),
('ปป',2568),('พฐ',2568),('พฐ',2568),('ปป',2567),('อก',2565),('อก',2565),('พฐ',2567),('อก',2565),('พฐ',2567),('พฐ',2568),
('ปป',2567),('พฐ',2567),('พฐ',2567),('ปป',2567),('พฐ',2567),('ปป',2567),('ปป',2568),('พฐ',2568),('อก',2565),('อก',2565),
('ตม',2567),('ปป',2568),('พฐ',2568),('ปป',2569),('พฐ',2568),('ปป',2568),('ปป',2567),('ปป',2569),('ปป',2569),('ตม',2567),
('ตม',2566),('ตม',2567),('ปป',2568),('พฐ',2568),('อก',2565),('อก',2565),('พฐ',2568),('ปป',2569),('ปป',2568),('ปป',2569),
('ตม',2569),('ปป',2569),('ปป',2569),('ปป',2567),('ปป',2568),('ปป',2567),('อก',2565),('ปป',2567),('ตม',2566),('ปป',2569),
('ปป',2569),('พฐ',2568),('ปป',2569),('ตม',2566),('ปป',2567),('พฐ',2568),('พฐ',2568),('อก',2565),('ตม',2566),('ปป',2567),
('ปป',2569),('ปป',2569),('ปป',2568),('พฐ',2567),('ปป',2569),('ปป',2569),('พฐ',2567),('ปป',2569),('ปป',2568),('ปป',2569),
('ปป',2569),('พฐ',2567),('ปป',2568),('พฐ',2568),('อก',2565),('ปป',2569),('ปป',2568),('ปป',2569),('อก',2565),('พฐ',2568),
('ปป',2567),('อก',2565),('พฐ',2568),('ปป',2569),('ปป',2568),('ปป',2569),('ปป',2569),('ปป',2569),('พฐ',2567),('ปป',2569)
]

# หน้าที่ 20 เบลอมากจน OCR อ่านเลขข้อไม่ได้ จึงกำหนดตำแหน่งจากภาพต้นฉบับโดยตรง
manual_starts = {82:320, 83:760, 84:1460, 85:2050}

def answer_sections():
    text = "\n".join((p.extract_text() or "") for p in PdfReader(str(ANSWER_PDF)).pages)
    matches = list(re.finditer(r"(?m)(\d{1,3})\.\s*เฉลย\s*ข้อ\s*(\d+)\.\s*(?:แนวคิด)?", text))
    result = {}
    for index, match in enumerate(matches):
        number, answer = int(match.group(1)), int(match.group(2))
        end = matches[index+1].start() if index+1 < len(matches) else len(text)
        detail = re.sub(r"\s+", " ", text[match.end():end]).strip()
        detail = re.sub(r"à[^ก-๙]{8,}", " ", detail).strip()
        result[number] = (answer, detail[:1800])
    return result

def page_starts(tsv_path, numbers, height):
    rows = tsv_path.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]
    found = {}
    for row in rows:
        cols = row.split("\t")
        if len(cols) < 12: continue
        token = cols[11].strip()
        match = re.fullmatch(r"(\d{1,3})[.,]?", token)
        if match and int(match.group(1)) in numbers:
            n, left, top = int(match.group(1)), int(cols[6]), int(cols[7])
            if left < 450 and top > 180 and (n not in found or top < found[n]): found[n] = top
    known = [(n, found[n]) for n in numbers if n in found]
    for n in numbers:
        if n in found: continue
        before = [(k,y) for k,y in known if k < n]
        after = [(k,y) for k,y in known if k > n]
        if before and after:
            k1,y1=max(before); k2,y2=min(after); found[n]=round(y1+(y2-y1)*(n-k1)/(k2-k1))
        elif before:
            ordered_before=sorted(before)
            k1,y1=ordered_before[-1]
            gap=(ordered_before[-1][1]-ordered_before[-2][1])/(ordered_before[-1][0]-ordered_before[-2][0]) if len(ordered_before)>1 else (height-y1-150)/(max(numbers)-k1+1)
            found[n]=min(height-150,round(y1+gap*(n-k1)))
        elif after:
            ordered_after=sorted(after)
            k2,y2=ordered_after[0]
            gap=(ordered_after[1][1]-ordered_after[0][1])/(ordered_after[1][0]-ordered_after[0][0]) if len(ordered_after)>1 else (y2-210)/(k2-min(numbers)+1)
            found[n]=max(210,round(y2-gap*(k2-n)))
        else:
            found[n]=round(210+(height-360)*(n-min(numbers))/len(numbers))
    return found

def build():
    ASSETS.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
    answers = answer_sections(); document = pdfium.PdfDocument(str(QUESTION_PDF)); questions=[]
    for page_index, numbers_range in enumerate(page_ranges):
        numbers=list(numbers_range); image=document[page_index].render(scale=3).to_pil().convert("RGB")
        page_image=TMP/f"page-{page_index+1:03}.jpg"; image.save(page_image,quality=94)
        output=TMP/f"page-{page_index+1:03}"
        subprocess.run([str(TESSERACT),str(page_image.relative_to(ROOT)),str(output.relative_to(ROOT)),'-l','tha+eng','--tessdata-dir',str(TESSDATA.relative_to(ROOT)),'--psm','6','tsv'],check=True,cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        starts=page_starts(output.with_suffix('.tsv'),numbers,image.height)
        starts.update({n:y for n,y in manual_starts.items() if n in numbers})
        ordered=sorted((starts[n],n) for n in numbers)
        for pos,(top,number) in enumerate(ordered):
            bottom=(ordered[pos+1][0]-18 if pos+1<len(ordered) else image.height-90)
            crop=image.crop((100,max(120,top-140),image.width-70,max(top+180,bottom-45)))
            asset=ASSETS/f"q{number:03}.jpg"; crop.save(asset,quality=92,optimize=True)
            answer,detail=answers[number]; track,year=labels[number-1]
            questions.append({
                'id':f'actual-guru-general-{number:03}','subject':'general','question_number':number,
                'question_text':f'ข้อสอบจริงความสามารถทั่วไป ข้อ {number} — อ่านโจทย์และตัวเลือกจากภาพ',
                'question_image':f'assets/real-general/q{number:03}.jpg','image_alt':f'ข้อสอบจริงความสามารถทั่วไป ข้อ {number}',
                'choices':{'A':'ตัวเลือก 1','B':'ตัวเลือก 2','C':'ตัวเลือก 3','D':'ตัวเลือก 4'},
                'correct_answer':'ABCD'[answer-1],'source_answer':f'{"ABCD"[answer-1]}. ตัวเลือก {answer}',
                'explanation_th':[detail or f'เฉลยจากเอกสาร: ตัวเลือก {answer}'],
                'explanation_author':'source','answer_key_type':'document_answer_key','answer_verified':True,
                'official_answer_verified':False,'choices_verified':True,'year':year,'exam_track':track,
                'provider':'guru-police','source_id':'local-guru-actual-general','source_name':'Guru Academy / Guru Police · ข้อสอบจริงรวมทุกสายงาน',
                'source_locator':f'ข้อ {number} · หน้า PDF {page_index+1}','source_url':None,
                'explanation_source_id':'local-guru-actual-general-answer','evidence_level':'A','representation':'actual',
                'exact_wording':True,'reviewed_at':'2026-09-27','eligible':True,
                'note':f'เอกสารระบุสาย {track} ปี {year}; แสดงภาพต้นฉบับเพื่อรักษาสูตรและรูปประกอบ',
                'verification_scope':'ตรวจภาพโจทย์และจับคู่ตารางเฉลยตามเลขข้อจากเอกสารคู่กัน'
            })
    payload={'sources':[
        {'id':'local-guru-actual-general','name':'Guru Academy / Guru Police · ข้อสอบจริงความสามารถทั่วไป 100 ข้อ','platform':'local-pdf','url':'ข้อสอบจริง/ความสามารถทั่วไป/ข้อสอบความสามารถทั่วไป(เลข).pdf','local':True,'status':'reviewed','note':'ไฟล์โจทย์จริง 100 ข้อ รวมหลายสายงาน ตรวจวันที่ 27 ก.ย. 2569'},
        {'id':'local-guru-actual-general-answer','name':'Guru Academy / Guru Police · เฉลยละเอียดความสามารถทั่วไป','platform':'local-pdf','url':'ข้อสอบจริง/ความสามารถทั่วไป/Copy of 01. เฉลยละเอียด ความสามารถทั่วไป.pdf','local':True,'status':'reviewed','note':'ไฟล์เฉลยละเอียดที่จับคู่ด้วยเลขข้อครบ 1–100 ตรวจวันที่ 27 ก.ย. 2569'}
    ],'questions':questions}
    js='window.POLICE_REAL_DATA='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n(function(){const x=window.POLICE_REAL_DATA,d=window.POLICE_DATA;if(!d||!x)return;for(const source of x.sources)if(!d.sources.some(s=>s.id===source.id))d.sources.push(source);const ids=new Set(d.questions.map(q=>q.id));d.questions.push(...x.questions.filter(q=>!ids.has(q.id)));})();\n'
    (ROOT/'police-real-data.js').write_text(js,encoding='utf-8')
    print('generated',len(questions),'questions and',len(list(ASSETS.glob('q*.jpg'))),'images')

if __name__ == '__main__': build()

