# app.py
import streamlit as st
import pandas as pd
import json

# Load parsed questions
with open("data/questions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

st.set_page_config(page_title="Exam Dashboard", layout="wide")
st.title("📚 Exam Question Dashboard")

# Sidebar Filters
st.sidebar.header("Filters")
years = ["All"] + sorted(df["year"].dropna().unique().astype(str).tolist())
topics = ["All"] + sorted(df["topic"].dropna().unique().tolist())
difficulties = ["All"] + sorted(df["difficulty"].dropna().unique().tolist())
marks_range = st.sidebar.slider("Marks range", 0, int(df["marks"].max()) if df["marks"].notna().any() else 10, (0, int(df["marks"].max()) if df["marks"].notna().any() else 10))

year_filter = st.sidebar.selectbox("Year", years)
topic_filter = st.sidebar.selectbox("Topic", topics)
difficulty_filter = st.sidebar.selectbox("Difficulty", difficulties)
search_text = st.sidebar.text_input("Search keyword")

# Apply filters
filtered = df
if year_filter != "All":
    filtered = filtered[filtered["year"] == int(year_filter)]
if topic_filter != "All":
    filtered = filtered[filtered["topic"] == topic_filter]
if difficulty_filter != "All":
    filtered = filtered[filtered["difficulty"] == difficulty_filter]
filtered = filtered[(filtered["marks"].fillna(0) >= marks_range[0]) & (filtered["marks"].fillna(0) <= marks_range[1])]
if search_text:
    filtered = filtered[filtered["text"].str.contains(search_text, case=False)]

st.write(f"Showing {len(filtered)} questions")

# Display questions with expandable cards
for _, row in filtered.iterrows():
    with st.expander(f"Q{row['question_number']} ({row['part']}) ({row['marks'] if row['marks'] else '?'} marks) - {row['source_pdf']}"):
        st.write(row["text"])
        st.caption(f"Topic: {row['topic']}, Difficulty: {row['difficulty']}")