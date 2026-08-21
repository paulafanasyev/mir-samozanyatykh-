/* CSP-safe host bridge for Svetlana v13. No inline JavaScript is required in index.html. */
(async function(){
  'use strict';

  let OrbitControls=null;
  try{
    ({OrbitControls}=await import('./vendor/three/0.179.1/examples/jsm/controls/OrbitControls.js'));
  }catch(_){ }

  function installControls(){
    const avatar=window.SvetlanaAvatar;
    if(!OrbitControls || !avatar?.camera || !avatar?.renderer?.domElement) return false;
    if(avatar.orbitControls) return true;
    const controls=new OrbitControls(avatar.camera, avatar.renderer.domElement);
    controls.enableDamping=true;
    controls.dampingFactor=0.08;
    controls.enablePan=false;
    controls.minDistance=1.45;
    controls.maxDistance=4.5;
    controls.minPolarAngle=Math.PI*0.31;
    controls.maxPolarAngle=Math.PI*0.67;
    controls.target.set(0,0.62,0);
    controls.update();
    avatar.orbitControls=controls;
    function tick(){ controls.update(); requestAnimationFrame(tick); }
    requestAnimationFrame(tick);
    return true;
  }

  let tries=0;
  const timer=setInterval(function(){
    if(installControls() || ++tries>120) clearInterval(timer);
  },100);

  window.addEventListener('message',function(e){
    if(e.origin!==location.origin && e.origin!=='null') return;
    const m=e.data||{};
    try{
      if(m.type==='svetlana.command') window.SvetlanaHost?.command(m.payload||{});
      if(m.type==='svetlana.speak') window.SvetlanaHost?.command({type:'ai.speech',payload:m.payload||{}});
      if(m.type==='svetlana.emotion') window.SvetlanaHost?.command({type:'avatar.emotion',name:m.name,duration:m.duration});
      if(m.type==='svetlana.stop') window.SvetlanaHost?.command({type:'avatar.stop'});
    }catch(_){ }
  });

  window.addEventListener('load',function(){
    document.getElementById('demo')?.addEventListener('click',function(){window.SvetlanaQA?.demo();});
    document.getElementById('queueDemo')?.addEventListener('click',function(){
      window.SvetlanaQueue?.addMany?.([
        {listenMs:700,thinkMs:500,tts:{audioUrl:'assets/svetlana_tts_smoke_test.wav',phonemes:window.SvetlanaQA_TIMELINE||[],emotion:'smile',emotionDuration:3600}},
        {listenMs:650,thinkMs:450,tts:{audioUrl:'assets/svetlana_tts_smoke_test.wav',phonemes:window.SvetlanaQA_TIMELINE||[],emotion:'none',emotionDuration:1800}}
      ]);
    });
  });

  window.parent?.postMessage({type:'svetlana.ready'},location.origin);
})();
