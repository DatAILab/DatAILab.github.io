import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Sample questions for demonstration
questions = [
    {"question_text": "Question 1?", "answer_text": "Answer A", "Category": "Prepare the data"},
    {"question_text": "Question 2?", "answer_text": "Answer B,Answer C", "Category": "Model the data"},
    {"question_text": "Question 3?", "answer_text": "Answer D", "Category": "PBI Service"},
    {"question_text": "Question 4?", "answer_text": "Answer E", "Category": "Visualization"},
]

# Initialize user answers if not already in session state
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {question["question_text"]: [] for question in questions}

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

    # Create a gauge chart
    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=correct_percentage,
        title={'text': "Correct Answers Percentage"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "white"},
            'steps': [
                {'range': [0, 69], 'color': "red"},
                {'range': [70, 100], 'color': "lightgreen"},
            ],
        }
    ))

    st.plotly_chart(gauge_fig)

    # Add a message based on the correct percentage
    if correct_percentage >= 70:
        st.success("🎉 Congratulations! You have successfully passed the exam! 🎉")
    else:
        st.error("❌ Unfortunately, you did not pass the exam. Better luck next time! ❌")

    st.markdown(f"**You got {correct_count} out of {total_questions} questions correct ({correct_percentage:.2f}%)!**")

    # Display category results
    st.markdown(f"**In the 'Prepare the data' category, you got {category_correct_count['Prepare the data']} questions correct out of 3.**")
    st.markdown(f"**In the 'Model the data' category, you got {category_correct_count['Model the data']} questions correct out of 4.**")
    st.markdown(f"**In the 'PBI Service' category, you got {category_correct_count['PBI Service']} questions correct out of 4.**")
    st.markdown(f"**In the 'Visualization' category, you got {category_correct_count['Visualization']} questions correct out of 4.**")

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