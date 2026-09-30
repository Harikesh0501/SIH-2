# 📋 MASTER IMPLEMENTATION ROADMAP: TASK & MINI-TASK CHECKLIST
## SIH26101: AI-Enabled Skill Intelligence & Learning Platform for India's Official Statistical System
### Integrated with iGOT Karmayogi & NSSTA TPAC | Sleek Coursera-Inspired Monochromatic UI

---

## 🎨 Design Philosophy & UI Specification (Coursera / Linear / Notion Aesthetic)
- **Palette**: Clean Monochromatic (Deep Black `#09090b`, Off-Black `#18181b`, Subtle Gray `#71717a`, Light Border `#e4e4e7`, Pure White `#ffffff`).
- **Accent**: High-contrast minimal highlights (Neutral slate, subtle emerald for verified badges, crisp borders).
- **Typography**: Inter / Geist / Newsreader for elegant academic & official statistical executive appeal.
- **Card Styling**: Ultra-clean minimalist cards with 1px border lines, subtle drop shadows, and high-density information display.
- **Data Visualizations**: Crisp black-and-white / grayscale radar charts, bar meters, and interactive heatmaps.

---

## 🏗️ Master Task Hierarchy & Tracking Checklist

---

### [x] PHASE 1: Project Architecture & Environment Scaffolding
- [x] **Task 1.1: Fullstack Monorepo Scaffolding**
  - [x] Mini-Task 1.1.1: Create root directories `/backend`, `/frontend`, `/data`, `/docs`, `/scripts`, `/sample_data`.
  - [x] Mini-Task 1.1.2: Initialize root `package.json` with unified workspace management scripts.
  - [x] Mini-Task 1.1.3: Configure `.gitignore` covering Python cache, Node modules, `.env` files, uploads, and DB files.
  - [x] Mini-Task 1.1.4: Author root `README.md` with architectural diagrams and quick-start instructions.
- [x] **Task 1.2: Backend Environment & Configuration Setup**
  - [x] Mini-Task 1.2.1: Create `backend/requirements.txt` with FastAPI, Uvicorn, SQLAlchemy, Pydantic v2, Google Generative AI (Gemini), PyPDF, Python-docx, Python-pptx, Jose/JWT, Passlib, ReportLab (PDF export), and HTTPX.
  - [x] Mini-Task 1.2.2: Setup `backend/.env.example` with parameters for `DATABASE_URL` (Neon/Supabase/SQLite), `GEMINI_API_KEY`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `ENVIRONMENT`.
  - [x] Mini-Task 1.2.3: Build `backend/app/core/config.py` using `pydantic-settings` with automatic DB fallback (PostgreSQL if provided, SQLite if offline).
  - [x] Mini-Task 1.2.4: Build `backend/app/core/database.py` with SQLAlchemy async/sync session management and health check probe.
- [x] **Task 1.3: Frontend Environment & UI Scaffolding (Coursera Theme)**
  - [x] Mini-Task 1.3.1: Initialize Next.js 14 (App Router) with TypeScript and Tailwind CSS in `/frontend`.
  - [x] Mini-Task 1.3.2: Configure `tailwind.config.ts` with custom Coursera-inspired monochromatic grayscale palette and typography.
  - [x] Mini-Task 1.3.3: Install and configure Lucide React icons, Class Variance Authority (CVA), clsx, and Tailwind Merge.
  - [x] Mini-Task 1.3.4: Install Recharts for official statistical radar charts, spider graphs, and heatmaps.
  - [x] Mini-Task 1.3.5: Build `frontend/src/lib/api-client.ts` for unified Axios/Fetch requests with JWT bearer injection.

---

