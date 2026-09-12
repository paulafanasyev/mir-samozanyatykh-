# Документация: Система Светланы следующего поколения

## Архитектура

Система Светланы построена по принципу "реалистичного живого аватара", с поддержкой нескольких уровней рендеринга:

```
REALTIME 3D AVATAR (будущее/опционально)
        ↓
ANIMATED 2D / IMAGE AVATAR (текущее основное)
        ↓
CANVAS FALLBACK (резервное)
```

## Как заменить текущий аватар

### Вариант 1: Замена изображений

1. Подготовьте изображения аватара в формате WebP:
   - `svetlana-current.webp` - аватар по умолчанию
   - `svetlana-light.webp` - аватар для светлой темы
   - `svetlana-dark.webp` - аватар для темной темы

2. Поместите изображения в директорию:
   ```
   static/images/svetlana/
   ```

3. Изображения будут автоматически использоваться системой с учетом текущей темы интерфейса.

### Вариант 2: Использование 3D модели

1. Создайте 3D модель с помощью Blender скрипта:
   ```bash
   blender --background --python scripts/blender/create_svetlana_avatar.py
   ```

2. Поместите полученный файл `OfficeGirl.glb` в директорию:
   ```
   static/models/svetlana/svetlana.glb
   ```

3. Система автоматически обнаружит модель и переключится на 3D рендеринг.

## Как добавить GLB/GLTF 3D-модель

1. Поместите 3D-модель в формате GLB или GLTF в директорию:
   ```
   static/models/svetlana/
   ```

2. Убедитесь, что модель поддерживает:
   - Morph targets для визем
   - ARKit-compatible facial expressions
   - Skeletal animation (если требуется)

3. В файле `avatar-renderer.js` раскомментируйте и настройте `Realtime3DAvatar`:
   ```javascript
   // В конструкторе AvatarRenderer
   this.avatarRenderers.Realtime3DAvatar = new Realtime3DAvatarRenderer();
   ```

## Как подключить lip-sync

Система lip-sync уже подготовлена. Для активации реального lip-sync:

1. В `voice-interaction.js`, в методе `speakResponse`, система автоматически запускает анализ аудио через `LipSyncSystem`.

2. Для подключения реального анализа аудио:
   - Реализуйте обработчик аудио-стрима
   - Подайте аудио в `LipSyncSystem.processAudio()`
   - Система будет автоматически обновлять виземы на аватаре

## Как подключить realtime voice

1. В `voice-interaction.js` система уже использует Web Speech API для голосового ввода и вывода.

2. Для подключения сторонних голосовых решений:
   - Замените вызовы `speechSynthesis.speak()` на ваш API
   - Обновите `recognition.onresult` для обработки голосового ввода
   - Убедитесь, что события синхронизированы с системой состояний

## Система состояний Светланы

Светлана может находиться в одном из следующих состояний:

- `IDLE` - готова к общению
- `LISTENING` - слушает пользователя
- `THINKING` - обрабатывает запрос
- `SPEAKING` - отвечает пользователю
- `ERROR` - ошибка в работе

Каждое состояние визуально отображается в интерфейсе и влияет на поведение аватара.

## API аватара

Доступные методы:

```javascript
// Инициализация
await avatarRenderer.init(container);

// Установка состояния
avatarRenderer.render(state);

// Установка эмоций
await avatarRenderer.setEmotion('happy');

// Установка виземы (для lip-sync)
await avatarRenderer.setViseme('AA');

// Установка lip-sync данных
await avatarRenderer.setLipSync(audioData);

// Уничтожение
await avatarRenderer.destroy();
```

## Интеграция с чатом

Система голосового взаимодействия интегрирована с существующим чатом:

1. Голосовой ввод активируется кнопкой на аватаре
2. Текст отправляется в существующий чат
3. Ответ отображается в чате и озвучивается Светланой
4. Аватар показывает соответствующее состояние

## Безопасность

- API ключи не передаются в HTML/JavaScript
- Все чувствительные данные остаются на бэкенде
- Ключи хранятся в переменных окружения или GitHub Secrets
- Backend endpoint `/api/chat` используется для всех AI запросов

## Адаптивность

Интерфейс поддерживает:
- Desktop: аватар и чат рядом
- Mobile: аватар, состояние, затем чат друг под другом
- Темы: светлая и темная
- prefers-reduced-motion: отключение анимаций по запросу пользователя

## Структура файлов

```
/workspace/
├── static/js/
│   ├── avatar-state.js           # Система состояний
│   ├── canvas-avatar.js          # Canvas fallback рендерер
│   ├── image-avatar.js           # Image рендерер
│   ├── realistic-3d-avatar.js    # 3D рендерер (Three.js)
│   ├── avatar-renderer.js        # Мульти-рендерер
│   ├── lip-sync.js               # Lip-sync система
│   ├── voice-interaction.js      # Голосовое взаимодействие
│   └── svetlana-main.js          # Главный скрипт инициализации
├── static/images/svetlana/       # Для изображений аватара
├── static/models/svetlana/       # Для 3D моделей (GLB/GLTF)
├── scripts/blender/
│   └── create_svetlana_avatar.py # Скрипт для создания 3D модели
└── docs/
    └── svetlana-nextgen.md       # Эта документация
```

## Поддерживаемые форматы

### Изображения
- WebP (рекомендуется)
- PNG
- JPG

### 3D модели
- GLB (рекомендуется)
- GLTF
- Поддержка morph targets
- Поддержка skeletal animations
- Поддержка PBR материалов

### Анимации
- Idle (дыхание, моргание)
- Listening (внимание)
- Thinking (обработка)
- Speaking (речь + lip-sync)
- Custom emotions

## Требования к браузерам

- Chrome 80+ (рекомендуется)
- Firefox 75+
- Safari 13+
- Edge 80+

Для Web Speech API:
- Требуется HTTPS или localhost
- Поддержка варьируется по браузерам

## Отладка

Включите логи в консоли разработчика:
```javascript
window.DEBUG_SVETLANA = true;
```

Доступные объекты для отладки:
```javascript
window.svetlanaState      // Система состояний
window.avatarRenderer     // Рендерер аватара
window.voiceInteraction   // Голосовое взаимодействие
window.lipSyncSystem      // Lip-sync система
```

## Будущие улучшения

- [ ] Realtime streaming avatar
- [ ] Advanced facial tracking
- [ ] Emotion recognition from voice
- [ ] Multi-language support
- [ ] Custom avatar builder
- [ ] AR/VR support
