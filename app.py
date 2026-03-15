# app.py
import streamlit as st
import fitz 
import pandas as pd
import json
from PIL import Image
import math

# Load parsed questions
with open("data/questions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

st.set_page_config(page_title="Exam Dashboard", layout="wide")
st.title("📚 Exam Question Dashboard")

# Sidebar Filters
st.sidebar.header("Filters")
years = ["All"] + sorted(df["year"].dropna().unique().astype(str).tolist())
topics = ["All"] + sorted({t for sublist in df["topic"].dropna() for t in sublist})
difficulties = ["All"] + sorted(df["difficulty"].dropna().unique().tolist())
marks_range = st.sidebar.slider("Marks range", 0, int(df["marks"].max()) if df["marks"].notna().any() else 10, (0, int(df["marks"].max()) if df["marks"].notna().any() else 10))

year_filter = st.sidebar.selectbox("Year", years)
topic_filter = st.sidebar.selectbox("Topic", topics)
difficulty_filter = st.sidebar.selectbox("Difficulty", difficulties)
search_text = st.sidebar.text_input("Search keyword")

# Apply filters
filtered = df

filtered = filtered[(filtered["marks"].fillna(0) >= marks_range[0]) & (filtered["marks"].fillna(0) <= marks_range[1])]

if year_filter != "All":
    filtered = filtered[filtered["year"] == int(year_filter)]

if topic_filter != "All":
    filtered = filtered[filtered["topic"].apply(lambda x: topic_filter in x)]

if difficulty_filter != "All":
    filtered = filtered[filtered["difficulty"] == difficulty_filter]

if search_text:
    filtered = filtered[filtered["text"].str.contains(search_text, case=False)]

st.write(f"Showing {len(filtered)} questions")

# Display questions with expandable cards
for _, row in filtered.iterrows():
    with st.expander(f"Q{row['question_number']} ({row['part']}) ({row['marks'] if row['marks'] else '?'} marks) - {row['source_pdf']}"):
        st.write(row["text"])
        st.caption(f"Topic: {row['topic']}, Difficulty: {row['difficulty']}")

def render_question_image(pdf_path, question, zoom=2):
    if "page_number" not in question or "bbox" not in question:
        return None
    if question["page_number"] is None or math.isnan(question["page_number"]):
        return None

    doc = fitz.open(pdf_path)
    page = doc[int(question["page_number"])]
    x0, y0, x1, y1 = question["bbox"]
    mat = fitz.Matrix(zoom, zoom)
    rect = fitz.Rect(x0, y0, x1, y1)
    pix = page.get_pixmap(matrix=mat, clip=rect)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


#for q in filtered.to_dict(orient="records"):
#    pdf_path = f"assets/exam_papers/{q['source_pdf']}"
#    if "bbox" in q:
#        img = render_question_image(pdf_path, q)
#        if img is not None:
#            st.image(img, caption=f"Q{q['question_number']} ({q['part']}) - {q['marks']} marks")
#    else:
#        st.write(q["text"])
#        st.caption(f"Topic: {q['topic']}, Difficulty: {q['difficulty']}")