### [x] PHASE 2: Official Statistical Domain Framework, FRAC & Database Modeling
- [x] **Task 2.1: MoSPI & NSSTA Competency Framework Codification**
  - [x] Mini-Task 2.1.1: Define Domain 1 (Statistical Competencies): Survey Design, Sampling (PPS/Stratified), National Accounts (SNA 2008/2025), Price Statistics (CPI/WPI/IIP), Labour (PLFS), Agriculture, Industrial (ASI), SDG Indicators, Data Quality (DQAF).
  - [x] Mini-Task 2.1.2: Define Domain 2 (Technical Competencies): Python for Statistics, R Econometrics, SQL/Data Warehousing, Stata/SPSS/SAS, GIS (Bhuvan/QGIS), Data Viz (Power BI/D3), AI/ML in Official Statistics, Open Data & APIs.
  - [x] Mini-Task 2.1.3: Define Domain 3 (Digital Governance): Cybersecurity in Gov Systems, DPDP Act 2023, MeghRaj Cloud, Digital Public Infrastructure (DPI & e-Sign).
  - [x] Mini-Task 2.1.4: Define Domain 4 (Behavioural & Managerial): Statistical Leadership, Dissemination & Policy Communication, Survey Project Management, UN Fundamental Principles of Official Statistics.
  - [x] Mini-Task 2.1.5: Define 5-tier proficiency level rubrics (Level 1: Novice to Level 5: Master) for all 35+ competencies.
- [x] **Task 2.2: Cadre Role Benchmark Matrix**
  - [x] Mini-Task 2.2.1: Define benchmark requirement profile for Junior Statistical Officer (JSO / SSS).
  - [x] Mini-Task 2.2.2: Define benchmark requirement profile for Senior Statistical Officer (SSO / SSS).
  - [x] Mini-Task 2.2.3: Define benchmark requirement profile for Assistant Director (ISS).
  - [x] Mini-Task 2.2.4: Define benchmark requirement profile for Deputy Director (ISS).
  - [x] Mini-Task 2.2.5: Define benchmark requirement profile for Director / Deputy Director General (ISS Senior Leadership).
