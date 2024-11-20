from supabase import create_client, Client
import streamlit as st

# Initialize Supabase client
url = "https://tjgmipyirpzarhhmihxf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRqZ21pcHlpcnB6YXJoaG1paHhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE2NzQ2MDEsImV4cCI6MjA0NzI1MDYwMX0.LNMUqA0-t6YtUKP6oOTXgVGYLu8Tpq9rMhH388SX4bI"
supabase: Client = create_client(url, key)

# Streamlit application layout
st.title("SQL Query Editor")

# Session state to store submitted queries
if 'submitted_queries' not in st.session_state:
    st.session_state.submitted_queries = []

# Single input field for SQL queries
query = st.text_input("Enter your SQL query:")

# Columns for buttons
col1, col2 = st.columns(2)

with col1:
    try_query = st.button("Try Query")

with col2:
    submit_query = st.button("Submit Query")

# Function to check for restricted queries
def is_query_restricted(query):
    restricted_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
    return any(keyword in query.strip().upper() for keyword in restricted_keywords)

# Try Query functionality
if try_query and query:
    if is_query_restricted(query):
        st.error("Error: This query is restricted and cannot be executed.")
    else:
        try:
            if query.strip().upper().startswith("SELECT"):
                response = supabase.rpc("execute_returning_sql", {"query_text": query}).execute()
            else:
                response = supabase.rpc("execute_non_returning_sql", {"query_text": query}).execute()

            if hasattr(response, 'data') and response.data:
                st.write("Query Results:")
                st.table(response.data)
            else:
                st.success("Query executed successfully.")

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.write("Debug info:")
            st.write(f"Query attempted: {query}")

# Submit Query functionality
if submit_query and query:
    if is_query_restricted(query):
        st.error("Error: This query is restricted and cannot be submitted.")
    else:
        try:
            # Add query to submitted queries list
            st.session_state.submitted_queries.append(query)
            st.success(f"Query '{query}' has been submitted!")

        except Exception as e:
            st.error(f"Error submitting query: {str(e)}")

# Display submitted queries
if st.session_state.submitted_queries:
    st.write("### Submitted Queries:")
    for idx, submitted_query in enumerate(st.session_state.submitted_queries, 1):
        st.write(f"{idx}. {submitted_query}")

# Optional: Clear submitted queries
if st.button("Clear Submitted Queries"):
    st.session_state.submitted_queries = []