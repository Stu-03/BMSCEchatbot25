import streamlit as st
from langchain_community.retrievers import TavilySearchAPIRetriever
from huggingface_hub import InferenceClient
import time  # Import time module for tracking duration

# Predefined API keys
TAVILY_API_KEY = "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"
HF_API_KEY = "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"

# Initialize retriever and inference client
retriever = TavilySearchAPIRetriever(api_key=TAVILY_API_KEY, k=15)
client = InferenceClient(api_key=HF_API_KEY)

# Streamlit UI
def main():
    st.set_page_config(
        page_title="BMSCE Chatbot",
        page_icon="🎓",
    )

    st.title("🎓 BMSCE Chatbot")
    st.write("Designed to query and receive information about the college!")

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Enter your query"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Retrieve documents and filter context
        with st.spinner("Retrieving and processing context..."):
            documents = retriever.invoke(prompt)
            filtered_content = [
                doc.page_content
                for doc in documents
                if doc.metadata.get('source', '').startswith('https://bmsce.ac.in')
            ]
            context = " ".join(filtered_content)

        # Display context in the sidebar
        with st.sidebar:
            st.subheader("Filtered Context")
            if filtered_content:
                st.write(filtered_content)
            else:
                st.write("No relevant content found.")

        # Prepare chatbot message
        messages = [
            {
                "role": "user",
                "content": (
                    f"You are a smart chatbot who can answer questions keeping the following context in mind: {context}. "
                    "Always add the line, 'for more information, visit https://www.bmsce.ac.in/', for additional reference."
                    "If there is no context, then just say that you don't have enough information to answer the question"
                )
            }
        ]

        # Generate response from chatbot
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    completion = client.chat.completions.create(
                        model="HuggingFaceH4/zephyr-7b-beta",
                        messages=messages,
                        max_tokens=500
                    )
                    response = completion.choices[0]["message"]["content"]
                except Exception as e:
                    response = f"An error occurred: {e}"
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
