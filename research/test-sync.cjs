const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const core=require('../police-sync-core.js');
const empty=core.empty;
const state=()=>({version:1,history:[{date:'24/9/2569 12:00:00',count:1,correct:1,total:1,manual:0}],attempts:[],session:null});
assert.deepEqual(core.validate(state()),state());
assert.throws(()=>core.validate({...state(),history:[{...state().history[0],date:'<img src=x>'}]}));
assert.throws(()=>core.validate({...state(),session:{ids:[]}}));
assert.equal(core.decision({state:empty(),revision:1,dirty:true},{revision:2,payload:state()}),'conflict');
assert.equal(core.decision({state:state(),revision:1,dirty:true},{revision:2,payload:state()}),'equal');
assert.equal(core.decision({state:empty(),revision:1,dirty:false},{revision:2,payload:state()}),'pull');

async function harness(){
  const listeners={},store=new Map(),nodes=[];let current=empty(),owner=null,auth,remote=null,writes=0,offline=false,race;
  function element(tag){const e={tag,children:[],textContent:'',setAttribute(){},append(...xs){this.children.push(...xs);},replaceChildren(){this.children=[];},after(){},click(){}};nodes.push(e);return e;}
  const bridge={snapshot:()=>structuredClone(current),active:()=>false,apply(s){current=core.validate(s);},switchOwner(id,s){owner=id;this.apply(s);}};
  const client={auth:{onAuthStateChange(fn){auth=fn;},async getSession(){return {data:{session:null}};},async signOut(){auth('SIGNED_OUT',null);return {};},async signInWithOAuth(){return {};}},from(){return {select(){return {eq(){return {async maybeSingle(){if(offline)return {error:Error('offline')};return {data:remote&&structuredClone(remote)};}};}};}};},async rpc(_name,args){writes++;if(offline)return {error:Error('offline')};if(args.expected_revision!==(remote?.revision||0))return {error:Error('PROGRESS_CONFLICT')};remote={revision:(remote?.revision||0)+1,payload:structuredClone(args.new_payload)};if(race){const fn=race;race=null;fn();}return {data:remote.revision};}};
  const document={createElement:element,querySelector:()=>element('header'),head:{append(s){s.onload();}},hidden:false};
  const window={PoliceProgress:bridge,PoliceSyncCore:core,POLICE_SYNC_CONFIG:{url:'https://test.supabase.co',publishableKey:'public-test'},supabase:client,addEventListener(k,f){listeners[k]=f;}};
  window.supabase={createClient:()=>client};
  const context={window,document,localStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),get length(){return store.size;},key:i=>[...store.keys()][i]},location:{href:'https://example.com/police_suppression_real_exam_by_subject.html'},URL,Blob,Date,console,confirm:()=>true,setTimeout:(fn,delay)=>{if(delay===0)queueMicrotask(fn);return 1;},clearTimeout(){},setInterval(){}};
  await vm.runInNewContext(fs.readFileSync(require.resolve('../police-sync.js'),'utf8'),context);
  const settle=()=>new Promise(resolve=>setImmediate(resolve));
  const login=async id=>{auth('SIGNED_IN',{user:{id,email:id+'@example.com'}});await settle();};
  const edit=s=>{bridge.apply(s);listeners['police-progress-change']();};
  const sync=async()=>{await listeners.focus();await settle();};
  const press=async text=>{const b=nodes.filter(x=>x.tag==='button'&&x.textContent===text).at(-1);assert.ok(b,text);b.onclick();await settle();};
  await login('alice');assert.equal(owner,'alice');assert.equal(writes,0);
  edit(state());await sync();assert.equal(writes,1);assert.equal(remote.revision,1);
  remote={revision:2,payload:empty()};edit({...state(),history:[...state().history,...state().history]});await sync();assert.equal(writes,1,'conflict must not write');assert.equal(current.history.length,2);
  await press('ใช้ข้อมูลออนไลน์');assert.equal(current.history.length,0);assert.ok(store.has('police-sync-backup:alice'));
  offline=true;edit(state());await sync();assert.equal(JSON.parse(store.get('police-cloud-cache:alice')).dirty,true);offline=false;await sync();assert.equal(remote.payload.history.length,1);
  edit(empty());race=()=>edit(state());await sync();assert.equal(JSON.parse(store.get('police-cloud-cache:alice')).dirty,true,'edits during upload remain dirty');await sync();assert.equal(JSON.parse(store.get('police-cloud-cache:alice')).dirty,false);
  await press('ออกจากระบบ');assert.equal(owner,null);assert.deepEqual(current,empty());
  remote=null;await login('bob');assert.deepEqual(current,empty(),'another account cannot inherit Alice progress');assert.equal(JSON.parse(store.get('police-cloud-cache:alice')).state.history.length,1);
  console.log('Passed: validation, CAS conflict, backup, offline retry, concurrent edits, logout and account isolation');
}
harness().catch(e=>{console.error(e);process.exitCode=1;});
