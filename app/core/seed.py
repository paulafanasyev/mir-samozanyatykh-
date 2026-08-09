"""Seed data for Mir Samozanyatykh v6.6
ANO CPS INN 9724016805
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.models import ContractTemplate


CONTRACT_TEMPLATES = [
    {
        "name": "Dogovor GPH",
        "category": "gpd",
        "content": """DOGOWOR No. {{contract_number}}

Mesto zaklyucheniya: {{city}}
Data: {{date}}

Ispolnitel: {{executor_name}}, INN {{executor_inn}}
Zakazchik: {{client_name}}, INN {{client_inn}}

1. PREDMET DOGOWORA
Ispolnitel okazyvaet uslugi: {{services_description}}.

2. STOWIMOST I PORYADOK RASCHETOW
Obshaya stoimost uslug: {{amount}} ₽.
Zakazchik oplachivaet w techeniye {{payment_days}} dney.

3. SROWKI
Nachalo rabot: {{start_date}}.
Okonchaniye rabot: {{end_date}}.

4. PODPISI
Ispolnitel: _________________ / {{executor_name}} /
Zakazchik: _________________ / {{client_name}} /
""",
        "variables": ["contract_number", "city", "date", "executor_name", "executor_inn", "client_name", "client_inn", "services_description", "amount", "payment_days", "start_date", "end_date"],
        "is_premium": False,
        "is_active": True,
        "sort_order": 1,
    },
    {
        "name": "Dogowor IT-autsorsinga",
        "category": "it_outsource",
        "content": """DOGOWOR No. {{contract_number}}

Mesto zaklyucheniya: {{city}}
Data: {{date}}

Ispolnitel: {{executor_name}}, INN {{executor_inn}}
Zakazchik: {{client_name}}, INN {{client_inn}}

1. PREDMET DOGOWORA
Ispolnitel predostavlyaet uslugi po razrabotke i soprovozhdeniyu programmnogo obespecheniya.

2. OBYEM USLUG
{{services_description}}

3. STOIMOST
Mesyachnaya stoimost: {{monthly_amount}} ₽.
Srok deystviya: {{contract_term}} mesyatsev.

4. PORYADOK OPLATY
Oplata do {{payment_day}}-go chisla kazhdogo mesyatsa.

5. PODPISI
Ispolnitel: _________________ / {{executor_name}} /
Zakazchik: _________________ / {{client_name}} /
""",
        "variables": ["contract_number", "city", "date", "executor_name", "executor_inn", "client_name", "client_inn", "services_description", "monthly_amount", "contract_term", "payment_day"],
        "is_premium": False,
        "is_active": True,
        "sort_order": 2,
    },
    {
        "name": "NDA (Soglasheniye o konfidentsialnosti)",
        "category": "nda",
        "content": """SOGLASHENIYE O KONFIDENSTIALNOSTI No. {{contract_number}}

Mesto zaklyucheniya: {{city}}
Data: {{date}}

Storona 1: {{party1_name}}, INN {{party1_inn}}
Storona 2: {{party2_name}}, INN {{party2_inn}}

1. PREDMET
Storony obyazuyutsya ne razglaschat konfidentsialnuyu informatsiyu, poluchennuyu v khode sotrudnichestva.

2. SROK DEYSTVIYA
Srok deystviya: {{term_years}} let s momenta podpisaniya.

3. OTWETSTWENNOST
Za razglasheniye konfidentsialnoy informatsii — shtraf {{penalty_amount}} ₽.

4. PODPISI
Storona 1: _________________ / {{party1_name}} /
Storona 2: _________________ / {{party2_name}} /
""",
        "variables": ["contract_number", "city", "date", "party1_name", "party1_inn", "party2_name", "party2_inn", "term_years", "penalty_amount"],
        "is_premium": False,
        "is_active": True,
        "sort_order": 3,
    },
    {
        "name": "Akt vypolnennykh rabot",
        "category": "act",
        "content": """AKT No. {{act_number}} ot {{date}}

Ispolnitel: {{executor_name}}, INN {{executor_inn}}
Zakazchik: {{client_name}}, INN {{client_inn}}

1. PREDMET
Ispolnitel vypolnil sleduyushchiye raboty:
{{works_description}}

2. STOIMOST
Obshaya stoimost: {{total_amount}} ₽.
NDS: {{vat_amount}} ₽.
Itogo: {{total_with_vat}} ₽.

3. ZAKLYUCHENIYE
Raboty vypolneny v polnom obyeme, v sootvetstvii s dogovorom.

PODPISI:
Ot Ispolnitelya: _________________ / {{executor_name}} /
Ot Zakazchika: _________________ / {{client_name}} /
""",
        "variables": ["act_number", "date", "executor_name", "executor_inn", "client_name", "client_inn", "works_description", "total_amount", "vat_amount", "total_with_vat"],
        "is_premium": False,
        "is_active": True,
        "sort_order": 4,
    },
    {
        "name": "Dogowor litsenzii (Premium)",
        "category": "license",
        "content": """LITSENZIONNYY DOGOWOR No. {{contract_number}}

Mesto zaklyucheniya: {{city}}
Data: {{date}}

Litsenzar: {{licensor_name}}, INN {{licensor_inn}}
Litsenziat: {{licensee_name}}, INN {{licensee_inn}}

1. PREDMET
Litsenzar predostavlyaet litsenziyu na ispolzovaniye: {{software_name}}.

2. TIP LITSENZII
{{license_type}} — ispolzovaniye na {{max_users}} polzovateley.

3. STOIMOST
Litsenzionnyy platezh: {{license_fee}} ₽.
Srok deystviya: {{term_years}} let.

4. OGRANICHENIYA
Zapreshchaetsya: peredacha tretim litsam, modifikatsiya, obratnaya inzheneriya.

5. PODPISI
Litsenzar: _________________ / {{licensor_name}} /
Litsenziat: _________________ / {{licensee_name}} /
""",
        "variables": ["contract_number", "city", "date", "licensor_name", "licensor_inn", "licensee_name", "licensee_inn", "software_name", "license_type", "max_users", "license_fee", "term_years"],
        "is_premium": True,
        "is_active": True,
        "sort_order": 5,
    },
]


async def seed_contract_templates(db: AsyncSession):
    """Seed contract templates into database"""
    for template_data in CONTRACT_TEMPLATES:
        template = ContractTemplate(**template_data)
        db.add(template)
    await db.commit()
    print(f"Seeded {len(CONTRACT_TEMPLATES)} contract templates")


async def main():
    async with async_session_maker() as session:
        await seed_contract_templates(session)


if __name__ == "__main__":
    asyncio.run(main())
