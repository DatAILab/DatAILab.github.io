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
    if not firebase_admin._apps:
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

def initialize_timer():
    if 'start_time' not in st.session_state:
        st.session_state.start_time = datetime.now()
        st.session_state.end_time = st.session_state.start_time + timedelta(minutes=60)

def display_timer():
    current_time = datetime.now()
    remaining_time = st.session_state.end_time - current_time
    
    # Convert to total seconds for comparison
    total_seconds_remaining = remaining_time.total_seconds()
    
    if total_seconds_remaining <= 0:
        st.error("⏰ Le temps est écoulé!")
        return True
    
    # Calculate minutes and seconds
    minutes = int(total_seconds_remaining // 60)
    seconds = int(total_seconds_remaining % 60)
    
    # Display timer with appropriate color based on remaining time
    if minutes >= 10:
        st.success(f"⏳ Temps restant: {minutes:02d}:{seconds:02d}")
    elif minutes >= 5:
        st.warning(f"⏳ Temps restant: {minutes:02d}:{seconds:02d}")
    else:
        st.error(f"⏳ Temps restant: {minutes:02d}:{seconds:02d}")
    
    # Return False if time hasn't expired
    return False

def main():
    # CSS personnalisé pour la minimisation de la barre latérale et le bouton retour en haut
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
        
        /* Style pour le bouton retour en haut */
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

    # Initialize Firebase
    initialize_firebase()
    
    # Initialize timer when starting a new quiz
    initialize_timer()
    
    # Create a placeholder for the timer at the top of the page
    timer_placeholder = st.empty()
    
    # Update and display the timer
    time_expired = display_timer()
    
    # If time has expired, show message and option to restart
    if time_expired:
        if st.button("Recommencer le quiz"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
        return

    # Rest of your existing quiz logic
    questions = fetch_all_questions()

    if 'sampled_questions' not in st.session_state:
        prepare_data_questions = [q for q in questions if q.get("Category") == "Prepare the data"]
        model_data_questions = [q for q in questions if q.get("Category") == "Model the data"]
        pbi_service_questions = [q for q in questions if q.get("Category") == "PBI Service"]
        visualization_questions = [q for q in questions if q.get("Category") == "Visualization"]

        prepare_data_questions = random.sample(prepare_data_questions, 12)
        model_data_questions = random.sample(model_data_questions, 10)
        visualization_questions = random.sample(visualization_questions, 12)
        pbi_service_questions = random.sample(pbi_service_questions, 6)

        st.session_state.sampled_questions = prepare_data_questions + model_data_questions + visualization_questions + pbi_service_questions

    questions = st.session_state.sampled_questions

    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: [] for q in questions}

    # Your existing question display and answer logic...
    for index, question in enumerate(questions, start=1):
        st.write(f"**Question {index}:** {question['question_text']}")
        
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

        choices = question.get("Choices", "").split(",")
        correct_answers = question.get("answer_text", "").split(",")

        if len(correct_answers) == 1:
            selected_answer = st.radio("Choisissez votre réponse:", choices, key=f"radio_{index}")
            if selected_answer:
                st.session_state.user_answers[question["question_text"]] = [selected_answer]
        elif len(correct_answers) > 1:
            selected_answers = []
            for choice in choices:
                unique_key = f"checkbox_{index}_{choice.strip()}"
                if st.checkbox(choice.strip(), key=unique_key):
                    selected_answers.append(choice.strip())
            st.session_state.user_answers[question["question_text"]] = selected_answers

    # Submit button and results display
    if st.button("Soumettre") or time_expired:
        # Your existing submission logic...
        correct_count = 0
        category_correct_count = {
            "Prepare the data": 0,
            "Model the data": 0,
            "PBI Service": 0,
            "Visualization": 0
        }

        correct_container = st.container()
        incorrect_container = st.container()
        
        with correct_container:
            st.markdown("### ✅ Questions correctes:")
        
        with incorrect_container:
            st.markdown("### ❌ Questions incorrectes:")

        for idx, question in enumerate(questions, 1):
            correct_answers = question.get("answer_text", "").split(",")
            user_answer = st.session_state.user_answers[question["question_text"]]

            if isinstance(user_answer, list):
                if set(user_answer) == set(correct_answers):
                    correct_count += 1
                    category_correct_count[question["Category"]] += 1
                    with correct_container:
                        st.success(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {', '.join(user_answer)}")
                else:
                    with incorrect_container:
                        st.error(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {', '.join(user_answer)}\n\n**Réponse(s) correcte(s) :** {', '.join(correct_answers)}")
            else:
                if user_answer in correct_answers:
                    correct_count += 1
                    category_correct_count[question["Category"]] += 1
                    with correct_container:
                        st.success(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {user_answer}")
                else:
                    with incorrect_container:
                        st.error(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {user_answer}\n\n**Réponse(s) correcte(s) :** {', '.join(correct_answers)}")

        total_questions = len(questions)
        correct_percentage = (correct_count / total_questions) * 100

        st.markdown("---")
        st.markdown(f"**Vous avez obtenu {correct_count} sur {total_questions} questions correctes ({correct_percentage:.2f}%)!**")

        if correct_percentage >= 70:
            st.success("Félicitations ! Vous avez réussi le quiz ! 🎉")
        else:
            st.error("Malheureusement, vous n'avez pas réussi le quiz. Vous aurez plus de chance la prochaine fois !")

        # Your existing visualization code...
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

        # Display category-wise results
        st.markdown(f"**Dans la catégorie « Préparer les données », vous avez obtenu {category_correct_count['Prepare the data']} questions correctes sur 12.**")
        st.markdown(f"**Dans la catégorie « Modéliser les données », vous avez obtenu {category_correct_count['Model the data']} questions correctes sur 10.**")
        st.markdown(f"**Dans la catégorie « Power BI Service», vous avez obtenu {category_correct_count['PBI Service']} questions correctes sur 6.**")
        st.markdown(f"**Dans la catégorie « Visualisation », vous avez obtenu {category_correct_count['Visualization']} questions correctes sur 12.**")

        # Create histogram
        categories = list(category_correct_count.keys())
        correct_values = list(category_correct_count.values())

        fig, ax = plt.subplots()
        ax.bar(categories, correct_values, color='skyblue')
        ax.set_xlabel('Catégorie')
        ax.set_ylabel('Réponses correctes')
        ax.set_title('Réponses correctes par catégorie')
        ax.set_yticks(np.arange(0, max(correct_values) + 1, 1))

        st.pyplot(fig)

        # Restart button
        if st.button("Recommencer"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

if __name__ == "__main__":
    main()