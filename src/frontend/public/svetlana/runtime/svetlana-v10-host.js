/* Svetlana Avatar v10.0 — production AI/TTS host protocol */
(function () {
  'use strict';
  const VERSION = '10.0.0';

  function emit(type, detail={}) {
    const payload = {type, version:VERSION, time:Date.now(), ...detail};
    try { window.dispatchEvent(new CustomEvent('svetlana:host',{detail:payload})); } catch (_) {}
    try { window.SvetlanaBridge?.emit?.(type,payload); } catch (_) {}
    return payload;
  }

  function safeUrl(url) {
    if (!url) return null;
    try {
      const u = new URL(String(url), location.href);
      if (u.protocol === 'blob:' || u.protocol === 'data:' || u.origin === location.origin) return u.href;
    } catch (_) {}
    return null;
  }

  function enqueueSpeech(payload={}) {
    const p = {...payload};
    if (p.tts) p.tts = {...p.tts, audioUrl:safeUrl(p.tts.audioUrl)};
    else if (p.audioUrl) p.audioUrl = safeUrl(p.audioUrl);
    const requestId = String(p.requestId || `speech-${Date.now()}-${Math.random().toString(36).slice(2,7)}`);
    p.requestId = requestId;
    emit('host-speech-request',{requestId,payload:p});
    const runtimeId = window.SvetlanaBridge?.enqueue?.(p);
    emit('host-speech-accepted',{requestId,runtimeId});
    return {requestId,runtimeId};
  }

  function command(message) {
    if (!message || typeof message !== 'object') throw new Error('invalid_command');
    switch(message.type) {
      case 'ai.speech': return enqueueSpeech(message.payload || {});
      case 'ai.cancel':
        window.SvetlanaBridge?.interrupt?.(message.reason || 'user');
        return true;
      case 'ai.stream.chunk': emit('host-stream-chunk',{requestId:message.requestId,chunk:message.chunk}); return true;
      case 'ai.stream.end': emit('host-stream-end',{requestId:message.requestId}); return true;
      case 'avatar.lookAt': window.SvetlanaBridge?.lookAt?.(message.x,message.y); return true;
      case 'avatar.emotion': window.SvetlanaBridge?.emotion?.(message.name,message.duration); return true;
      case 'avatar.stop': window.SvetlanaBridge?.interrupt?.('host-stop'); return true;
      case 'host.ping': emit('host-pong'); return true;
      default: throw new Error('command_not_allowed');
    }
  }

  window.SvetlanaHost = {version:VERSION,command,enqueueSpeech};
  window.SvetlanaAndroidCommandV10 = function(json) {
    try {
      const message = typeof json === 'string' ? JSON.parse(json) : json;
      return JSON.stringify({ok:true,result:command(message)});
    } catch(e) {
      emit('host-error',{error:String(e?.message || e)});
      return JSON.stringify({ok:false,error:String(e?.message || e)});
    }
  };

  window.addEventListener('message', e => {
    if (e.origin === location.origin || e.origin === 'null') {
      try { command(e.data); } catch (_) {}
    }
  });
  document.addEventListener('visibilitychange',() => emit(document.hidden?'visibility-hidden':'visibility-visible'));
  emit('host-ready');
})();
