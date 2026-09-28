import json, re, subprocess
from pathlib import Path
import pypdfium2 as pdfium
from extract_english_text import parse as parse_question_text

ROOT=Path(__file__).resolve().parents[1]
QUESTION_PDF=ROOT/'ข้อสอบจริง/อังกฤษ/ข้อสอบอังกฤษ.pdf'
ANSWER_PDF=ROOT/'ข้อสอบจริง/อังกฤษ/Copy of 01. เฉลยละเอียดภาษาอังกฤษv.1.pdf'
EXTRACT_PDF=ROOT/'ข้อสอบจริง/อังกฤษ/ข้อสอบอังกฤษ Extract.pdf'
Q_ASSETS=ROOT/'assets/real-english'
A_ASSETS=ROOT/'assets/real-english-explanations'
TMP=ROOT/'tmp/english-build'
TESSERACT=Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')
TESSDATA=ROOT/'tmp/tessdata'

question_ranges=[
 range(1,4),range(4,8),range(8,11),range(11,14),range(14,17),range(17,20),range(20,23),range(23,26),
 range(26,30),range(30,34),range(34,38),range(38,43),range(43,47),range(47,51),range(51,55),range(55,59),
 range(59,63),range(63,67),range(67,71),range(71,75),range(75,79),range(79,82),range(82,84),range(84,86),
 range(86,87),range(87,88),range(88,89),range(89,90),range(90,91),range(91,92),range(92,93),range(93,94),
 range(94,95),range(95,96),range(96,97),range(97,98),range(98,99),range(99,100),range(100,101)
]
answer_keys=[
2,2,2,3,2, 2,4,3,2,2, 1,4,2,2,3, 4,2,3,2,3,
2,1,3,1,3, 2,1,3,1,2, 3,1,1,2,3, 1,1,2,2,4,
1,2,1,2,4, 3,4,1,1,3, 1,4,4,4,3, 2,2,1,3,2,
4,3,2,1,3, 4,2,1,2,3, 1,1,2,1,2, 3,4,4,2,2,
2,2,3,2,2, 4,1,2,4,3, 3,2,2,2,4, 3,2,3,2,3]

