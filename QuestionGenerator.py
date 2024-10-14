import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase initialization (outside Streamlit components)
def initialize_firebase():
    if not firebase_admin._apps:  # Check if any Firebase app is already initialized
        print("Initializing Firebase...")
        cred = credentials.Certificate("C:/Users/Bayram/Desktop/Datailab/Questions/datailab.json")
        firebase_admin.initialize_app(cred)
    else:
        print("Firebase is already initialized.")

def fetch_all_questions():
    try:
        db = firestore.client()
        questions_ref = db.collection("questions")
        query_snapshot = questions_ref.get()

        questions = []
        for doc in query_snapshot:
            questions.append(doc.to_dict())

        if not questions:  # Ensure there are questions to choose from
            st.error("No questions found in the database.")
        return questions
    except Exception as e:
        st.error(f"Error retrieving questions: {e}")
        return []

def main():
    # Initialize Firebase
    initialize_firebase()

    st.title("Quiz Application")

    # Fetch all questions
    questions = fetch_all_questions()

    # Store user's answers in session state
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: None for q in questions}

    # Display all questions with radio buttons
    for question in questions:
        st.write("**Question:**", question["question_text"])
        
        # Prepare choices from the comma-separated string
        choices = question.get("Choices", "").split(",")  # Split the string into a list

        if choices:  # Only display if there are choices
            selected_answer = st.radio("Choose your answer:", choices, key=question["question_text"])  # No index parameter
            # Store the user's selected answer
            st.session_state.user_answers[question["question_text"]] = selected_answer
        else:
            st.warning(f"No choices available for question: {question['question_text']}")

    # "Submit" button to check answers
    if st.button("Submit"):
        correct_count = 0
        for question in questions:
            correct_answer = question.get("answer_text")
            user_answer = st.session_state.user_answers[question["question_text"]]
            if user_answer == correct_answer:
                correct_count += 1
                st.success(f"**{question['question_text']}** - Correct! Your answer is: {user_answer}", icon="✅")
            else:
                st.error(f"**{question['question_text']}** - Incorrect! Your answer was: {user_answer}. Correct answer: {correct_answer}", icon="❌")

        st.markdown(f"**You got {correct_count} out of {len(questions)} questions correct!**")

if __name__ == "__main__":
    main()
