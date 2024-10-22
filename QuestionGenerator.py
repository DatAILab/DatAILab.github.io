import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random

# [Previous initialize_firebase and fetch_all_questions functions remain the same]

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

            # [Rest of the results visualization code remains the same]

            # Add a button to restart the quiz
            if st.button("Recommencer le quiz"):
                st.session_state.showing_results = False
                st.session_state.user_answers = {q["question_text"]: [] for q in questions}
                st.experimental_rerun()

if __name__ == "__main__":
    main()