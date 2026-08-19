# Functional Runtime Audit v8.4.29

## Проверено статически

- Calendar update повторно проверяет ownership client/deal/task.
- Bank sync не возвращает внешнюю ошибку API пользователю.
- Mobile Calendar использует реальный `/api/calendar/events` и создаёт событие через API; демонстрационные события удалены.
- Mobile Accounting больше не показывает фиксированный баланс; баланс рассчитывается из загруженных транзакций.
- Mobile Bank получает `/api/bank/status` и не предлагает подключать интеграции со статусом `coming_soon`/`planned`.
- Mobile Contracts использует общий ApiClient.
- Mobile Notifications использует общий ApiClient для mark-all-read.
- Python compilation: PASS.

## Не подтверждено в этом окружении

- Flutter/Dart build/test: Flutter SDK отсутствует.
- Vite/npm build: зависимости проекта не установлены, npm registry недоступен.
- Docker/PostgreSQL/Redis E2E: Docker runtime недоступен.

Никакой из этих runtime пунктов не помечен как PASS без фактического выполнения.
