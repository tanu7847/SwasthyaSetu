from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2500)
db = client[settings.mongodb_db]

async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.patients.create_index("patient_id", unique=True)
    await db.emergency_requests.create_index("request_id", unique=True)
    await db.audit_logs.create_index("created_at")
