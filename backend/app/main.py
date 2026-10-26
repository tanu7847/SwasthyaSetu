from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4
import csv
from pathlib import Path
import httpx
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import db, client, ensure_indexes
from .schemas import RegisterIn, LoginIn, SymptomIn, NoteDraftIn, EmergencyIn
from .security import hash_password, verify_password, create_token, current_user, require_roles

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")
        await ensure_indexes()
    except Exception:
        # App can start for API docs even if MongoDB isn't ready; DB routes will fail until it is.
        pass
    yield
    client.close()

app = FastAPI(title="SwasthyaSetu API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def now_iso():
    return datetime.now(timezone.utc).isoformat()

async def audit(actor, action, details=None):
    await db.audit_logs.insert_one({"actor_id": str(actor), "action": action, "details": details or {}, "created_at": now_iso()})

@app.get("/")
async def root():
    return {"service": "SwasthyaSetu API", "status": "ok", "dispatch": "SIMULATION_ONLY"}

@app.get("/health")
async def health():
    try:
        await client.admin.command("ping")
        return {"api": "ok", "mongodb": "ok"}
    except Exception:
        return {"api": "ok", "mongodb": "unavailable"}

@app.post("/auth/register")
async def register(payload: RegisterIn):
    if payload.role != "patient":
        raise HTTPException(403, "Self-registration is patient-only. Staff accounts require administrator provisioning.")
    email = payload.email.strip().lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "Email already registered")
    user_id = str(uuid4())
    doc = {"_id": user_id, "email": email, "password_hash": hash_password(payload.password),
           "role": "patient", "display_name": payload.display_name, "language": payload.language,
           "status": "active", "created_at": now_iso()}
    await db.users.insert_one(doc)
    patient_id = "PAT-" + uuid4().hex[:10].upper()
    await db.patients.insert_one({"patient_id": patient_id, "user_id": user_id, "language": payload.language, "created_at": now_iso()})
    await audit(user_id, "patient_registered")
    return {"message": "Registration successful", "patient_id": patient_id}

@app.post("/auth/login")
async def login(payload: LoginIn):
    user = await db.users.find_one({"email": payload.email.strip().lower()})
    if not user or not verify_password(payload.password, user.get("password_hash", "")) or user.get("status") != "active":
        raise HTTPException(401, "Incorrect email or password")
    token = create_token(user["_id"], user["role"])
    await audit(user["_id"], "login")
    return {"access_token": token, "token_type": "bearer", "role": user["role"],
            "display_name": user.get("display_name", ""), "language": user.get("language", "en")}

@app.get("/me")
async def me(user=Depends(current_user)):
    return {"id": user["_id"], "email": user["email"], "role": user["role"],
            "display_name": user.get("display_name", ""), "language": user.get("language", "en")}

@app.post("/triage")
async def triage(payload: SymptomIn, user=Depends(current_user)):
    # Illustrative keyword screen only; never a substitute for validated clinical triage.
    text = payload.symptoms.lower()
    warning_terms = ["chest pain", "difficulty breathing", "can't breathe", "cannot breathe",
                     "unconscious", "severe bleeding", "stroke", "fits", "seizure"]
    warning = any(term in text for term in warning_terms)
    result = {"possible_warning_sign": warning,
              "message": ("Possible emergency warning sign. Do not wait for AI or this app; contact local emergency services now."
                          if warning else "No configured warning keyword detected. This does not rule out an emergency."),
              "disclaimer": "Illustrative prototype rules; not validated medical triage."}
    record = {"user_id": user["_id"], "symptoms": payload.symptoms, "duration": payload.duration,
              "language": payload.language, "allergies": payload.allergies,
              "current_medications": payload.current_medications, "result": result, "created_at": now_iso()}
    await db.symptoms.insert_one(record)
    await audit(user["_id"], "triage_screened", {"possible_warning_sign": warning})
    return result

@app.post("/emergency-requests")
async def create_emergency(payload: EmergencyIn, user=Depends(current_user)):
    # This is intentionally a simulation; no emergency service/ambulance is contacted.
    request_id = "EM-" + uuid4().hex[:12].upper()
    doc = {"request_id": request_id, "user_id": user["_id"], "symptoms": payload.symptoms,
           "location_text": payload.location_text, "callback": payload.callback,
           "symptoms_happening_now": payload.symptoms_happening_now,
           "status": "SIMULATED_REQUEST_CREATED", "dispatch_integration": "NOT_CONFIGURED",
           "created_at": now_iso(), "audit_history": [{"event": "created", "at": now_iso()}]}
    await db.emergency_requests.insert_one(doc)
    await audit(user["_id"], "emergency_request_simulated", {"request_id": request_id})
    return {"request_id": request_id, "status": doc["status"],
            "warning": "SIMULATION ONLY: no ambulance has been called. Contact emergency services directly if needed."}

