# parser/pdf_parser.py
import fitz  # PyMuPDF
import json
import os
import re

def extract_questions_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    questions = []

    year = extract_year(pdf_path)

    full_text = ""

    for page_num, page in enumerate(doc):

        text = page.get_text()

        # Remove continuation headers
        text = re.sub(r"continued\s+overleaf", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Question\s+\d+\s+continued\s+overleaf", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Question\s+\d+\s+continued", "", text, flags=re.IGNORECASE)

        # Remove total marks
        text = re.sub(r"\(Total\s+\d+\s+Marks\)", "", text, flags=re.IGNORECASE)

        full_text += f"\nPAGE_BREAK_{page_num}\n{text}"

    # Remove page markers and stray page numbers
    full_text = re.sub(r"PAGE_BREAK_\d+", "", full_text)
    full_text = re.sub(r"\n\s*\d+\s*\n", "\n", full_text)

    # Split by Question number
    question_blocks = re.split(r"Question\s+(\d+)", full_text)

    for i in range(1, len(question_blocks), 2):

        q_number = int(question_blocks[i])
        q_text = question_blocks[i + 1]

        parts = re.findall(
            r"\(([a-h])\)(.*?)(?=\(([a-h])\)|$)",
            q_text,
            flags=re.IGNORECASE | re.DOTALL
        )

        for part_letter, part_text, marks in parts:

            m = re.search(r"\((\d+)\s*marks?\)\s*$", part_text, flags=re.IGNORECASE | re.DOTALL)
            marks = int(m.group(1)) if m else None
            if m:
                part_text = part_text[:m.start()].strip()

            questions.append({
                "question_number": q_number,
                "part": part_letter.lower(),
                "text": part_text.strip(),
                "marks": marks,
                "source_pdf": os.path.basename(pdf_path),
                "year": year,
                "topic": infer_topic(part_text),
                "difficulty": infer_difficulty(marks)
            })

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
    "Sets": ["set", "union", "intersection", "subset", "superset", "cardinality", "Venn diagram"],
    "Logic & Propositional Logic": ["logic", "proposition", "logical", "truth table", "implication", "conjunction", "disjunction", "negation", "tautology", "contradiction"],
    "Relations & Functions": ["relation", "function", "domain", "codomain", "injective", "surjective", "bijective", "composition"],
    "Graph Theory": ["graph", "vertex", "edge", "adjacency", "degree", "path", "cycle", "tree", "connected", "bipartite", "planar"],
    "Number Theory": ["prime", "gcd", "lcm", "modulo", "congruence", "divisibility", "integer"],
    "Algorithms & Complexity": ["algorithm", "complexity", "big O", "time complexity", "space complexity"],
    "Boolean Algebra": ["boolean", "xor", "minterm", "maxterm", "truth table"],
    "Probability": ["probability", "random", "event", "outcome", "sample space", "conditional probability"],
    "Combinatorics": ["binomial", "expansion", "coefficient", "factorial", "permutation", "combination"]
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
            all_questions.extend(extract_questions_from_pdf(pdf_path))

    os.makedirs(os.path.dirname(output_json), exist_ok=True)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2)

    print(f"Parsed {len(all_questions)} question parts.")
    print(f"Saved to {output_json}")

if __name__ == "__main__":
    parse_all_pdfs()