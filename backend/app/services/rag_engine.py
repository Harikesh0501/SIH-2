"""
Sankhyiki Mitra (सांख्यिकी मित्र) - Official MoSPI RAG Engine & Statistical Tutor.
Indexes official MoSPI manuals (National Accounts, CPI, PLFS, DQAF) into searchable chunks,
performs context retrieval with exact citations, and executes bilingual LLM tutoring via NVIDIA NIM.
"""
from typing import List, Dict, Any, Optional, Tuple
import os
import re
import json
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# Official Bilingual MoSPI Terminology Dictionary
BILINGUAL_DICTIONARY: Dict[str, Dict[str, str]] = {
    "gva": {"en": "Gross Value Added (GVA) at basic prices", "hi": "मूल कीमतों पर सकल मूल्यवर्धन (GVA)"},
    "gdp": {"en": "Gross Domestic Product (GDP) at market prices", "hi": "बाजार मूल्यों पर सकल घरेलू उत्पाद (GDP)"},
    "cpi": {"en": "Consumer Price Index (CPI)", "hi": "उपभोक्ता मूल्य सूचकांक (CPI)"},
    "laspeyres": {"en": "Modified Laspeyres Formula", "hi": "संशोधित लास्पேயர்ஸ் सूत्र"},
    "jevons": {"en": "Jevons Geometric Mean Index", "hi": "जेवन्स ज्यामितीय माध्य सूचकांक"},
    "plfs": {"en": "Periodic Labour Force Survey (PLFS)", "hi": "आवधिक श्रम बल सर्वेक्षण (PLFS)"},
    "ups": {"en": "Usual Principal Status (UPS)", "hi": "सामान्य प्रमुख स्थिति (UPS)"},
    "upss": {"en": "Usual Principal & Subsidiary Status (UPSS)", "hi": "सामान्य प्रमुख एवं सहायक स्थिति (UPSS)"},
    "cws": {"en": "Current Weekly Status (CWS)", "hi": "वर्तमान साप्ताहिक स्थिति (CWS)"},
    "dqaf": {"en": "Data Quality Assurance Framework (DQAF)", "hi": "डेटा गुणवत्ता आश्वासन रूपरेखा (DQAF)"},
    "sampling": {"en": "Multi-stage Stratified Sampling", "hi": "बहु-चरणीय स्तरीकृत प्रतिचयन"},
    "fsu": {"en": "First Stage Unit (FSU)", "hi": "प्रथम चरण इकाई (FSU)"},
    "sut": {"en": "Supply and Use Tables (SUT)", "hi": "आपूर्ति एवं उपयोग तालिकाएं (SUT)"},
    "dpdp": {"en": "Digital Personal Data Protection Act", "hi": "डिजिटल व्यक्तिगत डेटा संरक्षण अधिनियम"},
}

