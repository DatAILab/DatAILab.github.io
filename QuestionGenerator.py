def main():
    # Initialize Firebase
    initialize_firebase()

    st.title("Quiz Certification PL-300")

    # Hide the footer using custom CSS
    hide_footer = """
    <style>
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_footer, unsafe_allow_html=True)

    # Fetch all questions
    questions = fetch_all_questions()

    # Filter questions by category
    prepare_data_questions = [q for q in questions if q.get("Category") == "Prepare the data"]
    model_data_questions = [q for q in questions if q.get("Category") == "Model the data"]
    pbi_service_questions = [q for q in questions if q.get("Category") == "PBI Service"]
    visualization_questions = [q for q in questions if q.get("Category") == "Visualization"]

    # Limit the number of questions
    prepare_data_questions = prepare_data_questions[:3]
    model_data_questions = model_data_questions[:4]
    pbi_service_questions = pbi_service_questions[:4]
    visualization_questions = visualization_questions[:4]

    # Combine questions
    questions = prepare_data_questions + model_data_questions + pbi_service_questions + visualization_questions

    # Store user answers in session state
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: [] for q in questions}

    # Display questions with appropriate input types
    for index, question in enumerate(questions, start=1):  # Enumerate questions starting from 1
        st.write(f"**Question {index}:** {question['question_text']}")
        
        # Check if there is an image URL and display it
        if 'image' in question and question['image']:
            st.image(question['image'], caption='Question Image', use_column_width=True)

        # Prepare choices from the comma-separated string
        choices = question.get("Choices", "").split(",")  # Split the string into a list
        correct_answers = question.get("answer_text", "").split(",")  # Split correct answers

        if len(correct_answers) == 1:  # Single correct answer
            selected_answer = st.radio("Choose your answer:", choices, key=f"radio_{question['question_text']}")  
            if selected_answer:
                st.session_state.user_answers[question["question_text"]] = [selected_answer]
        elif len(correct_answers) > 1:  # Multiple correct answers
            selected_answers = []
            for choice in choices:
                if st.checkbox(choice, key=f"checkbox_{question['question_text']}_{choice}"):
                    selected_answers.append(choice)
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

        st.markdown(f"**You got {correct_count} out of {total_questions} questions correct ({correct_percentage:.2f}%)!**")
        
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
    main()