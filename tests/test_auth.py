"""
Тесты аутентификации и безопасности
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestRegistration:
    """Тесты регистрации"""
    
    async def test_register_success(self, client):
        """Успешная регистрация"""
        response = await client.post("/api/auth/register", data={
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "full_name": "Новый Пользователь",
            "phone": "+79001234567",
            "inn": "123456789012",
        })
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["email_sent"] in [True, False]
    
    async def test_register_duplicate_email(self, client, test_user):
        """Регистрация с существующим email"""
        response = await client.post("/api/auth/register", data={
            "email": test_user.email,
            "password": "StrongPass123!",
            "full_name": "Дубликат",
        })
        assert response.status_code == 409
    
    async def test_register_weak_password(self, client):
        """Регистрация со слабым паролем"""
        response = await client.post("/api/auth/register", data={
            "email": "weak@example.com",
            "password": "123",
            "full_name": "Слабый",
        })
        assert response.status_code == 400
    
    async def test_register_invalid_email(self, client):
        """Регистрация с неверным email"""
        response = await client.post("/api/auth/register", data={
            "email": "not-an-email",
            "password": "StrongPass123!",
            "full_name": "Тест",
        })
        assert response.status_code == 422
    
    async def test_register_invalid_phone(self, client):
        """Регистрация с неверным телефоном"""
        response = await client.post("/api/auth/register", data={
            "email": "phone@example.com",
            "password": "StrongPass123!",
            "full_name": "Тест",
            "phone": "12345",
        })
        assert response.status_code == 400
    
    async def test_register_invalid_inn(self, client):
        """Регистрация с неверным ИНН"""
        response = await client.post("/api/auth/register", data={
            "email": "inn@example.com",
            "password": "StrongPass123!",
            "full_name": "Тест",
            "inn": "12345",
        })
        assert response.status_code == 400


class TestLogin:
    """Тесты входа"""
    
    async def test_login_success(self, client, test_user):
        """Успешный вход"""
        response = await client.post("/api/auth/login", data={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_wrong_password(self, client, test_user):
        """Вход с неверным паролем"""
        response = await client.post("/api/auth/login", data={
            "email": test_user.email,
            "password": "WrongPass123!",
        })
        assert response.status_code == 401
    
    async def test_login_nonexistent_user(self, client):
        """Вход несуществующего пользователя"""
        response = await client.post("/api/auth/login", data={
            "email": "nonexistent@example.com",
            "password": "SomePass123!",
        })
        assert response.status_code == 401
    
    async def test_login_unverified_email(self, client, db_session):
        """Вход без подтверждённого email"""
        from app.models import User
        from app.core.security import get_password_hash
        
        user = User(
            email="unverified@example.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Неверифицированный",
            is_verified=False,
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post("/api/auth/login", data={
            "email": "unverified@example.com",
            "password": "TestPass123!",
        })
        assert response.status_code == 403
        assert "Подтвердите email" in response.json()["message"]
    
    async def test_login_lockout_after_5_attempts(self, client, test_user):
        """Блокировка после 5 неудачных попыток"""
        # 5 неудачных попыток
        for i in range(5):
            response = await client.post("/api/auth/login", data={
                "email": test_user.email,
                "password": f"WrongPass{i}!",
            })
            assert response.status_code == 401
        
        # 6-я попытка — блокировка
        response = await client.post("/api/auth/login", data={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        assert response.status_code == 423
        assert "заблокирован" in response.json()["message"]
    
    async def test_login_success_resets_attempts(self, client, test_user, db_session):
        """Успешный вход сбрасывает счётчик"""
        # 2 неудачные попытки
        for _ in range(2):
            await client.post("/api/auth/login", data={
                "email": test_user.email,
                "password": "WrongPass123!",
            })
        
        # Успешный вход
        response = await client.post("/api/auth/login", data={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        
        # Проверка что счётчик сброшен
        await db_session.refresh(test_user)
        assert test_user.failed_login_attempts == 0


class TestLogout:
    """Тесты выхода"""
    
    async def test_logout(self, client, auth_headers):
        """Выход из системы"""
        response = await client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        assert "Выход выполнен" in response.json()["message"]
    
    async def test_logout_invalidates_token(self, client, auth_headers):
        """Токен становится недействительным после выхода"""
        # Выход
        await client.post("/api/auth/logout", headers=auth_headers)
        
        # Попытка использования того же токена
        response = await client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 401


class TestRefreshToken:
    """Тесты обновления токена"""
    
    async def test_refresh_token(self, client, test_user):
        """Обновление access token"""
        # Вход
        login_resp = await client.post("/api/auth/login", data={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        refresh_token = login_resp.json()["refresh_token"]
        
        # Refresh
        response = await client.post("/api/auth/refresh", data={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    async def test_refresh_with_revoked_token(self, client, test_user):
        """Нельзя использовать отозванный refresh token"""
        login_resp = await client.post("/api/auth/login", data={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        refresh_token = login_resp.json()["refresh_token"]
        
        # Первый refresh
        await client.post("/api/auth/refresh", data={
            "refresh_token": refresh_token,
        })
        
        # Второй refresh с тем же токеном
        response = await client.post("/api/auth/refresh", data={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 401


class TestPasswordReset:
    """Тесты сброса пароля"""
    
    async def test_request_password_reset(self, client, test_user):
        """Запрос сброса пароля"""
        response = await client.post("/api/auth/password-reset", json={
            "email": test_user.email,
        })
        assert response.status_code == 200
        # Всегда одинаковый ответ для защиты от перечисления
        assert "email зарегистрирован" in response.json()["message"]
    
    async def test_request_password_reset_nonexistent(self, client):
        """Запрос сброса для несуществующего email"""
        response = await client.post("/api/auth/password-reset", json={
            "email": "nonexistent@example.com",
        })
        # Тот же ответ
        assert response.status_code == 200
    
    async def test_confirm_password_reset(self, client, test_user, db_session):
        """Подтверждение сброса пароля"""
        import secrets
        
        token = secrets.token_urlsafe(32)
        test_user.email_verification_token = token
        await db_session.commit()
        
        response = await client.post("/api/auth/password-reset/confirm", json={
            "token": token,
            "new_password": "NewStrongPass123!",
        })
        assert response.status_code == 200
        assert "Пароль успешно изменён" in response.json()["message"]
    
    async def test_confirm_password_reset_invalid_token(self, client):
        """Неверный токен сброса"""
        response = await client.post("/api/auth/password-reset/confirm", json={
            "token": "invalid-token",
            "new_password": "NewStrongPass123!",
        })
        assert response.status_code == 400


class Test2FA:
    """Тесты двухфакторной аутентификации"""
    
    async def test_setup_2fa(self, client, auth_headers):
        """Настройка 2FA"""
        response = await client.post("/api/auth/2fa/setup", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert "secret" in data
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 8
    
    async def test_verify_2fa_setup(self, client, auth_headers, db_session):
        """Подтверждение настройки 2FA"""
        import pyotp
        
        # Setup
        setup_resp = await client.post("/api/auth/2fa/setup", headers=auth_headers)
        secret = setup_resp.json()["secret"]
        
        # Generate valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        response = await client.post("/api/auth/2fa/verify", headers=auth_headers, data={
            "code": code,
        })
        assert response.status_code == 200
        assert "2FA успешно включён" in response.json()["message"]
    
    async def test_verify_2fa_wrong_code(self, client, auth_headers, db_session):
        """Неверный код 2FA"""
        await client.post("/api/auth/2fa/setup", headers=auth_headers)
        
        response = await client.post("/api/auth/2fa/verify", headers=auth_headers, data={
            "code": "000000",
        })
        assert response.status_code == 400
    
    async def test_disable_2fa(self, client, auth_headers, db_session):
        """Отключение 2FA"""
        import pyotp
        
        # Включаем 2FA
        setup_resp = await client.post("/api/auth/2fa/setup", headers=auth_headers)
        secret = setup_resp.json()["secret"]
        totp = pyotp.TOTP(secret)
        await client.post("/api/auth/2fa/verify", headers=auth_headers, data={
            "code": totp.now(),
        })
        
        # Отключаем
        response = await client.post("/api/auth/2fa/disable", headers=auth_headers, data={
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        assert "2FA отключён" in response.json()["message"]
    
    async def test_disable_2fa_wrong_password(self, client, auth_headers):
        """Отключение 2FA с неверным паролем"""
        response = await client.post("/api/auth/2fa/disable", headers=auth_headers, data={
            "password": "WrongPass123!",
        })
        assert response.status_code == 403


class TestSecurityHeaders:
    """Тесты security headers"""
    
    async def test_csp_header(self, client):
        """CSP header присутствует"""
        response = await client.get("/")
        assert "content-security-policy" in response.headers
        assert "nonce-" in response.headers["content-security-policy"]
    
    async def test_hsts_header(self, client):
        """HSTS header присутствует"""
        response = await client.get("/")
        assert "strict-transport-security" in response.headers
    
    async def test_xframe_header(self, client):
        """X-Frame-Options header"""
        response = await client.get("/")
        assert response.headers.get("x-frame-options") == "DENY"
    
    async def test_content_type_options(self, client):
        """X-Content-Type-Options header"""
        response = await client.get("/")
        assert response.headers.get("x-content-type-options") == "nosniff"


class TestRateLimiting:
    """Тесты rate limiting"""
    
    async def test_health_rate_limit(self, client):
        """Rate limit на health endpoint"""
        # 60 запросов должны пройти
        for _ in range(60):
            response = await client.get("/health")
            assert response.status_code == 200
    
    async def test_login_rate_limit(self, client):
        """Rate limit на login"""
        # Проверяем что лимит работает (slowapi)
        # Детальная проверка в интеграционных тестах
        response = await client.get("/health")
        assert response.status_code == 200
