import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random
import time
from datetime import datetime, timedelta

# Initialisation de Firebase
def initialize_firebase():
    if not firebase_admin._apps:  # Vérifie si une application Firebase est déjà initialisée
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

# Récupération de toutes les questions
def fetch_all_questions():
    try:
        db = firestore.client()
        questions_ref = db.collection("questions")
        query_snapshot = questions_ref.get()

        questions = []
        for doc in query_snapshot:
            question_data = doc.to_dict()
            questions.append(question_data)

        if not questions:
            st.warning("Aucune question trouvée dans la base de données.")

        return questions
    except Exception as e:
        st.error(f"Erreur lors de la récupération des questions: {e}")
        return []

def format_time(seconds):
    return str(timedelta(seconds=seconds)).split('.')[0]

def initialize_timer():
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
        st.session_state.duration = 60 * 60  # 60 minutes in seconds

def display_timer():
    current_time = time.time()
    elapsed_time = int(current_time - st.session_state.start_time)
    remaining_time = max(st.session_state.duration - elapsed_time, 0)
    
    # Format remaining time
    time_str = format_time(remaining_time)
    
    # Create a progress bar for the timer
    progress = 1 - (remaining_time / st.session_state.duration)
    
    # Display timer with different colors based on remaining time
    if remaining_time <= 300:  # Last 5 minutes
        st.error(f"⏰ Temps restant: {time_str}")
        st.progress(progress, "Temps écoulé")
    elif remaining_time <= 600:  # Last 10 minutes
        st.warning(f"⏰ Temps restant: {time_str}")
        st.progress(progress, "Temps écoulé")
    else:
        st.info(f"⏰ Temps restant: {time_str}")
        st.progress(progress, "Temps écoulé")
    
    return remaining_time <= 0

