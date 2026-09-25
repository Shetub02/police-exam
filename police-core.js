(function(root){
function quotas(subjects,n){const totalWeight=subjects.reduce((sum,s)=>sum+s.quota,0);if(!subjects.length||!totalWeight)return [];const rows=subjects.map(s=>({id:s.id,n:Math.floor(n*s.quota/totalWeight),r:n*s.quota/totalWeight%1}));let left=n-rows.reduce((a,s)=>a+s.n,0);[...rows].sort((a,b)=>b.r-a.r).slice(0,left).forEach(s=>s.n++);return rows;}
function shuffle(xs){const a=[...xs];for(let i=a.length-1;i>0;i--){let j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function normalizeQuestionText(value){return String(value||'').normalize('NFKC').toLowerCase().replace(/คำสั่ง\s*:?\s*choose the best answer\.?/gi,'').replace(/[^\p{L}\p{N}]+/gu,'');}
function questionKey(q){return [q.subject,normalizeQuestionText(q.reading_passage),normalizeQuestionText(q.question_text||q.question)].join('|');}
function preferMixed(p,preferredProvider){
 const all=shuffle(p);if(!preferredProvider)return all;
 const preferred=all.filter(q=>q.provider===preferredProvider),others=all.filter(q=>q.provider!==preferredProvider),out=[];
 while(preferred.length||others.length){if(preferred.length)out.push(preferred.pop());if(preferred.length)out.push(preferred.pop());if(others.length)out.push(others.pop());}
 return out;
}
function ordered(p,{mode='all',preferredProvider,completedIds=[],wrongIds=[]}={}){
 const done=new Set(completedIds),wrong=new Set(wrongIds);
 const groups=mode==='unseen'
  ?[q=>!done.has(q.id),q=>done.has(q.id)]
  :mode==='wrong'
   ?[q=>wrong.has(q.id),q=>!wrong.has(q.id)&&!done.has(q.id),q=>done.has(q.id)&&!wrong.has(q.id)]
   :[()=>true];
 const usedIds=new Set(),usedQuestions=new Set(),out=[];
 for(const match of groups)for(const q of preferMixed(p.filter(match),preferredProvider)){
  const key=questionKey(q);if(!usedIds.has(q.id)&&!usedQuestions.has(key)){usedIds.add(q.id);usedQuestions.add(key);out.push(q);}
 }
 return out;
}
function sampleSmart(pool,subjects,n,options={}){const subject=options.subject||'';if(subject){const candidates=ordered(pool,options);if(candidates.length<n)throw Error('ข้อสอบที่เนื้อหาไม่ซ้ำในตัวเลือกนี้มีไม่พอ กรุณาลดจำนวนข้อ');return shuffle(candidates.slice(0,n));}let out=[];for(const s of quotas(subjects,n)){const candidates=ordered(pool.filter(q=>q.subject===s.id),options);if(candidates.length<s.n)throw Error('ข้อสอบบางวิชาที่มีเนื้อหาไม่ซ้ำมีไม่พอตามสัดส่วน กรุณาเลือกแหล่งอื่นร่วมด้วย หรือลดจำนวนข้อ');out.push(...candidates.slice(0,s.n));}return shuffle(out);}
function sample(pool,subjects,n,subject,preferredProvider){return sampleSmart(pool,subjects,n,{subject,preferredProvider});}
function score(qs,answers){let marked=qs.filter(q=>q.correct_answer&&q.choices);return {total:marked.length,correct:marked.filter(q=>answers[q.id]===q.correct_answer).length,manual:qs.length-marked.length};}
const api={quotas,sample,sampleSmart,questionKey,score};if(typeof module!=='undefined')module.exports=api;else root.PoliceCore=api;
})(typeof window!=='undefined'?window:this);
