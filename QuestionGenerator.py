import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random

# [Previous initialize_firebase and fetch_all_questions functions remain exactly the same]

def main():
    # Initialize Firebase
    initialize_firebase()

    st.title("Quiz Certification PL-300")

    # Add showing_results to session state if not present
    if 'showing_results' not in st.session_state:
        st.session_state.showing_results = False

    # [Previous question filtering and sampling code remains exactly the same]

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
                st.rerun()  # Changed from experimental_rerun() to rerun()

    # Show results if showing_results is True
    if st.session_state.showing_results:
        with results_container:
            # [Previous results display code remains exactly the same]

            # Add a button to restart the quiz
            if st.button("Recommencer le quiz"):
                st.session_state.showing_results = False
                st.session_state.user_answers = {q["question_text"]: [] for q in questions}
                st.rerun()  # Changed from experimental_rerun() to rerun()

if __name__ == "__main__":
    main()