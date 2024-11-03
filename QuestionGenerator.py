import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import plotly.graph_objects as go
import random
from datetime import timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Quiz PL-300",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Firebase initialization function
@st.cache_resource
def initialize_firebase():
    """Initialize Firebase with credentials from Streamlit secrets."""
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_all_questions():
    """Fetch all questions from Firestore database."""
    db = firestore.client()
    questions_ref = db.collection("questions")
    query_snapshot = questions_ref.get()
    questions = [doc.to_dict() for doc in query_snapshot]
    
    if not questions:
        st.warning("Aucune question trouvée dans la base de données.")
    
    return questions

def format_time(seconds):
    """Format seconds into HH:MM:SS string."""
    return str(timedelta(seconds=seconds)).split('.')[0]

def initialize_timer():
    """Initialize the quiz timer in session state."""
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
        st.session_state.duration = 60 * 60  # 60 minutes

def display_timer():
    """Display and manage the quiz timer."""
    current_time = time.time()
    elapsed_time = int(current_time - st.session_state.start_time)
    remaining_time = max(st.session_state.duration - elapsed_time, 0)
    
    time_str = format_time(remaining_time)
    progress = 1 - (remaining_time / st.session_state.duration)

    col1, col2 = st.columns([3, 1])
    
    with col2:
        if remaining_time <= 300:
            st.error(f"⏰ {time_str}")
        elif remaining_time <= 600:
            st.warning(f"⏰ {time_str}")
        else:
            st.info(f"⏰ {time_str}")

    with col1:
        st.progress(progress, "Temps écoulé")
    
    return remaining_time <= 0

def calculate_results(questions, user_answers):
    """Calculate quiz results and display correct/incorrect answers."""
    correct_count = 0
    category_correct_count = {
        "Prepare the data": 0,
        "Model the data": 0,
        "PBI Service": 0,
        "Visualization": 0
    }

    with st.expander("Voir les réponses détaillées", expanded=True):
        correct_container = st.container()
        incorrect_container = st.container()

        with correct_container:
            st.markdown("### ✅ Questions correctes:")
        
        with incorrect_container:
            st.markdown("### ❌ Questions incorrectes:")

        for idx, question in enumerate(questions, 1):
            correct_answers = [ans.strip() for ans in question.get("answer_text", "").split(",")]
            user_answer = user_answers.get(question["question_text"], [])
            is_correct = set(user_answer) == set(correct_answers)

            if is_correct:
                correct_count += 1
                category_correct_count[question["Category"]] += 1
                
                with correct_container:
                    st.success(f""" **Question {idx}:** {question['question_text']} **Votre réponse :** {', '.join(user_answer)} """)
            else:
                with incorrect_container:
                    st.error(f""" **Question {idx}:** {question['question_text']} **Votre réponse :** {', '.join(user_answer)} **Réponse(s) correcte(s) :** {', '.join(correct_answers)} """)
    
    return correct_count, category_correct_count

def display_results(correct_count, category_correct_count, total_questions):
    """Display quiz results with visualizations."""
    correct_percentage = (correct_count / total_questions) * 100
    
    st.markdown("---")
    st.markdown(
        f"<h2 style='text-align: center;'>Résultats du Quiz</h2>",
        unsafe_allow_html=True
    )

    # Main score display
    col1, col2 = st.columns(2)
    
    with col1:
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=correct_percentage,
            title={'text': "Score Total"},
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
        
        st.plotly_chart(gauge_fig)

    with col2:
        if correct_percentage >= 70:
            st.success(f""" # 🎉 Félicitations ! Vous avez réussi avec {correct_percentage:.1f}% de bonnes réponses ({correct_count}/{total_questions} questions) """)
        else:
            st.error(f""" # Continuez vos efforts Vous avez obtenu {correct_percentage:.1f}% de bonnes réponses ({correct_count}/{total_questions} questions) """)

def main():
    """Main application function."""
    
    initialize_firebase()
    
    # Initialize timer
    initialize_timer()

    # Fetch questions from Firestore
    questions = fetch_all_questions()

    # Check if sampled questions are already stored in session state
    if 'sampled_questions' not in st.session_state:
        # Sample questions from categories
        prepare_data_questions = random.sample([q for q in questions if q.get("Category") == "Prepare the data"], min(len(questions),12))
        model_data_questions = random.sample([q for q in questions if q.get("Category") == "Model the data"], min(len(questions),10))
        visualization_questions = random.sample([q for q in questions if q.get("Category") == "Visualization"], min(len(questions),12))
        pbi_service_questions = random.sample([q for q in questions if q.get("Category") == "PBI Service"], min(len(questions),6))

        # Combine sampled questions into session state
        st.session_state.sampled_questions = prepare_data_questions + model_data_questions + visualization_questions + pbi_service_questions

    # Store user answers in session state
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}

    # Display timer and check if time is up
    time_is_up = display_timer()

    if time_is_up and 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = True

    # Display questions if quiz not submitted 
    if not st.session_state.get('quiz_submitted', False):
        for index, question in enumerate(st.session_state.sampled_questions, start=1):
            st.write(f"**Question {index}:** {question['question_text']}")
            
            choices = question.get("Choices", "").split(",")
            
            if len(question.get("answer_text", "").split(",")) == 1: 
                selected_answer = st.radio("Choisissez votre réponse:", choices, key=f"radio_{index}")
                if selected_answer:
                    st.session_state.user_answers[question["question_text"]] = [selected_answer]
            else: 
                selected_answers = []
                for choice in choices:
                    unique_key = f"checkbox_{index}_{choice.strip()}"
                    if st.checkbox(choice.strip(), key=unique_key):
                        selected_answers.append(choice.strip())
                st.session_state.user_answers[question["question_text"]] = selected_answers

        # Submit button to check answers
        if st.button("Soumettre"):
            correct_count, category_correct_count = calculate_results(st.session_state.sampled_questions, st.session_state.user_answers)
            
            display_results(correct_count, category_correct_count, len(st.session_state.sampled_questions))

if __name__ == "__main__":
    main()