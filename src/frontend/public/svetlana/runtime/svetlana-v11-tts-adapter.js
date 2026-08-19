/* Svetlana v11.0 — AI/TTS adapter + deterministic integration harness */
(function(){
  'use strict';
  const VERSION='11.0.0';
  const providers=new Map();
  const tests=[];

  function register(name, provider){
    if(!name || !provider || typeof provider.synthesize!=='function') throw new Error('invalid_provider');
    providers.set(String(name), provider);
  }

  async function synthesize(req){
    const name=String(req?.provider||'default');
    const provider=providers.get(name);
    if(!provider) throw new Error('tts_provider_not_registered:'+name);
    const result=await provider.synthesize({
      text:String(req?.text||''),
      voice:req?.voice||null,
      locale:req?.locale||'ru-RU',
      signal:req?.signal
    });
    if(!result || (!result.audioUrl && !result.audioBlob)) throw new Error('tts_provider_returned_no_audio');
    return {...result, provider:name};
  }

  function normalizeAI(response){
    return {
      text:String(response?.text||''),
      emotion:String(response?.emotion||'neutral'),
      phonemes:Array.isArray(response?.phonemes)?response.phonemes:[],
      metadata:(response?.metadata && typeof response.metadata==='object')?response.metadata:{}
    };
  }

  async function speak(response, opts={}){
    const ai=normalizeAI(response);
    const tts=await synthesize({
      provider:opts.provider||'default',
      text:ai.text,
      voice:opts.voice,
      locale:opts.locale||'ru-RU',
      signal:opts.signal
    });
    const payload={
      id:opts.id||`turn-${Date.now()}`,
      text:ai.text,
      emotion:ai.emotion,
      phonemes:ai.phonemes,
      metadata:ai.metadata,
      tts:{audioUrl:tts.audioUrl||null,audioBlob:tts.audioBlob||null,phonemes:ai.phonemes,emotion:ai.emotion}
    };
    return window.SvetlanaBridge.enqueue(payload);
  }

  function test(name, fn){ tests.push({name,fn}); }

  async function runTests(){
    const results=[];
    for(const t of tests){
      const started=performance.now();
      try{
        await t.fn();
        results.push({name:t.name,ok:true,ms:Math.round(performance.now()-started)});
      }catch(e){
        results.push({name:t.name,ok:false,error:String(e?.message||e),ms:Math.round(performance.now()-started)});
      }
    }
    return results;
  }

  // Deterministic tests: no network, no secrets, no real TTS.
  test('AI normalization',()=>{
    const x=normalizeAI({text:'Привет',emotion:'smile',phonemes:[{p:'a',t:0}]});
    if(x.text!=='Привет'||x.emotion!=='smile'||x.phonemes.length!==1) throw new Error('normalize_failed');
  });
  test('Provider registration',()=>{
    register('__test__',{synthesize:async()=>({audioUrl:'data:audio/wav;base64,AA=='})});
    if(!providers.has('__test__')) throw new Error('provider_registration_failed');
  });
  test('Bridge presence',()=>{
    if(!window.SvetlanaBridge || typeof window.SvetlanaBridge.enqueue!=='function') throw new Error('bridge_missing');
  });

  window.SvetlanaTTSAdapter={version:VERSION,register,synthesize,speak,runTests};
})();
