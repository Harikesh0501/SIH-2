# 🏆 Karmayogi Sankhyiki — Live Presentation & Judging Walkthrough
**AI-Enabled Competency Gap Diagnosis, Multimodal Adaptive Assessment & Cadre Analytics Platform**  
*Developed for Ministry of Statistics and Programme Implementation (MoSPI) & National Statistical Systems Training Academy (NSSTA)*  
*Smart India Hackathon (SIH 2024 / Problem Statement SIH26101)*

---

## 🎯 Executive Summary & Value Proposition

India's statistical ecosystem under MoSPI employs over 5,000 personnel across the Indian Statistical Service (ISS) and Subordinate Statistical Service (SSS). Currently, training allocations are static and paper-bound, competency frameworks lack real-time visibility, and iGOT Karmayogi online modules are disconnected from NSSTA's high-impact residential training.

**Karmayogi Sankhyiki solves this end-to-end through four transformative pillars:**
1. **Dynamic Competency Diagnosis**: Mathematical Weighted Urgency Score ($WUS$) diagnosing individual and cadre-wide gaps across 18 official statistical competencies and 4 domains.
2. **Dual-Track Learning Pathways**: Seamlessly synchronizes asynchronous digital courses from **iGOT Karmayogi** with prioritized residential nominations for **NSSTA TPAC** (Training Programme Advisory Committee).
3. **Multimodal Bloom's CAT Engine**: Ingests official government manuals (PDF, DOCX, PPTX), extracts semantic chunks, generates Bloom's taxonomy MCQs with distractor rationales, and administers real-time Computerized Adaptive Tests (CAT) that automatically upgrade officer levels upon passing.
4. **Verifiable Digital Skill Passport & Cadre Analytics**: Cryptographically anchored (SHA-256) micro-credentials with zero-auth public QR verification, ReportLab PDF Skill Cards, division heatmaps, and a 1-click batch nomination allocator for NSSTA leadership.

---

## 🔑 Pre-Configured Demo Personas for Evaluators

The application includes an instant **Demo Persona Switcher** on the `/login` screen and top navigation bar. Evaluators can switch between personas with zero typing:

| Role / Persona | Officer Name | Cadre & Designation | Division | Email | Password |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Learner 1 (SSS)** | **Pooja Sharma** | Junior Statistical Officer (JSO) | FOD, New Delhi | `jso.sharma@mospi.gov.in` | `Password@123` |
| **Learner 2 (ISS)** | **Rajesh Verma** | Assistant Director (AD) | NAD, New Delhi | `ad.verma@mospi.gov.in` | `Password@123` |
| **Faculty / Trainer** | **Dr. Sunita Rao** | Senior Faculty | NSSTA Greater Noida | `faculty.nssta@nic.in` | `Password@123` |
| **Cadre Administrator**| **Alok Mathur** | Director & Cadre Admin | MoSPI HQ | `admin.cadre@mospi.gov.in` | `Password@123` |

---

