import * as THREE from './vendor/three/0.179.1/three.module.js';
import { GLTFLoader } from './vendor/three/0.179.1/examples/jsm/loaders/GLTFLoader.js';

// v4.0: use the native morph names authored into the GLB. No synthetic 31-target layer.
const CAP={blink_L:.82,blink_R:.82,browUp_L:.55,browUp_R:.55,jawOpen:.48,mouthOpen:.44,mouthSmile_L:.42,mouthSmile_R:.42,mouthPucker:.46,mouthFunnel:.36,mouthClose:.55};
const VIS={
 a:{jawOpen:.38,mouthOpen:.26}, ya:{jawOpen:.34,mouthOpen:.24},
 e:{mouthOpen:.18,mouthSmile_L:.08,mouthSmile_R:.08}, ye:{mouthOpen:.16,mouthSmile_L:.07,mouthSmile_R:.07},
 i:{mouthOpen:.12,mouthSmile_L:.10,mouthSmile_R:.10}, y:{mouthOpen:.13,mouthFunnel:.10},
 o:{jawOpen:.22,mouthOpen:.20,mouthPucker:.34}, yo:{jawOpen:.20,mouthOpen:.18,mouthPucker:.30},
 u:{mouthPucker:.38,mouthFunnel:.22,mouthOpen:.08}, yu:{mouthPucker:.34,mouthFunnel:.20,mouthOpen:.08},
 m:{mouthClose:.42,mouthPucker:.05},b:{mouthClose:.42,mouthPucker:.05},p:{mouthClose:.42,mouthPucker:.05},
 v:{mouthFunnel:.22,mouthOpen:.06},f:{mouthFunnel:.22,mouthOpen:.06},
 s:{mouthFunnel:.10,mouthOpen:.08},z:{mouthFunnel:.10,mouthOpen:.08},
 sh:{mouthPucker:.20,mouthFunnel:.13},zh:{mouthPucker:.20,mouthFunnel:.13},shch:{mouthPucker:.18,mouthFunnel:.12},
 l:{mouthOpen:.08,mouthFunnel:.08},t:{mouthOpen:.10,mouthClose:.10},d:{mouthOpen:.10,mouthClose:.10},
 k:{jawOpen:.12,mouthOpen:.10},g:{jawOpen:.12,mouthOpen:.10},n:{mouthOpen:.07,mouthClose:.08},r:{mouthOpen:.09,mouthFunnel:.07}
};

class SvetlanaAvatar{
 constructor(root){
  this.root=root;this.scene=new THREE.Scene();this.scene.background=new THREE.Color(0x10131a);
  this.camera=new THREE.PerspectiveCamera(28,1,.01,20);this.camera.position.set(0,.58,2.55);this.camera.lookAt(0,.62,0);
  this.renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));root.appendChild(this.renderer.domElement);
  this.meshes=[];this.state='idle';this.emotionName='none';this.emotionUntil=0;this.timeline=[];this.audio=null;this.speaking=false;this.speechStart=performance.now();this.timelineDuration=0;
  this.look={x:0,y:0,tx:0,ty:0};this.nextBlink=performance.now()+2400;this.blinkEnd=0;this.demoTimers=[];this.loaded=false;this.conversationRun=0;this.userHidden=false;this.queue=[];this.queueActive=false;this.queueToken=0;this.stateListeners=new Set();this.audioGeneration=0;this.lastStateAt=performance.now();
  this.scene.add(new THREE.HemisphereLight(0xffffff,0x202536,1.8));const key=new THREE.DirectionalLight(0xffffff,2.1);key.position.set(1.4,1.8,2.8);this.scene.add(key);
  addEventListener('resize',()=>this.resize());this.resize();this.animate();
 }
 resize(){const r=this.root.getBoundingClientRect();this.camera.aspect=r.width/Math.max(1,r.height);this.camera.updateProjectionMatrix();this.renderer.setSize(r.width,r.height,false)}
 async load(){const gltf=await new GLTFLoader().loadAsync('./model_base.glb');this.model=gltf.scene;this.scene.add(this.model);this.model.traverse(o=>{if(o.isMesh&&o.morphTargetInfluences&&o.morphTargetDictionary)this.meshes.push(o)});if(!this.meshes.length)throw Error('Native morph targets not found');const names=new Set();for(const m of this.meshes)Object.keys(m.morphTargetDictionary).forEach(n=>names.add(n));this.nativeMorphNames=[...names];this.loaded=true;this.setState('idle');const v=document.getElementById('vis');if(v)v.textContent='Native morphs: '+this.nativeMorphNames.join(' · ')}
 setState(s,meta={}){const prev=this.state;this.state=s;this.lastStateAt=performance.now();const labels={idle:'Светлана · спокойна',listen:'Светлана · слушает',think:'Светлана · думает',speak:'Светлана · говорит'};const t=document.getElementById('state');if(t)t.textContent=labels[s]||s;this.root.dataset.state=s;const detail={state:s,previous:prev,at:this.lastStateAt,...meta};this.root.dispatchEvent(new CustomEvent('svetlana-state',{detail}));for(const fn of this.stateListeners){try{fn(detail)}catch(e){console.error(e)}}}
 onState(fn){if(typeof fn==='function')this.stateListeners.add(fn);return()=>this.stateListeners.delete(fn)}
