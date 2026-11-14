import asyncio
import logging
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.entities import Block, Category, UtilityCompany

logger = logging.getLogger("cms_seed")
logging.basicConfig(level=logging.INFO)

INITIAL_BLOCKS = [
    {"code": "BLK-A", "name": "Block A"},
    {"code": "BLK-B", "name": "Block B"},
    {"code": "BLK-C", "name": "Block C"},
    {"code": "BLK-D", "name": "Block D"},
    {"code": "BLK-E", "name": "Block E"},
    {"code": "BLK-F", "name": "Block F"},
]

INITIAL_CATEGORIES = [
    {
        "name": "Electricity",
        "description": "Electrical supply, internal distribution, wiring, meters and society electrical fixtures.",
    },
    {
        "name": "Water",
        "description": "Water supply, society water pump, lines, valves and tanker coordination.",
    },
    {
        "name": "Gas",
        "description": "Gas line leakage, low pressure, and SSGC supply lines.",
    },
    {
        "name": "Sewerage",
        "description": "Drainage lines, manhole blockages, overflowing sewerage and society sanitation.",
    },
    {
        "name": "Streetlights",
        "description": "Street pole lighting, common area illumination, fixtures and timers.",
    },
]

INITIAL_UTILITIES = [
    {
        "name": "K-Electric",
        "contact_phone": "+92-21-118",
        "contact_email": "complaints@ke.com.pk",
        "contact_info": "K-Electric 24/7 Helpline & Karachi Fault Escalation",
    },
    {
        "name": "SSGC",
        "contact_phone": "+92-21-1199",
        "contact_email": "customer.service@ssgc.com.pk",
        "contact_info": "Sui Southern Gas Company Emergency Center, Karachi",
    },
    {
        "name": "Water Board",
        "contact_phone": "+92-21-99245138",
        "contact_email": "info@kwsc.gos.pk",
        "contact_info": "Karachi Water & Sewerage Corporation (KWSC) Complaint Cell",
    },
]


async def seed_database() -> None:
    async with AsyncSessionLocal() as session:
        # 1. Seed Blocks
        for b_data in INITIAL_BLOCKS:
            res = await session.execute(select(Block).where(Block.code == b_data["code"]))
            existing = res.scalars().first()
            if not existing:
                block = Block(code=b_data["code"], name=b_data["name"])
                session.add(block)
                logger.info("Seeded block: %s - %s", b_data["code"], b_data["name"])

        # 2. Seed Categories
        for c_data in INITIAL_CATEGORIES:
            res = await session.execute(select(Category).where(Category.name == c_data["name"]))
            existing = res.scalars().first()
            if not existing:
                cat = Category(name=c_data["name"], description=c_data["description"])
                session.add(cat)
                logger.info("Seeded category: %s", c_data["name"])

        # 3. Seed Utility Companies
        for u_data in INITIAL_UTILITIES:
            res = await session.execute(select(UtilityCompany).where(UtilityCompany.name == u_data["name"]))
            existing = res.scalars().first()
            if not existing:
                util = UtilityCompany(
                    name=u_data["name"],
                    contact_phone=u_data["contact_phone"],
                    contact_email=u_data["contact_email"],
                    contact_info=u_data["contact_info"],
                )
                session.add(util)
                logger.info("Seeded utility company: %s", u_data["name"])

        await session.commit()
        logger.info("Database seed complete.")


if __name__ == "__main__":
    asyncio.run(seed_database())
