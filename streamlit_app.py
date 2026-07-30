import streamlit as st

from src.services.quiz_service import build_quiz

st.set_page_config(page_title="Générateur de Quiz PDF", page_icon="📝")
st.title("📝 Générateur automatique de quiz à partir d'un PDF")

st.write(
    "Dépose un document PDF (cours, article, rapport...) et obtiens "
    "automatiquement un quiz à choix multiples généré à partir de son contenu."
)

uploaded_file = st.file_uploader("Choisis un fichier PDF", type=["pdf"])
n_questions = st.slider("Nombre de questions souhaitées", min_value=3, max_value=15, value=8)

if uploaded_file is not None:
    with open("temp_uploaded.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("Analyse du document et génération des questions..."):
        try:
            quiz = build_quiz("temp_uploaded.pdf", n_questions=n_questions)
        except ValueError as e:
            st.error(str(e))
            quiz = None

    if quiz:
        st.success(f"{quiz['num_questions']} questions générées (langue détectée : {quiz['language']})")

        score = 0
        user_answers = []

        for i, item in enumerate(quiz["questions"], start=1):
            st.subheader(f"Question {i}")
            st.write(item["question"])
            choice = st.radio(
                "Ta réponse :",
                item["choices"],
                key=f"q_{i}",
                index=None,
            )
            user_answers.append((choice, item["choices"][item["correct_index"]]))

        if st.button("Valider mes réponses"):
            score = sum(1 for user, correct in user_answers if user == correct)
            st.info(f"Score : {score} / {len(user_answers)}")