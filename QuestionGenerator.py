import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

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

# Fetch all questions for debugging
def fetch_all_questions():
    try:
        db = firestore.client()
        questions_ref = db.collection("questions")
        query_snapshot = questions_ref.get()

        questions = []
        for doc in query_snapshot:
            question_data = doc.to_dict()
            st.write(f"Retrieved question: {question_data}")  # Debugging line
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

    # Fetch all questions for debugging
    questions = fetch_all_questions()

    # Filter questions by category
    prepare_data_questions = [q for q in questions if q.get("category") == "Prepare the data"]
    model_data_questions = [q for q in questions if q.get("category") == "Model the data"]

    # Limit the number of questions
    prepare_data_questions = prepare_data_questions[:3]
    model_data_questions = model_data_questions[:5]

    # Combine questions
    questions = prepare_data_questions + model_data_questions

    # Store user answers in session state
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {q["question_text"]: None for q in questions}

    # Display questions with radio buttons
    for question in questions:
        st.write("**Question:**", question["question_text"])
        
        # Prepare choices from the comma-separated string
        choices = question.get("Choices", "").split(",")  # Split the string into a list

        if choices:  # Display only if there are choices
            selected_answer = st.radio("Choose your answer:", choices, key=question["question_text"])  
            # Store the selected answer
            st.session_state.user_answers[question["question_text"]] = selected_answer
        else:
            st.warning(f"No choices available for the question: {question['question_text']}")

    # Submit button to check answers
    if st.button("Soumettre"):
        correct_count = 0
        category_correct_count = {"Prepare the data": 0, "Model the data": 0}

        for question in questions:
            correct_answers = question.get("answer_text", "").split(",")  # Split correct answers
            user_answer = st.session_state.user_answers[question["question_text"]]
            if user_answer in correct_answers:
                correct_count += 1
                category_correct_count[question["category"]] += 1
                st.success(f"**{question['question_text']}** - Correct! Your answer is: {user_answer}", icon="✅")
            else:
                st.error(f"**{question['question_text']}** - Incorrect! Your answer was: {user_answer}. Correct answer(s): {', '.join(correct_answers)}", icon="❌")

        st.markdown(f"**You got {correct_count} out of {len(questions)} questions correct!**")
        st.markdown(f"**In the 'Prepare the data' category, you got {category_correct_count['Prepare the data']} questions correct.**")
        st.markdown(f"**In the 'Model the data' category, you got {category_correct_count['Model the data']} questions correct.**")

if __name__ == "__main__":
    main()