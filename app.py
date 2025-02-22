import streamlit as st
from langchain_community.retrievers import TavilySearchAPIRetriever
from huggingface_hub import InferenceClient
import time 
from tavily import TavilyClient
import re

TAVILY_KEY = st.secrets["TAVILY_KEY"]
HF_API_KEY = st.secrets["HF_API_KEY"]

def main():
    st.set_page_config(
        page_title="BMSCE Chatbot",
        page_icon="🎓",
    )

    st.title("🎓 BMSCE Chatbot")
    st.write("Your go-to assistant for all things BMSCE — ask, explore, and discover!")

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
            if prompt.lower() in ['hi', 'hello', 'hey']:
                client = InferenceClient(
                    api_key=HF_API_KEY
                )

                messages = [
                    {
                        "role": "user",
                        "content": "You are a chatbot designed to talk about BMS College of Engineering, so introduce yourself that way. You can also suggest the user to ask queries regarding the departments, clubs, or anything about the college in general. Subtly mention that your replies are verified and sourced from the official website 'https://bmsce.ac.in/'"
                    }
                ]

                completion = client.chat.completions.create(
                    model="HuggingFaceH4/zephyr-7b-beta", 
                    messages=messages, 
                    max_tokens=500,
                )

                x = completion.choices[0].message.content
            else:
                client = TavilyClient(api_key=TAVILY_KEY)
                x = ""
                response = client.search(
                    query=prompt,
                    include_answer="basic",
                    include_domains=["bmsce.ac.in"]
                )
                x = response['answer'] + "\nRefer the following URLs for more context"
                i = 1
                for result in response['results']:
                    r = result['url']
                    r = re.sub(r'\+', '%20', r)
                    x += "\n"+ str(i) + ". " + r
                    i += 1


        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                st.markdown(x)

        st.session_state.messages.append({"role": "assistant", "content": x})

if __name__ == "__main__":
    main()