def run_tsv(image_path, output_base):
    subprocess.run([str(TESSERACT),str(image_path.relative_to(ROOT)),str(output_base.relative_to(ROOT)),'-l','tha+eng','--tessdata-dir',str(TESSDATA.relative_to(ROOT)),'--psm','6','tsv'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def rows(tsv):
    out=[]
    for row in tsv.read_text(encoding='utf-8',errors='ignore').splitlines()[1:]:
        c=row.split('\t')
        if len(c)>=12: out.append({'left':int(c[6]),'top':int(c[7]),'text':c[11].strip()})
    return out

def grouped_rows(tsv):
    groups={}
    for row in tsv.read_text(encoding='utf-8',errors='ignore').splitlines()[1:]:
        c=row.split('\t')
        if len(c)<12: continue
        key=tuple(c[2:5])
        groups.setdefault(key,[]).append({'left':int(c[6]),'top':int(c[7]),'text':c[11].strip()})
    return list(groups.values())

def starts_for(tsv,numbers,height):
    found={}
    for r in rows(tsv):
        m=re.fullmatch(r'(\d{1,3})[.,]?',r['text'])
        if not m: continue
        n=int(m.group(1))
        # The question number begins near x=330; answer choices begin farther right.
        if n in numbers and r['left']<390 and r['top']>120 and (n not in found or r['top']<found[n]): found[n]=r['top']
    known=sorted(found.items())
    for n in numbers:
        if n in found: continue
        before=[x for x in known if x[0]<n]; after=[x for x in known if x[0]>n]
        if before and after:
            k1,y1=before[-1];k2,y2=after[0];found[n]=round(y1+(y2-y1)*(n-k1)/(k2-k1))
        elif before and len(before)>1:
            k1,y1=before[-1];k0,y0=before[-2];found[n]=min(height-150,round(y1+(y1-y0)*(n-k1)/(k1-k0)))
        elif after and len(after)>1:
            k2,y2=after[0];k3,y3=after[1];found[n]=max(160,round(y2-(y3-y2)*(k2-n)/(k3-k2)))
        else:
            pos=n-min(numbers);found[n]=round(190+(height-330)*pos/len(numbers))
    return found

def answer_starts(tsv):
    found={}
    for group in grouped_rows(tsv):
        text=''.join(r['text'] for r in group)
        m=re.match(r'\s*(\d{1,3})[.,]?\s*เฉ[ลอ]ย',text)
        if not m: continue
        n=int(m.group(1));top=min(r['top'] for r in group)
        if 1<=n<=100 and top>120: found[n]=top
    return found

def crop_page(image,starts,numbers,target,kind):
    ordered=sorted((starts[n],n) for n in numbers)
    for i,(top,n) in enumerate(ordered):
        bottom=ordered[i+1][0]-45 if i+1<len(ordered) else image.height-80
        margin=120 if kind=='question' else 70
        crop=image.crop((70,max(80,top-margin),image.width-55,max(top+180,bottom)))
        crop.save(target/f'q{n:03}.jpg',quality=91,optimize=True)

def build():
    Q_ASSETS.mkdir(parents=True,exist_ok=True);A_ASSETS.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
    qdoc=pdfium.PdfDocument(str(QUESTION_PDF)); years={}
    for page_index,nrange in enumerate(question_ranges):
        image=qdoc[page_index].render(scale=2.5).to_pil().convert('RGB');jpg=TMP/f'qpage-{page_index+1:03}.jpg'
        if not jpg.exists(): image.save(jpg,quality=92)
        base=TMP/f'qpage-{page_index+1:03}'
        if not base.with_suffix('.tsv').exists(): run_tsv(jpg,base)
        numbers=list(nrange);starts=starts_for(base.with_suffix('.tsv'),numbers,image.height)
        crop_page(image,starts,numbers,Q_ASSETS,'question')
        page_rows=rows(base.with_suffix('.tsv'))
        ordered=sorted((starts[n],n) for n in numbers)
        for i,(top,n) in enumerate(ordered):
            bottom=ordered[i+1][0] if i+1<len(ordered) else image.height
            text=' '.join(r['text'] for r in page_rows if top-30<=r['top']<bottom)
            matches=re.findall(r'(?:ปี\s*)?(6[5-9])\)?',text)
            years[n]=2560+int(matches[-1][-1]) if matches else 'หลายปี'
    adoc=pdfium.PdfDocument(str(ANSWER_PDF))
    explanation_numbers=set()
    for page_index in range(3,35):
        image=adoc[page_index].render(scale=2.5).to_pil().convert('RGB');jpg=TMP/f'apage-{page_index+1:03}.jpg'
        if not jpg.exists(): image.save(jpg,quality=92)
        base=TMP/f'apage-{page_index+1:03}'
        if not base.with_suffix('.tsv').exists(): run_tsv(jpg,base)
        starts=answer_starts(base.with_suffix('.tsv'));numbers=sorted(starts)
        if not numbers: raise RuntimeError(f'ไม่พบหัวเฉลยในหน้า {page_index+1}')
        crop_page(image,starts,numbers,A_ASSETS,'answer')
        explanation_numbers.update(numbers)
    missing=set(range(1,101))-explanation_numbers
    if missing: raise RuntimeError(f'เฉลยละเอียดไม่ครบ: {sorted(missing)}')
    questions=[]
    for n,answer in enumerate(answer_keys,1):
        text=parse_question_text(n)
        if not text['parsed'] or set(text['choices'])!=set('ABCD'): raise RuntimeError(f'อ่านข้อความข้อ {n} ไม่ครบ')
        questions.append({'id':f'actual-guru-english-{n:03}','subject':'english','question_number':n,
        'question_text':text['question'],'reading_passage':text.get('reading_passage'),'question_image':f'assets/real-english/q{n:03}.jpg' if 81<=n<=87 else None,'image_alt':f'ภาพประกอบข้อสอบจริงภาษาอังกฤษ ข้อ {n}' if 81<=n<=87 else None,
        'choices':text['choices'],'correct_answer':'ABCD'[answer-1],'source_answer':f'{"ABCD"[answer-1]}. {text["choices"]["ABCD"[answer-1]]}',
        'explanation_th':['ดูคำแปลและคำอธิบายละเอียดจากภาพเฉลยด้านล่าง'],'explanation_image':f'assets/real-english-explanations/q{n:03}.jpg',
        'explanation_author':'source','answer_key_type':'document_answer_key','answer_verified':True,'official_answer_verified':False,'choices_verified':True,
        'year':years[n],'exam_track':'รวมทุกสาย','provider':'guru-police','source_id':'local-guru-actual-english-extract','source_name':'Guru Academy / Guru Police · ข้อสอบจริงภาษาอังกฤษรวมทุกสาย (Extract)',
        'source_locator':f'ข้อ {n}','source_url':None,'explanation_source_id':'local-guru-actual-english-answer','evidence_level':'A','representation':'actual','exact_wording':True,
        'reviewed_at':'2026-09-27','eligible':True,'note':f'รวมทุกสายงาน; ปี {years[n]} ตามที่อ่านได้จากต้นฉบับ','verification_scope':'จับคู่เลขข้อกับหน้าเฉลยรวมท้ายไฟล์และไฟล์เฉลยละเอียด'})
    payload={'sources':[{'id':'local-guru-actual-english','name':'Guru Academy / Guru Police · ข้อสอบจริงภาษาอังกฤษ 100 ข้อ','platform':'local-pdf','url':'ข้อสอบจริง/อังกฤษ/ข้อสอบอังกฤษ.pdf','local':True,'status':'reviewed','note':'ไฟล์ภาพต้นฉบับของโจทย์ 100 ข้อ รวมทุกสายงานและมีเฉลยรวมท้ายไฟล์'},
    {'id':'local-guru-actual-english-extract','name':'Guru Academy / Guru Police · ข้อสอบจริงภาษาอังกฤษ 100 ข้อ (Extract)','platform':'local-pdf','url':'ข้อสอบจริง/อังกฤษ/ข้อสอบอังกฤษ Extract.pdf','local':True,'status':'reviewed','note':'ไฟล์ที่มีชั้นข้อความ ใช้ถอดโจทย์และตัวเลือก แล้วตรวจแก้กับภาพต้นฉบับ; คงภาพเฉพาะข้อป้ายและแผนที่'},
    {'id':'local-guru-actual-english-answer','name':'Guru Academy / Guru Police · เฉลยละเอียดภาษาอังกฤษ','platform':'local-pdf','url':'ข้อสอบจริง/อังกฤษ/Copy of 01. เฉลยละเอียดภาษาอังกฤษv.1.pdf','local':True,'status':'reviewed','note':'ไฟล์เฉลยละเอียดแยก จับคู่ตามเลขข้อ 1–100'}],'questions':questions}
    js='window.POLICE_REAL_ENGLISH_DATA='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n(function(){const x=window.POLICE_REAL_ENGLISH_DATA,d=window.POLICE_DATA;if(!d||!x)return;for(const source of x.sources)if(!d.sources.some(s=>s.id===source.id))d.sources.push(source);const ids=new Set(d.questions.map(q=>q.id));d.questions.push(...x.questions.filter(q=>!ids.has(q.id)));})();\n'
    (ROOT/'police-real-english-data.js').write_text(js,encoding='utf-8')
    print('generated',len(questions),'English questions')

if __name__=='__main__': build()
