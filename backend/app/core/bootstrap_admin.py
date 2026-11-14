import argparse
import asyncio
import logging
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.entities import AuditLog, Profile

logger = logging.getLogger("cms_bootstrap")
logging.basicConfig(level=logging.INFO)


async def bootstrap_admin(auth_user_id_str: str, full_name: str, email: str, phone: str = "") -> None:
    try:
        auth_user_id = uuid.UUID(auth_user_id_str)
    except ValueError:
        logger.error("Invalid UUID format for auth_user_id: %s", auth_user_id_str)
        return

    async with AsyncSessionLocal() as session:
        # Check if an administrator already exists
        admin_check = await session.execute(select(Profile).where(Profile.role == "administrator"))
        existing_admin = admin_check.scalars().first()
        if existing_admin:
            logger.warning(
                "An administrator already exists in the system (Email: %s, Profile ID: %s). Bootstrap aborted to prevent unauthorized overwrite.",
                existing_admin.email,
                existing_admin.id,
            )
            return

        # Check if profile already exists for this auth_user_id
        profile_check = await session.execute(select(Profile).where(Profile.auth_user_id == auth_user_id))
        existing_profile = profile_check.scalars().first()
        if existing_profile:
            logger.warning("Profile for Auth ID %s already exists. Updating to administrator.", auth_user_id)
            existing_profile.role = "administrator"
            existing_profile.full_name = full_name
            existing_profile.email = email
            target_profile = existing_profile
        else:
            target_profile = Profile(
                auth_user_id=auth_user_id,
                role="administrator",
                full_name=full_name,
                email=email,
                phone=phone,
                is_active=True,
            )
            session.add(target_profile)

        await session.flush()

        # Audit log creation
        audit = AuditLog(
            actor_profile_id=target_profile.id,
            action="BOOTSTRAP_INITIAL_ADMINISTRATOR",
            entity_type="profiles",
            entity_id=target_profile.id,
            new_values={"role": "administrator", "email": email, "auth_user_id": str(auth_user_id)},
        )
        session.add(audit)
        await session.commit()
        logger.info("Successfully bootstrapped initial administrator: %s (%s)", full_name, email)


def main():
    parser = argparse.ArgumentParser(description="Bootstrap initial system administrator for Housing Society CMS.")
    parser.add_argument("--auth-user-id", required=True, help="Supabase Auth UUID of the administrator user")
    parser.add_argument("--full-name", required=True, help="Full name of administrator")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--phone", default="", help="Administrator contact phone")
    args = parser.parse_args()

    asyncio.run(bootstrap_admin(args.auth_user_id, args.full_name, args.email, args.phone))


if __name__ == "__main__":
    main()