class RAGEngine:
    _index_cache: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def get_knowledge_index(cls) -> List[Dict[str, Any]]:
        """
        Loads and indexes official MoSPI training guides and manuals into semantic chunks.
        Caches index in memory for sub-millisecond retrieval.
        """
        if cls._index_cache is not None:
            return cls._index_cache

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sample_dir = os.path.join(base_dir, "..", "sample_data")
        if not os.path.exists(sample_dir):
            sample_dir = os.path.join(base_dir, "sample_data")

        chunks: List[Dict[str, Any]] = []
        chunk_id = 1

        if os.path.exists(sample_dir):
            for fname in os.listdir(sample_dir):
                if not fname.endswith(".txt"):
                    continue
                fpath = os.path.join(sample_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()

                    # Extract Document Title from first 3 lines
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    doc_title = lines[0] if lines else fname
                    for l in lines[:6]:
                        if "MANUAL" in l or "GUIDE" in l or "HANDBOOK" in l:
                            doc_title = l
                            break

                    # Split into major sections
                    raw_sections = text.split("\n\n")
                    curr_section = "General Overview"
                    sec_text_acc = []

                    for sec in raw_sections:
                        sec_strip = sec.strip()
                        if not sec_strip:
                            continue

                        # Check if section starts with a numbered heading e.g. "1. Introduction" or "CHAPTER"
                        first_line = sec_strip.split("\n")[0].strip()
                        if re.match(r'^(?:[0-9]+\.|\bCHAPTER\b|\bSection\b)', first_line, re.IGNORECASE):
                            if sec_text_acc:
                                chunk_text = "\n\n".join(sec_text_acc)
                                chunks.append({
                                    "id": chunk_id,
                                    "source_title": doc_title,
                                    "filename": fname,
                                    "section_title": curr_section,
                                    "text": chunk_text,
                                    "tokens": len(chunk_text.split()),
                                })
                                chunk_id += 1
                                sec_text_acc = []
                            curr_section = first_line

                        sec_text_acc.append(sec_strip)

                    if sec_text_acc:
                        chunk_text = "\n\n".join(sec_text_acc)
                        chunks.append({
                            "id": chunk_id,
                            "source_title": doc_title,
                            "filename": fname,
                            "section_title": curr_section,
                            "text": chunk_text,
                            "tokens": len(chunk_text.split()),
                        })
                        chunk_id += 1

                except Exception as e:
                    logger.error(f"Error reading {fname}: {e}")

        cls._index_cache = chunks
        logger.info(f"RAG Knowledge Base successfully indexed {len(chunks)} official MoSPI clauses.")
        return chunks

    @classmethod
    def retrieve_relevant_context(
        cls,
        query: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top K most relevant statistical clauses using BM25-style keyword density,
        phrase matching, and domain terminology weights.
        """
        index = cls.get_knowledge_index()
        if not index:
            return []

        query_clean = query.lower()
        query_words = set(re.findall(r'\b[a-zA-Z0-9_\u0900-\u097F]{3,}\b', query_clean))

        # Check for query acronym expansions
        for key, bi in BILINGUAL_DICTIONARY.items():
            if key in query_clean:
                query_words.update(re.findall(r'\b[a-zA-Z0-9]{3,}\b', bi["en"].lower()))

        scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

        for ch in index:
            text_lower = ch["text"].lower()
            section_lower = ch["section_title"].lower()
            score = 0.0

            # 1. Exact phrase match bonus
            if len(query_clean) > 8 and query_clean in text_lower:
                score += 5.0

            # 2. Section title match bonus
            for qw in query_words:
                if qw in section_lower:
                    score += 2.5
                if qw in text_lower:
                    # Term frequency count
                    freq = text_lower.count(qw)
                    score += min(3.0, freq * 0.5)

            # 3. Domain terms bonus
            for term in ["cpi", "gva", "gdp", "plfs", "dqaf", "sampling", "laspeyres", "jevons", "sut"]:
                if term in query_clean and term in text_lower:
                    score += 2.0

            if score > 0.0:
                scored_chunks.append((score, ch))

        # Sort descending by relevance score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = []

        for s, ch in scored_chunks[:top_k]:
            normalized_score = min(1.0, round(s / 10.0, 2))
            top_results.append({
                "source_title": ch["source_title"],
                "section_title": ch["section_title"],
                "filename": ch["filename"],
                "text": ch["text"],
                "relevance_score": normalized_score,
            })

        return top_results

    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Detects if user is asking in Hindi / Devanagari script.
        """
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        if hindi_chars >= 3 or any(w in text.lower() for w in ["kya", "hai", "kaise", "batao", "antar"]):
            return "hi"
        return "en"

    @classmethod
    def generate_tutoring_response(
        cls,
        query: str,
        session_id: str = "default",
        user_name: str = "Officer",
        user_designation: str = "Junior Statistical Officer",
    ) -> Dict[str, Any]:
        """
        Generates contextual answer as "Sankhyiki Mitra" with official citations.
        Uses NVIDIA NIM with smart bilingual statistical tutor persona.
        """
        lang = cls.detect_language(query)
        retrieved_contexts = cls.retrieve_relevant_context(query, top_k=2)

        # Build context prompt
        context_str = ""
        citations = []
        for idx, rc in enumerate(retrieved_contexts):
            citations.append({
                "source": rc["source_title"],
                "section": rc["section_title"],
                "relevance_score": rc["relevance_score"],
            })
            text_snippet = " ".join(rc["text"].split()[:200])
            context_str += f"\n[DOCUMENT {idx+1}: {rc['source_title']} | {rc['section_title']}]\n{text_snippet}\n"

        system_prompt = (
            "You are Sankhyiki Mitra, Official MoSPI Statistical Tutor. "
            "Answer concisely with mathematical precision. Cite MoSPI manuals. "
            "If query is in Hindi, reply in Hindi. Structure: Definition, Formula, Application, Citation."
        )

        user_prompt = (
            f"CONTEXT:\n{context_str or 'Use MoSPI official manuals.'}\n\n"
            f"QUESTION: {query}"
        )

        answer_text = ""
        provider = "NVIDIA_NIM_LLAMA_3.2"

        if settings.NVIDIA_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": settings.NVIDIA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.25,
                    "max_tokens": 400,
                }
                with httpx.Client(timeout=45.0, verify=False) as client:
                    resp = client.post(
                        f"{settings.NVIDIA_BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                if resp.status_code == 200:
                    answer_text = resp.json()["choices"][0]["message"]["content"].strip()
                else:
                    logger.warning(f"NVIDIA API status {resp.status_code}. Using intelligent tutor fallback.")
            except Exception as e:
                logger.warning(f"NVIDIA API error: {e}. Using intelligent tutor fallback.")

        # If LLM response failed or unavailable, use rich bilingual heuristic fallback
        if not answer_text:
            provider = "INTELLIGENT_BILINGUAL_FALLBACK"
            answer_text = cls._generate_fallback_answer(query, lang, retrieved_contexts)

        return {
            "answer": answer_text,
            "language": lang,
            "sources": citations,
            "provider": provider,
        }

    @classmethod
    def _generate_fallback_answer(
        cls,
        query: str,
        lang: str,
        contexts: List[Dict[str, Any]],
    ) -> str:
        """
        Bilingual heuristic tutor fallback ensuring zero-failure responses.
        """
        q_lower = query.lower()

        # National Accounts: GVA vs GDP
        if "gva" in q_lower or "gdp" in q_lower or "national accounts" in q_lower or "सकल मूल्य" in q_lower:
            if lang == "hi":
                return (
                    "**सांख्यिकी मित्र (Sankhyiki Mitra) - आधिकारिक मार्गदर्शन:**\n\n"
                    "### 1. सकल मूल्य वर्धन (GVA) और सकल घरेलू उत्पाद (GDP) में अंतर:\n"
                    "- **मूल कीमतों पर GVA (GVA at Basic Prices)**: यह उत्पादकों द्वारा अर्जित आय को मापता है। इसमें उत्पादन कर (Production Taxes जैसे भू-राजस्व) शामिल होते हैं और उत्पादन सब्सिडी घटाई जाती है, परंतु उत्पाद कर (Product Taxes जैसे GST) शामिल नहीं होते।\n"
                    "- **बाजार मूल्यों पर GDP (GDP at Market Prices)**: यह देश की भौगोलिक सीमा के भीतर अंतिम वस्तुओं और सेवाओं का कुल बाजार मूल्य है।\n\n"
                    "### 2. आधिकारिक गणितीय संबंध (SNA 2008):\n"
                    "$$\\text{GDP at Market Prices} = \\text{GVA at Basic Prices} + \\text{Product Taxes} - \\text{Product Subsidies}$$\n\n"
                    "### 3. MoSPI संचालन संदर्भ:\n"
                    "केंद्रीय सांख्यिकी कार्यालय (CSO) का राष्ट्रीय लेखा प्रभाग (NAD) प्रत्येक तिमाही इस सूत्र के आधार पर भारत के विकास आंकड़े जारी करता है।\n\n"
                    "**સંદર્ભ (Citation)**: *National Accounts Statistics: Sources and Methods (CSO, MoSPI)*"
                )
            else:
                return (
                    "**Sankhyiki Mitra (Official MoSPI Guidance):**\n\n"
                    "### 1. Conceptual Distinction: GVA at Basic Prices vs GDP at Market Prices\n"
                    "- **GVA at Basic Prices (मूल कीमतों पर सकल मूल्यवर्धन)**: Measures the value of output minus intermediate consumption from the producer's perspective. It includes production taxes (e.g., land revenues, stamp duty) and subtracts production subsidies, but excludes product taxes (e.g., GST, excise duty).\n"
                    "- **GDP at Market Prices (बाजार मूल्यों पर सकल घरेलू उत्पाद)**: Reflects total economic expenditure at purchaser's prices across the domestic economy.\n\n"
                    "### 2. Official National Accounts Identity (SNA 2008 Framework):\n"
                    "$$\\text{GDP at Market Prices} = \\text{GVA at Basic Prices} + \\text{Product Taxes} - \\text{Product Subsidies}$$\n\n"
                    "### 3. MoSPI Operational Application:\n"
                    "The National Accounts Division (NAD) of MoSPI utilizes this reconciliation to compute quarterly and annual economic growth rates.\n\n"
                    "**Official Citation**: *National Accounts Statistics Sources & Methods - Chapter 2 (CSO, MoSPI)*"
                )

        # CPI Price Statistics
        if "cpi" in q_lower or "price" in q_lower or "laspeyres" in q_lower or "उपभोक्ता मूल्य" in q_lower:
            if lang == "hi":
                return (
                    "**सांख्यिकी मित्र (Sankhyiki Mitra) - आधिकारिक मार्गदर्शन:**\n\n"
                    "### 1. उपभोक्ता मूल्य सूचकांक (CPI Base 2012=100) संकलन पद्धति:\n"
                    "MoSPI का राष्ट्रीय सांख्यिकी कार्यालय (NSO) ग्रामीण, शहरी और संयुक्त (Combined) क्षेत्रों के लिए दो-स्तरीय पद्धति का उपयोग करता है:\n"
                    "- **प्राथमिक एकत्रीकरण (Elementary Aggregation)**: बाजार स्तर पर जेवन्स ज्यामितीय माध्य सूत्र (Jevons Geometric Mean) का उपयोग होता है ताकि प्रतिस्थापन पूर्वाग्रह (substitution bias) न आए।\n"
                    "- **उच्च स्तरीय एकत्रीकरण (Higher Aggregation)**: उप-समूह और सामान्य सूचकांक के लिए संशोधित लास्पேயர்ஸ் सूत्र (Modified Laspeyres Formula) का उपयोग होता है।\n\n"
                    "### 2. आधिकारिक सूत्र:\n"
                    "$$I_t = \\frac{\\sum (W_i \\times \\frac{P_{it}}{P_{i0}})}{\\sum W_i} \\times 100$$\n\n"
                    "**સંદર્ભ (Citation)**: *Manual on Consumer Price Index (Base 2012=100), Chapter 3 (CSO/MoSPI)*"
                )
            else:
                return (
                    "**Sankhyiki Mitra (Official MoSPI Guidance):**\n\n"
                    "### 1. Consumer Price Index (उपभोक्ता मूल्य सूचकांक) Compilation Methodology:\n"
                    "MoSPI compiles All-India CPI (Base 2012=100) monthly across 1,181 rural markets (via India Post) and 1,114 urban markets (via FOD, NSO).\n"
                    "- **Stage 1 (Elementary Aggregation)**: Compiled using the Geometric Mean (Jevons Index) to prevent upward substitution bias.\n"
                    "- **Stage 2 (Higher Level Aggregation)**: Sub-groups and General Index use the Modified Laspeyres Arithmetic Mean Formula based on 68th Round HCES expenditure weights.\n\n"
                    "### 2. Standard Imputation Method for Missing Quotes:\n"
                    "MoSPI strictly mandates cell-mean imputation using observed relative price changes of comparable varieties in the stratum.\n\n"
                    "**Official Citation**: *Manual on Consumer Price Index (Base: 2012=100), Chapter 3 & 4 (CSO, MoSPI)*"
                )

        # General Official Statistics
        if contexts:
            c = contexts[0]
            return (
                f"**Sankhyiki Mitra (Official MoSPI Guidance):**\n\n"
                f"Based on **{c['source_title']}** (*{c['section_title']}*):\n\n"
                f"{c['text'][:500]}...\n\n"
                f"**Official Citation**: *{c['source_title']} ({c['filename']})*"
            )

        return (
            "**Sankhyiki Mitra (सांख्यिकी मित्र):**\n\n"
            "I am equipped with official MoSPI training manuals on National Accounts (SNA 2008), Consumer Price Index (CPI Base 2012=100), "
            "Periodic Labour Force Survey (PLFS), Data Quality Assurance Framework (DQAF), and the DPDP Act 2023.\n\n"
            "Please ask any question regarding official statistical concepts, sampling design, or macroeconomic identities in either English or Hindi."
        )
