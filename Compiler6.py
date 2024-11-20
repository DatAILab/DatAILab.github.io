from supabase import create_client, Client
import streamlit as st
import re

# Initialize Supabase client
url = "https://tjgmipyirpzarhhmihxf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRqZ21pcHlpcnB6YXJoaG1paHhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE2NzQ2MDEsImV4cCI6MjA0NzI1MDYwMX0.LNMUqA0-t6YtUKP6oOTXgVGYLu8Tpq9rMhH388SX4bI"
supabase: Client = create_client(url, key)


def is_safe_query(query: str) -> tuple[bool, str]:
    """
    Validate if the query is safe to execute.
    Returns a tuple of (is_safe, message).
    """
    # Convert to uppercase for consistent checking
    query_upper = query.strip().upper()

    # Check for DROP statements
    if re.search(r'\bDROP\b', query_upper):
        return False, "DROP queries are not allowed for security reasons."

    # Add additional checks if needed, for example:
    # if re.search(r'\bTRUNCATE\b', query_upper):
    #     return False, "TRUNCATE queries are not allowed."

    return True, "Query is safe"


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

# Try Query functionality
if try_query and query:
    # Validate query before execution
    is_safe, message = is_safe_query(query)

    if not is_safe:
        st.error(message)
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
    # Validate query before submission
    is_safe, message = is_safe_query(query)

    if not is_safe:
        st.error(message)
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