const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const context = { window: {} };
vm.createContext(context);
for (const file of ['police-data.js', 'police-real-data.js', 'police-real-general-fixes.js', 'police-real-english-data.js', 'police-real-thai-data.js', 'police-law-summary-data.js', 'police-real-law-data.js', 'police-real-computer-data.js', 'police-real-social-data.js', 'police-real-explanation-images.js']) {
  vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
}

const all = context.window.POLICE_DATA.questions;
const actual = all.filter(q => q.representation === 'actual');
const actualGeneral = actual.filter(q => q.subject === 'general');
const actualEnglish = actual.filter(q => q.subject === 'english');
const actualLaw = actual.filter(q => q.subject === 'law');
const actualComputer = actual.filter(q => q.subject === 'it');
const actualSocial = actual.filter(q => q.subject === 'social');
const actualThai = actual.filter(q => q.subject === 'thai');
assert.equal(actual.length, 600, 'must import all 600 usable actual questions');
assert.equal(new Set(actual.map(q => q.id)).size, 600, 'actual IDs must be unique');
assert.deepEqual(Array.from(actualGeneral, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));
assert.deepEqual(Array.from(actualEnglish, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));
assert.deepEqual(Array.from(actualLaw, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));
assert.deepEqual(Array.from(actualComputer, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));
assert.deepEqual(Array.from(actualSocial, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));
assert.deepEqual(Array.from(actualThai, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));

for (const q of actual) {
  assert.ok(['general', 'english', 'thai', 'law', 'it', 'social'].includes(q.subject), `${q.id}: invalid subject`);
  assert.ok(['english', 'thai', 'law', 'it', 'social'].includes(q.subject) ? q.exam_track === 'รวมทุกสาย' : ['ปป', 'พฐ', 'อก', 'ตม'].includes(q.exam_track), `${q.id}: invalid exam track`);
  assert.ok(q.year === 'หลายปี' || (Number.isInteger(q.year) && q.year >= 2558 && q.year <= 2569), `${q.id}: invalid year`);
  assert.deepEqual(Object.keys(q.choices), ['A', 'B', 'C', 'D']);
  assert.ok(['A', 'B', 'C', 'D'].includes(q.correct_answer));
  assert.ok(q.explanation_th.join('').trim().length > 10, `${q.id}: explanation missing`);
  if (q.question_image) assert.ok(fs.existsSync(path.join(root, q.question_image)), `${q.id}: image missing`);
  if (['english', 'thai', 'it', 'law', 'social'].includes(q.subject)) {
    assert.ok(q.explanation_image, `${q.id}: explanation image path missing`);
    assert.ok(fs.existsSync(path.join(root, q.explanation_image)), `${q.id}: explanation image missing`);
  }
  if (q.subject === 'english') {
    assert.ok(q.question_text.length > 10, `${q.id}: question text missing`);
    assert.ok(!Object.values(q.choices).some(v => /^ตัวเลือก [1-4]$/.test(v)), `${q.id}: placeholder choice remains`);
  }
  if (['general', 'thai', 'law', 'it', 'social'].includes(q.subject)) {
    assert.ok(q.question_text.length > 10, `${q.id}: question text missing`);
    assert.ok(!q.question_text.includes('อ่านโจทย์และตัวเลือกจากภาพ'), `${q.id}: image-only prompt remains`);
    assert.ok(!Object.values(q.choices).some(v => /^ตัวเลือก [1-4]$/.test(v)), `${q.id}: placeholder choice remains`);
  }
}

const general38 = actualGeneral.find(q => q.question_number === 38);
assert.equal(general38.question_text, 'ข้อใดต่อไปนี้ถูกต้อง ร้านค้าขายหนังสือ 12 เล่ม ราคา 624 บาท (ปป. ออกล่าสุดปี 69)');
assert.deepEqual(Array.from(Object.values(general38.choices)), ['หนังสือราคาเล่มละ 50 บาท', 'ร้านค้าขายหนังสือ 5 เล่ม ราคา 250 บาท', 'ถ้ามีเงิน 360 บาท จะซื้อหนังสือได้ 7 เล่ม', 'ร้านค้าขายหนังสือ 3 เล่ม ราคา 156 บาท']);

const unusableGeneralText = /ตัวเลือก\s+[A-D1-4]\s+จากโจทย์\s*OCR|คำตอบตามเอกสารเฉลย|เนื้อหาโจทย์ถอดจากไฟล์\s*OCR/i;
for (const question of actualGeneral) {
  assert.ok(!unusableGeneralText.test(question.question_text), `${question.id}: explanation or placeholder remains in question`);
  assert.ok(!Object.values(question.choices).some(choice => unusableGeneralText.test(choice)), `${question.id}: placeholder choice remains`);
  assert.equal(new Set(Object.values(question.choices)).size, 4, `${question.id}: choices must be distinct`);
}
assert.deepEqual(
  Array.from(actualGeneral.filter(q => q.question_image), q => q.question_number),
  [18, 52, 53, 80],
  'only questions that require diagrams or charts should retain question images'
);
const general77 = actualGeneral.find(q => q.question_number === 77);
assert.equal(general77.question_text, 'กำหนดให้ cos A = 5/13 แล้ว tan A มีค่าเท่าใด (ปป.67)');
assert.deepEqual(Array.from(Object.values(general77.choices)), ['2', '2.2', '2.4', '2.6']);
assert.equal(general77.correct_answer, 'C');

for (const number of [36, 38, 39, 40, 44, 96]) {
  const question = actualThai.find(q => q.question_number === number);
  assert.ok(question.question_text.includes('\n'), `actual-guru-thai-${String(number).padStart(3, '0')}: poetry line breaks missing`);
}
assert.equal(actualThai.find(q => q.question_number === 36).question_text.split('\n').filter(Boolean).length, 5, 'Thai question 36 must keep four verse lines plus its prompt');

for (const sourceId of ['local-guru-actual-general', 'local-guru-actual-general-answer', 'local-guru-actual-general-extract', 'local-guru-actual-english', 'local-guru-actual-english-extract', 'local-guru-actual-english-answer', 'local-guru-actual-thai', 'local-guru-actual-thai-answer', 'local-guru-actual-law', 'local-guru-actual-law-answer', 'local-guru-actual-computer', 'local-guru-actual-computer-answer', 'local-guru-actual-social', 'local-guru-actual-social-answer']) {
  assert.ok(context.window.POLICE_DATA.sources.some(s => s.id === sourceId), `${sourceId}: source missing`);
}

const counts = actual.reduce((out, q) => {
  const key = `${q.exam_track}-${q.year}`;
  out[key] = (out[key] || 0) + 1;
  return out;
}, {});
console.log(JSON.stringify({ totalQuestions: all.length, actualQuestions: actual.length, counts }, null, 2));
