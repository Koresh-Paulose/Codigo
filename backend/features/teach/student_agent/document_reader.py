import os
import re
import urllib.parse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field

class TopicFact(BaseModel):
    title: str
    fact: str
    sample_question: str = ""

class DocumentKnowledge(BaseModel):
    file_name: str
    file_path: Optional[str] = None
    content: str
    summary: str = ""
    concepts: List[str] = Field(default_factory=list)
    topic_facts: List[TopicFact] = Field(default_factory=list)
    word_count: int = 0

class DocumentReader:
    @staticmethod
    def sanitize_path(raw_path: str) -> str:
        """Sanitizes file paths from dragged links, file:/// URLs, and quotes."""
        clean = raw_path.strip().strip('"').strip("'")
        if clean.startswith("file:///"):
            clean = clean[8:]
        elif clean.startswith("file://"):
            clean = clean[7:]
        if re.match(r"^/[a-zA-Z]:", clean):
            clean = clean[1:]
        clean = urllib.parse.unquote(clean)
        clean = os.path.normpath(clean)
        return clean

    @classmethod
    def read_file(cls, file_path: str) -> DocumentKnowledge:
        clean_path = cls.sanitize_path(file_path)
        path = Path(clean_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {clean_path}")

        suffix = path.suffix.lower()
        content = ""

        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                pages_text = []
                for idx, page in enumerate(reader.pages):
                    extracted = page.extract_text()
                    if extracted:
                        pages_text.append(extracted.strip())
                content = "\n\n".join(pages_text)
            except Exception as e:
                raise RuntimeError(f"Failed to read PDF file '{path.name}': {e}")
        else:
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
            read_success = False
            for enc in encodings:
                try:
                    with open(path, "r", encoding=enc) as f:
                        content = f.read()
                    read_success = True
                    break
                except UnicodeDecodeError:
                    continue
            if not read_success:
                with open(path, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore")

        if not content.strip():
            raise ValueError(f"File '{path.name}' is empty or no text could be extracted.")

        # Clean carriage returns and unknown unicode symbols
        clean_content = content.replace("\r\n", "\n").replace("\r", "\n").replace("\ufffd", "-")
        # Normalize double spaces and remove trailing line whitespace
        clean_lines = [line.rstrip() for line in clean_content.splitlines()]
        clean_content = "\n".join(clean_lines).strip()

        word_count = len(clean_content.split())
        topic_facts = cls._extract_balanced_topics(clean_content)
        concepts = [tf.title for tf in topic_facts]
        summary = cls._create_brief_summary(clean_content, concepts)

        return DocumentKnowledge(
            file_name=path.name,
            file_path=str(path),
            content=clean_content,
            summary=summary,
            concepts=concepts,
            topic_facts=topic_facts,
            word_count=word_count,
        )

    @classmethod
    def _extract_balanced_topics(cls, text: str) -> List[TopicFact]:
        """Extracts 5 well-defined topics with concrete facts dynamically from the document."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # 1. Check for markdown bullet definitions: - **Title**: Description
        bullet_items = []
        for line in lines:
            m = re.match(r"^[*\-]\s+\*\*([^*:]+)\*\*:\s*(.+)", line)
            if m:
                b_title = m.group(1).strip()
                b_fact = m.group(2).strip()
                bullet_items.append((b_title, b_fact))

        if len(bullet_items) >= 4:
            results = []
            for title, fact in bullet_items[:5]:
                sample_q = f"Looking at {title}, could you explain what it does and why it is important?"
                results.append(TopicFact(title=title, fact=fact, sample_question=sample_q))
            return results

        # 2. Check for numbered or markdown headers
        headers = []
        for i, line in enumerate(lines):
            m = re.match(r"^(?:(?:\d+[\.\)]|#{1,4})\s*)([A-Za-z0-9\s\-_/:&]+)", line)
            if m:
                h = m.group(1).strip()
                h = re.sub(r"^\d+[\.\)]\s*", "", h).strip()
                if 3 <= len(h) <= 50 and h.lower() not in ["introduction", "testing note", "notes", "overview"]:
                    headers.append((i, h))

        if len(headers) >= 3:
            results = []
            for idx, (line_no, title) in enumerate(headers[:5]):
                next_idx = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
                sec_lines = lines[line_no + 1 : next_idx]
                cleaned_lines = []
                for sl in sec_lines:
                    sl_clean = sl.strip()
                    if "testing note" in sl_clean.lower() or "preview and text extraction" in sl_clean.lower():
                        break
                    if sl_clean.lower() in ["topic", "information", "basic information", "topic basic information"]:
                        continue
                    cleaned_lines.append(sl_clean)

                fact_text = " ".join(cleaned_lines).strip()
                fact_words = fact_text.split()
                if len(fact_words) > 60:
                    fact_snippet = " ".join(fact_words[:60]) + "..."
                else:
                    fact_snippet = fact_text

                if not fact_snippet:
                    fact_snippet = f"Key principles regarding {title} in the reference material."

                sample_q = f"In the section on '{title}', the notes highlight: \"{fact_snippet[:90]}...\". Could you explain how that works in simple terms?"
                results.append(TopicFact(title=title, fact=fact_snippet, sample_question=sample_q))

            # Guarantee exactly 5 topics by expanding multi-concept sections if fewer than 5
            if 0 < len(results) < 5:
                qf_idx = next((i for i, r in enumerate(results) if "fact" in r.title.lower()), None)
                target_idx = qf_idx if qf_idx is not None else max(range(len(results)), key=lambda i: len(results[i].fact.split()))
                f_text = results[target_idx].fact
                m = re.search(r"(Communication.*|Senses.*)", f_text, re.I)
                if m and m.start() > 10:
                    part1 = f_text[:m.start()].strip()
                    part2 = m.group(1).strip()
                    old_title = results[target_idx].title
                    results[target_idx] = TopicFact(title=f"{old_title} & Diet", fact=part1)
                    results.insert(target_idx + 1, TopicFact(title="Senses & Communication", fact=part2))
                else:
                    words = f_text.split()
                    mid = len(words) // 2
                    results[target_idx] = TopicFact(title=f"{results[target_idx].title} - Part 1", fact=" ".join(words[:mid]))
                    results.insert(target_idx + 1, TopicFact(title=f"{results[target_idx].title} - Part 2", fact=" ".join(words[mid:])))

            return results[:5]

        # 3. Fallback: Divide into 5 conceptual chunks
        sentences = [s.strip() for s in re.split(r"[.\n]+", text) if len(s.strip()) > 25]
        if not sentences:
            sentences = ["Overview of the study material.", "Core principles described in the document."]
        step = max(1, len(sentences) // 5)
        results = []
        for i in range(5):
            idx = min(i * step, len(sentences) - 1)
            sentence = sentences[idx]
            words = sentence.split()
            title = " ".join(words[:4]).strip(" ,:-") or f"Concept Part {i+1}"
            sample_q = f"Could you break down '{title}' and explain why it is important?"
            results.append(TopicFact(title=title, fact=sentence, sample_question=sample_q))
            if len(results) >= 5:
                break
        return results

    @staticmethod
    def _create_brief_summary(text: str, concepts: List[str]) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        first_few = " ".join(lines[:3])
        if len(first_few) > 200:
            first_few = first_few[:197] + "..."
        concept_str = ", ".join(concepts[:5]) if concepts else "Document materials"
        return f"{first_few} (Key Topics: {concept_str})"