_emit(type,detail={}){this.root.dispatchEvent(new CustomEvent('svetlana:'+type,{detail}))}
setEmotion(e,d=1800){this.emotionName=e||'none';this.emotionUntil=performance.now()+Math.max(1,d);return e}
 setLook(x,y){this.look.tx=THREE.MathUtils.clamp(Number(x)||0,-.7,.7);this.look.ty=THREE.MathUtils.clamp(Number(y)||0,-.4,.4)}
 lookAt(x,y){this.setLook(x,y)}
 _normalizeTimeline(items,durationMs=null){const out=(items||[]).map(x=>({t:Number(x.t??x.start??0),d:Math.max(35,Number(x.d ?? (((x.end ?? 0) - (x.start ?? 0)) || 80))),p:String(x.phoneme||x.p||x.v||'').toLowerCase()})).filter(x=>Number.isFinite(x.t)&&x.p).sort((a,b)=>a.t-b.t);const end=out.reduce((m,x)=>Math.max(m,x.t+x.d),0);if(durationMs&&end>0&&Math.abs(durationMs-end)>durationMs*.08){const scale=durationMs/end;for(const x of out){x.t*=scale;x.d*=scale}}return out}
 setTimeline(items,durationMs=null){this.speechStart=performance.now();this.timeline=this._normalizeTimeline(items,durationMs);this.timelineDuration=this.timeline.reduce((m,x)=>Math.max(m,x.t+x.d),0);this.speaking=this.timeline.length>0;if(this.speaking)this.setState('speak');return this.timeline.length}
 setPhonemeTimeline(items,durationMs=null){return this.setTimeline(items,durationMs)}
 setVisemeTimeline(items,durationMs=null){return this.setTimeline(items,durationMs)}
 _safeAudioUrl(url){if(!url)return null;try{const u=new URL(url,location.href);if(u.protocol==='blob:'||u.protocol==='data:')return u.href;if(u.origin===location.origin)return u.href;return null}catch{return null}}
 playTTS(packet={}){this.stop({keepQueue:true,reason:'replace'});const generation=++this.audioGeneration;if(packet.emotion)this.setEmotion(packet.emotion,packet.emotionDuration||2500);const tl=packet.phonemes||packet.timeline||[];const safeUrl=this._safeAudioUrl(packet.audioUrl);const finish=(reason='ended')=>{if(generation!==this.audioGeneration)return;this.speaking=false;this.timeline=[];this.timelineDuration=0;this.audio=null;this.setState('idle',{reason});this._emit('speech-end',{reason});this._drainQueue()};if(safeUrl){const a=new Audio();a.preload='auto';a.crossOrigin='anonymous';this.audio=a;this._emit('speech-start',{source:'audio',audioUrl:safeUrl});a.onloadedmetadata=()=>{if(generation!==this.audioGeneration)return;this.setTimeline(tl,a.duration*1000)};a.onplay=()=>{if(generation!==this.audioGeneration)return;this.speaking=true;this.setState('speak',{source:'audio'});this._emit('speech-playing')};a.onpause=()=>{if(generation!==this.audioGeneration)return;if(!a.ended){this.speaking=false;this.setState('think',{reason:'paused'})}};a.onended=()=>finish('ended');a.onerror=()=>finish('error');a.src=safeUrl;a.load();a.play().catch(()=>{if(generation===this.audioGeneration){this.setState('think',{reason:'autoplay-blocked'});this._emit('speech-error',{reason:'autoplay-blocked'})}})}else if(tl.length){this._emit('speech-start',{source:'timeline'});this.setTimeline(tl,packet.durationMs||null);this.setState('speak',{source:'timeline'})}else{this.setState('think',{reason:'no-audio'});this._emit('speech-error',{reason:'no-audio'})}return true}
 pause(){if(this.audio)this.audio.pause();this._emit('speech-pause')}
 resume(){if(this.audio){this.audio.play().then(()=>{this.speaking=true;this.setState('speak',{source:'audio'});this._emit('speech-resume')}).catch(()=>{})}}
 stop(options={}){++this.conversationRun;++this.audioGeneration;for(const id of this.demoTimers)clearTimeout(id);this.demoTimers=[];if(this.audio){this.audio.onended=null;this.audio.onpause=null;this.audio.onerror=null;this.audio.onloadedmetadata=null;this.audio.onplay=null;this.audio.pause();this.audio.removeAttribute('src');this.audio.load();this.audio=null}this.timeline=[];this.timelineDuration=0;this.speaking=false;this.setState('idle',{reason:options.reason||'stop'});if(!options.keepQueue)this._clearQueue();this._emit('speech-stop',{reason:options.reason||'stop'})}
 reset(){this.stop({reason:'reset'});this.setLook(0,0);this.setEmotion('none',1);this.nextBlink=performance.now()+2200;this.blinkEnd=0;this._clearQueue()}