@app.get("/emergency-requests")
async def list_emergency(user=Depends(require_roles("operator", "admin"))):
    items = await db.emergency_requests.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return items

@app.get("/dashboard/summary")
async def summary(user=Depends(require_roles("doctor", "operator", "admin"))):
    return {"users": await db.users.count_documents({}),
            "patients": await db.patients.count_documents({}),
            "consultations": await db.consultations.count_documents({}),
            "emergency_requests_simulated": await db.emergency_requests.count_documents({})}

@app.get("/medicines/search")
async def medicines_search(q: str = ""):
    # Demo catalogue search only. This endpoint must not recommend medication.
    path = Path(__file__).resolve().parents[1] / "data" / "medicines.csv"
    matches = []
    if q.strip() and path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if q.lower() in (row.get("name", "") + " " + row.get("category", "")).lower():
                    matches.append(row)
    return {"results": matches[:20], "notice": "Catalogue lookup only; not a prescribing or treatment recommendation."}

@app.post("/ai/clinical-note-draft")
async def clinical_note_draft(payload: NoteDraftIn, user=Depends(require_roles("doctor", "admin"))):
    if not payload.symptoms.strip():
        raise HTTPException(400, "Symptoms are required")
    if not settings.groq_api_key:
        return {"draft": True, "provider": "fallback",
                "note": {"summary": "AI is not configured. Clinician must write and verify the note manually.",
                         "reported_symptoms": payload.symptoms, "history": payload.history,
                         "language": payload.language, "transcript": payload.transcript},
                "safety": "No diagnosis or medication recommendation has been generated."}
    prompt = ("Create a concise clinical documentation DRAFT from the information below. "
              "Do not invent facts, do not diagnose, do not recommend or prescribe medicines. "
              "Clearly separate patient-reported information from clinician-confirmed findings. "
              "Return plain text with sections: Summary, Reported symptoms, Relevant history, "
              "Missing information, Safety considerations. This is for a qualified clinician to review.\n"
              f"Language: {payload.language}\nSymptoms: {payload.symptoms}\nHistory: {payload.history}\n"
              f"Transcript: {payload.transcript}")
    try:
        async with httpx.AsyncClient(timeout=35) as client_http:
            response = await client_http.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={"model": settings.groq_chat_model, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.2})
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
    except Exception:
        return {"draft": True, "provider": "fallback",
                "note": {"summary": "AI service unavailable. Review the source information and create the note manually.",
                         "reported_symptoms": payload.symptoms, "history": payload.history},
                "safety": "AI failure was handled safely; no prescription was created."}
    await audit(user["_id"], "ai_note_draft_generated")
    return {"draft": True, "provider": "groq", "note": content,
            "safety": "Clinician review required. This is not a diagnosis or prescription."}

@app.post("/ai/transcribe")
async def transcribe_audio(file: UploadFile = File(...), user=Depends(current_user)):
    if not settings.groq_api_key:
        raise HTTPException(503, "Set GROQ_API_KEY in backend/.env to enable cloud transcription")
    if file.content_type not in {"audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/x-m4a", "audio/ogg"}:
        raise HTTPException(415, "Unsupported audio content type")
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "Audio file must be under 20 MB")
    try:
        async with httpx.AsyncClient(timeout=90) as client_http:
            response = await client_http.post("https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                data={"model": settings.groq_stt_model, "response_format": "json"},
                files={"file": (file.filename or "audio.webm", raw, file.content_type)})
            response.raise_for_status()
            result = response.json()
    except Exception:
        raise HTTPException(502, "Transcription provider failed; retry or enter transcript manually")
    return {"transcript": result.get("text", ""), "draft": True,
            "notice": "Review transcript for errors. RNNoise is not applied by this endpoint."}

@app.get("/doctor/review-queue")
async def review_queue(user=Depends(require_roles("doctor", "admin"))):
    return {"items": [], "message": "Starter endpoint. Connect consultation records and doctor credential verification before clinical use."}
