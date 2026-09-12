/**
 * Canvas Avatar Renderer
 * Ультрареалистичное процедурное лицо Светланы (Fallback)
 * Внешность: 25 лет, брюнетка, голубые глаза
 */

class CanvasAvatarRenderer {
  constructor() {
    this.canvas = null;
    this.ctx = null;
    this.container = null;
    this.animationFrame = null;
    this.isVisible = false;
    
    // Параметры лица
    this.params = {
      skinColor: '#f5d0b0',
      skinShadow: '#e0b090',
      hairColor: '#2a1a10', // Темно-каштановые
      eyeWhite: '#ffffff',
      eyeIris: '#4a90e2', // Голубые
      eyePupil: '#000000',
      lipColor: '#d46a6a',
      lipGloss: '#ff8a8a',
      blushColor: 'rgba(230, 100, 100, 0.15)'
    };
    
    // Состояние анимации
    this.state = {
      time: 0,
      blink: 0,
      blinkSpeed: 0.15,
      breath: 0,
      headX: 0,
      headY: 0,
      mouthOpen: 0,
      smile: 0,
      eyebrowL: 0,
      eyebrowR: 0,
      eyeX: 0,
      eyeY: 0
    };
    
    // Таймеры
    this.nextBlinkTime = 0;
    this.blinkDuration = 0;
  }

  async init(container) {
    this.container = container;
    
    // Создаем canvas
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'svetlana-avatar-canvas';
    this.canvas.width = 500;
    this.canvas.height = 500;
    this.ctx = this.canvas.getContext('2d');
    
    container.appendChild(this.canvas);
    
    // Инициализация состояния
    this.resetState();
    this.scheduleNextBlink();
    
    // Запуск анимации
    this.isVisible = true;
    this.animate();
    
    console.log('Canvas Avatar Renderer initialized');
  }

  resetState() {
    this.state = {
      time: 0,
      blink: 1, // 1 = открыты, 0 = закрыты
      blinkSpeed: 0.15,
      breath: 0,
      headX: 0,
      headY: 0,
      mouthOpen: 0,
      smile: 0.2, // Легкая улыбка по умолчанию
      eyebrowL: 0,
      eyebrowR: 0,
      eyeX: 0,
      eyeY: 0
    };
  }

  scheduleNextBlink() {
    const delay = 3000 + Math.random() * 2000; // 3-5 секунд
    this.nextBlinkTime = Date.now() + delay;
    this.blinkDuration = 150 + Math.random() * 100; // 150-250 мс
  }

  animate() {
    if (!this.isVisible) return;
    
    const now = Date.now();
    this.state.time += 0.016; // ~60 FPS
    
    // Дыхание
    this.state.breath = Math.sin(this.state.time * 0.5) * 2;
    
    // Покачивание головы (idle)
    this.state.headX = Math.sin(this.state.time * 0.3) * 3;
    this.state.headY = Math.cos(this.state.time * 0.4) * 2;
    
    // Моргание
    if (now > this.nextBlinkTime && this.state.blink === 1) {
      this.state.blink = 0;
      setTimeout(() => {
        this.state.blink = 1;
        this.scheduleNextBlink();
      }, this.blinkDuration);
    }
    
    // Движение глаз (случайное)
    if (Math.random() < 0.02) {
      this.state.eyeX = (Math.random() - 0.5) * 8;
      this.state.eyeY = (Math.random() - 0.5) * 4;
    }
    
    // Возврат глаз в центр
    this.state.eyeX *= 0.95;
    this.state.eyeY *= 0.95;
    
    this.draw();
    this.animationFrame = requestAnimationFrame(() => this.animate());
  }

  draw() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    
    // Очистка
    ctx.clearRect(0, 0, w, h);
    
