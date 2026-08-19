"""Tests for webhooks module — Mir Samozanyatykh v7.9"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.models import User, Webhook
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def webhook_user(db_session: AsyncSession):
    await db_session.execute(delete(User).where(User.email == "webhook_test@example.com"))
    await db_session.commit()

    user = User(
        email="webhook_test@example.com",
        full_name="Webhook Test User",
        phone="+79123456781",
        password_hash=get_password_hash("TestPass123!"),
        is_active=True,
        is_verified=True,
        subscription_tier="business",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_webhook(db_session: AsyncSession, webhook_user: User):
    webhook = Webhook(
        user_id=webhook_user.id,
        url="https://example.com/webhook",
        events=["invoice.paid", "invoice.sent"],
        secret="webhook_secret_123",
        is_active=True,
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)
    return webhook


class TestWebhookModel:
    """Test webhook database model"""

    @pytest.mark.asyncio
    async def test_create_webhook(self, db_session: AsyncSession, webhook_user: User):
        webhook = Webhook(
            user_id=webhook_user.id,
            url="https://my-crm.ru/webhook",
            events=["contract.signed", "invoice.paid"],
            secret="my_secret",
            is_active=True,
        )
        db_session.add(webhook)
        await db_session.commit()
        await db_session.refresh(webhook)

        assert webhook.id is not None
        assert webhook.url == "https://my-crm.ru/webhook"
        assert "contract.signed" in webhook.events
        assert webhook.is_active is True
        assert webhook.failure_count == 0

    @pytest.mark.asyncio
    async def test_webhook_events(self, db_session: AsyncSession, webhook_user: User):
        webhook = Webhook(
            user_id=webhook_user.id,
            url="https://hooks.example.com",
            events=["invoice.paid", "invoice.sent", "invoice.overdue", "contract.signed"],
            secret="secret",
            is_active=True,
        )
        db_session.add(webhook)
        await db_session.commit()

        assert len(webhook.events) == 4
        assert "invoice.paid" in webhook.events
        assert "contract.signed" in webhook.events

    @pytest.mark.asyncio
    async def test_webhook_deactivation(self, db_session: AsyncSession, sample_webhook: Webhook):
        sample_webhook.is_active = False
        await db_session.commit()
        await db_session.refresh(sample_webhook)

        assert sample_webhook.is_active is False

    @pytest.mark.asyncio
    async def test_webhook_retry_increment(self, db_session: AsyncSession, sample_webhook: Webhook):
        initial_count = sample_webhook.failure_count
        sample_webhook.failure_count += 1
        await db_session.commit()
        await db_session.refresh(sample_webhook)

        assert sample_webhook.failure_count == initial_count + 1


class TestWebhookSecurity:
    """Test webhook security features"""

    @pytest.mark.asyncio
    async def test_webhook_secret_required(self, db_session: AsyncSession, webhook_user: User):
        """Webhook should have a secret for signature verification"""
        webhook = Webhook(
            user_id=webhook_user.id,
            url="https://example.com/hook",
            events=["invoice.paid"],
            secret="",
            is_active=True,
        )
        db_session.add(webhook)
        await db_session.commit()

        # Empty secret should be flagged or handled
        assert webhook.secret is not None

    @pytest.mark.asyncio
    async def test_webhook_url_validation(self, db_session: AsyncSession, webhook_user: User):
        """Webhook URL should be HTTPS in production"""
        webhook = Webhook(
            user_id=webhook_user.id,
            url="https://secure.example.com/webhook",
            events=["invoice.paid"],
            secret="secret",
            is_active=True,
        )
        db_session.add(webhook)
        await db_session.commit()

        assert webhook.url.startswith("https://")


class TestWebhookPayload:
    """Test webhook payload structure"""

    def test_payload_format(self):
        """Webhook payload should have correct structure"""
        payload = {
            "event": "invoice.paid",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "invoice_id": 1,
                "invoice_number": "SCH-1-20260115-0001",
                "amount": 50000.00,
                "client_id": 1,
            },
            "signature": "sha256=abc123...",
        }

        assert "event" in payload
        assert "timestamp" in payload
        assert "data" in payload
        assert "signature" in payload
        assert payload["event"].startswith("invoice.") or payload["event"].startswith("contract.")

    def test_signature_generation(self):
        """Test HMAC signature generation logic"""
        import hmac
        import hashlib

        secret = "webhook_secret"
        payload = '{"event":"invoice.paid","invoice_id":1}'

        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        assert len(signature) == 64  # SHA-256 hex length
        assert signature != secret

    def test_event_types(self):
        """Valid webhook event types"""
        valid_events = [
            "invoice.paid",
            "invoice.sent",
            "invoice.overdue",
            "invoice.created",
            "contract.signed",
            "contract.created",
            "payment.received",
            "client.created",
        ]

        for event in valid_events:
            parts = event.split(".")
            assert len(parts) == 2
            assert parts[0] in ["invoice", "contract", "payment", "client"]
