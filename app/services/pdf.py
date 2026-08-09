"""
PDF генерация для счетов, договоров, актов
ReportLab + QR-коды
"""

import io
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode

from app.core.config import settings
from app.core.logging import logger


# Цветовая схема
PRIMARY = HexColor("#0D47A1")
PRIMARY_LIGHT = HexColor("#1976D2")
TEXT_DARK = HexColor("#1a1a2e")
TEXT_MUTED = HexColor("#64748B")
BORDER = HexColor("#E2E8F0")
SUCCESS = HexColor("#10B981")
WARNING = HexColor("#F59E0B")
DANGER = HexColor("#EF4444")


class PDFService:
    """Сервис генерации PDF документов"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Настройка кастомных стилей"""
        self.title_style = ParagraphStyle(
            "DocTitle",
            parent=self.styles["Heading1"],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=24,
            textColor=PRIMARY,
            fontName="Helvetica-Bold",
        )
        
        self.heading_style = ParagraphStyle(
            "DocHeading",
            parent=self.styles["Heading2"],
            fontSize=13,
            spaceAfter=12,
            spaceBefore=16,
            textColor=PRIMARY,
            fontName="Helvetica-Bold",
        )
        
        self.subheading_style = ParagraphStyle(
            "DocSubheading",
            parent=self.styles["Heading3"],
            fontSize=11,
            spaceAfter=8,
            textColor=TEXT_DARK,
            fontName="Helvetica-Bold",
        )
        
        self.body_style = ParagraphStyle(
            "DocBody",
            parent=self.styles["Normal"],
            fontSize=10,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=8,
            textColor=TEXT_DARK,
        )
        
        self.body_bold_style = ParagraphStyle(
            "DocBodyBold",
            parent=self.body_style,
            fontName="Helvetica-Bold",
        )
        
        self.footer_style = ParagraphStyle(
            "DocFooter",
            parent=self.styles["Normal"],
            fontSize=8,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            leading=12,
        )
        
        self.right_style = ParagraphStyle(
            "DocRight",
            parent=self.body_style,
            alignment=TA_RIGHT,
        )
        
        self.table_header_style = ParagraphStyle(
            "TableHeader",
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=white,
            alignment=TA_CENTER,
        )
        
        self.table_cell_style = ParagraphStyle(
            "TableCell",
            fontSize=9,
            textColor=TEXT_DARK,
            alignment=TA_LEFT,
        )
        
        self.table_cell_right = ParagraphStyle(
            "TableCellRight",
            fontSize=9,
            textColor=TEXT_DARK,
            alignment=TA_RIGHT,
        )
    
    def _create_qr(self, data: str, size: int = 40) -> Image:
        """Создание QR-кода"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return Image(buffer, width=size * mm, height=size * mm)
    
    def _doc_id(self, data: Any) -> str:
        """Генерация ID документа"""
        return hashlib.sha256(str(data).encode()).hexdigest()[:16].upper()
    
    def generate_invoice(
        self,
        invoice_number: str,
        seller: Dict[str, str],
        buyer: Dict[str, str],
        items: List[Dict[str, Any]],
        total: Decimal,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
        status: str = "draft",
    ) -> bytes:
        """Генерация PDF счёта"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )
        
        story = []
        
        # Шапка
        story.append(Paragraph("<b>МИР САМОЗАНЯТЫХ</b>", self.title_style))
        story.append(Paragraph("СЧЁТ НА ОПЛАТУ", self.heading_style))
        story.append(Spacer(1, 8))
        
        # Номер и статус
        status_colors = {
            "draft": TEXT_MUTED,
            "sent": PRIMARY_LIGHT,
            "paid": SUCCESS,
            "overdue": DANGER,
            "cancelled": TEXT_MUTED,
        }
        status_labels = {
            "draft": "ЧЕРНОВИК",
            "sent": "ВЫСТАВЛЕН",
            "paid": "ОПЛАЧЕН",
            "overdue": "ПРОСРОЧЕН",
            "cancelled": "ОТМЕНЁН",
        }
        status_color = status_colors.get(status, TEXT_MUTED)
        status_label = status_labels.get(status, status.upper())
        
        header_data = [
            [Paragraph(f"<b>Счёт №:</b> {invoice_number}", self.body_bold_style),
             Paragraph(f"<b>Статус:</b> <font color='#{status_color.hexval()[2:8]}'>{status_label}</font>", self.body_bold_style)],
            [Paragraph(f"<b>Дата:</b> {datetime.now(timezone.utc).strftime('%d.%m.%Y')}", self.body_style),
             Paragraph(f"<b>Срок оплаты:</b> {due_date or '—'}", self.body_style)],
        ]
        header_table = Table(header_data, colWidths=[85 * mm, 85 * mm])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 16))
        
        # Реквизиты сторон
        story.append(Paragraph("<b>РЕКВИЗИТЫ</b>", self.subheading_style))
        
        sides_data = [
            [Paragraph("<b>Продавец (Исполнитель):</b>", self.body_bold_style),
             Paragraph("<b>Покупатель (Заказчик):</b>", self.body_bold_style)],
            [Paragraph(f"{seller.get('name', '—')}", self.body_style),
             Paragraph(f"{buyer.get('name', '—')}", self.body_style)],
            [Paragraph(f"ИНН: {seller.get('inn', '—')}", self.body_style),
             Paragraph(f"ИНН: {buyer.get('inn', '—')}", self.body_style)],
            [Paragraph(f"Email: {seller.get('email', '—')}", self.body_style),
             Paragraph(f"Email: {buyer.get('email', '—')}", self.body_style)],
            [Paragraph(f"Тел: {seller.get('phone', '—')}", self.body_style),
             Paragraph(f"Тел: {buyer.get('phone', '—')}", self.body_style)],
        ]
        sides_table = Table(sides_data, colWidths=[85 * mm, 85 * mm])
        sides_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, 0), (-1, 0), 1, BORDER),
            ("LINEBELOW", (0, -1), (-1, -1), 1, BORDER),
        ]))
        story.append(sides_table)
        story.append(Spacer(1, 20))
        
        # Таблица позиций
        story.append(Paragraph("<b>ПОЗИЦИИ СЧЁТА</b>", self.subheading_style))
        
        items_data = [[
            Paragraph("№", self.table_header_style),
            Paragraph("Наименование", self.table_header_style),
            Paragraph("Кол-во", self.table_header_style),
            Paragraph("Цена", self.table_header_style),
            Paragraph("Сумма", self.table_header_style),
        ]]
        
        for i, item in enumerate(items, 1):
            qty = Decimal(str(item.get("quantity", 1)))
            price = Decimal(str(item.get("unit_price", 0)))
            line_total = qty * price
            
            items_data.append([
                Paragraph(str(i), self.table_cell_style),
                Paragraph(str(item.get("description", "—")), self.table_cell_style),
                Paragraph(str(qty), self.table_cell_right),
                Paragraph(f"{price:,.2f} ₽", self.table_cell_right),
                Paragraph(f"{line_total:,.2f} ₽", self.table_cell_right),
            ])
        
        # Итого
        items_data.append([
            "", "", "",
            Paragraph("<b>ИТОГО:</b>", self.table_cell_right),
            Paragraph(f"<b>{total:,.2f} ₽</b>", self.table_cell_right),
        ])
        
        items_table = Table(items_data, colWidths=[10 * mm, 75 * mm, 20 * mm, 35 * mm, 30 * mm])
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -2), 0.5, BORDER),
            ("LINEBELOW", (0, -1), (-1, -1), 2, PRIMARY),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (1, 0), (1, -1), 6),
            ("BACKGROUND", (0, -1), (-1, -1), HexColor("#F8FAFC")),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # QR-код для оплаты
        if status in ("draft", "sent", "overdue"):
            qr_data = (
                f"ST00012|"
                f"Name={seller.get('name', '')}|"
                f"PersonalAcc={seller.get('bank_account', '')}|"
                f"BIC={seller.get('bank_bik', '')}|"
                f"PayeeINN={seller.get('inn', '')}|"
                f"Sum={int(total * 100)}|"
                f"Purpose=Оплата по счету {invoice_number}"
            )
            
            story.append(Paragraph("<b>БЫСТРАЯ ОПЛАТА ПО QR-КОДУ</b>", self.subheading_style))
            qr_img = self._create_qr(qr_data, size=35)
            story.append(qr_img)
            story.append(Paragraph(
                "Отсканируйте QR-код в мобильном банке для мгновенной оплаты",
                self.footer_style,
            ))
            story.append(Spacer(1, 16))
        
        # Примечания
        if notes:
            story.append(Paragraph("<b>ПРИМЕЧАНИЯ</b>", self.subheading_style))
            story.append(Paragraph(notes, self.body_style))
            story.append(Spacer(1, 16))
        
        # Подписи
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>ПОДПИСИ СТОРОН</b>", self.subheading_style))
        
        sign_data = [
            [Paragraph("Исполнитель:<br/><br/>_________________ / _________________", self.body_style),
             Paragraph("Заказчик:<br/><br/>_________________ / _________________", self.body_style)],
        ]
        sign_table = Table(sign_data, colWidths=[85 * mm, 85 * mm])
        sign_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        story.append(sign_table)
        
        # Футер
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"<i>Сформировано на платформе «Мир Самозанятых»</i>",
            self.footer_style,
        ))
        story.append(Paragraph(
            f"<i>Документ ID: {self._doc_id(invoice_number)} | ИНН 9724016805</i>",
            self.footer_style,
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_contract(
        self,
        template_type: str,
        data: Dict[str, Any],
        signature: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Генерация PDF договора"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )
        
        story = []
        
        # Заголовок
        story.append(Paragraph("<b>МИР САМОЗАНЯТЫХ</b>", self.title_style))
        
        template_names = {
            "gpd": "ДОГОВОР ГПД",
            "it_outsource": "ДОГОВОР IT-АУТСОРСИНГА",
            "nda": "СОГЛАШЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ",
            "license": "ЛИЦЕНЗИОННЫЙ ДОГОВОР",
            "services": "ДОГОВОР ОКАЗАНИЯ УСЛУГ",
            "act": "АКТ ВЫПОЛНЕННЫХ РАБОТ",
        }
        story.append(Paragraph(f"<b>{template_names.get(template_type, 'ДОГОВОР')}</b>", self.heading_style))
        story.append(Spacer(1, 12))
        
        # Инфо блок
        doc_info = [
            ["Дата создания:", datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")],
            ["Уникальный номер:", f"MS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{self._doc_id(data)[:8]}"],
        ]
        if signature:
            doc_info.extend([
                ["Электронная подпись:", "✓ Подписано"],
                ["Дата подписи:", signature.get("timestamp", "—")],
                ["Основание:", "ГК РФ ст. 160"],
            ])
        
        info_table = Table(doc_info, colWidths=[50 * mm, 110 * mm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), TEXT_DARK),
            ("TEXTCOLOR", (1, 0), (1, -1), PRIMARY),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Контент договора
        story.append(Paragraph("<b>1. ПРЕДМЕТ ДОГОВОРА</b>", self.heading_style))
        
        if template_type == "gpd":
            story.append(Paragraph(
                f"Исполнитель <b>{data.get('contractor_name', '—')}</b> (ИНН: {data.get('contractor_inn', '—')}) "
                f"обязуется выполнить для Заказчика <b>{data.get('client_name', '—')}</b> "
                f"(ИНН: {data.get('client_inn', '—')}) следующие работы/услуги:",
                self.body_style,
            ))
            story.append(Paragraph(f"<i>{data.get('subject', '—')}</i>", self.body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("<b>2. СТОИМОСТЬ И ПОРЯДОК РАСЧЁТОВ</b>", self.heading_style))
            story.append(Paragraph(
                f"2.1. Общая стоимость работ составляет <b>{data.get('price', '—')} ₽</b>.",
                self.body_style,
            ))
            story.append(Paragraph(
                f"2.2. Порядок оплаты: {data.get('payment_terms', '100% по факту выполнения')}",
                self.body_style,
            ))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("<b>3. СРОКИ ВЫПОЛНЕНИЯ</b>", self.heading_style))
            story.append(Paragraph(
                f"3.1. Работы подлежат выполнению в срок до <b>{data.get('deadline', '—')}</b>.",
                self.body_style,
            ))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("<b>4. ПОДПИСИ СТОРОН</b>", self.heading_style))
            story.append(Paragraph(
                "4.1. Настоящий договор составлен в простой письменной форме в соответствии с ГК РФ ст. 161.",
                self.body_style,
            ))
            story.append(Paragraph(
                "4.2. Стороны подтверждают, что условия договора им понятны и они согласны с ними.",
                self.body_style,
            ))
        
        elif template_type == "it_outsource":
            story.append(Paragraph(
                f"Исполнитель <b>{data.get('contractor_name', '—')}</b> (ИНН: {data.get('contractor_inn', '—')}) "
                f"обязуется оказывать Заказчику <b>{data.get('client_name', '—')}</b> "
                f"IT-услуги в соответствии с настоящим договором.",
                self.body_style,
            ))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("<b>Перечень услуг:</b>", self.subheading_style))
            story.append(Paragraph(data.get("services", "—"), self.body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph("<b>Условия:</b>", self.subheading_style))
            conditions = [
                f"Ежемесячная плата: <b>{data.get('monthly_fee', '—')} ₽</b>",
                f"Срок договора: <b>{data.get('contract_term', '—')} мес.</b>",
                f"Время реакции: <b>{data.get('response_time', '—')} ч</b>",
                f"Уровень SLA: <b>{data.get('sla_level', '—')}</b>",
            ]
            for cond in conditions:
                story.append(Paragraph(f"• {cond}", self.body_style))
        
        elif template_type == "nda":
            story.append(Paragraph(
                f"Настоящее Соглашение заключено между <b>{data.get('party1_name', '—')}</b> "
                f"и <b>{data.get('party2_name', '—')}</b>.",
                self.body_style,
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Предмет конфиденциальности:</b>", self.subheading_style))
            story.append(Paragraph(data.get("confidential_info", "—"), self.body_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"Срок действия: <b>{data.get('term_years', '3')} лет</b>",
                self.body_style,
            ))
        
        elif template_type == "license":
            story.append(Paragraph(
                f"Лицензиар <b>{data.get('licensor_name', '—')}</b> предоставляет "
                f"лицензиату <b>{data.get('licensee_name', '—')}</b> право использования объекта.",
                self.body_style,
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Объект лицензии:</b>", self.subheading_style))
            story.append(Paragraph(data.get("object_description", "—"), self.body_style))
            story.append(Spacer(1, 10))
            conditions = [
                f"Тип лицензии: <b>{data.get('license_type', '—')}</b>",
                f"Территория: <b>{data.get('territory', '—')}</b>",
                f"Вознаграждение: <b>{data.get('license_fee', '—')} ₽</b>",
                f"Срок: <b>{data.get('term_months', '—')} мес.</b>",
            ]
            for cond in conditions:
                story.append(Paragraph(f"• {cond}", self.body_style))
        
        elif template_type == "act":
            story.append(Paragraph(
                f"Дата составления: <b>{data.get('act_date', datetime.now(timezone.utc).strftime('%d.%m.%Y'))}</b>",
                self.body_style,
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"Исполнитель: <b>{data.get('contractor_name', '—')}</b> (ИНН: {data.get('contractor_inn', '—')})",
                self.body_style,
            ))
            story.append(Paragraph(
                f"Заказчик: <b>{data.get('client_name', '—')}</b> (ИНН: {data.get('client_inn', '—')})",
                self.body_style,
            ))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Выполненные работы:</b>", self.subheading_style))
            story.append(Paragraph(data.get("works_description", "—"), self.body_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                f"<b>Стоимость работ: {data.get('total', '—')} ₽</b>",
                self.body_bold_style,
            ))
            story.append(Paragraph(
                "Стороны подтверждают, что работы выполнены в полном объёме, в срок и надлежащего качества.",
                self.body_style,
            ))
        
        # Блок подписи
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
        story.append(Spacer(1, 12))
        
        if signature:
            story.append(Paragraph("<b>БЛОК ЭЛЕКТРОННОЙ ПОДПИСИ</b>", self.heading_style))
            story.append(Paragraph(f"Тип: {signature.get('type', '—')}", self.body_style))
            story.append(Paragraph(f"Алгоритм: {signature.get('algorithm', '—')}", self.body_style))
            story.append(Paragraph(f"Дата: {signature.get('timestamp', '—')}", self.body_style))
            story.append(Paragraph(f"Подписант ID: {signature.get('signer_id', '—')}", self.body_style))
            story.append(Paragraph(f"Правовое основание: {signature.get('legal_basis', '—')}", self.body_style))
            story.append(Spacer(1, 5))
            story.append(Paragraph(
                f"Хеш: <font size=7 face='Courier'>{signature.get('signature', '—')[:64]}...</font>",
                self.body_style,
            ))
            story.append(Paragraph(
                "<i>Данная простая электронная подпись признаётся равнозначной собственноручной подписи в соответствии с ГК РФ ст. 160.</i>",
                self.footer_style,
            ))
        else:
            story.append(Paragraph("<b>ПОДПИСИ СТОРОН:</b>", self.subheading_style))
            story.append(Paragraph(
                "Документ требует подписания. Используйте кнопку «Подписать электронной подписью» в личном кабинете.",
                self.body_style,
            ))
        
        # Футер
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "<i>Сформировано на платформе «Мир Самозанятых»</i>",
            self.footer_style,
        ))
        story.append(Paragraph(
            f"<i>Документ ID: {self._doc_id(data)} | ИНН 9724016805</i>",
            self.footer_style,
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


# Singleton
pdf_service = PDFService()
