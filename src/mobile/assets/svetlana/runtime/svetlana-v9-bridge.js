/* Svetlana Avatar v9.0 — Web/Android integration bridge */
(function () {
  'use strict';

  const VERSION = '9.0.0';
  const listeners = new Map();

  function on(type, fn) {
    if (!listeners.has(type)) listeners.set(type, new Set());
    listeners.get(type).add(fn);
    return () => listeners.get(type)?.delete(fn);
  }

  function emit(type, detail = {}) {
    const event = { type, version: VERSION, time: performance.now(), ...detail };
    (listeners.get(type) || []).forEach(fn => { try { fn(event); } catch (_) {} });
    try { window.dispatchEvent(new CustomEvent('svetlana:' + type, { detail: event })); } catch (_) {}
    return event;
  }

  function safeNumber(v, fallback = 0, min = 0, max = 120000) {
    const n = Number(v);
    return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : fallback;
  }

  const ALLOWED_EMOTIONS = new Set(['neutral','none','smile','surprise','sad','angry','thinking']);
  const MAX_TEXT = 8000;
  const MAX_QUEUE = 32;

  function normalize(input) {
    const t = input?.tts || {};
    const phonemes = t.phonemes ?? input?.phonemes ?? [];
    return {
      id: String(input?.id || `job-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`),
      text: String(input?.text || t.text || '').slice(0, MAX_TEXT),
      listenMs: safeNumber(input?.listenMs ?? 500, 500),
      thinkMs: safeNumber(input?.thinkMs ?? 350, 350),
      emotion: ALLOWED_EMOTIONS.has(String(input?.emotion || t.emotion || 'neutral')) ? String(input?.emotion || t.emotion || 'neutral') : 'neutral',
      emotionDuration: safeNumber(input?.emotionDuration ?? t.emotionDuration ?? 1800, 1800),
      audioUrl: t.audioUrl || input?.audioUrl || null,
      phonemes: Array.isArray(phonemes) ? phonemes : [],
      metadata: (input?.metadata && typeof input.metadata === 'object') ? input.metadata : {}
    };
  }

  let active = null;
  let token = 0;

  function interrupt(reason = 'user') {
    token++;
    const old = active;
    active = null;
    try { window.SvetlanaQueue?.interrupt?.(); } catch (_) {}
    try { window.SvetlanaAvatar?.stop?.({ reason }); } catch (_) {}
    emit('interrupt', { reason, previousId: old?.id || null });
  }

  function enqueue(input) {
    if (window.SvetlanaQueue?.size?.() >= MAX_QUEUE) { emit('error', {error:'queue_limit'}); return null; }
    const job = normalize(input);
    emit('queue-add', { job });
    try {
      const id = window.SvetlanaQueue?.add?.({
        id: job.id,
        listenMs: job.listenMs,
        thinkMs: job.thinkMs,
        tts: {
          audioUrl: job.audioUrl,
          phonemes: job.phonemes,
          emotion: job.emotion,
          emotionDuration: job.emotionDuration,
          text: job.text
        }
      });
      emit('queue-accepted', { job, runtimeId: id ?? job.id });
      return id ?? job.id;
    } catch (error) {
      emit('error', { job, error: String(error?.message || error) });
      return null;
    }
  }

  function addMany(items) {
    if (!Array.isArray(items)) return [];
    return items.map(enqueue);
  }

  function lookAt(x = 0, y = 0) {
    try { window.SvetlanaAvatar?.setLook?.(safeNumber(x, 0, -1, 1), safeNumber(y, 0, -1, 1)); }
    catch (error) { emit('error', { error: String(error?.message || error) }); }
  }

  function emotion(name = 'neutral', duration = 1200) {
    try { window.SvetlanaAvatar?.setEmotion?.(String(name), safeNumber(duration, 1200)); }
    catch (error) { emit('error', { error: String(error?.message || error) }); }
  }

  function post(message) {
    if (!message || typeof message !== 'object') return;
    switch (message.type) {
      case 'svetlana.enqueue': enqueue(message.payload); break;
      case 'svetlana.enqueueMany': addMany(message.items); break;
      case 'svetlana.interrupt': interrupt(message.reason); break;
      case 'svetlana.lookAt': lookAt(message.x, message.y); break;
      case 'svetlana.emotion': emotion(message.name, message.duration); break;
      case 'svetlana.stop': interrupt('stop'); break;
      case 'svetlana.ping': emit('pong'); break;
      default: emit('unknown-message', { messageType: message.type });
    }
  }

  window.SvetlanaBridge = {
    version: VERSION,
    on, emit, enqueue, addMany, interrupt, lookAt, emotion, post,
    get active() { return active; }
  };

  // Trusted same-origin web messages.
  window.addEventListener('message', e => {
    if (e.origin === window.location.origin) post(e.data);
  });

  // Native Android/WebView can call this JavaScript entry point after validating
  // the origin and payload on the native side.
  window.SvetlanaAndroidCommand = function (json) {
    try {
      const message = typeof json === 'string' ? JSON.parse(json) : json;
      post(message);
      return JSON.stringify({ ok: true, version: VERSION });
    } catch (error) {
      emit('error', { error: String(error?.message || error) });
      return JSON.stringify({ ok: false, error: String(error?.message || error) });
    }
  };

  window.addEventListener('svetlana:state', e => emit('state', e.detail));
  window.addEventListener('svetlana:speech-start', e => emit('speech-start', e.detail));
  window.addEventListener('svetlana:speech-end', e => emit('speech-end', e.detail));

  document.addEventListener('visibilitychange', () => {
    emit(document.hidden ? 'visibility-hidden' : 'visibility-visible');
  });

  emit('ready');
})();