- [x] **Task 2.3: Relational Database Schema Design (SQLAlchemy)**
  - [x] Mini-Task 2.3.1: Build `User` model with Cadre, Designation, Division (NAD, ESD, FOD, SDRD, SSD), Supervisor ID, Experience, Education, and Role (LEARNER, TRAINER, SUPERVISOR, ADMIN).
  - [x] Mini-Task 2.3.2: Build `Competency`, `CompetencyLevel`, and `RoleBenchmark` models.
  - [x] Mini-Task 2.3.3: Build `UserCompetency` model with current level, assessment source (SELF, SUPERVISOR, QUIZ, IGOT), confidence score, and timestamps.
  - [x] Mini-Task 2.3.4: Build `Course` model supporting dual sources (`IGOT_KARMAYOGI` and `NSSTA_TPAC`), duration, provider, delivery mode, and competency mappings.
  - [x] Mini-Task 2.3.5: Build `Enrollment` model with tracking states (`RECOMMENDED`, `ENROLLED`, `IN_PROGRESS`, `COMPLETED`), scores, and certificates.
  - [x] Mini-Task 2.3.6: Build `LearningMaterial` and `MaterialChunk` models supporting PDF, DOCX, PPTX, and Video/Audio Transcripts.
  - [x] Mini-Task 2.3.7: Build `Quiz`, `Question` (MCQ with Bloom's levels, options, explanation, citation), and `QuizAttempt` models with Adaptive Difficulty Tracking.
  - [x] Mini-Task 2.3.8: Build `DigitalCredential` / `SkillPassport` model for QR-verifiable certificate issuance.
  - [x] Mini-Task 2.3.9: Build `ChatMessage` model for storing "Sankhyiki Mitra" AI conversations.
- [x] **Task 2.4: Comprehensive Seed Data Generator (`seed_database.py`)**
  - [x] Mini-Task 2.4.1: Seed all 4 competency domains and 35+ granular official statistics competencies.
  - [x] Mini-Task 2.4.2: Seed role benchmark matrices for all 5 key MoSPI designations.
  - [x] Mini-Task 2.4.3: Seed 30+ authentic iGOT Karmayogi digital micro-courses with competencies and duration.
  - [x] Mini-Task 2.4.4: Seed 15+ NSSTA TPAC approved in-person and blended training programs (Residential at Greater Noida).
  - [x] Mini-Task 2.4.5: Seed 4 realistic persona accounts (JSO Pooja Sharma, AD Rajesh Verma, Faculty Dr. Sunita Rao, Admin Alok Mathur).
  - [x] Mini-Task 2.4.6: Seed sample official MoSPI learning materials (CPI Manual excerpt, PLFS concepts, National Accounts handbook).

---

### [x] PHASE 3: Core Backend APIs & Security Layer
- [x] **Task 3.1: Authentication & Authorization Service**
  - [x] Mini-Task 3.1.1: Implement password hashing with `passlib[bcrypt]`.
  - [x] Mini-Task 3.1.2: Implement JWT token creation with claims (`sub`, `role`, `cadre`, `designation`).
  - [x] Mini-Task 3.1.3: Build `POST /api/auth/login` endpoint for email/password authentication.
  - [x] Mini-Task 3.1.4: Build `POST /api/auth/register` endpoint with cadre and designation capture.
  - [x] Mini-Task 3.1.5: Build `POST /api/auth/igot-sso` endpoint simulating Parichay / iGOT Karmayogi Single Sign-On.
  - [x] Mini-Task 3.1.6: Build `GET /api/auth/me` returning current authenticated user profile.
  - [x] Mini-Task 3.1.7: Build `GET /api/auth/demo-users` for instant 1-click persona switching during live evaluation.
- [x] **Task 3.2: User Profile & Cadre Management API**
  - [x] Mini-Task 3.2.1: Build `PUT /api/profile` to update personal details, department division, and years of experience.
  - [x] Mini-Task 3.2.2: Build `POST /api/profile/self-assessment` to allow officers to record baseline ratings (1-5).
  - [x] Mini-Task 3.2.3: Build `GET /api/profile/cadre-structure` returning MoSPI divisions and designations.

---

### [x] PHASE 4: AI Competency Gap Analysis & Team Matrix Engine
- [x] **Task 4.1: Gap Analysis Computation Algorithm**
  - [x] Mini-Task 4.1.1: Develop mathematical gap evaluation: $\text{Gap}_i = \max(0, \text{Required}_i - \text{Current}_i)$.
  - [x] Mini-Task 4.1.2: Implement Weighted Urgency Score (WUS) factoring in role criticality, mandatory compliance, and level distance.
  - [x] Mini-Task 4.1.3: Aggregate domain readiness percentages (Statistical, Technical, Governance, Managerial).
- [x] **Task 4.2: Competency Endpoints & Visual Data Structures**
  - [x] Mini-Task 4.2.1: Build `GET /api/competencies/framework` returning full dictionary with descriptions and indicators.
  - [x] Mini-Task 4.2.2: Build `GET /api/competencies/user-status` returning user's evaluated levels vs benchmark.
  - [x] Mini-Task 4.2.3: Build `GET /api/competencies/gap-analysis` delivering radar-chart ready JSON payloads.
  - [x] Mini-Task 4.2.4: Build `POST /api/competencies/career-simulation` projecting gaps if officer targets a higher designation.
- [x] **Task 4.3: Supervisor / Division Team Skill Matrix**
  - [x] Mini-Task 4.3.1: Build `GET /api/competencies/team-matrix` returning aggregated subordinate competency scores for division directors.
  - [x] Mini-Task 4.3.2: Build `POST /api/competencies/supervisor-calibrate` allowing supervisors to calibrate subordinate ratings.

---

### [x] PHASE 5: Dual-Track Personalized Recommendation & TPAC Batch Nomination
- [x] **Task 5.1: Hybrid Recommendation Matching Logic**
  - [x] Mini-Task 5.1.1: Build rule-based gap-to-course indexer matching urgent competencies ($WUS > 0$) to course modules.
  - [x] Mini-Task 5.1.2: Build keyword and semantic similarity matcher evaluating course titles and descriptions against officer profile.
  - [x] Mini-Task 5.1.3: Categorize output into:
    - Track A: **iGOT Karmayogi** (Self-paced asynchronous digital micro-modules).
    - Track B: **NSSTA TPAC** (Institutional, in-person residential / blended training).
  - [x] Mini-Task 5.1.4: Generate personalized rationale text for each recommendation.
- [x] **Task 5.2: Recommendation & iGOT Integration Endpoints**
  - [x] Mini-Task 5.2.1: Build `GET /api/recommendations/my-pathway` with filtering by source, domain, and duration.
  - [x] Mini-Task 5.2.2: Build `POST /api/igot/enroll/{course_id}` simulating registration dispatch to Karmayogi API.
  - [x] Mini-Task 5.2.3: Build `POST /api/igot/complete-webhook` to receive completion triggers and auto-upgrade competency scores.
  - [x] Mini-Task 5.2.4: Build `GET /api/enrollments/my-courses` to track active, recommended, and completed courses.
  - [x] Mini-Task 5.2.5: Build `POST /api/recommendations/nominate-batch` allowing supervisors to nominate officers for TPAC batches.

---

### [x] PHASE 6: Multimodal AI Assessment & Adaptive (CAT) Quiz Engine
- [x] **Task 6.1: Multimodal Learning Material Ingestion Pipeline**
  - [x] Mini-Task 6.1.1: Build upload endpoint `POST /api/assessments/upload-material` supporting PDF, DOCX, PPTX, and TXT files.
  - [x] Mini-Task 6.1.2: Implement PPTX slide extractor pulling title and bullet content slide-by-slide.
  - [x] Mini-Task 6.1.3: Build Video/Audio Transcript ingestion endpoint `POST /api/assessments/ingest-transcript` accepting webinar/YouTube transcripts.
  - [x] Mini-Task 6.1.4: Implement semantic text chunking (600-800 tokens, 100 overlap) with section and slide metadata preservation.
- [x] **Task 6.2: Gemini 1.5 / NVIDIA NIM LLM Prompt Engineering for MCQs**
  - [x] Mini-Task 6.2.1: Author structured prompt enforcing strict Pydantic JSON schema output for generated questions.
  - [x] Mini-Task 6.2.2: Integrate Bloom's Taxonomy cognitive stratification (Remembering, Understanding, Applying, Analyzing, Evaluating).
  - [x] Mini-Task 6.2.3: Force generation of authentic distractors based on common statistical misconceptions with explicit rationale.
  - [x] Mini-Task 6.2.4: Extract exact source text citations (page number, slide number, section reference).
  - [x] Mini-Task 6.2.5: Implement intelligent local fallback generator so assessment generation functions even without an API key.
- [x] **Task 6.3: Computerized Adaptive Testing (CAT) & Quiz Engine**
  - [x] Mini-Task 6.3.1: Build `POST /api/assessments/generate-quiz` to trigger generation from uploaded material or custom topic.
  - [x] Mini-Task 6.3.2: Build `GET /api/assessments/quizzes` to list diagnostic and practice assessments.
  - [x] Mini-Task 6.3.3: Build `GET /api/assessments/quizzes/{id}` returning quiz questions without revealing answers.
  - [x] Mini-Task 6.3.4: Build Adaptive Quiz Execution API: Dynamically adjusts subsequent question difficulty based on prior answers.
  - [x] Mini-Task 6.3.5: Build `POST /api/assessments/quizzes/{id}/submit` to evaluate answers, calculate score, and log attempt.
  - [x] Mini-Task 6.3.6: Dynamic Competency Upgrading: If score $\ge 75\%$, automatically promote user's competency level.
  - [x] Mini-Task 6.3.7: Provide detailed diagnostic feedback report with answer explanations and recommended remedial reading.

---

### [x] PHASE 7: "Sankhyiki Mitra" AI Statistical Tutor with Bilingual Voice & RAG
- [x] **Task 7.1: MoSPI Statistical Knowledge Base & RAG Engine**
  - [x] Mini-Task 7.1.1: Index official MoSPI manuals (National Accounts, CPI, PLFS, DQAF) into semantic searchable chunks.
  - [x] Mini-Task 7.1.2: Implement context retrieval pipeline matching user queries to relevant statistical clauses.
  - [x] Mini-Task 7.1.3: Build conversational prompt persona: "Sankhyiki Mitra - Official Statistical Tutor of India".
  - [x] Mini-Task 7.1.4: Add bilingual capability (English and Hindi statistical terminology).
- [x] **Task 7.2: Conversational & Voice Endpoints**
  - [x] Mini-Task 7.2.1: Build `POST /api/chat/message` with contextual answer generation and official document citations.
  - [x] Mini-Task 7.2.2: Add voice query handling and Web Speech API ready payload in chat endpoints (frontend player in Task 10.6).
  - [x] Mini-Task 7.2.3: Build `GET /api/chat/history` to retrieve prior discussions and `DELETE /api/chat/history` to reset session.
  - [x] Mini-Task 7.2.4: Pre-configure suggested quick prompts ("Explain GVA at basic prices vs GDP", "How is PPS sampling done in NSS?", etc.).

---

### [x] PHASE 8: MoSPI Digital Skill Passport, QR Verification & PDF Report Generation
- [x] **Task 8.1: Digital Skill Passport & QR-Verified Credentials**
  - [x] Mini-Task 8.1.1: Build `GET /api/passport/my-passport` compiling all verified competencies, badges, and completed courses.
  - [x] Mini-Task 8.1.2: Generate unique verification URL and embeddable QR Code for each credential.
  - [x] Mini-Task 8.1.3: Build public verification endpoint `GET /api/passport/verify/{credential_id}` for external audit.
- [x] **Task 8.2: Automated PDF Report Generation**
  - [x] Mini-Task 8.2.1: Build `GET /api/reports/officer-skill-card/{user_id}` generating downloadable PDF Skill Card using ReportLab.
  - [x] Mini-Task 8.2.2: Build `GET /api/reports/ministry-capacity-readiness` generating comprehensive PDF report with division metrics for TPAC review.

---

### [x] PHASE 9: Admin Cadre Analytics & Division Heatmaps
- [x] **Task 9.1: Cadre-Wide Analytics Service**
  - [x] Mini-Task 9.1.1: Compute organization-wide competency health index and average readiness score.
  - [x] Mini-Task 9.1.2: Generate division-wise competency gap matrix (NAD vs FOD vs ESD vs SDRD).
  - [x] Mini-Task 9.1.3: Identify top 5 systemic competency bottlenecks across all statistical personnel.
- [x] **Task 9.2: NSSTA TPAC Training Batch Allocation Engine**
  - [x] Mini-Task 9.2.1: Build automated recommendation algorithm nominating officers with high gap scores for upcoming TPAC residential batches.
  - [x] Mini-Task 9.2.2: Build `GET /api/admin/dashboard` delivering macro metrics, division heatmaps, and batch allocation queues.
  - [x] Mini-Task 9.2.3: Build `POST /api/admin/allocate-batch` to confirm nominations and send training alerts.

---

### [x] PHASE 10: Coursera-Style Minimalist Black & White Frontend
- [x] **Task 10.1: Core Layout, Header & Monochromatic Theme Shell**
  - [x] Mini-Task 10.1.1: Build root layout with sleek top navigation, MoSPI / National Emblem branding, and profile status.
  - [x] Mini-Task 10.1.2: Build role switcher / demo persona selector (JSO, AD, Faculty, Admin) for effortless judging demonstration.
  - [x] Mini-Task 10.1.3: Implement accessible Coursera-style typography, breadcrumbs, and card containers.
- [x] **Task 10.2: Authentication & Onboarding Screens**
  - [x] Mini-Task 10.2.1: Build `/login` page with standard email login and high-contrast "Sign in with iGOT Karmayogi" button.
  - [x] Mini-Task 10.2.2: Build `/onboarding` wizard allowing officers to select cadre, division, and self-assess competencies.
- [x] **Task 10.3: Learner Dashboard ("My Competency Hub")**
  - [x] Mini-Task 10.3.1: Build Competency Radar Chart component (Recharts) displaying Current vs Target Levels across all 4 domains.
  - [x] Mini-Task 10.3.2: Build "High-Priority Competency Gaps" alert cards with direct one-click remediation pathways.
  - [x] Mini-Task 10.3.3: Build "My Learning Pathway" dual carousel: iGOT Karmayogi micro-modules and NSSTA TPAC residential courses.
  - [x] Mini-Task 10.3.4: Build Metrics Bar: Assessed Competencies, Training Hours Completed, Active Badges.
- [x] **Task 10.4: Career Progression Simulator**
  - [x] Mini-Task 10.4.1: Build interactive career trajectory simulator dropdown (target role: "Deputy Director" or "Director").
  - [x] Mini-Task 10.4.2: Visually render projected competency gap delta and recommended upskilling roadmap.
- [x] **Task 10.5: AI Assessment Studio (Multimodal Upload, Generate, Adaptive Quiz)**
  - [x] Mini-Task 10.5.1: Build Multimodal Upload View: Drag-and-drop for PDF, DOCX, PPTX, and Video/Audio transcript tab.
  - [x] Mini-Task 10.5.2: Build Question Generator Studio: Controls for question count, difficulty, and Bloom's Taxonomy toggles.
  - [x] Mini-Task 10.5.3: Build MCQ Review & Edit Screen: Preview generated questions, answer choices, distractor rationales, and citations.
  - [x] Mini-Task 10.5.4: Build Interactive Adaptive Test Taking Environment: Distraction-free quiz interface, countdown timer, question navigator.
  - [x] Mini-Task 10.5.5: Build Quiz Diagnostic Results View: Score report, Bloom's cognitive breakdown, detailed explanations, and competency upgrade animation.
- [x] **Task 10.6: "Sankhyiki Mitra" AI Chat Interface with Voice Support**
  - [x] Mini-Task 10.6.1: Build clean conversation screen with prompt chips, streaming responses, and official document citations.
  - [x] Mini-Task 10.6.2: Add Microphone Voice Input button and Text-to-Speech audio read-aloud.
  - [x] Mini-Task 10.6.3: Add language switcher (English / Hindi) and markdown formula rendering.
- [x] **Task 10.7: MoSPI Digital Skill Passport & Credential View**
  - [x] Mini-Task 10.7.1: Build Digital Skill Passport screen displaying verified competencies, badges, and QR code.
  - [x] Mini-Task 10.7.2: Build 1-click Download Skill Card (PDF) button.
  - [x] Mini-Task 10.7.3: Build public certificate verification view (`/verify/[id]`).
- [x] **Task 10.8: Ministry Administrator & Supervisor Dashboard**
  - [x] Mini-Task 10.8.1: Build Macro Workforce Competency Health widget.
  - [x] Mini-Task 10.8.2: Build Division Competency Heatmap (NAD vs FOD vs ESD vs SDRD).
  - [x] Mini-Task 10.8.3: Build Supervisor Team Matrix view for division directors.
  - [x] Mini-Task 10.8.4: Build NSSTA TPAC Batch Allocator tool with 1-click batch nomination and PDF export.

---

### [x] PHASE 11: Verification, Packaging & Deployment Readiness
- [x] **Task 11.1: Automated Verification & Unit Tests**
  - [x] Mini-Task 11.1.1: Backend pytest suite covering gap analysis math, WUS scores, and competency upgrading logic.
  - [x] Mini-Task 11.1.2: API integration tests for auth, recommendations, and assessment endpoints.
  - [x] Mini-Task 11.1.3: Frontend production build verification (`npm run build`).
- [x] **Task 11.2: Cloud Deployment Configurations**
  - [x] Mini-Task 11.2.1: Author `render.yaml` and `Dockerfile` for backend hosting on Render / Railway.
  - [x] Mini-Task 11.2.2: Configure `frontend/vercel.json` for seamless 1-click deployment on Vercel.
  - [x] Mini-Task 11.2.3: Document step-by-step instructions for connecting Neon / Supabase cloud database and Gemini API key.
- [x] **Task 11.3: Presentation & Judging Walkthrough Artifact**
  - [x] Mini-Task 11.3.1: Package real MoSPI sample documents in `/sample_data` for live judging demonstration.
  - [x] Mini-Task 11.3.2: Create step-by-step live demo script with pre-configured persona credentials.
