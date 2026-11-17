import asyncio
import datetime
import logging
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.entities import (
    Block,
    Category,
    Complaint,
    Incident,
    IncidentComplaintLink,
    Profile,
    Property,
    PropertyResident,
    Resident,
    UtilityCompany,
    WorkAssignment,
)

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

DEMO_PROFILES = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "auth_user_id": uuid.UUID("a1111111-1111-1111-1111-111111111111"),
        "role": "resident",
        "full_name": "Fahad Resident (Flat A-204)",
        "phone": "+92-300-1234567",
        "email": "resident@jauhar.com",
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "auth_user_id": uuid.UUID("a2222222-2222-2222-2222-222222222222"),
        "role": "complaint_officer",
        "full_name": "Tariq Mehmood (Complaint Officer)",
        "phone": "+92-300-7654321",
        "email": "officer@jauhar.com",
    },
    {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "auth_user_id": uuid.UUID("a3333333-3333-3333-3333-333333333333"),
        "role": "field_staff",
        "full_name": "Imran Khan (Society Electrician)",
        "phone": "+92-321-9876543",
        "email": "staff@jauhar.com",
    },
    {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "auth_user_id": uuid.UUID("a4444444-4444-4444-4444-444444444444"),
        "role": "administrator",
        "full_name": "Society Administrator",
        "phone": "+92-333-5555555",
        "email": "admin@jauhar.com",
    },
]


async def seed_database() -> None:
    async with AsyncSessionLocal() as session:
        # 1. Seed Blocks
        block_map = {}
        for b_data in INITIAL_BLOCKS:
            res = await session.execute(select(Block).where(Block.code == b_data["code"]))
            block = res.scalars().first()
            if not block:
                block = Block(code=b_data["code"], name=b_data["name"])
                session.add(block)
                await session.flush()
                logger.info("Seeded block: %s - %s", b_data["code"], b_data["name"])
            block_map[b_data["code"]] = block

        # 2. Seed Categories
        cat_map = {}
        for c_data in INITIAL_CATEGORIES:
            res = await session.execute(select(Category).where(Category.name == c_data["name"]))
            cat = res.scalars().first()
            if not cat:
                cat = Category(name=c_data["name"], description=c_data["description"])
                session.add(cat)
                await session.flush()
                logger.info("Seeded category: %s", c_data["name"])
            cat_map[c_data["name"]] = cat

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

        # 4. Seed Properties
        properties_to_seed = [
            {"block_code": "BLK-A", "number": "A-101", "type": "flat", "note": "1st Floor"},
            {"block_code": "BLK-A", "number": "A-102", "type": "flat", "note": "1st Floor"},
            {"block_code": "BLK-A", "number": "A-204", "type": "flat", "note": "2nd Floor Main"},
            {"block_code": "BLK-B", "number": "B-101", "type": "house", "note": "Ground+1 West Open"},
            {"block_code": "BLK-B", "number": "B-102", "type": "house", "note": "Corner House"},
            {"block_code": "BLK-C", "number": "C-201", "type": "flat", "note": "Park Facing"},
            {"block_code": "BLK-D", "number": "D-105", "type": "house", "note": "East Open Single Story"},
        ]
        prop_map = {}
        for p_data in properties_to_seed:
            block = block_map.get(p_data["block_code"])
            if not block:
                continue
            res = await session.execute(
                select(Property).where(Property.block_id == block.id, Property.property_number == p_data["number"])
            )
            prop = res.scalars().first()
            if not prop:
                prop = Property(
                    block_id=block.id,
                    property_number=p_data["number"],
                    property_type=p_data["type"],
                    address_note=p_data["note"],
                )
                session.add(prop)
                await session.flush()
                logger.info("Seeded property: %s in %s", p_data["number"], p_data["block_code"])
            prop_map[p_data["number"]] = prop

        # 5. Seed Profiles
        for p_data in DEMO_PROFILES:
            res = await session.execute(select(Profile).where(Profile.id == p_data["id"]))
            profile = res.scalars().first()
            if not profile:
                profile = Profile(
                    id=p_data["id"],
                    auth_user_id=p_data["auth_user_id"],
                    role=p_data["role"],
                    full_name=p_data["full_name"],
                    phone=p_data["phone"],
                    email=p_data["email"],
                    is_active=True,
                )
                session.add(profile)
                logger.info("Seeded profile: %s (%s)", p_data["full_name"], p_data["role"])

        await session.flush()

        # 6. Seed Resident & Property Association (Flat A-204)
        res_id = uuid.UUID("55555555-5555-5555-5555-555555555555")
        res_check = await session.execute(select(Resident).where(Resident.id == res_id))
        resident = res_check.scalars().first()
        if not resident:
            resident = Resident(
                id=res_id,
                profile_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                verification_status="verified",
                verified_by=uuid.UUID("44444444-4444-4444-4444-444444444444"),
                verified_at=datetime.datetime.now(datetime.timezone.utc),
            )
            session.add(resident)
            await session.flush()
            logger.info("Seeded verified resident: Fahad Resident")

        a204 = prop_map.get("A-204")
        if a204:
            assoc_check = await session.execute(
                select(PropertyResident).where(
                    PropertyResident.resident_id == resident.id,
                    PropertyResident.property_id == a204.id,
                )
            )
            if not assoc_check.scalars().first():
                assoc = PropertyResident(
                    resident_id=resident.id,
                    property_id=a204.id,
                    relationship_type="owner",
                    valid_from=datetime.date(2024, 1, 1),
                    is_primary_contact=True,
                )
                session.add(assoc)
                logger.info("Associated Resident with property A-204")

        # 7. Seed Initial Complaint & Incident
        elec_cat = cat_map.get("Electricity")
        if elec_cat and a204:
            cmp_check = await session.execute(select(Complaint).where(Complaint.complaint_number == "CMP-2026-0001"))
            cmp_record = cmp_check.scalars().first()
            if not cmp_record:
                cmp_record = Complaint(
                    complaint_number="CMP-2026-0001",
                    resident_id=resident.id,
                    property_id=a204.id,
                    category_id=elec_cat.id,
                    description="Main electrical distribution box sparking and breaker tripping in Block A corridor.",
                    status="in_progress",
                    is_urgent=True,
                    urgency_reason="Electrical sparking hazard endangering corridor residents.",
                    intake_channel="portal",
                )
                session.add(cmp_record)
                await session.flush()
                logger.info("Seeded initial complaint: CMP-2026-0001")

                inc_record = Incident(
                    incident_number="INC-2026-0001",
                    category_id=elec_cat.id,
                    title="Block A Main Power Distribution Sparking & Trip Fault",
                    description="Investigation of electrical surge and burnt distribution breaker on Block A 2nd floor.",
                    priority="urgent",
                    status="in_progress",
                    area_description="Block A, 2nd Floor Distribution Board",
                    created_by=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                )
                session.add(inc_record)
                await session.flush()
                logger.info("Seeded initial incident: INC-2026-0001")

                link = IncidentComplaintLink(
                    incident_id=inc_record.id,
                    complaint_id=cmp_record.id,
                    linked_by=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                )
                session.add(link)

                assignment = WorkAssignment(
                    incident_id=inc_record.id,
                    staff_profile_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                    assigned_by_profile_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                    status="in_progress",
                )
                session.add(assignment)
                logger.info("Assigned INC-2026-0001 to Imran Khan (field_staff)")

        await session.commit()
        logger.info("Database seed complete successfully with sample data!")


if __name__ == "__main__":
    asyncio.run(seed_database())
