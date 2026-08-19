# Мир Самозанятых v8.4.9 — Functional/API Contract Audit

Дата: 16 августа 2026

## Выполнено
- Исправлен mobile `moveDeal`: backend использует POST, mobile теперь POST.
- Исправлен mobile notification read: backend использует PUT.
- Исправлен mobile bank connect payload: `api_token` вместо `token`.
- Исправлен mobile bank transactions: использует существующий accounting transaction contract; добавлен отдельный bank transactions endpoint для совместимости.
- Исправлен mobile invoice detail: `/api/sales/invoices/{id}`.
- Исправлен mobile revenue analytics: совместим с `/api/analytics/revenue-chart` и добавлен `/api/analytics/revenue` compatibility endpoint.
- Добавлены совместимые `/api/referrals/stats` и `/api/referrals/code`, оба используют фактическую referral-статистику пользователя.
- Добавлен `/api/svetlana/history` с честным пустым контрактом (`persisted=false`), поскольку история чата ещё не сохраняется в БД.
- Удалены из frontend API-документации phantom endpoints для task move, Svetlana voice/status, старого admin tier endpoint, generic CSV/import paths.
- Исправлена сортировка bank transactions по фактическому `transaction_date`.
- Проверен Python compileall.
- Release очищен от `.git`, `.pyc`, `__pycache__`, `.db`.

## Ограничения проверки
- Flutter SDK отсутствует в текущем runtime.
- `node_modules` отсутствует; npm install не завершился в доступное время.
- Поэтому `flutter analyze/build` и полноценный frontend build не объявляются PASS.
