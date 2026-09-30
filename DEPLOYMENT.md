# 🚀 Karmayogi Sankhyiki — Cloud Deployment Guide
**MoSPI / NSSTA AI-Enabled Statistical Competency Platform (SIH Problem Statement SIH26101)**

---

## 🏛️ 1. Architecture & Deployment Topology

Karmayogi Sankhyiki is built as a cloud-native, decoupled enterprise system:

```
                          ┌───────────────────────────────────────┐
                          │         Edge CDN / Vercel             │
                          │   Next.js 14 App Router (React 18)    │
                          │  Monochromatic Coursera-style UI      │
                          └──────────────────┬────────────────────┘
                                             │ HTTPS REST / SSE
                                             ▼
                          ┌───────────────────────────────────────┐
                          │       Render / Railway / Docker       │
                          │      FastAPI (Python 3.11 ASGI)       │
                          │   Bloom's CAT Engine, RAG, Passport   │
                          └──────┬─────────────────────────┬──────┘
                                 │                         │
                                 ▼                         ▼
            ┌───────────────────────────┐   ┌───────────────────────────┐
            │   Neon.tech Serverless    │   │  NVIDIA NIM Cloud Engine  │
            │ PostgreSQL 16 (SSL Pooled)│   │ Llama-3.2-11b / Nemotron  │
            │ MoSPI Framework & Cadre   │   │  OpenAI-Compatible Micro  │
            └───────────────────────────┘   └───────────────────────────┘
```

| Component | Technology | Target Hosting Platform | Primary Config Files |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 14, Tailwind CSS, Recharts | **Vercel** / Cloudflare Pages | `frontend/vercel.json`, `next.config.mjs` |
| **Backend** | FastAPI, SQLAlchemy, ReportLab | **Render** / Railway / Cloud Run | `render.yaml`, `backend/Dockerfile` |
| **Database** | PostgreSQL 16 with SSL Pooling | **Neon.tech** / Supabase | `backend/.env`, `seed_database.py` |
| **AI Inference**| NVIDIA NIM Microservices | **NVIDIA API Catalog** (or Gemini) | `NVIDIA_API_KEY`, `NVIDIA_MODEL` |

---

## 🗄️ 2. Step 1: Cloud PostgreSQL Setup (Neon.tech / Supabase)

Karmayogi Sankhyiki utilizes cloud-native PostgreSQL with strict SSL enforcement.

