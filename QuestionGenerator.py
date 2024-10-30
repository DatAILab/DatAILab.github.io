import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta
import time

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
        st.session_state.last_update = datetime.now()

def format_time(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"

def display_timer():
    current_time = datetime.now()
    remaining_time = st.session_state.end_time - current_time
    total_seconds_remaining = remaining_time.total_seconds()
    
    # Auto-refresh logic
    if (current_time - st.session_state.last_update).total_seconds() >= 1:
        st.session_state.last_update = current_time
        time.sleep(0.1)  # Small delay to prevent excessive reruns
        st.rerun()
    
    if total_seconds_remaining <= 0:
        st.markdown("""
            <div class="fixed-timer" style="color: red;">
                ⏰ 00:00
            </div>
        """, unsafe_allow_html=True)
        return True
    
    time_str = format_time(total_seconds_remaining)
    color = "green" if total_seconds_remaining > 600 else "orange" if total_seconds_remaining > 300 else "red"
    
    st.markdown(f"""
        <div class="fixed-timer" style="color: {color};">
            ⏰ {time_str}
        </div>
    """, unsafe_allow_html=True)
    
    return False

def main():
    # CSS for fixed timer and other styling
    st.markdown("""
        <style>
        .fixed-timer {
            position: fixed;
            top: 10px;
            left: 10px;
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.8);
            border-radius: 5px;
            z-index: 9999;
        }
        
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

        .stButton button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    st.markdown("""
        <a href="#top" class="back-to-top">
            ⬆️
        </a>
    """, unsafe_allow_html=True)

    st.title("Quiz Certification PL-300")

    # Initialize Firebase and timer
    initialize_firebase()
    initialize_timer()
    
    # Display timer
    time_expired = display_timer()
    
    if time_expired:
        st.error("Le temps est écoulé! Veuillez soumettre vos réponses ou recommencer le quiz.")
        if st.button("Recommencer le quiz"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return

    # Fetch and prepare questions
    questions = fetch_all_questions()

    if 'sampled_questions' not in st.session_state:
        prepare_data_questions = [q for q in questions if q.get("Category") == "Prepare the data"]
        model_data_questions = [q for q in questions if q.get("Category") == "Model the data"]
        pbi_service_questions = [q for q in questions if q.get("Category") == "PBI Service"]
        visualization_questions = [q for q in questions if q.get("Category") == "Visualization"]

        # Only sample if we have enough questions in each category
        n_prepare = min(len(prepare_data_questions), 12)
        n_model = min(len(model_data_questions), 10)
        n_viz = min(len(visualization_questions), 12)
        n_service = min(len(pbi_service_questions), 6)

        prepare_data_questions = random.sample(prepare_data_questions, n_prepare)
        model_data_questions = random.sample(model_data_questions, n_model)
        visualization_questions = random.sample(visualization_questions, n_viz)
        pbi_service_questions = random.sample(pbi_service_questions, n_service)

        st.session_state.sampled_questions = prepare_data_questions + model_data_questions + visualization_questions + pbi_service_questions

    questions = st.session_state.sampled_questions

    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: [] for q in questions}

    # Display questions
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
        choices = [choice.strip() for choice in choices]  # Strip whitespace from choices
        correct_answers = question.get("answer_text", "").split(",")
        correct_answers = [answer.strip() for answer in correct_answers]  # Strip whitespace from answers

        if len(correct_answers) == 1:
            selected_answer = st.radio(
                "Choisissez votre réponse:",
                choices,
                key=f"radio_{index}",
                index=None
            )
            if selected_answer:
                st.session_state.user_answers[question["question_text"]] = [selected_answer]
        else:
            selected_answers = []
            for choice in choices:
                unique_key = f"checkbox_{index}_{choice}"
                if st.checkbox(choice, key=unique_key):
                    selected_answers.append(choice)
            st.session_state.user_answers[question["question_text"]] = selected_answers

    # Submit button and results
    if st.button("Soumettre") or time_expired:
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
            correct_answers = [ans.strip() for ans in question.get("answer_text", "").split(",")]
            user_answer = st.session_state.user_answers[question["question_text"]]
            
            if isinstance(user_answer, list):
                user_answer = [ans.strip() for ans in user_answer]
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

        # Calculate and display results
        total_questions = len(questions)
        correct_percentage = (correct_count / total_questions) * 100

        st.markdown("---")
        st.markdown(f"**Vous avez obtenu {correct_count} sur {total_questions} questions correctes ({correct_percentage:.2f}%)!**")

        if correct_percentage >= 70:
            st.success("Félicitations ! Vous avez réussi le quiz ! 🎉")
        else:
            st.error("Malheureusement, vous n'avez pas réussi le quiz. Vous aurez plus de chance la prochaine fois !")

        # Display gauge chart
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

        # Display category results
        category_targets = {
            "Prepare the data": 12,
            "Model the data": 10,
            "PBI Service": 6,
            "Visualization": 12
        }

        for category, target in category_targets.items():
            actual = category_correct_count[category]
            st.markdown(f"**Dans la catégorie « {category} », vous avez obtenu {actual} questions correctes sur {target}.**")

        # Create and display histogram
        categories = list(category_correct_count.keys())
        correct_values = list(category_correct_count.values())

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(categories, correct_values, color='skyblue')
        ax.set_xlabel('Catégorie')
        ax.set_ylabel('Réponses correctes')
        ax.set_title('Réponses correctes par catégorie')
        plt.xticks(rotation=45, ha='right')
        ax.set_yticks(np.arange(0, max(correct_values) + 1, 1))

        st.pyplot(fig)

        # Restart button
        if st.button("Recommencer"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()