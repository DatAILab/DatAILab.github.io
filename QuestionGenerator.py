import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random
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

def fetch_all_questions():
    try:
        db = firestore.client()
        questions_ref = db.collection("questions")
        query_snapshot = questions_ref.get()
        
        questions = []
        for doc in query_snapshot:
            question_data = doc.to_dict()
            questions.append(question_data)
            
        return questions
    except Exception as e:
        st.error(f"Erreur lors de la récupération des questions: {e}")
        return []

def init_session_state():
    if 'initialized' not in st.session_state or st.session_state.get('needs_reset', False):
        st.session_state.initialized = True
        st.session_state.quiz_version = int(time.time())
        st.session_state.submitted = False
        st.session_state.needs_reset = False
        
        # Fetch and sample questions
        all_questions = fetch_all_questions()
        
        # Filter questions by category
        prepare_data = [q for q in all_questions if q.get("Category") == "Prepare the data"]
        model_data = [q for q in all_questions if q.get("Category") == "Model the data"]
        pbi_service = [q for q in all_questions if q.get("Category") == "PBI Service"]
        visualization = [q for q in all_questions if q.get("Category") == "Visualization"]
        
        # Sample questions
        st.session_state.questions = (
            random.sample(prepare_data, 12) +
            random.sample(model_data, 10) +
            random.sample(visualization, 12) +
            random.sample(pbi_service, 6)
        )
        random.shuffle(st.session_state.questions)
        
        # Initialize answers
        st.session_state.user_answers = {q["question_text"]: [] for q in st.session_state.questions}

def reset_quiz():
    # Mark the quiz for reset instead of directly modifying session state
    st.session_state.needs_reset = True
    # Clear user answers
    st.session_state.user_answers = {}
    # Reset submission status
    st.session_state.submitted = False

def main():
    st.markdown("""
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
        """, unsafe_allow_html=True)

    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    st.markdown(
        '''<a href="#top" class="back-to-top">⬆️</a>''',
        unsafe_allow_html=True
    )

    st.title("Quiz Certification PL-300")

    # Initialize Firebase
    initialize_firebase()
    
    # Initialize or reset session state
    init_session_state()
    
    # Display questions
    for i, question in enumerate(st.session_state.questions, 1):
        st.write(f"**Question {i}:** {question['question_text']}")
        
        # Handle images
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

        # Handle answers
        choices = question.get("Choices", "").split(",")
        correct_answers = question.get("answer_text", "").split(",")
        
        unique_key = f"{question['question_text']}_{st.session_state.quiz_version}"
        
        if len(correct_answers) == 1:
            selected = st.radio(
                "Choisissez votre réponse:",
                choices,
                key=f"radio_{unique_key}"
            )
            if selected:
                st.session_state.user_answers[question["question_text"]] = [selected]
        else:
            selected = []
            for choice in choices:
                if st.checkbox(
                    choice.strip(),
                    key=f"checkbox_{choice}_{unique_key}"
                ):
                    selected.append(choice.strip())
            st.session_state.user_answers[question["question_text"]] = selected

    # Submit button
    if st.button("Soumettre", key=f"submit_{st.session_state.quiz_version}"):
        st.session_state.submitted = True
        
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

        for idx, question in enumerate(st.session_state.questions, 1):
            correct_answers = question.get("answer_text", "").split(",")
            user_answer = st.session_state.user_answers[question["question_text"]]
            
            if set(user_answer) == set(correct_answers):
                correct_count += 1
                category_correct_count[question["Category"]] += 1
                with correct_container:
                    st.success(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {', '.join(user_answer)}")
            else:
                with incorrect_container:
                    st.error(f"**Question {idx}:** {question['question_text']}\n\n**Votre réponse :** {', '.join(user_answer)}\n\n**Réponse(s) correcte(s) :** {', '.join(correct_answers)}")

        total_questions = len(st.session_state.questions)
        correct_percentage = (correct_count / total_questions) * 100

        st.markdown("---")
        st.markdown(f"**Vous avez obtenu {correct_count} sur {total_questions} questions correctes ({correct_percentage:.2f}%)!**")

        if correct_percentage >= 70:
            st.success("Félicitations ! Vous avez réussi le quiz ! 🎉")
        else:
            st.error("Malheureusement, vous n'avez pas réussi le quiz. Vous aurez plus de chance la prochaine fois !")

        # Gauge chart
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

        # Category results
        st.markdown(f"**Dans la catégorie « Préparer les données », vous avez obtenu {category_correct_count['Prepare the data']} questions correctes sur 12.**")
        st.markdown(f"**Dans la catégorie « Modéliser les données », vous avez obtenu {category_correct_count['Model the data']} questions correctes sur 10.**")
        st.markdown(f"**Dans la catégorie « Power BI Service», vous avez obtenu {category_correct_count['PBI Service']} questions correctes sur 6.**")
        st.markdown(f"**Dans la catégorie « Visualisation », vous avez obtenu {category_correct_count['Visualization']} questions correctes sur 12.**")

        # Bar chart
        fig, ax = plt.subplots()
        ax.bar(list(category_correct_count.keys()), list(category_correct_count.values()), color='skyblue')
        ax.set_xlabel('Catégorie')
        ax.set_ylabel('Réponses correctes')
        ax.set_title('Réponses correctes par catégorie')
        ax.set_yticks(np.arange(0, max(category_correct_count.values()) + 1, 1))
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)

        # Restart button
        if st.button("Reprendre", key=f"restart_{st.session_state.quiz_version}"):
            reset_quiz()
            st.experimental_rerun()

if __name__ == "__main__":
    main()