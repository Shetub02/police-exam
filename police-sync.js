(async function(){
  'use strict';
  const bridge=window.PoliceProgress,core=window.PoliceSyncCore,config=window.POLICE_SYNC_CONFIG||{};
  const panel=document.createElement('section');panel.className='sync-panel';panel.setAttribute('aria-label','บัญชีและการซิงก์');document.querySelector('header').after(panel);
  let client,user=null,entry=null,busy=false,conflict=null,timer,epoch=0,status='บันทึกในเครื่องนี้';
  const guest=bridge.snapshot();
  const key=id=>'police-cloud-cache:'+id;
  const read=k=>{try{return JSON.parse(localStorage.getItem(k));}catch{return null;}};
  const persist=()=>{if(user&&entry)localStorage.setItem(key(user.id),JSON.stringify(entry));};
  function button(label,fn){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=()=>Promise.resolve().then(fn).catch(fail);return b;}
  function fail(){status='ซิงก์ไม่สำเร็จ ข้อมูลยังอยู่ในเครื่อง ลองใหม่เมื่อเชื่อมต่ออินเทอร์เน็ตได้';render();}
  function backup(){
    const records={exportedAt:new Date().toISOString(),current:bridge.snapshot(),guest};
    for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith('police-cloud-cache:')||k.startsWith('police-sync-backup:'))records[k]=read(k);}
    const url=URL.createObjectURL(new Blob([JSON.stringify(records,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='police-progress-backup.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function retain(){localStorage.setItem('police-sync-backup:'+user.id,JSON.stringify({savedAt:Date.now(),state:bridge.snapshot()}));}
  function summary(state){return `${state.history.length} ผลสอบ · ${state.session?state.session.ids.length:0} ข้อในชุดล่าสุด`;}
  function render(){
    const footer=document.querySelector('footer');if(footer)footer.textContent=user?'พื้นที่ฝึกส่วนตัว · ซิงก์ประวัติผ่านบัญชีของคุณ':'พื้นที่ฝึกส่วนตัว · บันทึกการทำข้อสอบในเบราว์เซอร์เครื่องนี้';
    panel.replaceChildren();const title=document.createElement('b');title.textContent=user?'บัญชี: '+(user.email||'Google'):'เก็บผลสอบไว้ใช้ทุกเครื่อง';panel.append(title);
    const p=document.createElement('p');p.setAttribute('role','status');p.textContent=status;panel.append(p);
    const actions=document.createElement('div');actions.className='actions';panel.append(actions);
    if(!client){p.textContent=config.url?'เชื่อมระบบบัญชีไม่สำเร็จ รีเฟรชเพื่อลองใหม่ · ยังฝึกในเครื่องได้':'ยังไม่เปิดใช้งานบัญชีออนไลน์ · ประวัติเดิมยังบันทึกในเครื่องนี้';actions.append(button('สำรองข้อมูลในเครื่อง',backup));return;}
    if(!user){actions.append(button('เข้าสู่ระบบด้วย Google',async()=>{const {error}=await client.auth.signInWithOAuth({provider:'google',options:{redirectTo:new URL('police_suppression_real_exam_by_subject.html',location.href).href}});if(error)throw error;}));return;}
    if(conflict){
      const note=document.createElement('p');note.textContent='พบข้อมูลต่างกัน: เครื่องนี้ '+summary(entry.state)+' / ออนไลน์ '+summary(conflict.payload)+' เลือกข้อมูลที่ต้องการใช้ (สำรองชุดเดิมให้อัตโนมัติ)';panel.append(note);
      actions.append(button('ใช้ข้อมูลออนไลน์',()=>resolve(false)),button('ใช้ข้อมูลเครื่องนี้',()=>resolve(true)));
    }else{const b=button('ซิงก์ตอนนี้',()=>sync());b.disabled=busy;actions.append(b);}
    actions.append(button('สำรองข้อมูล',backup),button('ออกจากระบบ',async()=>{
      if(busy)return;
      if(entry.dirty&&!confirm('ยังมีข้อมูลที่ไม่ได้ซิงก์ จะเก็บไว้ในเครื่องเพื่อซิงก์เมื่อเข้าบัญชีนี้อีกครั้ง ต้องการออกจากระบบหรือไม่?'))return;
      const {error}=await client.auth.signOut({scope:'local'});if(error)throw error;
    }));
    if(guest.session||guest.history.length){const d=document.createElement('details');const s=document.createElement('summary');s.textContent='นำประวัติเดิมของเครื่องเข้าบัญชี';d.append(s,button('ใช้ประวัติเดิมของเครื่อง',()=>{
      if(busy||!confirm('นำข้อมูลก่อนล็อกอินมาแทนข้อมูลบัญชีที่แสดงอยู่? จะสำรองข้อมูลปัจจุบันไว้ก่อน'))return;
      retain();bridge.apply(guest);entry.state=bridge.snapshot();entry.dirty=true;persist();sync();
    }));panel.append(d);}
  }
  async function resolve(useLocal){
    if(busy||!conflict)return;
    retain();const remote=conflict;conflict=null;
    if(!useLocal){bridge.apply(remote.payload);entry.state=bridge.snapshot();entry.dirty=false;}
    entry.revision=remote.revision;persist();await sync();
  }
  async function sync(){
    if(!user||busy||conflict)return;
    busy=true;const generation=epoch,id=user.id;status='กำลังซิงก์…';render();
    try{
      const {data:remote,error}=await client.from('police_progress').select('revision,payload').eq('user_id',id).maybeSingle();
      if(generation!==epoch)return;if(error)throw error;
      if(remote)core.validate(remote.payload);
      const action=core.decision(entry,remote);
      if(action==='conflict'||(action==='pull'&&bridge.active())){conflict=remote;status='เลือกข้อมูลที่จะใช้ต่อ';return;}
      if(action==='pull'){retain();bridge.apply(remote.payload);entry.state=bridge.snapshot();entry.revision=remote.revision;entry.dirty=false;}
      if(action==='equal'){entry.revision=remote.revision;entry.dirty=false;}
      if(action==='push'){
        const sent=JSON.stringify(entry.state);
        const {data:revision,error:saveError}=await client.rpc('save_police_progress',{expected_revision:entry.revision,new_payload:JSON.parse(sent)});
        if(generation!==epoch)return;
        if(saveError){if(saveError.message?.includes('PROGRESS_CONFLICT')){status='มีข้อมูลใหม่จากอีกเครื่อง กดซิงก์อีกครั้งเพื่อเลือกข้อมูล';return;}throw saveError;}
        entry.revision=revision;entry.dirty=JSON.stringify(entry.state)!==sent;
      }
      persist();status=entry.dirty?'มีข้อมูลใหม่ รอซิงก์':'ซิงก์แล้ว · '+new Date().toLocaleTimeString('th-TH');
    }catch{if(generation===epoch)fail();}
    finally{if(generation===epoch){busy=false;render();}}
  }
  function changeAccount(next){
    if((next?.id||null)===(user?.id||null))return;
    epoch++;busy=false;conflict=null;clearTimeout(timer);user=next;
    if(!user){entry=null;bridge.switchOwner(null,guest);status='ออกจากระบบแล้ว · แสดงข้อมูลเดิมในเครื่อง';render();return;}
    const cached=read(key(user.id));
    entry=cached||{state:core.empty(),revision:0,dirty:false};
    try{core.validate(entry.state);if(!Number.isInteger(entry.revision)||entry.revision<0)throw Error();bridge.switchOwner(user.id,entry.state);}
    catch{user=null;entry=null;bridge.switchOwner(null,guest);status='เปิดข้อมูลบัญชีไม่ได้ กรุณาสำรองข้อมูลและรีเฟรช';render();return;}
    sync();
  }
  window.addEventListener('police-progress-change',()=>{
    if(!user){Object.assign(guest,bridge.snapshot());return;}
    entry.state=bridge.snapshot();entry.dirty=true;
    try{persist();status='บันทึกในเครื่องแล้ว · รอซิงก์';}catch{status='พื้นที่บันทึกเต็ม กรุณาสำรองข้อมูล';}
    render();clearTimeout(timer);timer=setTimeout(sync,900);
  });
  render();
  if(!config.url||!config.publishableKey)return;
  try{
    if(!/^https:\/\//.test(config.url)||config.publishableKey.startsWith('sb_secret_'))throw Error();
    await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.57.4/dist/umd/supabase.js';s.onload=resolve;s.onerror=reject;document.head.append(s);});
    client=window.supabase.createClient(config.url,config.publishableKey);
    client.auth.onAuthStateChange((_event,session)=>setTimeout(()=>changeAccount(session?.user||null),0));
    const {data,error}=await client.auth.getSession();if(error)throw error;changeAccount(data.session?.user||null);render();
    window.addEventListener('online',sync);window.addEventListener('focus',sync);
    setInterval(()=>{if(!document.hidden)sync();},30000);
  }catch(error){console.error('Supabase initialization failed:',error);client=null;render();}
})();
