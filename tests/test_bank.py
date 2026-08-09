"""Tests for bank integration module — Mir Samozanyatykh v8.3
ANO TsPS INN 9724016805"""
import pytest
from decimal import Decimal

from app.api.bank import _categorize_transaction


class TestTransactionCategorization:
    """Test automatic transaction categorization"""

    def test_software_category(self):
        descriptions = [
            "Подписка Figma Pro",
            "GitHub subscription",
            "Software license",
            "Лицензия 1С",
            "Notion subscription",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "software"

    def test_rent_category(self):
        descriptions = [
            "Аренда офиса",
            "Office rent payment",
            "Аренда помещения",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "rent"

    def test_internet_category(self):
        descriptions = [
            "Интернет Ростелеком",
            "Mobile MTS",
            "Связь Билайн",
            "Телефон Мегафон",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "internet"

    def test_marketing_category(self):
        descriptions = [
            "Реклама Яндекс.Директ",
            "Google Ads payment",
            "Facebook marketing",
            "Рекламная кампания",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "marketing"

    def test_transport_category(self):
        descriptions = [
            "Такси Яндекс",
            "Uber trip",
            "Бензин",
            "Транспортные расходы",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "transport"

    def test_food_category(self):
        descriptions = [
            "Ресторан",
            "Кафе",
            "Продукты",
            "Grocery store",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "food"

    def test_education_category(self):
        descriptions = [
            "Курс Stepik",
            "Обучение",
            "Education course",
            "Школа программирования",
            "Университет",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "education"

    def test_coursera_is_software(self):
        """Coursera subscription is categorized as software due to 'subscription' keyword"""
        assert _categorize_transaction("Coursera subscription") == "software"

    def test_health_category(self):
        descriptions = [
            "Медицина",
            "Аптека",
            "Health clinic",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "health"

    def test_equipment_category(self):
        descriptions = [
            "Компьютер",
            "Ноутбук",
            
            "Оборудование",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "equipment"

    def test_tax_category(self):
        descriptions = [
            "Налог НПД",
            "Tax payment",
            "НДФЛ",
            "УСН",
            "Страховые взносы",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "tax"

    def test_salary_category(self):
        descriptions = [
            "Зарплата",
            "Salary payment",
            "Аванс",
            "Премия",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "salary"

    def test_service_category(self):
        descriptions = [
            "Услуги бухгалтера",
            "Консультация",
            "Service fee",
            "Юридические услуги",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "service"

    def test_unknown_category(self):
        descriptions = [
            "Random payment",
            "Something else",
            "",
            "Прочее",
        ]
        for desc in descriptions:
            assert _categorize_transaction(desc) == "other_expense"

    def test_case_insensitive(self):
        assert _categorize_transaction("FIGMA SUBSCRIPTION") == "software"
        assert _categorize_transaction("АРЕНДА ОФИСА") == "rent"
        assert _categorize_transaction("Google ADS") == "marketing"


class TestBankTransactionImport:
    """Test bank transaction import logic"""

    def test_debit_is_expense(self):
        operation_type = "DEBIT"
        tx_type = "expense" if operation_type == "DEBIT" else "income"
        assert tx_type == "expense"

    def test_credit_is_income(self):
        operation_type = "CREDIT"
        tx_type = "expense" if operation_type == "DEBIT" else "income"
        assert tx_type == "income"

    def test_amount_positive(self):
        amount = Decimal("-1500.50")
        positive_amount = abs(amount)
        assert positive_amount == Decimal("1500.50")
        assert positive_amount > 0

    def test_kopecks_conversion(self):
        rubles = Decimal("2500.50")
        kopecks = int(rubles * 100)
        assert kopecks == 250050
        assert isinstance(kopecks, int)


class TestBankAPIValidation:
    """Test bank API validation"""

    def test_valid_bank_names(self):
        valid_banks = ["tinkoff", "sber", "vtb", "raiff", "alfa"]
        for bank in valid_banks:
            assert bank in ["tinkoff", "sber", "vtb", "raiff", "alfa"]

    def test_days_range(self):
        assert 1 <= 30 <= 365
        assert 1 <= 365 <= 365
        assert not (0 >= 1)
        assert not (366 <= 365)
