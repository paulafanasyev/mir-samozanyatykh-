# Changelog

## [8.4.33] - 2026-08-17

### Functional persistence and business-flow hardening
- White-label settings are persisted per user and validated; SVG logo uploads are disabled to avoid stored-XSS risk.
- Svetlana chat messages are persisted per user with bounded history retrieval.
- Email campaigns are persisted with queued/completed/failed status and send counters.
- Added Alembic v852 migration for the new persistence tables/column.
- Added regression coverage for the new persistence flows.


## [8.6.1] - 2026-08-15

### Mobile (Flutter)
- Полностью переработана мобильная часть
- Исправлен pubspec.yaml (был сломан в одну строку)
- Добавлена Android конфигурация (build.gradle, AndroidManifest, ProGuard)
- Создано 25+ экранов с Material 3 дизайном
- Добавлена навигация GoRouter с ShellRoute и BottomNavigationBar (9 пунктов)
- Реализована светлая/тёмная тема с Google Fonts Inter
- Добавлен Riverpod state management с biometric auth
- Создан Dio API client с interceptors, retry logic, token refresh
- Реализован ИИ-ассистент Светлана с быстрыми вопросами
- Добавлены экраны: CRM (клиенты, сделки), финансы (счета, бухгалтерия), задачи, календарь
- Добавлены: банковские подключения, проверка чеков ФНС, маркетплейс, договоры
- Добавлена админ-панель с RBAC
- Добавлена аналитика с графиками (fl_chart)
- Добавлены интеграции: API ключи, вебхуки, экспорт
- Добавлена реферальная программа
- Добавлен центр уведомлений
- Добавлены common widgets: StatCard, ActionCard, LoadingWidget, EmptyState
- Добавлен analysis_options.yaml, .gitignore, README

### CI/CD
- Обновлён GitHub Actions workflow
- Добавлены jobs: analyze, test, build-android, build-ios
- Добавлена загрузка артефактов и автоматический release

## [8.1.0] - 2026-08-12

### Backend
- FastAPI + SQLAlchemy async
- 35+ API роутеров
- JWT авторизация с jti
- CSRF защита, rate limiting, CSP nonce
- RBAC (admin/moderator/support)
- Audit logs
- OpenRouter AI (Светлана)
- YooKassa интеграция
- Telegram Bot API
- WebRTC для видеозвонков

### Frontend
- React + TypeScript + Vite
- 26 TSX компонентов
- Zustand state management
- Material 3 компоненты

## [8.0.0] - 2026-08-10

### Initial Enterprise Release
- Полная архитектура backend/frontend/mobile
- Docker + Docker Compose
- Traefik + Let's Encrypt
- Alembic миграции
- pytest тесты (124/125)

CI/CD hardening: v8.4.19
