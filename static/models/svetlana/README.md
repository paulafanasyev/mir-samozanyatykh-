# 3D модели аватара Светланы

Поместите сюда 3D модель аватара Светланы:

- `svetlana.glb` - основная 3D модель (рекомендуется GLB)
- `svetlana.gltf` - альтернативный формат GLTF

## Как создать модель

Используйте Blender скрипт:
```bash
blender --background --python ../../../scripts/blender/create_svetlana_avatar.py
```

Скрипт создаст модель в директории `~/office_avatar_assets/OfficeGirl.glb`.
Скопируйте её сюда и переименуйте в `svetlana.glb`.

## Требования к моделям

- Формат: GLB (рекомендуется) или GLTF
- Полигоны: < 50,000 для мобильной производительности
- Текстуры: 1024x1024 или 2048x2048
- Анимации: Idle, Talk, Wave (опционально)
- Morph targets: MouthOpen, Happy, Sad, Angry, Blink

## Поддерживаемые функции

- Скелетная анимация
- Morph targets / Blend shapes
- PBR материалы
- ARKit-compatible facial expressions
- Visemes для lip-sync

## Автоматическое использование

Система автоматически обнаружит модель в этой директории и переключится на 3D рендеринг.
Если модель не найдена, будет использован Image или Canvas fallback.
