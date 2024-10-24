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

    # Fetch all questions
    questions = fetch_all_questions()

    # Check if questions are already sampled and stored in session state
    if 'sampled_questions' not in st.session_state:
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
        st.session_state.sampled_questions = prepare_data_questions + model_data_questions + visualization_questions + pbi_service_questions

    questions = st.session_state.sampled_questions

    # Store user answers in session state
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: [] for q in questions}

    # Display questions with appropriate input types
    for index, question in enumerate(questions, start=1):
        st.write(f"**Question {index}:** {question['question_text']}")
        
        # Check if 'image_url' exists and handle multiple images
        if 'image_url' in question and question['image_url']:
            # Split the image_url string into individual URLs
            image_urls = [url.strip() for url in question['image_url'].split(',')]
            
            # Create columns for multiple images if needed
            if len(image_urls) > 1:
                cols = st.columns(len(image_urls))
                for idx, url in enumerate(image_urls):
                    if url:  # Check if URL is not empty
                        try:
                            cols[idx].image(url, caption=f'Image {idx + 1}', use_column_width=True)
                        except Exception as e:
                            cols[idx].error(f"Error loading image {idx + 1}: {e}")
            else:  # Single image
                try:
                    st.image(image_urls[0], caption='Question Image', use_column_width=True)
                except Exception as e:
                    st.error(f"Error loading image: {e}")

        # Prepare choices from the comma-separated string
        choices = question.get("Choices", "").split(",")  # Split the string into a list
        correct_answers = question.get("answer_text", "").split(",")  # Split correct answers

        if len(correct_answers) == 1:  # Single correct answer
            selected_answer = st.radio("Choose your answer:", choices, key=f"radio_{index}")  
            if selected_answer:
                st.session_state.user_answers[question["question_text"]] = [selected_answer]
        elif len(correct_answers) > 1:  # Multiple correct answers
            selected_answers = []
            for choice in choices:
                # Create a unique key for each checkbox
                unique_key = f"checkbox_{index}_{choice.strip()}"
                if st.checkbox(choice.strip(), key=unique_key):
                    selected_answers.append(choice.strip())
            st.session_state.user_answers[question["question_text"]] = selected_answers

    # Submit button to check answers
    if st.button("Soumettre"):
        correct_count = 0
        category_correct_count = {
            "Prepare the data": 0,
            "Model the data": 0,
            "PBI Service": 0,
            "Visualization": 0
        }

        for question in questions:
            correct_answers = question.get("answer_text", "").split(",")  # Split correct answers
            user_answer = st.session_state.user_answers[question["question_text"]]

            # Check if the user's answer is correct
            if isinstance(user_answer, list):  # If multiple answers were selected
                if set(user_answer) == set(correct_answers):
                    correct_count += 1
                    category_correct_count[question["Category"]] += 1
                    st.success(f"**{question['question_text']}** - C'est exact ! Votre réponse est : {', '.join(user_answer)}", icon="✅")
                else:
                    st.error(f"**{question['question_text']}** - C'est faux ! Votre réponse est: {', '.join(user_answer)}. Réponse(s) correcte(s): {', '.join(correct_answers)}", icon="❌")
            else:  # Single answer
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
        ax.set_yticks(np.arange(0, max(correct_values) + 1, 1))

        st.pyplot(fig)

if __name__ == "__main__":
    main()