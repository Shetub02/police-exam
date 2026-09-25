(function(root){
  'use strict';
  const object=x=>!!x&&typeof x==='object'&&!Array.isArray(x);
  const finite=x=>Number.isFinite(x)&&x>=0;
  const ids=x=>Array.isArray(x)&&x.length<=2000&&x.every(id=>typeof id==='string'&&/^[\w-]+$/.test(id))&&new Set(x).size===x.length;
  const answers=x=>object(x)&&Object.entries(x).every(([k,v])=>/^[\w-]+$/.test(k)&&typeof v==='string'&&v.length<=1000);
  const score=x=>object(x)&&finite(x.correct)&&finite(x.total)&&x.correct<=x.total&&finite(x.manual)&&typeof x.date==='string'&&/^[\d\s/:.,-]+$/.test(x.date);
  function validate(s){
    if(!object(s)||s.version!==1||!Array.isArray(s.history)||s.history.length>30||!s.history.every(x=>score(x)&&finite(x.count))||!Array.isArray(s.attempts)||s.attempts.length>30||!s.attempts.every(x=>score(x)&&ids(x.ids)&&answers(x.answers)))throw Error('ข้อมูลความคืบหน้าไม่รองรับ กรุณาอัปเดตเว็บทั้งสองเครื่อง');
    const q=s.session;
    if(q!==null&&(!object(q)||!ids(q.ids)||!q.ids.length||!answers(q.answers)||!ids(q.flags)||!q.flags.every(id=>q.ids.includes(id))||!Number.isInteger(q.index)||q.index<0||q.index>=q.ids.length||!finite(q.remaining)||!finite(q.deadline)||!finite(q.created)||typeof q.paused!=='boolean'||typeof q.finished!=='boolean'))throw Error('ข้อมูลชุดข้อสอบไม่สมบูรณ์');
    return JSON.parse(JSON.stringify(s));
  }
  function decision(local,remote){
    if(!remote)return local.dirty?'push':'idle';
    if(remote.revision===local.revision)return local.dirty?'push':'idle';
    if(JSON.stringify(local.state)===JSON.stringify(remote.payload))return 'equal';
    return local.dirty?'conflict':'pull';
  }
  const api={validate,decision,empty:()=>({version:1,history:[],attempts:[],session:null})};
  if(typeof module!=='undefined')module.exports=api;else root.PoliceSyncCore=api;
})(typeof window==='undefined'?this:window);
