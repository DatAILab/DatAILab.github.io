import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import firebase_admin
from firebase_admin import credentials

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

# Call the function to initialize Firebase
initialize_firebase()

# Sample questions for demonstration
questions = [
    {"question_text": "Question 1? (Choose A)", "answer_text": "Answer A", "Category": "Prepare the data"},
    {"question_text": "Question 2? (Choose B or C)", "answer_text": "Answer B,Answer C", "Category": "Model the data"},
    {"question_text": "Question 3? (Choose D)", "answer_text": "Answer D", "Category": "PBI Service"},
    {"question_text": "Question 4? (Choose E)", "answer_text": "Answer E", "Category": "Visualization"},
]

# Initialize user answers if not already in session state
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {question["question_text"]: "" for question in questions}

# Display questions and gather user answers
for question in questions:
    if question["answer_text"].count(",") > 0:  # If there are multiple answers
        user_answer = st.multiselect(question["question_text"], options=question["answer_text"].split(","))
        st.session_state.user_answers[question["question_text"]] = user_answer
    else:
        user_answer = st.radio(question["question_text"], options=question["answer_text"].split(","))
        st.session_state.user_answers[question["question_text"]] = user_answer

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
                st.success(f"**{question['question_text']}** - Correct! Your answers are: {', '.join(user_answer)}", icon="✅")
            else:
                st.error(f"**{question['question_text']}** - Incorrect! Your answers were: {', '.join(user_answer)}. Correct answer(s): {', '.join(correct_answers)}", icon="❌")
        else:  # Single answer
            if user_answer in correct_answers:
                correct_count += 1
                category_correct_count[question["Category"]] += 1
                st.success(f"**{question['question_text']}** - Correct! Your answer is: {user_answer}", icon="✅")
            else:
                st.error(f"**{question['question_text']}** - Incorrect! Your answer was: {user_answer}. Correct answer(s): {', '.join(correct_answers)}", icon="❌")

    total_questions = len(questions)
    correct_percentage = (correct_count / total_questions) * 100

    # Create a gauge chart with a target value of 70
    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=correct_percentage,
        title={'text': "Correct Answers Percentage"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "white"},
            'steps': [
                {'range': [0, 69], 'color': "red"},
                {'range': [70, 100], 'color': "blue"},
            ],
            'threshold': {
                'line': {'color': "blue", 'width': 4},
                'thickness': 0.75,
                'value': 70  # This sets the target value at 70
            }
        }
    ))

    # Add a target value label
    gauge_fig.add_annotation(
        x=0.5,
        y=0.5,
        text="Target: 70",
        showarrow=False,
        font=dict(size=16, color="blue"),
        bgcolor="white",
        bordercolor="blue",
        borderwidth=2,
        borderpad=4,
        opacity=0.8
    )

    st.plotly_chart(gauge_fig)

    st.markdown(f"**You got {correct_count} out of {total_questions} questions correct ({correct_percentage:.2f}%)!**")

    # Display category results
    for category, count in category_correct_count.items():
        st.markdown(f"**In the '{category}' category, you got {count} questions correct.**")

    # Plot a histogram
    categories = list(category_correct_count.keys())
    correct_values = list(category_correct_count.values())

    fig, ax = plt.subplots()
    ax.bar(categories, correct_values, color='skyblue')
    ax.set_xlabel('Category')
    ax.set_ylabel('Correct Answers')
    ax.set_title('Correct Answers per Category')
    ax.set_yticks(np.arange(0, max(correct_values) + 1, 1))  # Set Y-axis ticks incrementing by 1

    st.pyplot(fig)

if __name__ == "__main__":
    st.title("Quiz Application")