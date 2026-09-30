# 🇮🇳 Karmayogi Sankhyiki (SIH26101)
### AI-Enabled Skill Intelligence & Capacity Building Platform for India's Official Statistical System
**Integrated with iGOT Karmayogi Ecosystem & NSSTA TPAC Framework**

---

## 🏛️ Project Overview
**Karmayogi Sankhyiki** is an enterprise-grade AI-powered skill intelligence and personalized learning platform developed for the **Ministry of Statistics and Programme Implementation (MoSPI)** and the **National Statistical Systems Training Academy (NSSTA)**.

It addresses the fundamental capacity-building challenges in India's Official Statistical System:
1. **Official Statistical Competency Framework**: Standardized 4-domain framework (**Statistical**, **Technical**, **Digital Governance**, **Behavioural & Managerial**) across 5 proficiency levels (Novice to Master).
2. **Automated Competency Gap Diagnosis**: Computes real-time gap vectors and Weighted Urgency Scores ($WUS$) against role benchmarks for Indian Statistical Service (ISS) and Subordinate Statistical Service (SSS) cadres.
3. **Dual-Track Learning Pathways**:
   - **Track A (iGOT Karmayogi)**: Asynchronous, digital micro-learning modules (15 mins – 4 hours).
   - **Track B (NSSTA TPAC)**: High-impact institutional and residential programmes at NSSTA Greater Noida.
4. **Multimodal AI Assessment Engine**: Ingests official manuals, reports, and presentations (PDF, DOCX, PPTX) as well as **Video/Audio Transcripts**, generating high-validity MCQs classified across **Bloom's Taxonomy** with distractor rationales and page citations.
5. **Computerized Adaptive Testing (CAT)**: Real-time dynamic question difficulty adjustment matching candidate performance.
6. **MoSPI Digital Skill Passport**: Issues verifiable credentials with embeddable **QR codes** for tamper-proof competency verification.
7. **"Sankhyiki Mitra" (AI Statistical Tutor)**: Bilingual conversational RAG tutor with microphone voice input and audio speech output.
8. **Supervisor Team Matrix & Executive PDF Reports**: Division-level skill aggregation and 1-click official PDF reporting.

---

## 🎨 UI/UX Philosophy
Inspired by **Coursera, Linear, and Notion**, the platform utilizes a sleek, distraction-free monochromatic (Black & White) aesthetic designed for high-density statistical visualization, modern government elegance, and international academic appeal.

---

## 🏗️ System Architecture
```
                                +-----------------------------------+
                                |    Coursera-Inspired UI Layer     |
                                |     (Next.js 14 + Tailwind)       |
                                +-----------------+-----------------+
                                                  |
                                                  v
                                +-----------------+-----------------+
                                |      FastAPI Application Core     |
                                +--------+--------+--------+--------+
                                         |        |        |
         +-------------------------------+        |        +-------------------------------+
         |                                        |                                        |
         v                                        v                                        v
+-----------------+                      +-----------------+                      +-----------------+
| Competency &    |                      | Multimodal AI   |                      | Dual-Track      |
| Gap Analysis    |                      | Assessment (CAT)|                      | Recommendations |
| Engine          |                      | & Gemini 1.5    |                      | (iGOT + TPAC)   |
+--------+--------+                      +--------+--------+                      +--------+--------+
         |                                        |                                        |
         +-------------------------------+        |        +-------------------------------+
                                         |        |        |
                                         v        v        v
                                +-----------------+-----------------+
                                | PostgreSQL / Neon / SQLite Store  |
                                |       (ACID Database Layer)       |
                                +-----------------------------------+
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Node.js 18+ (Node.js 20 recommended)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Seed MoSPI competencies, benchmarks, iGOT & TPAC courses
python seed_database.py

# Run FastAPI server
uvicorn app.main:app --reload --port 8000
```
Interactive API Documentation will be available at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The application will launch at: `http://localhost:3000`

---

## 🔑 Environment Variables
See `backend/.env.example`:
- `DATABASE_URL`: Defaults to SQLite (`sqlite:///./karmayogi.db`). For cloud deployment, paste your **Neon.tech** or **Supabase** PostgreSQL URL.
- `GEMINI_API_KEY`: (Optional) Free API key from [Google AI Studio](https://aistudio.google.com/) for live Gemini 1.5 LLM document parsing and chatbot generation.
