const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const context = { window: {} };
vm.createContext(context);
for (const file of ['police-data.js', 'police-real-data.js', 'police-real-english-data.js']) {
  vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
}

const all = context.window.POLICE_DATA.questions;
const actual = all.filter(q => q.representation === 'actual');
const actualGeneral = actual.filter(q => q.subject === 'general');
const actualEnglish = actual.filter(q => q.subject === 'english');
assert.equal(actual.length, 200, 'must import all 200 actual questions');
assert.equal(new Set(actual.map(q => q.id)).size, 200, 'actual IDs must be unique');
assert.deepEqual(Array.from(actualGeneral, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));
assert.deepEqual(Array.from(actualEnglish, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));

for (const q of actual) {
  assert.ok(['general', 'english'].includes(q.subject), `${q.id}: invalid subject`);
  assert.ok(q.subject === 'english' ? q.exam_track === 'รวมทุกสาย' : ['ปป', 'พฐ', 'อก', 'ตม'].includes(q.exam_track), `${q.id}: invalid exam track`);
  assert.ok(q.year === 'หลายปี' || [2565, 2566, 2567, 2568, 2569].includes(q.year), `${q.id}: invalid year`);
  assert.deepEqual(Object.keys(q.choices), ['A', 'B', 'C', 'D']);
  assert.ok(['A', 'B', 'C', 'D'].includes(q.correct_answer));
  assert.ok(q.explanation_th.join('').trim().length > 10, `${q.id}: explanation missing`);
  if (q.question_image) assert.ok(fs.existsSync(path.join(root, q.question_image)), `${q.id}: image missing`);
  if (q.subject === 'english') assert.ok(fs.existsSync(path.join(root, q.explanation_image)), `${q.id}: explanation image missing`);
  if (q.subject === 'english') {
    assert.ok(q.question_text.length > 10, `${q.id}: question text missing`);
    assert.ok(!Object.values(q.choices).some(v => /^ตัวเลือก [1-4]$/.test(v)), `${q.id}: placeholder choice remains`);
  }
}

for (const sourceId of ['local-guru-actual-general', 'local-guru-actual-general-answer', 'local-guru-actual-english', 'local-guru-actual-english-extract', 'local-guru-actual-english-answer']) {
  assert.ok(context.window.POLICE_DATA.sources.some(s => s.id === sourceId), `${sourceId}: source missing`);
}

const counts = actual.reduce((out, q) => {
  const key = `${q.exam_track}-${q.year}`;
  out[key] = (out[key] || 0) + 1;
  return out;
}, {});
console.log(JSON.stringify({ totalQuestions: all.length, actualQuestions: actual.length, counts }, null, 2));
