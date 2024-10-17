import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import random

# Initialisation de Firebase (en dehors des composants Streamlit)
def initialize_firebase():
    if not firebase_admin._apps:  # Check if any Firebase app is already initialized
        print("Initializing Firebase...")
        cred = credentials.Certificate({
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"]
        })
        firebase_admin.initialize_app(cred)
    else:
        print("Firebase est déjà initialisé.")

def fetch_questions_by_category(category, limit):
    try:
        db = firestore.client()
        questions_ref = db.collection("questions").where("category", "==", category)
        query_snapshot = questions_ref.limit(limit).get()

        questions = []
        for doc in query_snapshot:
            questions.append(doc.to_dict())

        return questions
    except Exception as e:
        st.error(f"Erreur lors de la récupération des questions : {e}")
        return []

def main():
    # Initialiser Firebase
    initialize_firebase()

    st.title("Quiz Certification PL-300")

    # Récupérer les questions
    prepare_data_questions = fetch_questions_by_category("Prepare the data", 3)
    model_data_questions = fetch_questions_by_category("Model the data", 5)
    questions = prepare_data_questions + model_data_questions

    # Stocker les réponses de l'utilisateur dans l'état de session
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: None for q in questions}

    # Afficher toutes les questions avec des boutons radio
    for question in questions:
        st.write("**Question:**", question["question_text"])
        
        # Prepare choices from the comma-separated string
        choices = question.get("Choices", "").split(",")  # Split the string into a list

        if choices:  # Afficher uniquement s'il y a des choix
            selected_answer = st.radio("Choisissez votre réponse:", choices, key=question["question_text"])  
            # Stocker la réponse sélectionnée par l'utilisateur
            st.session_state.user_answers[question["question_text"]] = selected_answer
        else:
            st.warning(f"Aucun choix disponible pour la question : {question['question_text']}")

    # Bouton « Soumettre » pour vérifier les réponses
    if st.button("Soumettre"):
        correct_count = 0
        category_correct_count = {"Prepare the data": 0, "Model the data": 0}

        for question in questions:
            correct_answers = question.get("answer_text", "").split(",")  # Split correct answers
            user_answer = st.session_state.user_answers[question["question_text"]]
            if user_answer in correct_answers:
                correct_count += 1
                category_correct_count[question["category"]] += 1
                st.success(f"**{question['question_text']}** - Correct! Your answer is: {user_answer}", icon="✅")
            else:
                st.error(f"**{question['question_text']}** - Incorrect! Your answer was: {user_answer}. Correct answer(s): {', '.join(correct_answers)}", icon="❌")

        st.markdown(f"**Tu as eu {correct_count} sur {len(questions)} questions correctes!**")
        st.markdown(f"**Dans la catégorie 'Prepare the data', tu as eu {category_correct_count['Prepare the data']} questions correctes.**")
        st.markdown(f"**Dans la catégorie 'Model the data', tu as eu {category_correct_count['Model the data']} questions correctes.**")

if __name__ == "__main__":
    main()