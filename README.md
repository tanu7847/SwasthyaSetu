# SwasthyaSetu — Native Android + AI Backend

A runnable starter project for a native Java Android app, FastAPI backend, MongoDB, Groq AI documentation, Whisper-compatible transcription, and React staff dashboard.

## Important scope and safety notes
- This is a development prototype with synthetic/demo data, not a clinically validated product.
- AI outputs are drafts for qualified clinician review. The app does not diagnose or independently prescribe medication.
- Medicine dataset in `backend/data/medicines.csv` is a tiny illustrative catalogue, **not** a treatment recommendation dataset.
- Emergency screening is a minimal illustrative warning-sign check, not a validated triage algorithm. Do not delay emergency help for AI, verification, login, or operator approval. In India, call 112 directly for emergencies.
- No ambulance dispatch provider is integrated; emergency requests are explicitly marked `SIMULATED`.
- Groq transcription availability/models can change; configure a supported model in `.env`.
- RNNoise is represented by an optional processing integration point. Actual RNNoise needs a compatible native library/binary and device/audio-pipeline integration; this starter does not claim that raw audio is denoised when it isn't.
- Doctor document upload/review and WebRTC video calls need production implementation before real patient use.

## Structure
```text
SwasthyaSetu-Native-App/
├── android/       Java Android app (Android Studio)
├── backend/       FastAPI + MongoDB + Groq + tests + demo seed data
└── dashboard/     React + Vite staff dashboard
```

## Requirements
- Windows 10/11
- Android Studio (current stable) with Android SDK installed
- JDK 17 (Android Studio bundled JDK is fine)
- Python 3.11+
- Node.js 20+
- MongoDB Community Server running locally, or MongoDB Atlas URI
- Optional Groq API key for AI note drafting/transcription

## 1. Start MongoDB
Install and start MongoDB Community Server, or create a MongoDB Atlas database. Default local URI:
`mongodb://127.0.0.1:27017`

## 2. Run backend (PowerShell)
```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `backend/.env`: set a long random `JWT_SECRET`. Add `GROQ_API_KEY` only if you want Groq features. Keep secrets on the backend.

Start API:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API docs: http://127.0.0.1:8000/docs

Seed demo users in another backend terminal:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m scripts.seed
```
Demo accounts:
- patient@example.test / PatientDemo123!
- doctor@example.test / DoctorDemo123!
- operator@example.test / OperatorDemo123!
- admin@example.test / AdminDemo123!

## 3. Run Android app
1. Open Android Studio.
2. Choose **Open**, select the `android` folder.
3. Let Gradle sync finish, install Android SDK Platform 35 if prompted.
4. Run on emulator or Android phone.

Backend URL:
- Android emulator talking to host PC: `http://10.0.2.2:8000/`
- Physical phone on same Wi-Fi: change `BASE_URL` in `android/app/src/main/java/com/swasthyasetu/app/ApiClient.java` to `http://YOUR_PC_LAN_IP:8000/`.
- Ensure Windows Firewall permits port 8000 on your private network.
- Cleartext HTTP is enabled for local development only. Use HTTPS for deployment.

## 4. Run React dashboard
Open a second PowerShell terminal:
```powershell
cd dashboard
npm install
Copy-Item .env.example .env
npm run dev
```
Open the URL Vite prints, usually http://localhost:5173

Dashboard demo credentials: same demo accounts. Only use synthetic data.

## 5. Run tests
From `backend` with virtual environment activated:
```powershell
python -m pytest
```

## Included features
- Java Android app: login, language selector, role display, symptom form, illustrative emergency warning screen, AI note draft request, emergency request simulation.
- FastAPI: password hashing, JWT, role-based route protection, MongoDB collections/indexes, demo seed script, medicine catalogue lookup, Groq note drafting, compatible audio transcription endpoint, audit logs, simple rate limiting.
- React dashboard: API status, sign-in, counts and emergency request list.
- CSV medicine catalogue for demo search only.
- `.env.example`, API docs, tests and PowerShell setup commands.

## Not production-ready yet
You still need clinical review/validation, secure doctor licence document workflow and human credential verification, real WebRTC/video calling, real RNNoise native integration, production-grade file storage, privacy/legal review, monitoring, backup/retention policies, robust multilingual translation, validated prescription PDF generation, dispatch integration, and end-to-end security testing. Never use this prototype to make real clinical decisions.