def calculate_results(questions, user_answers):
    correct_count = 0
    category_correct_count = {
        "Prepare the data": 0,
        "Model the data": 0,
        "PBI Service": 0,
        "Visualization": 0
    }
    
    # Création des conteneurs pour les réponses correctes et incorrectes
    correct_container = st.container()
    incorrect_container = st.container()
    
    with correct_container:
        st.markdown("### ✅ Questions correctes:")
    
    with incorrect_container:
        st.markdown("### ❌ Questions incorrectes:")

    for idx, question in enumerate(questions, 1):
        correct_answers = question.get("answer_text", "").split(",")
        user_answer = user_answers[question["question_text"]]

        # Vérification si la réponse de l'utilisateur est correcte
        is_correct = False
        if isinstance(user_answer, list):  # Pour les réponses multiples
            is_correct = set(user_answer) == set(answer.strip() for answer in correct_answers)
            if is_correct:
                correct_count += 1
                category_correct_count[question["Category"]] += 1
                with correct_container:
                    st.success(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {', '.join(user_answer)}")
            else:
                with incorrect_container:
                    st.error(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {', '.join(user_answer)}\n\n**Réponse(s) correcte(s) :** {', '.join(correct_answers)}")
        
    return correct_count, category_correct_count

def display_results(correct_count, category_correct_count, total_questions):
    correct_percentage = (correct_count / total_questions) * 100

    st.markdown("---")
    st.markdown(f"**Vous avez obtenu {correct_count} sur {total_questions} questions correctes ({correct_percentage:.2f}%)!**")

    # Message de félicitations basé sur la performance
    if correct_percentage >= 70:
        st.success("Félicitations ! Vous avez réussi le quiz ! 🎉")
    else:
        st.error("Malheureusement, vous n'avez pas réussi le quiz. Vous aurez plus de chance la prochaine fois !")

    # Création du graphique de jauge
    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=correct_percentage,
        title={'text': "Pourcentage de réponses correctes"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "white"},
            'steps': [
                {'range': [0, 69], 'color': "red"},
                {'range': [70, 100], 'color': "lightgreen"},
            ],
            'threshold': {
                'line': {'color': "blue", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    gauge_fig.add_annotation(
        x=0.5,
        y=0.5,
        text="Objectif: 70",
        showarrow=False,
        font=dict(size=16, color="blue"),
        bgcolor="white",
        bordercolor="blue",
        borderwidth=2,
        borderpad=4,
        opacity=0.8
    )

    st.plotly_chart(gauge_fig)

    # Affichage des résultats par catégorie
    st.markdown(f"**Dans la catégorie « Préparer les données », vous avez obtenu {category_correct_count['Prepare the data']} questions correctes sur 12.**")
    st.markdown(f"**Dans la catégorie « Modéliser les données », vous avez obtenu {category_correct_count['Model the data']} questions correctes sur 10.**")
    st.markdown(f"**Dans la catégorie « Power BI Service», vous avez obtenu {category_correct_count['PBI Service']} questions correctes sur 6.**")
    st.markdown(f"**Dans la catégorie « Visualisation », vous avez obtenu {category_correct_count['Visualization']} questions correctes sur 12.**")

    # Création de l'histogramme
    categories = list(category_correct_count.keys())
    correct_values = list(category_correct_count.values())

    fig, ax = plt.subplots()
    ax.bar(categories, correct_values, color='skyblue')
    ax.set_xlabel('Catégorie')
    ax.set_ylabel('Réponses correctes')
    ax.set_title('Réponses correctes par catégorie')
    ax.set_yticks(np.arange(0, max(correct_values) + 1, 1))
    plt.xticks(rotation=45)

    st.pyplot(fig)

def main():
    # CSS personnalisé
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 1px;
            max-width: 200px;
        }
        [data-testid="stSidebar"][aria-expanded="false"] {
            margin-left: -1px;
        }
        
        .back-to-top {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background-color: #0E1117;
            color: white;
            padding: 10px 15px;
            border-radius: 50%;
            text-decoration: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
            transition: background-color 0.3s;
        }
        .back-to-top:hover {
            background-color: #262730;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    st.markdown(
        '''
        <a href="#top" class="back-to-top">
            ⬆️
        </a>
        ''',
        unsafe_allow_html=True
    )

    st.title("Quiz Certification PL-300")

    # Initialize timer
    initialize_timer()
    
    # Display timer at the top of the page
    time_is_up = display_timer()

    # Initialisation de Firebase
    initialize_firebase()

    # Récupération de toutes les questions
    all_questions = fetch_all_questions()

    # Initialisation des questions échantillonnées
    if 'sampled_questions' not in st.session_state:
        # Filtrage des questions par catégorie
        prepare_data_questions = [q for q in all_questions if q.get("Category") == "Prepare the data"]
        model_data_questions = [q for q in all_questions if q.get("Category") == "Model the data"]
        pbi_service_questions = [q for q in all_questions if q.get("Category") == "PBI Service"]
        visualization_questions = [q for q in all_questions if q.get("Category") == "Visualization"]

        # Échantillonnage aléatoire
        st.session_state.sampled_questions = (
            random.sample(prepare_data_questions, 12) +
            random.sample(model_data_questions, 10) +
            random.sample(visualization_questions, 12) +
            random.sample(pbi_service_questions, 6)
        )

    questions = st.session_state.sampled_questions

    # Initialisation des réponses utilisateur
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: [] for q in questions}

    # Vérification du temps écoulé
    if time_is_up and 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = True
        st.error("⏰ Le temps est écoulé ! Le quiz va être automatiquement soumis.")
        st.experimental_rerun()

    # Affichage des questions si le quiz n'est pas soumis
    if not st.session_state.get('quiz_submitted', False):
        for index, question in enumerate(questions, start=1):
            st.write(f"**Question {index}:** {question['question_text']}")
            
            # Gestion des images
            if 'image_url' in question and question['image_url']:
                image_urls = [url.strip() for url in question['image_url'].split(',')]
                
                if len(image_urls) > 1:
                    cols = st.columns(len(image_urls))
                    for idx, url in enumerate(image_urls):
                        if url:
                            try:
                                cols[idx].image(url, caption=f'Image {idx + 1}', use_column_width=True)
                            except Exception as e:
                                cols[idx].error(f"Erreur de chargement de l'image {idx + 1}: {e}")
                else:
                    try:
                        st.image(image_urls[0], caption='Image de la question', use_column_width=True)
                    except Exception as e:
                        st.error(f"Erreur de chargement de l'image: {e}")

            # Gestion des réponses
            choices = question.get("Choices", "").split(",")
            correct_answers = question.get("answer_text", "").split(",")

            if len(correct_answers) == 1:
                selected_answer = st.radio(
                    "Choisissez votre réponse:",
                    choices,
                    key=f"radio_{index}"
                )
                if selected_answer:
                    st.session_state.user_answers[question["question_text"]] = [selected_answer]
            else:
                selected_answers = []
                for choice in choices:
                    if st.checkbox(
                        choice.strip(),
                        key=f"checkbox_{index}_{choice.strip()}"
                    ):
                        selected_answers.append(choice.strip())
                st.session_state.user_answers[question["question_text"]] = selected_answers

    # Gestion de la soumission
    if st.button("Soumettre") or st.session_state.get('quiz_submitted', False):
        st.session_state.quiz_submitted = True
        
        # Calcul et affichage des résultats
        correct_count, category_correct_count = calculate_results(
            questions,
            st.session_state.user_answers
        )
        display_results(correct_count, category_correct_count, len(questions))

        # Bouton pour recommencer
        if st.button("Recommencer"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

if __name__ == "__main__":
    main()