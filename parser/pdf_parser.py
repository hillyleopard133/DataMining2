# parser/pdf_parser.py
import fitz  # PyMuPDF
import json
import os
import re
from difflib import SequenceMatcher

def extract_questions_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    questions = []

    year = extract_year(pdf_path)

    full_text = ""

    for page_num, page in enumerate(doc):

        text = page.get_text()

        # Remove continuation headers
        text = re.sub(r"continued\s+overleaf", "", text, flags=re.IGNORECASE)
        text = re.sub(r"continues\s+overleaf", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Question\s+\d+\s+continued\s+overleaf", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Question\s+\d+\s+continued", "", text, flags=re.IGNORECASE)

        # Remove total marks
        text = re.sub(r"\(Total\s+\d+\s+Marks\)", "", text, flags=re.IGNORECASE)

        full_text += f"\n{text}\n"

    # Remove page markers and stray page numbers
    full_text = re.sub(r"PAGE_BREAK_\d+", " ", full_text)
    full_text = re.sub(r"\n\s*\d+\s*\n", "\n", full_text)
    full_text = re.sub(r"\n+", "\n", full_text)
    
    # Remove everything starting from "Laws of Logic" to the end of the document
    full_text = re.sub(r"Laws of Logic.*", "", full_text, flags= re.DOTALL)
    full_text = re.sub(r"Laws of Algebra sets.*", "", full_text, flags= re.DOTALL)
    full_text = re.sub(r"PLEASE ASK FOR THE NEW MATHEMATICS TABLES.*", "", full_text, flags= re.DOTALL)

    # Split by Question number
    question_blocks = re.split(r"Question\s+(\d+)", full_text)

    for i in range(1, len(question_blocks), 2):

        q_number = int(question_blocks[i])
        q_text = question_blocks[i + 1]

        parts = re.findall(
            r"^\s*\(([a-h])\)\s*(.*?)(?=^\s*\([a-h]\)|\Z)",
            q_text,
            flags = re.MULTILINE | re.DOTALL
        )

        for part_letter, part_text in parts:

            part_text = re.sub(r"\s*(\(\w+\))", r"\n\1", part_text)

            marks_matches = re.findall(r"(\d+(?:\.\d+)?)\s*marks?\)", part_text, flags=re.IGNORECASE)
            marks = sum(float(m) for m in marks_matches) if marks_matches else None

            text = part_text.strip()

            if(len(text) != 0):
                questions.append({
                    "question_number": q_number,
                    "part": part_letter.lower(),
                    "text": text,
                    "marks": marks,
                    "source_pdf": os.path.basename(pdf_path),
                    "year": year,
                    "topic": infer_topic(part_text),
                    "difficulty": infer_difficulty(marks)
                })

    return questions

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def assign_bounds_to_questions(pdf_path, questions):
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc):

        page_width = page.rect.width

        blocks = page.get_text("blocks")  
        blocks = sorted(blocks, key=lambda b: b[1])  

        for q in questions:
            if "bbox" in q:
                continue

            q_text_clean = " ".join(q["text"][:50].split())  
            matched_blocks = []

            for block in blocks:
                _, y0, _, y1, text, _, _ = block
                text_clean = " ".join(text.split())

                if q_text_clean.startswith(text_clean) or text_clean in q_text_clean:
                    matched_blocks.append((y0, y1))

            if matched_blocks:
                y0s, y1s = zip(*matched_blocks)
                q["bbox"] = (0, min(y0s), page_width, max(y1s))
                q["page_number"] = page_num

    return questions

# Helper functions
def extract_year(filename):
    match = re.search(r"\d{4}", filename)
    return int(match.group()) if match else None

def infer_difficulty(marks):
    if marks is None: total_marks = 0
    elif isinstance(marks, list): total_marks = sum(marks)
    else: total_marks = marks

    if total_marks <= 2: return "Easy"
    elif total_marks <= 5: return "Medium"
    else: return "Hard"

TOPIC_KEYWORDS = {
    "Sets": ["set", "union", "intersection", "subset", "superset", "cardinality", "Venn diagram", "∈"],
    "Logic & Propositional Logic": ["logic", "proposition", "logical", "truth table", "implication", "conjunction", "disjunction", "negation", 
        "tautology", "contradiction", "truth value"],
    "Relations & Functions": ["relation", "function", "domain", "codomain", "injective", "surjective", "bijective", "composition", "inverse"],
    "Graph Theory": ["vertices", "graph", "vertex", "edge", "adjacency", "degree", "path", "cycle", "tree", "connected", "bipartite", "planar"],
    "Number Theory": ["prime", "gcd", "lcm", "modulo", "congruence", "divisibility", "integer"],
    "Algorithms & Complexity": ["algorithm", "complexity", "big O", "time complexity", "space complexity", "sub-string", "string", "sequence"],
    "Boolean Algebra": ["boolean", "xor", "minterm", "maxterm", "truth table"],
    "Probability": ["probability", "random", "event", "outcome", "sample space", "conditional probability"],
    "Combinatorics": ["binomial", "expansion", "coefficient", "factorial", "permutation", "combination", "derangement"],
    "Algebra": ["partial fractions", "expand and simplify", "series", "progression"],
    "Code" : ["python", "code"]
}

def infer_topic(text):
    text_lower = text.lower()
    matched_topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword.lower() in text_lower for keyword in keywords):
            matched_topics.append(topic)

    if not matched_topics:
        matched_topics = ["Other"] 

    return matched_topics



def parse_all_pdfs(folder_path="assets/exam_papers", output_json="data/questions.json"):
    all_questions = []

    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf") and not file.upper().endswith("MS.PDF"):
            pdf_path = os.path.join(folder_path, file)
            #all_questions.extend(extract_questions_from_pdf(pdf_path))
            questions = extract_questions_from_pdf(pdf_path)
            questions_with_bounds = assign_bounds_to_questions(pdf_path, questions)
            all_questions.extend(questions_with_bounds)

    os.makedirs(os.path.dirname(output_json), exist_ok=True)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2)

    print(f"Parsed {len(all_questions)} question parts.")
    print(f"Saved to {output_json}")

if __name__ == "__main__":
    parse_all_pdfs()