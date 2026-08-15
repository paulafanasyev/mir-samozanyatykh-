"""
Seed data for initial deployment
MIR Samozanyatykh v8.4 - ANO TsPS INN 9724016805
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from app.core.security import get_password_hash


async def seed_database():
    """Fill database with initial data"""
    async with async_session() as session:
        from sqlalchemy import select, func
        from app.models import User, SubscriptionTier, Achievement, FAQ, BlogPost

        result = await session.execute(select(func.count()).select_from(User))
        user_count = result.scalar()

        if user_count > 0:
            print("Database already seeded, skipping...")
            return

        print("Seeding database...")

        # Admin user
        admin = User(
            email="admin@mirsamozanyatykh.ru",
            hashed_password=get_password_hash("MirSamo2026!Admin#Secure"),
            full_name="Administrator",
            is_active=True,
            is_superuser=True,
            role="admin",
            phone="+79000000000",
            inn="9724016805",
        )
        session.add(admin)

        # Subscription tiers
        tiers = [
            SubscriptionTier(name="START", slug="start", price=0,
                description="Free starter plan",
                features='["base", "profile", "calculator"]',
                max_contracts=5, max_clients=10, ai_requests_per_day=10),
            SubscriptionTier(name="PRO", slug="pro", price=300,
                description="Professional plan",
                features='["base", "profile", "calculator", "contracts", "ai", "crm"]',
                max_contracts=50, max_clients=100, ai_requests_per_day=100),
            SubscriptionTier(name="BUSINESS", slug="business", price=990,
                description="Business plan",
                features='["base", "profile", "calculator", "contracts", "ai", "crm", "marketplace", "priority"]',
                max_contracts=999999, max_clients=999999, ai_requests_per_day=999999),
            SubscriptionTier(name="ENTERPRISE", slug="enterprise", price=0,
                description="Enterprise plan (custom)",
                features='["all"]', max_contracts=999999, max_clients=999999, ai_requests_per_day=999999),
        ]
        for tier in tiers:
            session.add(tier)

        # Achievements
        achievements = [
            Achievement(name="First Steps", description="Register on platform", icon="star", points=10, slug="first-steps"),
            Achievement(name="First Contract", description="Create your first contract", icon="file", points=25, slug="first-contract"),
            Achievement(name="Tax Guru", description="Use NPD calculator 10 times", icon="calculator", points=50, slug="tax-guru"),
            Achievement(name="AI Friend", description="Ask Svetlana 50 questions", icon="robot", points=75, slug="ai-friend"),
            Achievement(name="Pro User", description="Subscribe to PRO plan", icon="crown", points=100, slug="pro-subscriber"),
        ]
        for ach in achievements:
            session.add(ach)

        # FAQs
        faqs = [
            FAQ(question="What is NPD?", answer="Professional Income Tax - special tax regime for self-employed. 4% for individuals, 6% for legal entities.", category="Taxes", order=1),
            FAQ(question="How to register as self-employed?", answer="Through My Tax app, partner banks, or our platform.", category="Registration", order=2),
            FAQ(question="What documents are needed?", answer="Passport, INN, SNILS, phone and email.", category="Registration", order=3),
            FAQ(question="How to create a GPD contract?", answer="In Contracts section select template, fill data, generate PDF.", category="Contracts", order=4),
            FAQ(question="How does AI Svetlana work?", answer="Uses OpenRouter API for tax and business questions. No data storage.", category="AI", order=5),
        ]
        for faq in faqs:
            session.add(faq)

        # Blog posts
        blog_posts = [
            BlogPost(title="NPD in 2026: What Changed", slug="npd-2026-changes",
                content="Important changes in 2026: income limit raised to 5M rubles, new activity categories, simplified reporting.",
                excerpt="Key NPD changes for 2026", author="ANO TsPS", category="Taxes",
                tags='["NPD", "2026", "taxes"]', is_published=True, views=1523),
            BlogPost(title="How to Create GPD Contract", slug="gpd-contract-guide",
                content="Complete guide to GPD contracts with templates and examples.",
                excerpt="Guide to GPD contracts for self-employed", author="Legal Dept ANO TsPS", category="Contracts",
                tags='["GPD", "contract", "template"]', is_published=True, views=2341),
        ]
        for post in blog_posts:
            session.add(post)

        await session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
