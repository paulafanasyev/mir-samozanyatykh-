"""
Email сервис с SMTP SSL
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger


class EmailService:
    """Сервис отправки email через SMTP SSL"""
    
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_name = settings.SMTP_FROM_NAME
        
        self._enabled = all([self.host, self.user, self.password])
        if not self._enabled:
            logger.warning("SMTP not fully configured")
    
    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> MIMEMultipart:
        """Создание MIME сообщения"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.user}>"
        msg["To"] = to_email
        
        # Text version
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        
        # HTML version
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        # Attachments
        if attachments:
            for att in attachments:
                part = MIMEApplication(
                    att["content"],
                    Name=att["filename"],
                )
                part["Content-Disposition"] = f'attachment; filename="{att["filename"]}"'
                msg.attach(part)
        
        return msg
    
    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Отправка email"""
        if not self._enabled:
            logger.warning(f"SMTP disabled, email not sent: {subject}")
            return False
        
        try:
            msg = self._create_message(to_email, subject, html_body, text_body, attachments)
            
            # Always use SSL/TLS — never unencrypted
            with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as server:
                server.login(self.user, self.password)
                server.sendmail(self.user, [to_email], msg.as_string())
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_verification(self, email: str, token: str) -> bool:
        """Отправка письма верификации"""
        verification_url = f"https://{settings.DOMAIN}/verify-email?token={token}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Подтверждение email</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #0D47A1 0%, #1976D2 100%); padding: 40px 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">Мир Самозанятых</h1>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0;">Платформа для самозанятых</p>
        </div>
        <div style="padding: 40px 30px;">
            <h2 style="color: #1a1a2e; margin: 0 0 20px;">Подтвердите ваш email</h2>
            <p style="color: #4a5568; line-height: 1.6; margin: 0 0 30px;">
                Для завершения регистрации на платформе «Мир Самозанятых» нажмите кнопку ниже:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="display: inline-block; background: #0D47A1; color: white; padding: 16px 40px; 
                          text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Подтвердить email
                </a>
            </div>
            <p style="color: #718096; font-size: 14px; line-height: 1.5;">
                Если кнопка не работает, скопируйте ссылку:<br>
                <code style="background: #f7fafc; padding: 8px 12px; border-radius: 4px; word-break: break-all; display: block; margin-top: 8px;">
                    {verification_url}
                </code>
            </p>
            <p style="color: #a0aec0; font-size: 12px; margin-top: 30px;">
                Если вы не регистрировались на платформе, просто проигнорируйте это письмо.
            </p>
        </div>
        <div style="background: #f7fafc; padding: 20px 30px; text-align: center;">
            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                АНО ЦПС «Мир Самозанятых» | ИНН 9724016805<br>
                <a href="https://{settings.DOMAIN}" style="color: #0D47A1;">{settings.DOMAIN}</a>
            </p>
        </div>
    </div>
</body>
</html>"""
        
        return await self.send(email, "Подтверждение email — Мир Самозанятых", html)
    
    async def send_invoice(self, email: str, invoice_number: str, pdf_content: bytes, total: float) -> bool:
        """Отправка счёта клиенту"""
        html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0D47A1;">Счёт на оплату</h2>
    <p>Здравствуйте!</p>
    <p>Вы получили счёт № <strong>{invoice_number}</strong> на сумму <strong>{total:,.2f} ₽</strong>.</p>
    <p>Счёт во вложении. Вы можете оплатить его по ссылке в личном кабинете.</p>
    <p>С уважением,<br>Мир Самозанятых</p>
</body>
</html>"""
        
        attachments = [{
            "filename": f"Счет_{invoice_number}.pdf",
            "content": pdf_content,
        }]
        
        return await self.send(
            email,
            f"Счёт на оплату № {invoice_number}",
            html,
            attachments=attachments,
        )
    
    async def send_password_reset(self, email: str, token: str) -> bool:
        """Отправка ссылки сброса пароля"""
        reset_url = f"https://{settings.DOMAIN}/reset-password?token={token}"
        
        html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #0D47A1;">Сброс пароля</h2>
    <p>Вы запросили сброс пароля на платформе «Мир Самозанятых».</p>
    <p>Для установки нового пароля перейдите по ссылке:</p>
    <a href="{reset_url}" style="display: inline-block; background: #0D47A1; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px;">Сбросить пароль</a>
    <p style="color: #666; font-size: 12px;">Ссылка действительна 1 час. Если вы не запрашивали сброс, проигнорируйте письмо.</p>
</body>
</html>"""
        
        return await self.send(email, "Сброс пароля — Мир Самозанятых", html)
    
    async def send_overdue_reminder(self, email: str, invoice_number: str, total: float, days_overdue: int) -> bool:
        """Напоминание о просроченном платеже"""
        html = f"""<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #E53E3E;">Напоминание об оплате</h2>
    <p>Счёт № <strong>{invoice_number}</strong> на сумму <strong>{total:,.2f} ₽</strong> просрочен на {days_overdue} дн.</p>
    <p>Просим произвести оплату в ближайшее время.</p>
    <p>Если оплата уже произведена — приносим извинения за беспокойство.</p>
</body>
</html>"""
        
        return await self.send(
            email,
            f"Напоминание об оплате — Счёт {invoice_number}",
            html,
        )


# Singleton
email_service = EmailService()
