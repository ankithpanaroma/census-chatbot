import streamlit as st
import requests

# Backend API URLs
ASK_URL = "http://localhost:8000/api/answer_question"
TEST_URL = "http://localhost:8000/api/test"

st.set_page_config(page_title="Chatbot", layout="wide")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []  # List to store chat history

# Custom CSS for styling
st.markdown(
    """
    <style>
    .chat-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .chat-card h4 {
        margin: 0;
        color: #333;
    }
    .chat-card p {
        margin: 5px 0 0;
        color: #555;
    }
    .header {
        text-align: center;
        padding: 10px 0;
    }
    .header h1 {
        color: #4CAF50;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="header"><h1>Chatbot</h1></div>', unsafe_allow_html=True)
st.markdown("""
This chatbot answers questions based on the Census of India instruction manuals.
""")

# Ask Question Page
st.header("💬 Ask a Question")
question = st.text_area("Question", help="Enter the question you want to ask.")

if st.button("Get Answer"):
    if question:
        with st.spinner("Fetching answer..."):
            payload = {
                "document_id": "doc1",  # Replace with the appropriate document ID
                "question": question,
                "chat_history": st.session_state["chat_history"],  # Include chat history
            }
            response = requests.post(ASK_URL, json=payload)
            
            try:
                response_data = response.json()  # Attempt to parse JSON
                if "answer" in response_data:
                    answer = response_data["answer"]
                    st.success("✅ Answer fetched successfully!")
                    st.write(f"**Answer:** {answer}")  # Ensure the answer is displayed as a string
                    
                    # Add the question and answer to the chat history
                    st.session_state["chat_history"].append({"question": question, "answer": answer})
                elif "error" in response_data:
                    st.error(f"❌ Backend Error: {response_data['error']}")
                else:
                    st.error("❌ Unexpected response format from the backend.")
            except requests.exceptions.JSONDecodeError:
                st.error("❌ Failed to decode JSON response from the backend.")
                st.text(response.text)  # Display raw response for debugging
    else:
        st.warning("⚠️ Please provide a question.")
    
# Display chat history
if st.session_state["chat_history"]:
    st.subheader("📝 Chat History")
    total = len(st.session_state["chat_history"])
    for i, chat in enumerate(reversed(st.session_state["chat_history"])):
        q_num = total - i  # Reverse the index
        st.markdown(
            f"""
            <div class="chat-card">
                <h4>Q{q_num}: {chat['question']}</h4>
                <p>A{q_num}: {chat['answer']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
