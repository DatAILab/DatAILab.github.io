import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Quiz PL-300",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
.stProgress > div > div > div > div { background-color: #1f77b4; }
.stProgress { margin-bottom: 20px; }
.st-emotion-cache-16idsys p { font-size: 20px; font-weight: bold; }
.quiz-header { text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 30px; }
.question-card { padding: 20px; background-color: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# Firebase initialization function
@st.cache_resource
def initialize_firebase():
    """Initialize Firebase with credentials from Streamlit secrets."""
    try:
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
            logger.info("Firebase initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        st.error(f"Error initializing Firebase: {e}")
        return False

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_all_questions():
    """Fetch all questions from Firestore database."""
    try:
        logger.info("Starting to fetch questions...")
        # Check if Firebase is initialized
        if not initialize_firebase():
            return []
        db = firestore.client()
        questions_ref = db.collection("questions")
        # Add timeout to the query
        query_snapshot = questions_ref.get(timeout=30)
        questions = []
        for doc in query_snapshot:
            question_data = doc.to_dict()
            questions.append(question_data)
        logger.info(f"Successfully fetched {len(questions)} questions")
        if not questions:
            st.warning("Aucune question trouvée dans la base de données.")
            logger.warning("No questions found in database")
        return questions
    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        st.error(f"Erreur lors de la récupération des questions: {e}")
        return []

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
        if remaining_time <= 300:  # Less than 5 minutes
            st.error(f"⏰ {time_str}")
        elif remaining_time <= 600:  # Less than 10 minutes
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

    # Category results
    st.markdown("### Résultats par catégorie")
    
    categories = {
        'Prepare the data': 12,
        'Model the data': 10,
        'PBI Service': 6,
        'Visualization': 12
    }
    
    for category, total in categories.items():
        score = category_correct_count[category]
        percentage = (score / total) * 100
        
        st.markdown(f""" #### {category} - Score: {score}/{total} ({percentage:.1f}%) """)
        
        st.progress(percentage / 100)

def main():
    """Main application function."""
    
    try:
        st.markdown("<h1 style='text-align: center;'>Quiz Certification PL-300</h1>", unsafe_allow_html=True)

        # Show loading message 
        with st.spinner('Chargement des questions...'):
            # Initialize Firebase and fetch questions
            questions = fetch_all_questions()
            
            if not questions:
                st.error("Impossible de charger les questions. Veuillez réessayer.")
                return
            
            # Initialize Firebase and timer
            initialize_firebase()
            initialize_timer()

            # Display timer 
            time_is_up = display_timer()

            # Get questions 
            all_questions = fetch_all_questions()

            # Sample questions if not already done 
            if 'sampled_questions' not in st.session_state:
                questions_by_category = {
                    "Prepare the data": [q for q in all_questions if q.get("Category") == "Prepare the data"],
                    "Model the data": [q for q in all_questions if q.get("Category") == "Model the data"],
                    "PBI Service": [q for q in all_questions if q.get("Category") == "PBI Service"],
                    "Visualization": [q for q in all_questions if q.get("Category") == "Visualization"]
                }

                st.session_state.sampled_questions = (
                    random.sample(questions_by_category["Prepare the data"], 12) +
                    random.sample(questions_by_category["Model the data"], 10) +
                    random.sample(questions_by_category["Visualization"], 12) +
                    random.sample(questions_by_category["PBI Service"], 6)
                )
                
                questions = st.session_state.sampled_questions

            # Initialize user answers 
            if 'user_answers' not in st.session_state:
                st.session_state.user_answers = {}

            # Check if time is up 
            if time_is_up and 'quiz_submitted' not in st.session_state:
                st.session_state.quiz_submitted = True
                st.experimental_rerun()

            # Display questions if quiz not submitted 
            if not st.session_state.get('quiz_submitted', False):
                for index, question in enumerate(questions, start=1):
                    with st.container():
                        st.markdown(f"""
                        <div class="question-card">
                            <h3>Question {index}</h3>
                            <p>{question['question_text']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Handle images 
                        if 'image_url' in question and question['image_url']:
                            image_urls = [url.strip() for url in question['image_url'].split(',')]
                            if len(image_urls) > 1:
                                cols = st.columns(len(image_urls))
                                for idx, url in enumerate(image_urls):
                                    if url:
                                        try:
                                            cols[idx].image(url, use_column_width=True)
                                        except Exception as e:
                                            cols[idx].error(f"Erreur de chargement de l'image {idx + 1}")
                            else:
                                try:
                                    st.image(image_urls[0], use_column_width=True)
                                except Exception as e:
                                    st.error("Erreur de chargement de l'image")

                        # Handle answers 
                        choices = [choice.strip() for choice in question.get("Choices", "").split(",")]
                        correct_answers = question.get("answer_text", "").split(",")

                        if len(correct_answers) == 1:
                            answer = st.radio(
                                "Sélectionnez votre réponse:",
                                choices,
                                key=f"radio_{index}"
                            )
                            if answer:
                                st.session_state.user_answers[question["question_text"]] = [answer]
                        else:
                            selected = st.multiselect(
                                "Sélectionnez toutes les réponses appropriées:",
                                choices,
                                key=f"multiselect_{index}"
                            )
                            st.session_state.user_answers[question["question_text"]] = selected

                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col2:
                        if st.button("📝 Soumettre le Quiz", use_container_width=True):
                            st.session_state.quiz_submitted = True
                            st.experimental_rerun()

            # Handle submission 
            if st.session_state.get('quiz_submitted', False):
                correct_count, category_correct_count = calculate_results(
                    questions,
                    st.session_state.user_answers
                )
                
                display_results(correct_count, category_correct_count, len(questions))

                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    if st.button("🔄 Recommencer le Quiz", use_container_width=True):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.experimental_rerun()

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        st.error(f"Une erreur est survenue: {e}")

if __name__ == "__main__":
    main()