    // Фон (прозрачный или легкий градиент)
    const theme = document.documentElement.getAttribute('data-theme') || 'light';
    if (theme === 'dark') {
      const grad = ctx.createRadialGradient(cx, cy, 100, cx, cy, 300);
      grad.addColorStop(0, 'rgba(40, 40, 50, 0.3)');
      grad.addColorStop(1, 'rgba(20, 20, 30, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    } else {
      const grad = ctx.createRadialGradient(cx, cy, 100, cx, cy, 300);
      grad.addColorStop(0, 'rgba(240, 245, 255, 0.5)');
      grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    }
    
    ctx.save();
    ctx.translate(cx + this.state.headX, cy + this.state.headY + this.state.breath);
    
    // --- Волосы (задняя часть) ---
    ctx.fillStyle = this.params.hairColor;
    ctx.beginPath();
    ctx.ellipse(0, 20, 140, 160, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // --- Шея ---
    ctx.fillStyle = this.params.skinShadow;
    ctx.beginPath();
    ctx.ellipse(0, 140, 40, 60, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // --- Лицо (основа) ---
    ctx.fillStyle = this.params.skinColor;
    ctx.beginPath();
    ctx.ellipse(0, 20, 110, 130, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // Тени лица
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.beginPath();
    ctx.ellipse(-60, 40, 30, 80, 0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(60, 40, 30, 80, -0.2, 0, Math.PI * 2);
    ctx.fill();
    
    // Румянец
    ctx.fillStyle = this.params.blushColor;
    ctx.beginPath();
    ctx.ellipse(-70, 60, 25, 15, 0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(70, 60, 25, 15, -0.3, 0, Math.PI * 2);
    ctx.fill();
    
    // --- Глаза ---
    const eyeY = 10;
    const eyeXOffset = 45;
    
    // Белки
    ctx.fillStyle = this.params.eyeWhite;
    
    // Левый глаз
    ctx.beginPath();
    if (this.state.blink < 0.5) {
      // Закрыт
      ctx.ellipse(-eyeXOffset, eyeY, 18, 8, 0, 0, Math.PI * 2);
    } else {
      // Открыт
      ctx.ellipse(-eyeXOffset, eyeY, 18, 14, 0, 0, Math.PI * 2);
    }
    ctx.fill();
    
    // Правый глаз
    ctx.beginPath();
    if (this.state.blink < 0.5) {
      ctx.ellipse(eyeXOffset, eyeY, 18, 8, 0, 0, Math.PI * 2);
    } else {
      ctx.ellipse(eyeXOffset, eyeY, 18, 14, 0, 0, Math.PI * 2);
    }
    ctx.fill();
    
    // Радужка и зрачок
    if (this.state.blink >= 0.5) {
      ctx.fillStyle = this.params.eyeIris;
      
      // Левый
      ctx.beginPath();
      ctx.arc(-eyeXOffset + this.state.eyeX, eyeY + this.state.eyeY, 9, 0, Math.PI * 2);
      ctx.fill();
      
      // Правый
      ctx.beginPath();
      ctx.arc(eyeXOffset + this.state.eyeX, eyeY + this.state.eyeY, 9, 0, Math.PI * 2);
      ctx.fill();
      
      // Зрачки
      ctx.fillStyle = this.params.eyePupil;
      ctx.beginPath();
      ctx.arc(-eyeXOffset + this.state.eyeX, eyeY + this.state.eyeY, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(eyeXOffset + this.state.eyeX, eyeY + this.state.eyeY, 4, 0, Math.PI * 2);
      ctx.fill();
      
      // Блик в глазах
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
      ctx.beginPath();
      ctx.arc(-eyeXOffset + this.state.eyeX + 3, eyeY + this.state.eyeY - 3, 2.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(eyeXOffset + this.state.eyeX + 3, eyeY + this.state.eyeY - 3, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
    
    // Веки (верхние)
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(-eyeXOffset, eyeY - 2, 18, Math.PI, 0);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(eyeXOffset, eyeY - 2, 18, Math.PI, 0);
    ctx.stroke();
    
    // Брови
    ctx.strokeStyle = this.params.hairColor;
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    
    const browY = -15 + this.state.eyebrowL;
    ctx.beginPath();
    ctx.moveTo(-eyeXOffset - 20, browY);
    ctx.quadraticCurveTo(-eyeXOffset, browY - 5, -eyeXOffset + 20, browY);
    ctx.stroke();
    
    const browYR = -15 + this.state.eyebrowR;
    ctx.beginPath();
    ctx.moveTo(eyeXOffset - 20, browYR);
    ctx.quadraticCurveTo(eyeXOffset, browYR - 5, eyeXOffset + 20, browYR);
    ctx.stroke();
    
    // Нос
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 40);
    ctx.lineTo(-5, 65);
    ctx.stroke();
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.beginPath();
    ctx.ellipse(-3, 68, 8, 5, 0, 0, Math.PI * 2);
    ctx.fill();
    
    // Рот
    const mouthY = 90;
    const mouthWidth = 35;
    const baseMouthHeight = 12;
    const openAmount = this.state.mouthOpen * 15; // 0 to 15
    
    ctx.fillStyle = '#5a2a2a'; // Внутри рта
    ctx.beginPath();
    if (openAmount > 1) {
      // Открытый рот
      ctx.ellipse(0, mouthY, mouthWidth, baseMouthHeight + openAmount, 0, 0, Math.PI * 2);
    } else {
      // Закрытый рот с улыбкой
      const smileCurve = 8 + this.state.smile * 10;
      ctx.moveTo(-mouthWidth, mouthY);
      ctx.quadraticCurveTo(0, mouthY + smileCurve, mouthWidth, mouthY);
      ctx.quadraticCurveTo(0, mouthY + smileCurve - 5, -mouthWidth, mouthY);
    }
    ctx.fill();
    
    // Губы
    ctx.fillStyle = this.params.lipColor;
    if (openAmount <= 1) {
      ctx.beginPath();
      const smileCurve = 8 + this.state.smile * 10;
      // Верхняя губа
      ctx.moveTo(-mouthWidth, mouthY);
      ctx.quadraticCurveTo(-mouthWidth/2, mouthY - 10, 0, mouthY - 5);
      ctx.quadraticCurveTo(mouthWidth/2, mouthY - 10, mouthWidth, mouthY);
      ctx.quadraticCurveTo(0, mouthY + smileCurve - 5, -mouthWidth, mouthY);
      ctx.fill();
      
      // Блеск
      ctx.fillStyle = this.params.lipGloss;
      ctx.globalAlpha = 0.6;
      ctx.beginPath();
      ctx.moveTo(-mouthWidth/2, mouthY - 5);
      ctx.quadraticCurveTo(0, mouthY - 2, mouthWidth/2, mouthY - 5);
      ctx.quadraticCurveTo(0, mouthY, -mouthWidth/2, mouthY - 5);
      ctx.fill();
      ctx.globalAlpha = 1.0;
    }
    
    // --- Волосы (передняя часть/челка) ---
    ctx.fillStyle = this.params.hairColor;
    ctx.beginPath();
    ctx.moveTo(-110, -20);
    ctx.quadraticCurveTo(-60, -80, 0, -90);
    ctx.quadraticCurveTo(60, -80, 110, -20);
    ctx.quadraticCurveTo(80, -40, 0, -50);
    ctx.quadraticCurveTo(-80, -40, -110, -20);
    ctx.fill();
    
    // Боковые пряди
    ctx.beginPath();
    ctx.moveTo(-110, -20);
    ctx.quadraticCurveTo(-130, 50, -120, 120);
    ctx.quadraticCurveTo(-100, 100, -90, 20);
    ctx.fill();
    
    ctx.beginPath();
    ctx.moveTo(110, -20);
    ctx.quadraticCurveTo(130, 50, 120, 120);
    ctx.quadraticCurveTo(100, 100, 90, 20);
    ctx.fill();
    
    ctx.restore();
  }

  async render(state) {
    // Обновление состояния в зависимости от режима
    switch(state) {
      case 'idle':
        this.state.smile = 0.2;
        this.state.mouthOpen = 0;
        this.state.eyebrowL = 0;
        this.state.eyebrowR = 0;
        break;
        
      case 'listening':
        this.state.smile = 0.3;
        this.state.eyebrowL = -2;
        this.state.eyebrowR = -2;
        break;
        
      case 'thinking':
        this.state.smile = 0.1;
        this.state.eyebrowL = 3;
        this.state.eyebrowR = -1;
        break;
        
      case 'speaking':
        this.state.smile = 0.4;
        // Анимация рта будет управляться через setViseme
        break;
        
      case 'error':
        this.state.smile = -0.3;
        this.state.eyebrowL = 5;
        this.state.eyebrowR = 5;
        break;
    }
  }

  async setEmotion(emotion) {
    switch(emotion) {
      case 'happy':
        this.state.smile = 0.8;
        this.state.eyebrowL = -3;
        this.state.eyebrowR = -3;
        break;
      case 'sad':
        this.state.smile = -0.5;
        this.state.eyebrowL = 5;
        this.state.eyebrowR = 5;
        break;
      case 'surprised':
        this.state.mouthOpen = 0.8;
        this.state.eyebrowL = -8;
        this.state.eyebrowR = -8;
        break;
      default:
        this.state.smile = 0.2;
        this.state.eyebrowL = 0;
        this.state.eyebrowR = 0;
    }
  }

  async setViseme(viseme) {
    // Преобразование виземы в открытие рта (0.0 - 1.0)
    let openness = 0.0;
    
    if (viseme) {
      const openVisemes = ['AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW'];
      const midVisemes = ['B', 'M', 'P', 'F', 'V', 'W', 'Y'];
      
      if (openVisemes.includes(viseme)) {
        openness = 0.8 + Math.random() * 0.2;
      } else if (midVisemes.includes(viseme)) {
        openness = 0.3 + Math.random() * 0.3;
      } else {
        openness = 0.1;
      }
    }
    
    // Плавная интерполяция
    this.state.mouthOpen += (openness - this.state.mouthOpen) * 0.3;
  }

  async setLipSync(audioData) {
    // Простая эмуляция по громкости
    if (audioData && audioData.length > 0) {
      const volume = audioData.reduce((a, b) => a + b, 0) / audioData.length;
      this.state.mouthOpen = Math.min(1.0, volume / 50);
    } else {
      this.state.mouthOpen = 0;
    }
  }

  show() {
    this.isVisible = true;
    if (this.canvas) this.canvas.style.display = 'block';
    this.animate();
  }

  hide() {
    this.isVisible = false;
    if (this.canvas) this.canvas.style.display = 'none';
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
  }

  async destroy() {
    this.hide();
    if (this.canvas && this.canvas.parentNode) {
      this.canvas.parentNode.removeChild(this.canvas);
    }
    this.canvas = null;
    this.ctx = null;
  }
}

window.CanvasAvatarRenderer = CanvasAvatarRenderer;
