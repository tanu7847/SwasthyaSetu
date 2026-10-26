import asyncio
from app.db import db, ensure_indexes
from app.security import hash_password

DEMO_USERS = [
    ("patient@example.test", "PatientDemo123!", "patient", "Demo Patient"),
    ("doctor@example.test", "DoctorDemo123!", "doctor", "Demo Doctor"),
    ("operator@example.test", "OperatorDemo123!", "operator", "Demo Operator"),
    ("admin@example.test", "AdminDemo123!", "admin", "Demo Admin"),
]

async def main():
    await ensure_indexes()
    for email, password, role, name in DEMO_USERS:
        await db.users.update_one({"email": email}, {"$set": {
            "_id": email, "email": email, "password_hash": hash_password(password),
            "role": role, "display_name": name, "language": "en", "status": "active"
        }}, upsert=True)
    print("Seed complete. Demo accounts created/updated.")
    print("Use synthetic data only.")
    from app.db import client
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