### 2.1 Create Neon.tech Database Instance
1. Go to [Neon.tech](https://neon.tech/) and sign in.
2. Click **Create Project**, name it `karmayogi-sankhyiki`, and choose a region close to your users (e.g. `ap-southeast-1` Singapore or `eu-central-1` Frankfurt).
3. In the Neon Console Dashboard, navigate to **Connection Details**.
4. Select **Pooled Connection** and ensure **PostgreSQL 16** is chosen.
5. Copy the connection string. It will look like:
   ```text
   postgresql://neondb_owner:YOUR_PASSWORD@ep-restless-leaf-b3uvsy6o-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
   > [!IMPORTANT]
   > Ensure the connection string includes `?sslmode=require`. The backend's SQLAlchemy engine in `backend/app/core/database.py` is configured with `sslmode="require"` and `pool_pre_ping=True` for resilient serverless connection pooling.

### 2.2 Initialize Schema & Seed Official MoSPI Framework
Run the automated seed script to populate the complete official MoSPI competency framework (4 domains, 18 competencies, 5-level rubrics, 36 role benchmarks, and 7 demo personnel):

```bash
# From repository root
cd backend
python -m pip install -r requirements.txt
python seed_database.py
```

Expected output:
```text
============================================================
[*] KARMAYOGI SANKHYIKI - DATABASE SEEDING ENGINE
============================================================
[1/7] Initializing clean database schema...
[2/7] Seeding Official Statistical Competency Framework...
   -> Seeded 18 competencies across 4 domains with 90 rubric levels.
[3/7] Seeding Role Benchmarks (JSO, SSO, AD, DD, Director)...
   -> Seeded 36 role-competency level requirements.
[4/7] Seeding Dual-Track Courses (iGOT + NSSTA TPAC)...
   -> Seeded 12 courses with multimodal materials and Bloom taxonomy chunks.
[5/7] Seeding Officer Personnel & Initial Competency Profiles...
   -> Seeded 7 officers across SSS & ISS cadres with gap profiles.
[6/7] Generating Verifiable Digital Passports & Cryptographic Badges...
   -> Generated SHA-256 passports and base64 QR codes.
[7/7] Seeding Official MoSPI Knowledgebase (21 Clauses)...
   -> Indexed CPI, NSS, SNA, IIP, and National Data Governance guidelines.
============================================================
[SUCCESS] Database seeded successfully on Neon.tech Cloud!
============================================================
```

---

## 🤖 3. Step 2: AI Engine Setup (NVIDIA NIM / Google Gemini)

Karmayogi Sankhyiki utilizes NVIDIA NIM (Inference Microservices) for Bloom's taxonomy MCQ generation, distractor analysis, and bilingual RAG chat, with seamless fallback support for Google Gemini.

### 3.1 Obtain NVIDIA NIM API Key
1. Visit the [NVIDIA API Catalog](https://build.nvidia.com/).
2. Sign in and select a model: `meta/llama-3.2-11b-vision-instruct` (recommended default) or `nvidia/llama-3.1-nemotron-70b-instruct`.
3. Click **Get API Key** and generate an API key starting with `nvapi-...`.
4. Note your credentials:
   - `NVIDIA_API_KEY`: `nvapi-xxxxxxxxxxxxxxxxxxxxxxxx`
   - `NVIDIA_BASE_URL`: `https://integrate.api.nvidia.com/v1`
   - `NVIDIA_MODEL`: `meta/llama-3.2-11b-vision-instruct`

### 3.2 (Optional) Google Gemini Fallback
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Generate an API Key and set:
   - `GEMINI_API_KEY`: `AIzaSyxxxxxxxxxxxxxxxxx`

---

## 🐍 4. Step 3: Backend Deployment (Render / Railway)

### Option A: Render 1-Click Blueprint (`render.yaml`) — Recommended
1. Fork or push this repository to GitHub.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub repository. Render will automatically detect `render.yaml`.
5. Provide the required environment variables:
   - `DATABASE_URL`: Your Neon.tech connection string with `?sslmode=require`.
   - `NVIDIA_API_KEY`: Your NVIDIA NIM API key (`nvapi-...`).
   - `PUBLIC_VERIFY_BASE_URL`: Your frontend verification URL (e.g. `https://karmayogi-sankhyiki.vercel.app/verify`).
6. Click **Apply**. Render will automatically build the environment, install requirements, and start the Uvicorn server on port `$PORT`.

### Option B: Railway Container Deployment
1. Log in to [Railway](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Set the Root Directory to `backend` (or use the root `Dockerfile`).
4. In Railway **Variables**, add:
   ```env
   PORT=8000
   ENVIRONMENT=production
   DATABASE_URL=postgresql://...
   NVIDIA_API_KEY=nvapi-...
   SECRET_KEY=karmayogi_sankhyiki_secret_key_sih26101_secure_token_salt_2026
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   PUBLIC_VERIFY_BASE_URL=https://<your-frontend-domain>/verify
   ```
5. Click **Deploy**.

### Option C: Standalone Docker Run
```bash
cd backend
docker build -t karmayogi-backend:latest .
docker run -d -p 8000:8000 \
  -e DATABASE_URL="postgresql://neondb_owner:password@ep-...neon.tech/neondb?sslmode=require" \
  -e NVIDIA_API_KEY="nvapi-..." \
  -e SECRET_KEY="your-secret-key" \
  --name karmayogi-api karmayogi-backend:latest
```

### Backend Health Check Verification
Once deployed, verify your service by requesting the health endpoint:
```bash
curl https://your-backend.onrender.com/api/health
```
Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_engine": "nvidia_nim",
  "nvidia_model": "meta/llama-3.2-11b-vision-instruct",
  "environment": "production"
}
```
Open Swagger UI documentation at: `https://your-backend.onrender.com/docs`.

---

## ⚡ 5. Step 4: Frontend Deployment (Vercel)

The Next.js 14 App Router frontend is optimized for zero-config deployment on Vercel Edge.

### 5.1 Import Project to Vercel
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository.
4. In the **Configure Project** screen:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click *Edit* and select `frontend`.
   - **Build Command**: `npm run build` (auto-detected).
   - **Output Directory**: `.next` (auto-detected).

### 5.2 Set Environment Variables on Vercel
Add the following environment variable in the Vercel dashboard:

| Variable Name | Value | Purpose |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com/api` | Target backend REST API endpoint |

5. Click **Deploy**. Vercel will build all 14 static and dynamic routes:
   - `/` (Learner Dashboard & Radar Chart)
   - `/login` (iGOT SSO Simulation & Quick Switcher)
   - `/onboarding` (MoSPI Cadre & Division Rubric Wizard)
   - `/career-simulator` (3-Layer Interactive Promotion Simulator)
   - `/assessments` (Multimodal AI Studio & Adaptive CAT Test)
   - `/chat` ("Sankhyiki Mitra" Voice & Bilingual RAG)
   - `/passport` (Digital Skill Passport, Badges, Micro-credentials)
   - `/verify` and `/verify/[id]` (Public Zero-Auth Credential Verification)
   - `/admin` (Cadre Workforce Health, Heatmap & TPAC Allocator)
   - `/team-matrix` (Supervisor Matrix & Calibration)

---

## 🐳 6. Step 5: Full-Stack Local Deployment with Docker Compose

To run the complete system locally with a single command:

```bash
# 1. Clone repository
git clone https://github.com/Harikesh0501/Food_Delivery_app.git
cd Food_Delivery_app

# 2. Configure .env file at root with your keys
cp backend/.env.example .env

# 3. Launch both backend and frontend containers
docker compose up --build
```

- Frontend UI: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Interactive Docs: `http://localhost:8000/docs`

---

## 🔑 7. Environment Variables Reference Matrix

### Backend (`backend/.env` or Render/Railway Settings)
| Variable | Required | Default / Example | Purpose |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | No | `production` | Execution environment mode |
| `PORT` | No | `8000` | Port for Uvicorn server |
| `DATABASE_URL` | **Yes** | `postgresql://...@neon.tech/neondb?sslmode=require` | PostgreSQL connection string |
| `SECRET_KEY` | **Yes** | `karmayogi_sankhyiki_secret_key_...` | HMAC-SHA256 signing secret for JWT tokens |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| No | `1440` (24 hours) | JWT token lifespan |
| `NVIDIA_API_KEY` | **Yes** | `nvapi-...` | NVIDIA NIM Inference API Key |
| `NVIDIA_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` | NVIDIA NIM OpenAI-compatible endpoint |
| `NVIDIA_MODEL` | No | `meta/llama-3.2-11b-vision-instruct` | LLM model identifier |
| `GEMINI_API_KEY` | No | `AIzaSy...` | Fallback Google Gemini API key |
| `IGOT_API_BASE_URL` | No | `https://igotkarmayogi.gov.in/api/v1` | iGOT Karmayogi API base URL |
| `IGOT_MOCK_MODE` | No | `true` | Enables zero-latency iGOT SSO mock mode |
| `PUBLIC_VERIFY_BASE_URL` | No | `https://<frontend-domain>/verify` | Domain for generated QR verification links |

### Frontend (`frontend/.env.local` or Vercel Settings)
| Variable | Required | Default / Example | Purpose |
| :--- | :---: | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | **Yes** | `https://<backend-app>.onrender.com/api` | Points frontend fetch calls to backend API |

---

## 👥 8. Pre-Configured Demo Persona Credentials for Evaluators

For fast evaluation without manual signups, use the pre-seeded official demo personas:

| Official Persona | Cadre & Designation | Division | Email | Password | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pooja Sharma** | Junior Statistical Officer (JSO) | FOD, New Delhi | `jso.sharma@mospi.gov.in` | `Password@123` | Learner (SSS) |
| **Rajesh Verma** | Assistant Director (AD) | NAD, New Delhi | `ad.verma@mospi.gov.in` | `Password@123` | Learner (ISS) |
| **Dr. Sunita Rao** | Senior Faculty | NSSTA Greater Noida | `faculty.nssta@nic.in` | `Password@123` | Faculty / Trainer |
| **Alok Mathur** | Director & Cadre Administrator | MoSPI HQ | `admin.cadre@mospi.gov.in` | `Password@123` | Cadre Admin |

*(Alternatively, use the **1-Click Demo Persona Switcher** on the `/login` screen or the top navigation bar).*

---

## 🛡️ 9. Production Security & Hardening Checklist

- [x] **SSL Strict Mode**: PostgreSQL connection requires `?sslmode=require` with certificate validation.
- [x] **CORS Isolation**: In production, restrict `allow_origins` in `backend/app/main.py` to your Vercel frontend domain.
- [x] **Password Protection**: Passwords salted and hashed with direct `bcrypt` algorithm.
- [x] **Tamper-Evident Passports**: Passports cryptographically anchored with SHA-256 hashes of officer ID, competencies, timestamps, and issuing authority.
- [x] **Rate Limiting & Safety**: Public verification portal `/api/passport/verify/{code}` exposes zero personally identifiable information (PII masked as `p****@mospi.gov.in`).
- [x] **Edge Security Headers**: Vercel configuration injects `X-Frame-Options`, `X-Content-Type-Options`, and `Strict-Transport-Security`.