_clearQueue(){this.queue=[];this.queueActive=false;this.queueToken++}
_enqueue(item){this.queue.push(item);this._emit('queue',{length:this.queue.length});this._drainQueue()}
async _drainQueue(){
  if(this.queueActive||!this.queue.length)return;
  this.queueActive=true;
  const token=this.queueToken;
  const item=this.queue.shift();
  this._emit('queue-start',{length:this.queue.length});
  try{ await this._runConversation(item,token); }
  finally{
    if(token===this.queueToken){
      this.queueActive=false;
      this._emit('queue-idle',{length:this.queue.length});
      if(this.queue.length)this._drainQueue();
    }
  }
}
_runConversation(item,token){
  return new Promise(resolve=>{
    const listenMs=Math.max(0,Number(item.listenMs??650));
    const thinkMs=Math.max(0,Number(item.thinkMs??500));
    const run=++this.conversationRun;
    this.setState('listen',{queued:true});
    this.setLook(0,0);
    const done=()=>{if(token!==this.queueToken||run!==this.conversationRun)return resolve();resolve();};
    this.demoTimers.push(setTimeout(()=>{
      if(token!==this.queueToken||run!==this.conversationRun)return done();
      this.setState('think',{queued:true});
      this.setLook(Number(item.lookX??.12),Number(item.lookY??-.03));
      this.demoTimers.push(setTimeout(()=>{
        if(token!==this.queueToken||run!==this.conversationRun)return done();
        const packet=item.tts||item.speech;
        if(packet){
          const once=e=>{
            if(['ended','error','no-audio'].includes(e.detail?.reason)){
              this.root.removeEventListener('svetlana:speech-end',once);
              done();
            }
          };
          this.root.addEventListener('svetlana:speech-end',once);
          this.playTTS(packet);
        }else{this.setState('idle',{reason:'conversation-no-tts'});done();}
      },thinkMs));
    },listenMs));
  });
}
queueConversation(item){this._enqueue(item);return this.queue.length}
queueConversations(items=[]){for(const item of items)this._enqueue(item);return this.queue.length}
interrupt(){this._clearQueue();this.stop({reason:'interrupt'});return true}
 speakText(text='Здравствуйте! Я Светлана. Я готова помочь вам.'){if(!('speechSynthesis'in window))return false;this.stop();const u=new SpeechSynthesisUtterance(text);u.lang='ru-RU';u.rate=.96;u.pitch=1.02;const voices=speechSynthesis.getVoices();u.voice=voices.find(v=>/^ru(-|$)/i.test(v.lang))||null;let start=0,last=0;u.onstart=()=>{start=performance.now();this.speechStart=start;last=0;this.speaking=true;this.setState('speak');this.timeline=[]};u.onboundary=e=>{const c=[...text][e.charIndex]||'';const p=CHAR[c.toLowerCase()];if(!p)return;const now=performance.now();const t=now-start;const d=Math.max(65,last?t-last:110);last=t;this.timeline.push({t:Math.max(0,t-20),d:d*1.12,p});this.timelineDuration=Math.max(this.timelineDuration,t+d*1.12)};u.onend=()=>{this.speaking=false;this.timeline=[];this.timelineDuration=0;this.setState('idle')};u.onerror=()=>{this.speaking=false;this.timeline=[];this.timelineDuration=0;this.setState('think')};speechSynthesis.speak(u);return true}
 beginConversationDemo(){this.stop();const run=++this.conversationRun;this.setState('listen');this.setLook(0,0);this.demoTimers.push(setTimeout(()=>{if(run!==this.conversationRun)return;this.setState('think');this.setLook(.16,-.04)},1100));this.demoTimers.push(setTimeout(()=>{if(run!==this.conversationRun)return;this.playTTS({audioUrl:'assets/svetlana_tts_smoke_test.wav',phonemes:QA_TIMELINE,emotion:'smile',emotionDuration:4200})},2200));return true}
 conversation({listenMs=1100,thinkMs=1100,tts=null,lookX=.16,lookY=-.04}={}){this.interrupt();this.queueConversation({listenMs,thinkMs,tts,lookX,lookY});return true}
 _currentTime(){if(this.audio)return this.audio.currentTime*1000;return this.speaking?performance.now()-this.speechStart:0}
 _target(){const q={};const now=performance.now();if(this.speaking&&!this.audio&&this.timeline.length){const elapsed=this._currentTime();if(this.timelineDuration>0&&elapsed>=this.timelineDuration+80){this.speaking=false;this.timeline=[];this.timelineDuration=0;this.setState('idle',{reason:'timeline-ended'});this._emit('speech-end',{reason:'timeline-ended'});this._drainQueue();}}this.look.x+=(this.look.tx-this.look.x)*.06;this.look.y+=(this.look.ty-this.look.y)*.06;
  if(this.emotionName==='smile'&&now<this.emotionUntil){q.mouthSmile_L=.30;q.mouthSmile_R=.30}
  if(this.emotionName==='surprise'&&now<this.emotionUntil){q.browUp_L=.22;q.browUp_R=.22;q.mouthOpen=.12}
  if(this.emotionName==='sad'&&now<this.emotionUntil){q.mouthSmile_L=.06;q.mouthSmile_R=.06;q.mouthFunnel=.08}
  
  if(now>this.nextBlink){this.blinkEnd=now+125;this.nextBlink=now+2400+Math.random()*3200}
  if(now<this.blinkEnd){const x=(now-(this.blinkEnd-125))/125;const b=Math.sin(Math.PI*THREE.MathUtils.clamp(x,0,1))*.76;q.blink_L=b;q.blink_R=b*.94}
  if(this.speaking&&this.timeline.length){const t=this._currentTime();let i=-1;for(let j=0;j<this.timeline.length;j++){if(t>=this.timeline[j].t&&t<=this.timeline[j].t+this.timeline[j].d){i=j;break}}if(i>=0){const cur=this.timeline[i],w=VIS[cur.p]||{};const rel=(t-cur.t)/cur.d,fade=.72+.28*Math.sin(Math.PI*THREE.MathUtils.clamp(rel,0,1));for(const[k,v]of Object.entries(w))q[k]=(q[k]||0)+v*fade;if(i>0){const prev=this.timeline[i-1],pw=VIS[prev.p]||{},blend=Math.max(0,1-(t-(prev.t+prev.d))/110)*.12;for(const[k,v]of Object.entries(pw))q[k]=(q[k]||0)+v*blend}}}
  for(const k of Object.keys(q))q[k]=THREE.MathUtils.clamp(q[k],0,CAP[k]??0);return q}
 animate(){requestAnimationFrame(()=>this.animate());const t=performance.now(),q=this._target();for(const m of this.meshes){for(const name of this.nativeMorphNames){const i=m.morphTargetDictionary[name];const target=q[name]||0;const cur=m.morphTargetInfluences[i]||0;m.morphTargetInfluences[i]+=((target)-cur)*.20}}
  const hm=THREE.MathUtils.clamp(this.look.x*.10,-.10,.10),hp=THREE.MathUtils.clamp(this.look.y*.055,-.055,.055);if(this.model){this.model.rotation.y+=(hm-this.model.rotation.y)*.04;this.model.rotation.x+=(hp-this.model.rotation.x)*.04;const idleBob=this.state==='idle'?Math.sin(t/1500)*.0012:Math.sin(t/900)*.0006;this.model.position.y=idleBob}
  this.renderer.render(this.scene,this.camera)}
}

