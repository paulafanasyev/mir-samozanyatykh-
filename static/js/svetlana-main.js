/**
 * Светлана NextGen - Главный скрипт инициализации
 * Интегрирует все компоненты системы аватара
 */

document.addEventListener('DOMContentLoaded', async function() {
  console.log('🚀 Initializing Svetlana NextGen System...');
  
  try {
    // Находим контейнер для аватара
    const avatarContainer = document.getElementById('svetlana-avatar-container');
    if (!avatarContainer) {
      console.warn('Avatar container not found, skipping initialization');
      return;
    }
    
    // === 1. Инициализация системы состояний ===
    const svetlanaState = new window.SvetlanaState();
    console.log('✓ State system initialized');
    
    // === 2. Инициализация рендерера аватара ===
    const avatarRenderer = new window.AvatarRenderer('svetlana-avatar-container');
    await avatarRenderer.init();
    console.log('✓ Avatar renderer initialized');
    
    // === 3. Инициализация lip-sync системы ===
    const lipSyncSystem = new window.LipSyncSystem(avatarRenderer);
    await lipSyncSystem.init();
    console.log('✓ Lip-sync system initialized');
    
    // === 4. Инициализация голосового взаимодействия ===
    const voiceInteraction = new window.VoiceInteraction(
      svetlanaState, 
      avatarRenderer, 
      lipSyncSystem
    );
    await voiceInteraction.init();
    console.log('✓ Voice interaction initialized');
    
    // === 5. Привязка кнопки голосового ввода ===
    const voiceBtn = document.getElementById('voice-control-btn');
    if (voiceBtn) {
      voiceBtn.addEventListener('click', async () => {
        await voiceInteraction.toggleListening();
        
        // Обновляем визуальное состояние кнопки
        if (svetlanaState.getState() === svetlanaState.states.LISTENING) {
          voiceBtn.classList.add('listening');
          voiceBtn.setAttribute('aria-label', 'Остановить прослушивание');
        } else {
          voiceBtn.classList.remove('listening');
          voiceBtn.setAttribute('aria-label', 'Начать голосовой ввод');
        }
      });
      
      // Добавляем tooltip
      voiceBtn.title = 'Нажмите для голосового ввода';
    }
    
    // === 6. Подписка на изменения состояний ===
    svetlanaState.onStateChange(svetlanaState.states.IDLE, () => {
      voiceBtn?.classList.remove('listening');
      voiceBtn?.setAttribute('aria-label', 'Начать голосовой ввод');
      console.log('🟢 Svetlana: IDLE');
    });
    
    svetlanaState.onStateChange(svetlanaState.states.LISTENING, () => {
      voiceBtn?.classList.add('listening');
      voiceBtn?.setAttribute('aria-label', 'Остановить прослушивание');
      console.log('🔵 Svetlana: LISTENING');
    });
    
    svetlanaState.onStateChange(svetlanaState.states.THINKING, () => {
      console.log('🟡 Svetlana: THINKING');
    });
    
    svetlanaState.onStateChange(svetlanaState.states.SPEAKING, async () => {
      console.log('🟣 Svetlana: SPEAKING');
      // Запускаем lip-sync при начале речи
      if (lipSyncSystem) {
        await lipSyncSystem.startAnalysis();
      }
    });
    
    svetlanaState.onStateChange(svetlanaState.states.ERROR, () => {
      console.error('🔴 Svetlana: ERROR');
      // Автоматический возврат к IDLE через 2 секунды
      setTimeout(() => {
        if (svetlanaState.getState() === svetlanaState.states.ERROR) {
          svetlanaState.setState(svetlanaState.states.IDLE);
        }
      }, 2000);
    });
    
    // === 7. Установка начального состояния ===
    svetlanaState.setState(svetlanaState.states.IDLE);
    
    console.log('✅ Svetlana NextGen System fully initialized!');
    console.log('   - Canvas Fallback: Ready');
    console.log('   - Image Avatar: Ready');
    console.log('   - 3D Avatar: Pending (awaiting GLB model)');
    console.log('   - Voice Input: Ready');
    console.log('   - Lip-Sync: Ready');
    
    // === 8. Сохранение экземпляров для отладки ===
    window.svetlanaInstance = {
      state: svetlanaState,
      renderer: avatarRenderer,
      voice: voiceInteraction,
      lipSync: lipSyncSystem
    };
    
    // === 9. Обработка переключения темы ===
    const themeObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          console.log('🎨 Theme changed, updating avatar...');
          // Аватар автоматически обновится через MutationObserver в image-avatar.js
        }
      });
    });
    
    themeObserver.observe(document.documentElement, { attributes: true });
    
  } catch (error) {
    console.error('❌ Failed to initialize Svetlana system:', error);
    
    // Показываем пользователю сообщение об ошибке
    const errorContainer = document.querySelector('.avatar-state-description');
    if (errorContainer) {
      errorContainer.textContent = 'Ошибка инициализации. Обновите страницу.';
      errorContainer.style.color = '#ef4444';
    }
  }
});

// === Очистка ресурсов при закрытии страницы ===
window.addEventListener('beforeunload', async function() {
  try {
    if (window.svetlanaInstance) {
      console.log('🧹 Cleaning up Svetlana resources...');
      
      if (window.svetlanaInstance.voice) {
        await window.svetlanaInstance.voice.destroy();
      }
      
      if (window.svetlanaInstance.renderer) {
        await window.svetlanaInstance.renderer.destroy();
      }
      
      if (window.svetlanaInstance.lipSync) {
        await window.svetlanaInstance.lipSync.destroy();
      }
      
      window.svetlanaInstance = null;
    }
  } catch (error) {
    console.error('Error during cleanup:', error);
  }
});

// === Глобальные команды для отладки в консоли ===
window.SvetlanaDebug = {
  getState: () => window.svetlanaInstance?.state?.getState(),
  setState: (state) => window.svetlanaInstance?.state?.setState(state),
  setEmotion: (emotion) => window.svetlanaInstance?.renderer?.currentRenderer?.setEmotion(emotion),
  speak: (text) => window.svetlanaInstance?.voice?.speakResponse(text),
  testLipSync: () => {
    const visemes = ['AA', 'EH', 'IH', 'OW', 'UW', 'B', 'M', 'F'];
    let i = 0;
    const interval = setInterval(() => {
      if (i >= visemes.length) {
        clearInterval(interval);
        window.svetlanaInstance?.renderer?.currentRenderer?.setViseme(null);
        return;
      }
      console.log('Testing viseme:', visemes[i]);
      window.svetlanaInstance?.renderer?.currentRenderer?.setViseme(visemes[i]);
      i++;
    }, 200);
  }
};

console.log('💡 Debug commands available: window.SvetlanaDebug.*');
