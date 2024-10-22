import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random

# Initialize Firebase
def initialize_firebase():
    if not firebase_admin._apps:  # Check if any Firebase app is already initialized
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
        print("Firebase is already initialized.")

# Fetch all questions
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
            st.warning("No questions found in the database.")

        return questions
    except Exception as e:
        st.error(f"Error fetching questions: {e}")
        return []

def main():
    # Initialize Firebase
    initialize_firebase()

    st.title("Quiz Certification PL-300")

    # Add showing_results to session state if not present
    if 'showing_results' not in st.session_state:
        st.session_state.showing_results = False

    # Fetch all questions
    questions = fetch_all_questions()

    # Filter questions by category
    prepare_data_questions = [q for q in questions if q.get("Category") == "Prepare the data"]
    model_data_questions = [q for q in questions if q.get("Category") == "Model the data"]
    pbi_service_questions = [q for q in questions if q.get("Category") == "PBI Service"]
    visualization_questions = [q for q in questions if q.get("Category") == "Visualization"]

    # Randomly sample the required number of questions from each category
    prepare_data_questions = random.sample(prepare_data_questions, 12)
    model_data_questions = random.sample(model_data_questions, 10)
    visualization_questions = random.sample(visualization_questions, 12)
    pbi_service_questions = random.sample(pbi_service_questions, 6)

    # Combine questions
    questions = prepare_data_questions + model_data_questions + visualization_questions + pbi_service_questions

    # Store user answers in session state
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: [] for q in questions}

    # Create two containers: one for questions and one for results
    questions_container = st.container()
    results_container = st.container()

    # Show questions only if not showing results
    if not st.session_state.showing_results:
        with questions_container:
            for index, question in enumerate(questions, start=1):
                st.write(f"**Question {index}:** {question['question_text']}")
                
                # Check if there is an image URL and display it
                if 'image' in question and question['image']:
                    st.image(question['image'], caption='Question Image', use_column_width=True)

                # Prepare choices from the comma-separated string
                choices = question.get("Choices", "").split(",")
                correct_answers = question.get("answer_text", "").split(",")

                if len(correct_answers) == 1:  # Single correct answer
                    selected_answer = st.radio("Choose your answer:", choices, key=f"radio_{index}")
                    if selected_answer:
                        st.session_state.user_answers[question["question_text"]] = [selected_answer]
                elif len(correct_answers) > 1:  # Multiple correct answers
                    selected_answers = []
                    for choice in choices:
                        unique_key = f"checkbox_{index}_{choice.strip()}"
                        if st.checkbox(choice.strip(), key=unique_key):
                            selected_answers.append(choice.strip())
                    st.session_state.user_answers[question["question_text"]] = selected_answers

            if st.button("Soumettre"):
                st.session_state.showing_results = True
                st.experimental_rerun()

    # Show results if showing_results is True
    if st.session_state.showing_results:
        with results_container:
            correct_count = 0
            category_correct_count = {
                "Prepare the data": 0,
                "Model the data": 0,
                "PBI Service": 0,
                "Visualization": 0
            }

            for question in questions:
                correct_answers = question.get("answer_text", "").split(",")
                user_answer = st.session_state.user_answers[question["question_text"]]

                # Check if the user's answer is correct
                if isinstance(user_answer, list):
                    if set(user_answer) == set(correct_answers):
                        correct_count += 1
                        category_correct_count[question["Category"]] += 1
                        st.success(f"**{question['question_text']}** - C'est exact ! Votre réponse est : {', '.join(user_answer)}", icon="✅")
                    else:
                        st.error(f"**{question['question_text']}** - C'est faux ! Votre réponse est: {', '.join(user_answer)}. Réponse(s) correcte(s): {', '.join(correct_answers)}", icon="❌")
                else:
                    if user_answer in correct_answers:
                        correct_count += 1
                        category_correct_count[question["Category"]] += 1
                        st.success(f"**{question['question_text']}** - C'est exact ! Votre réponse est: {user_answer}", icon="✅")
                    else:
                        st.error(f"**{question['question_text']}** - C'est faux ! Votre réponse était: {user_answer}. Réponse(s) correcte(s): {', '.join(correct_answers)}", icon="❌")

            total_questions = len(questions)
            correct_percentage = (correct_count / total_questions) * 100

            st.markdown(f"**Vous avez obtenu {correct_count} sur {total_questions} questions correctes ({correct_percentage:.2f}%)!**")

            # Congratulatory message based on performance
            if correct_percentage >= 70:
                st.success("Félicitations ! Vous avez réussi le quiz ! 🎉")
            else:
                st.error("Malheureusement, vous n'avez pas réussi le quiz. Vous aurez plus de chance la prochaine fois !")

            # Create a gauge chart with a target value of 70
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
            # Add a target value label
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

            st.markdown(f"**Dans la catégorie « Préparer les données », vous avez obtenu {category_correct_count['Prepare the data']} questions correctes sur 12.**")
            st.markdown(f"**Dans la catégorie « Modéliser les données », vous avez obtenu {category_correct_count['Model the data']} questions correctes sur 10.**")
            st.markdown(f"**Dans la catégorie « Power BI Service», vous avez obtenu {category_correct_count['PBI Service']} questions correctes sur 6.**")
            st.markdown(f"**Dans la catégorie « Visualisation », vous avez obtenu {category_correct_count['Visualization']} questions correctes sur 12.**")

            # Plot a histogram
            categories = list(category_correct_count.keys())
            correct_values = list(category_correct_count.values())

            fig, ax = plt.subplots()
            ax.bar(categories, correct_values, color='skyblue')
            ax.set_xlabel('Catégorie')
            ax.set_ylabel('Réponses correctes')
            ax.set_title('Réponses correctes par catégorie')
            ax.set_yticks(np.arange(0, max(correct_values) + 1, 1))  # Set Y-axis ticks incrementing by 1

            plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
            plt.tight_layout()  # Adjust layout to prevent label cutoff
            
            st.pyplot(fig)

            # Add a button to restart the quiz
            if st.button("Recommencer le quiz"):
                st.session_state.showing_results = False
                st.session_state.user_answers = {q["question_text"]: [] for q in questions}
                st.experimental_rerun()

if __name__ == "__main__":
    main()