const QA_RAW=[['з',0.00,0.12],['д',0.12,0.11],['р',0.23,0.12],['а',0.35,0.13],['в',0.48,0.11],['с',0.59,0.11],['т',0.70,0.12],['у',0.82,0.13],['й',0.95,0.08],['т',1.03,0.12],['е',1.15,0.13],['я',1.28,0.12],['с',1.40,0.11],['в',1.51,0.11],['е',1.62,0.13],['т',1.75,0.12],['л',1.87,0.11],['а',1.98,0.13],['н',2.11,0.12],['а',2.23,0.13]];
const QA_SCALE=3455/(QA_RAW[QA_RAW.length-1][1]*1000+QA_RAW[QA_RAW.length-1][2]*1000);
const QA_TIMELINE=QA_RAW.map(([p,t,d])=>({t:t*1000*QA_SCALE,d:d*1000*QA_SCALE,phoneme:p}));
window.SvetlanaQA_TIMELINE=QA_TIMELINE;
window.SvetlanaHealth=()=>({
  loaded:!!avatar?.loaded,
  state:avatar?.state||'unknown',
  morphTargets:Array.isArray(avatar?.nativeMorphNames)?avatar.nativeMorphNames.length:0,
  audio:!!avatar?.audio,
  runtime:'svetlana-v13'
});
const root=document.getElementById('stage');const avatar=new SvetlanaAvatar(root);window.SvetlanaAvatar=avatar;window.SvetlanaNativeRig=avatar;
document.querySelectorAll('[data-emotion]').forEach(b=>b.onclick=()=>avatar.setEmotion(b.dataset.emotion,2200));
document.getElementById('speak')?.addEventListener('click',()=>avatar.speakText());
document.getElementById('local')?.addEventListener('click',()=>avatar.playTTS({audioUrl:'assets/svetlana_tts_smoke_test.wav',phonemes:QA_TIMELINE,emotion:'smile',emotionDuration:4200}));
document.getElementById('pause')?.addEventListener('click',()=>avatar.pause());document.getElementById('resume')?.addEventListener('click',()=>avatar.resume());document.getElementById('stop')?.addEventListener('click',()=>avatar.stop());document.getElementById('reset')?.addEventListener('click',()=>avatar.reset());
window.addEventListener('pointermove',e=>avatar.lookAt((e.clientX/innerWidth-.5)*.7,(e.clientY/innerHeight-.5)*-.4));
addEventListener('visibilitychange',()=>{avatar.userHidden=document.hidden;if(document.hidden&&avatar.audio&&!avatar.audio.paused)avatar.audio.pause();avatar._emit('visibility',{hidden:document.hidden})});addEventListener('pagehide',()=>{if(avatar.audio&&!avatar.audio.paused)avatar.audio.pause();avatar._emit('lifecycle',{event:'pagehide'})});addEventListener('pageshow',()=>avatar._emit('lifecycle',{event:'pageshow'}));
window.addEventListener('message',e=>{if(e.source!==window&&e.source!==window.parent)return;if(e.origin!==location.origin)return;if(e.data?.type==='svetlana.tts')avatar.playTTS(e.data)});
window.SvetlanaConversation=(options)=>avatar.conversation(options);
window.SvetlanaQueue={add:(item)=>avatar.queueConversation(item),addMany:(items)=>avatar.queueConversations(items),interrupt:()=>avatar.interrupt(),clear:()=>avatar._clearQueue(),size:()=>avatar.queue.length};
window.SvetlanaEvents={on:(fn)=>avatar.onState(fn),onState:(fn)=>avatar.onState(fn)};
window.SvetlanaQA={set:(mode)=>{avatar.reset();if(mode==='blink'){avatar.blinkEnd=performance.now()+125;avatar.nextBlink=performance.now()+999999}else if(mode==='smile'){avatar.setEmotion('smile',5000)}else if(mode==='surprise'){avatar.setEmotion('surprise',5000)}else if(mode==='speak'){avatar.playTTS({audioUrl:'assets/svetlana_tts_smoke_test.wav',phonemes:QA_TIMELINE,emotion:'smile',emotionDuration:4200})}else if(mode==='listen'){avatar.setState('listen');avatar.setLook(-.15,.02)}else if(mode==='think'){avatar.setState('think');avatar.setLook(.18,-.05)}else if(mode==='lookLeft'){avatar.setLook(-.55,.02)}else if(mode==='lookRight'){avatar.setLook(.55,.02)}},demo:()=>avatar.beginConversationDemo()};
avatar.load().then(()=>{const health=window.SvetlanaHealth?.()||{};window.parent?.postMessage({type:'svetlana.ready',health},'*');const qs=new URLSearchParams(location.search);const qa=qs.get('qa');if(qa)setTimeout(()=>window.SvetlanaQA.set(qa),600);if(qs.get('demo'))setTimeout(()=>window.SvetlanaQA.demo(),700)}).catch(e=>{console.error(e);window.parent?.postMessage({type:'svetlana.error',error:'avatar-load-failed'},'*');document.getElementById('state').textContent='Ошибка загрузки модели'});
