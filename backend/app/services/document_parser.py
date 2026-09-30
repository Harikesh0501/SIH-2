"""
Multimodal Document Parser & Semantic Chunking Engine.
Supports PDF, DOCX, PPTX presentations, TXT documents, and Video/Audio Transcripts.
Preserves slide numbers, page numbers, and structural section headers.
"""
from typing import List, Dict, Any, Tuple, Optional
import os
import re

class DocumentParser:
    @staticmethod
    def parse_pdf(file_path: str) -> Tuple[str, int, List[Dict[str, Any]]]:
        """
        Extracts text from PDF page by page using pypdf.
        Returns (full_text, page_count, pages_metadata).
        """
        import pypdf
        reader = pypdf.PdfReader(file_path)
        pages_metadata: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            clean_text = text.strip()
            if clean_text:
                full_text_parts.append(clean_text)
                # Try to extract a section title from the first line
                first_line = clean_text.split("\n")[0][:120].strip()
                pages_metadata.append({
                    "page_number": page_num,
                    "section_title": first_line if len(first_line) > 3 else f"Page {page_num}",
                    "text": clean_text,
                })

        full_text = "\n\n".join(full_text_parts)
        return full_text, len(reader.pages), pages_metadata

    @staticmethod
    def parse_pptx(file_path: str) -> Tuple[str, int, List[Dict[str, Any]]]:
        """
        Extracts title, bullet points, and tables slide-by-slide from PPTX presentations.
        Returns (full_text, slide_count, slides_metadata).
        """
        from pptx import Presentation
        prs = Presentation(file_path)
        slides_metadata: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for idx, slide in enumerate(prs.slides):
            slide_num = idx + 1
            slide_title = f"Slide {slide_num}"
            bullet_texts: List[str] = []

            # 1. Look for slide title shape
            if slide.shapes.title and slide.shapes.title.text:
                slide_title = slide.shapes.title.text.strip()

            # 2. Extract text from all other shapes and tables
            for shape in slide.shapes:
                if shape == slide.shapes.title:
                    continue
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = para.text.strip()
                        if text:
                            bullet_texts.append(text)
                elif shape.has_table:
                    for row in shape.table.rows:
                        row_vals = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_vals:
                            bullet_texts.append(" | ".join(row_vals))

            slide_body = "\n".join(bullet_texts)
            formatted_slide = f"## Slide {slide_num}: {slide_title}\n{slide_body}"
            full_text_parts.append(formatted_slide)

            slides_metadata.append({
                "page_number": slide_num,
                "section_title": slide_title,
                "text": f"{slide_title}\n{slide_body}".strip(),
            })

        full_text = "\n\n".join(full_text_parts)
        return full_text, len(prs.slides), slides_metadata

    @staticmethod
    def parse_docx(file_path: str) -> Tuple[str, int, List[Dict[str, Any]]]:
        """
        Extracts structured sections and paragraphs from Word (.docx) files.
        Returns (full_text, estimated_pages, sections_metadata).
        """
        import docx
        doc = docx.Document(file_path)
        sections_metadata: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        current_heading = "Overview"
        current_paragraphs: List[str] = []
        page_approx = 1
        word_count = 0

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Check if this paragraph is a heading
            if para.style and "heading" in para.style.name.lower():
                if current_paragraphs:
                    sec_text = "\n".join(current_paragraphs)
                    sections_metadata.append({
                        "page_number": page_approx,
                        "section_title": current_heading,
                        "text": sec_text,
                    })
                    current_paragraphs = []
                current_heading = text
            else:
                current_paragraphs.append(text)
                word_count += len(text.split())
                if word_count > 400:
                    page_approx += 1
                    word_count = 0

            full_text_parts.append(text)

        if current_paragraphs:
            sections_metadata.append({
                "page_number": page_approx,
                "section_title": current_heading,
                "text": "\n".join(current_paragraphs),
            })

        full_text = "\n\n".join(full_text_parts)
        return full_text, max(1, page_approx), sections_metadata

    @staticmethod
    def parse_txt(file_path: str) -> Tuple[str, int, List[Dict[str, Any]]]:
        """
        Extracts content from plain text (.txt) files.
        Returns (full_text, estimated_pages, sections_metadata).
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            full_text = f.read()

        sections_metadata: List[Dict[str, Any]] = []
        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]

        current_section = "General Section"
        current_chunk_paras: List[str] = []
        current_words = 0
        page_num = 1

        for p in paragraphs:
            # Check for header-like lines
            lines = p.split("\n")
            if lines[0].startswith("#") or lines[0].isupper() or len(lines[0]) < 60 and lines[0].endswith(":"):
                current_section = lines[0].strip("#: \t")

            current_chunk_paras.append(p)
            current_words += len(p.split())

            if current_words >= 350:
                sections_metadata.append({
                    "page_number": page_num,
                    "section_title": current_section,
                    "text": "\n\n".join(current_chunk_paras),
                })
                current_chunk_paras = []
                current_words = 0
                page_num += 1

        if current_chunk_paras:
            sections_metadata.append({
                "page_number": page_num,
                "section_title": current_section,
                "text": "\n\n".join(current_chunk_paras),
            })

        return full_text, max(1, page_num), sections_metadata

    @staticmethod
    def parse_transcript(transcript_text: str, video_url: Optional[str] = None) -> Tuple[str, int, List[Dict[str, Any]]]:
        """
        Parses video/audio transcript text with timestamp detection and speaker tagging.
        Returns (full_text, segment_count, segments_metadata).
        """
        clean_text = transcript_text.strip()
        lines = clean_text.split("\n")
        segments: List[Dict[str, Any]] = []

        current_time = "00:00"
        current_block: List[str] = []
        segment_idx = 1
        word_count = 0

        # Regex for common timestamp patterns e.g. [01:23], 01:23, (01:23)
        time_pattern = re.compile(r'\[?\(?(\d{1,2}:\d{2}(?::\d{2})?)\)?\]?')

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Look for timestamp in line
            match = time_pattern.search(line_str)
            if match:
                current_time = match.group(1)

            current_block.append(line_str)
            word_count += len(line_str.split())

            if word_count >= 300:
                segments.append({
                    "page_number": segment_idx,
                    "section_title": f"Webinar Segment @ {current_time}",
                    "text": "\n".join(current_block),
                })
                current_block = []
                word_count = 0
                segment_idx += 1

        if current_block:
            segments.append({
                "page_number": segment_idx,
                "section_title": f"Webinar Segment @ {current_time}",
                "text": "\n".join(current_block),
            })

        return clean_text, len(segments), segments

    @staticmethod
    def chunk_extracted_content(
        units_metadata: List[Dict[str, Any]],
        target_chunk_words: int = 350,
        overlap_words: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic chunking (600-800 tokens / 300-450 words) with overlap.
        Preserves section titles and slide/page citations.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for unit in units_metadata:
            text = unit.get("text", "").strip()
            page_or_slide = unit.get("page_number", 1)
            section = unit.get("section_title", f"Section {page_or_slide}")

            words = text.split()
            if not words:
                continue

            # If unit is already reasonably sized (< 450 words), keep as a unified chunk
            if len(words) <= target_chunk_words:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "chunk_text": text,
                    "page_or_slide_number": page_or_slide,
                    "section_title": section,
                })
                chunk_idx += 1
            else:
                # Sliding window chunking with overlap
                start = 0
                step = target_chunk_words - overlap_words
                while start < len(words):
                    chunk_slice = words[start : start + target_chunk_words]
                    chunk_str = " ".join(chunk_slice)
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "chunk_text": chunk_str,
                        "page_or_slide_number": page_or_slide,
                        "section_title": section,
                    })
                    chunk_idx += 1
                    start += step

        return chunks
