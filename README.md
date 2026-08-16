# МИР Самозанятых v8.7.0

Платформа для самозанятых — договоры, финансы, CRM, маркетплейс, гранты, ИИ-ассистент Светлана.

## Быстрый старт

```bash
pip install -r requirements.txt
python app/main.py
```

## Деплой на Render

```bash
gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 1 --bind 0.0.0.0:$PORT --timeout 120
```

## Flutter APK

```bash
cd flutter_app
flutter build apk --release
```

## Версия
v8.7.0 — 17.08.2026
