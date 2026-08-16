# Деплой МИР Самозанятых v8.7.0

## Render (рекомендуется)

[Deploy Blueprint](https://dashboard.render.com/blueprint/new?repo=https://github.com/paulafanasyev/mir-samozanyatykh-)

Или вручную:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers 1 --bind 0.0.0.0:$PORT --timeout 120`

## Docker

```bash
docker build -t mir-samozanyatykh .
docker run -p 8000:8000 -e SECRET_KEY=your-secret mir-samozanyatykh
```

## Локально

```bash
pip install -r requirements.txt
python app/main.py
```

Откроется на http://localhost:8000

## Flutter APK

```bash
cd flutter_app
flutter build apk --release
```

APK: `flutter_app/build/app/outputs/flutter-apk/app-release.apk`
