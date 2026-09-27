const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const context = { window: {} };
vm.createContext(context);
for (const file of ['police-data.js', 'police-real-data.js']) {
  vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
}

const all = context.window.POLICE_DATA.questions;
const actual = all.filter(q => q.representation === 'actual');
assert.equal(actual.length, 100, 'must import all 100 actual questions');
assert.equal(new Set(actual.map(q => q.id)).size, 100, 'actual IDs must be unique');
assert.deepEqual(Array.from(actual, q => q.question_number), Array.from({ length: 100 }, (_, i) => i + 1));

for (const q of actual) {
  assert.equal(q.subject, 'general');
  assert.ok(['ปป', 'พฐ', 'อก', 'ตม'].includes(q.exam_track), `${q.id}: invalid exam track`);
  assert.ok([2565, 2566, 2567, 2568, 2569].includes(q.year), `${q.id}: invalid year`);
  assert.deepEqual(Object.keys(q.choices), ['A', 'B', 'C', 'D']);
  assert.ok(['A', 'B', 'C', 'D'].includes(q.correct_answer));
  assert.ok(q.explanation_th.join('').trim().length > 10, `${q.id}: explanation missing`);
  assert.ok(fs.existsSync(path.join(root, q.question_image)), `${q.id}: image missing`);
}

for (const sourceId of ['local-guru-actual-general', 'local-guru-actual-general-answer']) {
  assert.ok(context.window.POLICE_DATA.sources.some(s => s.id === sourceId), `${sourceId}: source missing`);
}

const counts = actual.reduce((out, q) => {
  const key = `${q.exam_track}-${q.year}`;
  out[key] = (out[key] || 0) + 1;
  return out;
}, {});
console.log(JSON.stringify({ totalQuestions: all.length, actualQuestions: actual.length, counts }, null, 2));
