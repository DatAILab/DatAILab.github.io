import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random

# [Previous functions remain the same until the main() function]

def main():
    # Initialize Firebase
    initialize_firebase()

    st.title("Quiz Certification PL-300")

    # Fetch all questions
    questions = fetch_all_questions()

    # [Previous session state handling and question display code remains the same until the submit button]

    # Submit button to check answers
    if st.button("Soumettre"):
        correct_count = 0
        category_correct_count = {
            "Prepare the data": 0,
            "Model the data": 0,
            "PBI Service": 0,
            "Visualization": 0
        }

        # Create containers for correct and incorrect answers
        correct_container = st.container()
        incorrect_container = st.container()
        
        with correct_container:
            st.markdown("### ✅ Questions correctes:")
        
        with incorrect_container:
            st.markdown("### ❌ Questions incorrectes:")

        for idx, question in enumerate(questions, 1):
            correct_answers = question.get("answer_text", "").split(",")
            user_answer = st.session_state.user_answers[question["question_text"]]

            # Check if the user's answer is correct
            if isinstance(user_answer, list):  # If multiple answers were selected
                if set(user_answer) == set(correct_answers):
                    correct_count += 1
                    category_correct_count[question["Category"]] += 1
                    with correct_container:
                        st.success(f"**Question {idx}:** {question['question_text']}\nVotre réponse : {', '.join(user_answer)}")
                else:
                    with incorrect_container:
                        st.error(f"**Question {idx}:** {question['question_text']}\nVotre réponse : {', '.join(user_answer)}\nRéponse(s) correcte(s) : {', '.join(correct_answers)}")
            else:  # Single answer
                if user_answer in correct_answers:
                    correct_count += 1
                    category_correct_count[question["Category"]] += 1
                    with correct_container:
                        st.success(f"**Question {idx}:** {question['question_text']}\nVotre réponse : {user_answer}")
                else:
                    with incorrect_container:
                        st.error(f"**Question {idx}:** {question['question_text']}\nVotre réponse : {user_answer}\nRéponse(s) correcte(s) : {', '.join(correct_answers)}")

        total_questions = len(questions)
        correct_percentage = (correct_count / total_questions) * 100

        st.markdown("---")
        st.markdown(f"**Vous avez obtenu {correct_count} sur {total_questions} questions correctes ({correct_percentage:.2f}%)!**")

        # [Rest of the code remains the same - congratulatory message, gauge chart, category statistics, and histogram]

if __name__ == "__main__":
    main()