## 🎬 5-Act Live Demonstration Script

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       5-ACT DEMO WALKTHROUGH FLOW                          │
│                                                                            │
│  [ACT 1] Officer Hub & Gap Diagnosis (Pooja Sharma, JSO)                   │
│          └─ Radar Chart, WUS Urgency, Dual-Track Pathway, Career Simulator │
│                                                                            │
│  [ACT 2] Multimodal AI Assessment Studio (Dr. Sunita Rao, Faculty)         │
│          └─ MoSPI PDF Ingestion, Bloom's MCQs, Adaptive CAT Test Taking    │
│                                                                            │
│  [ACT 3] Sankhyiki Mitra AI Copilot (Bilingual Voice & RAG)                │
│          └─ Voice Input/TTS, Strict MoSPI Citations, English & Hindi       │
│                                                                            │
│  [ACT 4] Cryptographic Digital Skill Passport (Tamper-Proof)               │
│          └─ SHA-256 Micro-Credentials, Public QR Verify, Official PDF Card │
│                                                                            │
│  [ACT 5] Cadre Macro Analytics & TPAC Allocator (Alok Mathur, Admin)       │
│          └─ Division Heatmaps, Top 5 Bottlenecks, 1-Click Batch Allocation │
└────────────────────────────────────────────────────────────────────────────┘
```

---

### 🟢 ACT 1: The Statistical Officer Experience (Pooja Sharma, JSO)
*Goal: Demonstrate personalized competency diagnosis, mathematical urgency calculations, dual-track pathways, and career forward-planning.*

1. **Access Login (`/login`)**:
   - Click the quick-fill button **"JSO (Pooja Sharma)"** or click **"Sign in with iGOT Karmayogi"**.
   - Note the seamless OAuth/SSO simulation authenticating against the government single sign-on standard.
2. **Explore Learner Dashboard (`/`)**:
   - **Metrics Bar**: Highlight 4 assessed competencies, 36 training hours, and active verified badges.
   - **Interactive Radar Chart**: Recharts radar comparing Pooja's *Current Level* vs *Target Level* across MoSPI's 4 core domains (Macroeconomic Statistics, Price Statistics, Sample Surveys, Statistical Quality).
   - **High-Priority Competency Gaps Alert**:
     - Point out `PRICE-CPI-01` (Consumer Price Index Methodology) flagged as **Critical Gap**.
     - Explain the $WUS$ formula:
       $$\text{WUS} = \Delta \times \text{Weight} \times \text{UrgencyMultiplier}$$
     - Show the clear remediation recommendation.
   - **Dual-Track Learning Carousel**:
     - *Track 1 (iGOT Karmayogi)*: Self-paced micro-modules (e.g. *"CPI Elementary Aggregation & Index Compilation"*).
     - *Track 2 (NSSTA TPAC)*: In-person residential workshop (e.g. *"Advanced Field Sampling & CAPI Verification"* at Greater Noida).
3. **Career Progression Simulator (`/career-simulator`)**:
   - Select Target Role: **"Senior Statistical Officer (SSO)"** or **"Assistant Director (AD)"**.
   - Watch the interactive radar render a 3-layer comparison: *Current Level*, *Current Benchmark (JSO)*, and *Target Role Benchmark (AD)*.
   - Inspect the automatically generated upskilling roadmap showing prerequisite courses to qualify for promotion.

---

### 🔵 ACT 2: Multimodal AI Assessment Studio & Adaptive CAT Test (Dr. Sunita Rao)
*Goal: Demonstrate automated ingestion of real MoSPI guidelines, Bloom's cognitive taxonomy question generation, and computerized adaptive testing.*

1. **Switch Role to NSSTA Faculty**:
   - Click the role badge in the header or use the persona selector -> switch to **Dr. Sunita Rao (`faculty.nssta@nic.in`)**.
2. **Navigate to AI Assessment Studio (`/assessments`)**:
   - Tab 1: **Upload MoSPI Source Material**:
     - Drag-and-drop or select an official sample document from `/sample_data/`:
       - `cpi_manual_methodology_excerpt.pdf` (or `national_accounts_gva_gdp_guide.pdf` or `plfs_sampling_and_concepts.docx`).
     - Mention: *The platform supports multi-format parsing (PDF, DOCX, PPTX, text) using PyPDF and python-docx.*
   - Tab 2: **Configure Question Generator**:
     - Set Question Count: `5`
     - Select Target Difficulty: `Intermediate`
     - Select Cognitive Depth: `Apply / Analyze (Bloom's L3-L4)`
     - Click **"Generate Assessment with AI"**.
   - Tab 3: **Review Generated Questions**:
     - Showcase questions generated via NVIDIA NIM.
     - Note each question includes:
       - **Bloom's Cognitive Level** badge (`REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`).
       - **Official Citation**: Direct clause reference to the MoSPI manual.
       - **Distractor Rationales**: Specific explanations for why each incorrect option is false.
3. **Launch Computerized Adaptive Test (CAT)**:
   - Click **"Start Live Adaptive Quiz"**.
   - Note the distraction-free exam layout, live timer, and question navigator.
   - **Adaptive Difficulty Progression**:
     - Answer Question 1 correctly: The engine dynamically escalates difficulty to Level 3 / Level 4.
     - Answer incorrectly: The engine serves a foundational question to isolate the misunderstanding.
4. **Diagnostic Score Report & Automated Level Upgrade**:
   - Click **"Submit Assessment"**.
   - View the diagnostic breakdown: overall score percentage, Bloom's cognitive accuracy radar, and distractor analysis.
   - **Live Level Upgrade**: When score exceeds 75%, celebrate the animated notification:
     *“🎉 Competency Level Upgraded: PRICE-CPI-01 upgraded from Level 2 to Level 3!”*

---

### 🟣 ACT 3: "Sankhyiki Mitra" AI Copilot (Bilingual Voice & RAG)
*Goal: Showcase an official MoSPI-grounded assistant with zero hallucinations, bilingual Hindi/English capabilities, and voice interaction.*

1. **Navigate to Chat (`/chat`)**:
   - Point out the quick prompt chips:
     - *"What is the difference between GVA and GDP under SNA 2008?"*
     - *"Explain the two-stage aggregation formula in CPI."*
     - *"What are the sampling stages in PLFS?"*
2. **Execute Bilingual Inquiries**:
   - Click **English Prompt**: *"Explain the two-stage aggregation formula in CPI."*
     - Observe the streamed response citing **Jevons Index** for elementary aggregates and **Modified Laspeyres** for group levels, referencing *MoSPI CPI Manual Chapter 3, Clause 4*.
   - Toggle language to **Hindi (हिन्दी)** and ask:
     - *"राष्ट्रीय लेखा सांख्यिकी में जीवीए (GVA) और जीडीपी (GDP) में क्या अंतर है?"*
     - Observe the response generated in Hindi with exact mathematical identities:
       $$\text{GDP (Market Prices)} = \text{GVA (Basic Prices)} + \text{Net Product Taxes}$$
3. **Voice Input & Text-to-Speech**:
   - Click the **Microphone** icon to demonstrate browser speech-to-text.
   - Click the **Speaker** icon on any message to trigger natural speech synthesis read-aloud.

---

### 🟡 ACT 4: Cryptographic Digital Skill Passport & Micro-Credentials
*Goal: Demonstrate tamper-proof skill passports, instant public QR verification, and printable official ReportLab PDF skill cards.*

1. **Navigate to Digital Passport (`/passport`)**:
   - Switch back to **Pooja Sharma (JSO)**.
   - Inspect the **Verified Digital Skill Passport**:
     - Officer Name, Cadre (Subordinate Statistical Service), Employee ID, MoSPI Division.
     - Verified micro-credential badges with date stamps and issuing authority (NSSTA / iGOT).
     - Cryptographic SHA-256 fingerprint anchoring the officer's verified competencies.
2. **1-Click Official MoSPI Skill Card (PDF)**:
   - Click **"Download Official Skill Card (PDF)"**.
   - Open the generated PDF (compiled with ReportLab):
     - Official Government of India & MoSPI banner.
     - Competency level breakdown table.
     - Embedded cryptographic QR code.
3. **Public Zero-Auth Verification (`/verify`)**:
   - Click the Passport QR code or navigate to `/verify`.
   - Enter passport code: `MOSPI-SSS-2024-001` (or click the preview verification link).
   - Point out the **Security & Privacy Guardrails**:
     - Fully public, requires zero login.
     - Zero PII exposure: Officer email is masked (`p****@mospi.gov.in`).
     - Cryptographically validates that the certificate hash matches the tamper-proof ledger.

---

### 🔴 ACT 5: Cadre Macro Analytics & TPAC Allocator (Alok Mathur, Admin)
*Goal: Demonstrate institutional visibility, division heatmaps, bottleneck discovery, and automated NSSTA batch allocation.*

1. **Switch Role to Cadre Administrator**:
   - Select **Alok Mathur (`admin.cadre@mospi.gov.in`)**.
   - Navigate to `/admin`.
2. **Macro Workforce Competency Health**:
   - View top-level KPIs: Total Officers (7), Overall Cadre Readiness (64%), Total Gaps Identified (12), Priority Remediation Needed (5).
3. **Division Competency Heatmap**:
   - Compare competencies across divisions: **NAD** (National Accounts), **FOD** (Field Operations), **ESD** (Economic Statistics), and **SDRD** (Survey Design).
   - Point out how colour contrast immediately exposes that FOD has a high gap in sampling estimation while NAD has a gap in SUT compilation.
4. **Systemic Institutional Bottlenecks**:
   - Inspect the **Top 5 Competency Bottlenecks** table ranked by urgency and officer count.
   - Identify that 4 officers across SSS urgently require *"Advanced Field Survey Design & CAPI Tools"*.
5. **1-Click NSSTA TPAC Residential Batch Allocator**:
   - In the batch allocation panel:
     - Select Course: *"NSSTA Residential Workshop on Advanced Sampling (Greater Noida)"*.
     - Batch Capacity: `5` officers.
     - Allocation Strategy: `Prioritize Highest Weighted Urgency Score (WUS)`.
   - Click **"Generate Optimized Batch Allocation"**.
   - Watch the engine automatically select the top 5 officers with the most severe verified gaps.
   - Click **"Export Official Nomination Order (PDF)"** to produce the formal ministry training order.
6. **Supervisor Team Matrix (`/team-matrix`)**:
   - View division officers in a single comparative grid.
   - Demonstrate the **Supervisor Calibration** feature: division director adjusts an officer's competency level with written administrative justification.

---

## 🛡️ Technical Architecture & Judge Defense Points

### 1. "How is this different from generic LMS platforms like Moodle or Diksha?"
- **Domain-Specific Ontology**: Karmayogi Sankhyiki embeds the official MoSPI Competency Framework (18 competencies across 4 domains, 5-level rubrics, 36 role benchmarks for JSO, SSO, AD, DD, Director).
- **Dual-Track Synchronization**: Links self-paced digital courses on iGOT Karmayogi with physical residential capacity planning at NSSTA Greater Noida.
- **Bloom's CAT Engine**: Rather than static questions, assessments adapt to the officer's performance in real time using Bloom's cognitive taxonomy.
- **Tamper-Evident Micro-Credentials**: Passports use SHA-256 cryptographic hashes and privacy-masked public QR verification.

### 2. "How do you ensure AI responses are not hallucinated?"
- **Strict Retrieval-Augmented Generation (RAG)**: The assistant indexes 21 official MoSPI methodological guidelines (CPI, NSS, SNA 2008, IIP, DQAF).
- **Mandatory Clause Citations**: Every response requires explicit paragraph citations. If content is outside the indexed MoSPI repository, the system gracefully discloses boundaries.

### 3. "How does the platform align with Government of India policies?"
- **Mission Karmayogi**: Direct implementation of Rule-based to Role-based human resource management.
- **Digital Personal Data Protection (DPDP) Act 2023**: Zero PII leakage in public QR verification; cryptographic anonymization.
- **National Data Governance Framework Policy (NDGFP)**: Enforces DQAF standards and UN Fundamental Principles of Official Statistics.

---

## 📊 Summary of Verified System Routes

| Route | Page Name | Primary Target Persona | Core Features |
| :--- | :--- | :--- | :--- |
| `/` | **Competency Hub** | SSS / ISS Officers | Recharts Radar, WUS Urgency, Dual-Track Carousel |
| `/login` | **Authentication & SSO** | All Personas | iGOT SSO Simulation, 1-Click Persona Switcher |
| `/onboarding` | **Cadre Wizard** | New Officers | Division selection, 5-level rubric self-assessment |
| `/career-simulator` | **Career Progression** | SSS / ISS Officers | 3-Layer Comparative Radar, Promotion Readiness % |
| `/assessments` | **AI Assessment Studio** | NSSTA Faculty / Officers | Multimodal parser, Bloom's MCQs, Adaptive CAT test |
| `/chat` | **Sankhyiki Mitra** | All Statistical Officers | Bilingual (EN/HI) RAG, Voice input, Speech synthesis |
| `/passport` | **Digital Skill Passport** | Statistical Officers | Verified Badges, SHA-256 Hash, ReportLab PDF |
| `/verify` | **Public Verification** | Public / External Agencies | Zero-auth QR verification, Privacy masking |
| `/admin` | **Cadre Analytics** | MoSPI Leadership | Division Heatmaps, Bottlenecks, TPAC Allocator |
| `/team-matrix` | **Supervisor Matrix** | Division Directors | Team competency matrix, Live supervisor calibration |
