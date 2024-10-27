import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import random

# [Previous initialization functions remain the same]
def initialize_firebase():
    if not firebase_admin._apps:
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
        print("Firebase est déjà initialisé.")

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
            st.warning("Aucune question trouvée dans la base de données.")

        return questions
    except Exception as e:
        st.error(f"Erreur lors de la récupération des questions: {e}")
        return []

def main():
    # Minimize sidebar width using custom CSS
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 1px;
            max-width: 200px;
        }
        [data-testid="stSidebar"][aria-expanded="false"] {
            margin-left: -1px;
        }
        
        /* Style for the back to top button */
        .back-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: #0E1117;
            color: white;
            padding: 10px 15px;
            border-radius: 50%;
            text-decoration: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
            transition: background-color 0.3s;
        }
        .back-to-top:hover {
            background-color: #262730;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Create an anchor for the top of the page
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)

    # Add the back to top button at the bottom of the page
    st.markdown(
        '''
        <a href="#top" class="back-to-top">
            ⬆️
        </a>
        ''',
        unsafe_allow_html=True
    )

    st.title("Quiz Certification PL-300")

    # Rest of your code remains the same...
    # [Include the rest of your main() function here]

    initialize_firebase()
    questions = fetch_all_questions()

    # [Rest of your existing code...]

if __name__ == "__main__":
    main()