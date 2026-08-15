# Мир Самозанятых — Мобильное приложение

## Версия: 8.6.0+860

### Структура проекта

```
lib/
├── main.dart                          # Точка входа
├── core/
│   ├── constants/app_constants.dart   # Константы приложения
│   ├── theme/app_theme.dart           # Light/Dark темы (Material 3)
│   └── extensions/                    # Расширения Dart
├── data/
│   ├── models/                        # Freezed модели
│   ├── repositories/                  # Репозитории
│   └── datasources/
│       ├── local/                     # Hive, SharedPreferences
│       └── remote/                    # Dio API client
├── domain/
│   ├── entities/                      # Бизнес-сущности
│   ├── repositories/                  # Интерфейсы репозиториев
│   └── usecases/                      # Use cases (Clean Architecture)
├── presentation/
│   ├── navigation/
│   │   └── app_router.dart            # GoRouter конфигурация
│   ├── providers/                     # Riverpod провайдеры
│   ├── screens/                       # 20+ экранов
│   │   ├── auth/                      # Login, Register, Biometric
│   │   ├── home/                      # Dashboard
│   │   ├── clients/                   # CRM клиенты
│   │   ├── deals/                     # Воронка продаж
│   │   ├── invoices/                  # Счета и платежи
│   │   ├── tasks/                     # Kanban задачи
│   │   ├── calendar/                  # Календарь событий
│   │   ├── accounting/                # Бухгалтерия
│   │   ├── svetlana/                  # ИИ-ассистент
│   │   ├── profile/                   # Профиль пользователя
│   │   ├── settings/                  # Настройки
│   │   ├── referrals/                 # Реферальная программа
│   │   ├── notifications/             # Центр уведомлений
│   │   ├── bank/                      # Банковские подключения
│   │   ├── receipt/                   # Проверка чеков ФНС
│   │   ├── marketplace/               # Маркетплейс услуг
│   │   ├── contracts/                 # Договоры
│   │   ├── analytics/                 # Аналитика и графики
│   │   ├── integrations/              # API и вебхуки
│   │   └── admin/                     # Админ-панель
│   └── widgets/
│       ├── common/                    # Loading, EmptyState, Navbar
│       ├── cards/                     # StatCard, ActionCard
│       ├── charts/                    # Графики
│       └── forms/                     # Формы
└── services/                          # FCM, Notifications
```

### Быстрый старт

```bash
# Установка зависимостей
flutter pub get

# Генерация кода (Freezed, Retrofit, Hive)
flutter pub run build_runner build --delete-conflicting-outputs

# Запуск в debug режиме
flutter run

# Сборка APK
flutter build apk --release

# Сборка App Bundle
flutter build appbundle --release
```

### Архитектура

- **State Management:** Riverpod + StateNotifier
- **Navigation:** GoRouter
- **HTTP:** Dio + Retrofit
- **Local Storage:** Hive + SharedPreferences
- **DI:** Riverpod (built-in)
- **Theming:** Material 3 + Google Fonts Inter
- **Backend API:** https://api.mir-samozanyatykh.ru

### Функции

- 🔐 JWT авторизация + биометрия
- 👥 CRM: клиенты, сделки, воронка
- 📝 Счета, договоры, акты
- ✅ Kanban задачи
- 📅 Календарь с интеграцией
- 💰 Бухгалтерия и налоговые отчёты
- 🤖 ИИ-ассистент Светлана
- 🔔 Push-уведомления (FCM)
- 🏦 Банковские подключения (Тинькофф)
- 📷 Сканер QR чеков ФНС
- 📊 Аналитика и графики
- 🔗 API ключи и вебхуки
- 👮 Админ-панель (RBAC)

### Лицензия

АНО ЦПС «Мир Самозанятых» | ИНН 9724016805
