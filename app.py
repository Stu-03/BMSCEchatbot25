import streamlit as st
from huggingface_hub import InferenceClient
import time 
from tavily import TavilyClient
import re, random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import spacy
from rapidfuzz import process, fuzz
import os

T1 = st.secrets["TKEY1"]
T2 = st.secrets["TKEY2"]
T3 = st.secrets["TKEY3"]
T4 = st.secrets["TKEY4"]
tavkey = [T1, T2, T3, T4]
HF_API_KEY = st.secrets["HF_API_KEY"]

nlp = spacy.load("en_core_web_sm")

DEPARTMENT_ALIASES = {
    "Computer Science and Engineering": ["CSE", "CS", "Comp Sci", "Computer Science"],
    "Information Science and Engineering": ["ISE", "IS", "IT"],
    "Electronics and Communication Engineering": ["ECE", "Electronics", "Electronics & Communication"],
    "Mechanical Engineering": ["ME", "Mechanical"],
    "Civil Engineering": ["CE", "Civil"],
    "Electrical and Electronics Engineering": ["EEE", "Electrical"],
    "Machine Learning (AI and ML)": ["AIML", "AI & ML", "AI/ML"],
    "Computer Science and Engineering (DS)": ["DS", "Data Science","CSE DS","CSE(DS)", "CD", "csds"],
    "Computer Science and Engineering (IoT and CS)": ["cs(iot)", "cse(iot)", "iot", "cybersecurity"],
    "Computer Science and Business Systems": ["csbs", "business systems", "computer science and business systems"],
    "Artificial Intelligence and Data Science": ["aids", "ai and data science", "Artificial Intelligence and Data Science"],
    "Aerospace Engineering": ["aerospace", "aerospace engineering"],
    "Chemistry Department": ["chemistry"],
    "Physics Department": ["physics"],
    "Mathematics Department": ["mathematics"],
    "Industrial Engineering and Management":["iem", "industrial engineering"],
    "Electronics and Telecommunication Engineering": ["telecom", "telecommunication", "electronics and telecommunication"],
    "Electronics and Instrumentation Engineering":["instrumentation", "electronics and instrumentation"],
    "Medical Electronics Engineering": ["medical electronics"],
    "Chemical Engineering":["chemical", "chemical engineering"],
    "Bio-Technology":["biotech", "biotechnology"],
    "Computer Applications (MCA)":["mca", "computer applications"],
    "Management Studies and Research Centre":["mba", "management studies"],
}
def extract_syllabus_links(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to load {url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", class_="table table-hover")

    syllabus_dict = {}

    if table:
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:  # Ensure there are at least 3 columns
                    dept_name = cols[1].text.strip()  # Second <td> as key
                    link_tag = cols[2].find("a", href=True)  # Third <td> contains the link

                    if link_tag:
                        syllabus_url = urljoin(url, link_tag["href"])  # Get absolute URL
                        syllabus_dict[dept_name] = syllabus_url

    return syllabus_dict
def extract_department_from_query(query):
    doc = nlp(query.lower().strip())  # Convert query to lowercase and clean it
    possible_terms = [token.text for token in doc if token.pos_ in ["PROPN", "NOUN", "ADJ"]]

    # Flatten alias dictionary
    alias_map = {alias.lower(): dept for dept, aliases in DEPARTMENT_ALIASES.items() for alias in aliases}

    # 🔹 *Check for an exact match first*
    for term in possible_terms:
        if term.lower() in alias_map:
            return alias_map[term.lower()]

    # 🔹 *If no exact match, use fuzzy matching*
    best_match, score, _ = process.extractOne(" ".join(possible_terms), alias_map.keys(), scorer=fuzz.ratio)

    if score > 75:  # Confidence threshold
        return alias_map[best_match]
    else:
        return None
def get_syllabus_by_query(url, user_query):
    syllabus_dict = extract_syllabus_links(url)

    if not syllabus_dict:
        print("Failed to extract syllabus links.")
        return None

    dept_name = extract_department_from_query(user_query)
    print(dept_name)

    if dept_name and dept_name in syllabus_dict:
        return syllabus_dict[dept_name]
    else:
        print(f"Could not find a syllabus for: {user_query}")
        return None
def extract_years_from_url(url):
    decoded_url = unquote(url)  # Decode %20 spaces
    match = re.findall(r'(\d{4})-\d{2}', decoded_url)  # Find patterns like '2022-25'
    return max(map(int, match)) if match else 0
def get_syllabus_links(url):
    syllabus_links = {"UG": [], "PG": []}  # Store UG and PG separately

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to load {url}")

    # Parse the HTML page for syllabus links
    soup = BeautifulSoup(response.text, 'html.parser')
    sections = soup.find_all(class_="toggle active")

    for section in sections:
        label = section.find('label')
        if label:
            category = None
            if "UG Syllabus" in label.text.strip():
                category = "UG"
            elif "PG Syllabus" in label.text.strip():
                category = "PG"

            if category:
                links = section.find_all('a', href=True)
                for link in links:
                    absolute_link = urljoin(url, link['href']).replace(" ", "%20")
                    year = extract_years_from_url(absolute_link)
                    syllabus_links[category].append((absolute_link, year))

    # Sort by year (latest first) and pick the most recent syllabus link
    latest_ug = max(syllabus_links["UG"], key=lambda x: x[1], default=None)
    latest_pg = max(syllabus_links["PG"], key=lambda x: x[1], default=None)

    # Return only the latest UG and PG syllabus links
    final_links = []
    if latest_ug:
        final_links.append(latest_ug[0])
    if latest_pg:
        final_links.append(latest_pg[0])

    return final_links if final_links else None
page_url = "https://bmsce.ac.in/home/All-Department-Syllabus"

def main():
    st.set_page_config(
        page_title="BMSCE Chatbot",
        page_icon="🎓",
    )
    st.markdown("""
        <style>
            /* Change header and footer background to blue */
            .stApp {
                background-color: #FFFFFF !important;
            }
            header, footer {
                background-color: #0088cc !important;
                padding: 10px !important;
            }

            /* Change all text and headers to blue */
            .stText, .stMarkdown .stHeader, .stSubheader, h1, h2, h3, h4, h5, h6, p, span {
                color: #0088cc !important;
            }

            .stTitle{
                color: #000000 !important;
            }

            /* Chat input bar */
            .stChatInputContainer {
                background-color: #0088cc !important;
                border-radius: 8px !important;
            }
            .stChatInputContainer input {
                color: white !important;
            }
            .stButton button{
            background-color: #0088cc !important;
            
            }

            /* Thumbs-up & Thumbs-down button container */
            .thumbs-buttons {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: white;
                padding: 10px;
                border-radius: 10px;
                box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
                display: flex;
                gap: 10px;
                align-items: center;
            }
            .thumbs-buttons button {
                border: none;
                background: none;
                font-size: 20px;
                cursor: pointer;
            }
            .counter-display {
                font-size: 18px;
                font-weight: bold;
                margin-left: 10px;
            }
            .disclaimer-box {
                background-color:rgb(103, 141, 179);
                padding: 10px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
                margin-bottom: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    logo_path = "logo.png"  # Replace with your logo path

# Create a two-column layout
    col1, col2 = st.columns([0.1, 0.9])  # Adjust column width as needed

    with col1:
        st.image(logo_path, width=70)  # Adjust width to match title size

    with col2:
        st.title("BMSCE Chatbot")

    st.write("Your go-to assistant for your queries - admissions, courses, activities and more!")

    if "disclaimer_visible" not in st.session_state:
        st.session_state.disclaimer_visible = True

    if st.session_state.disclaimer_visible:
        with st.expander("**Disclaimer**"):
            st.write("""
            This chatbot provides information related to **BMS College of Engineering**.  
            Replies are sourced from the official website: [bmsce.ac.in](https://bmsce.ac.in/).  

            The chatbot **does not store any personal information** and is currently in the **testing phase**.  

            For any queries, contact [here](mailto:stuthi.cd22@bmsce.ac.in).
            """)

    options = ["Admissions", "Departments", "News and Events", "Activites"]
    selection = st.pills("", options, selection_mode="single")
    if selection:
        TAVILY_KEY = random.choice(tavkey)
        client = TavilyClient(api_key=TAVILY_KEY)
        x = ""
        response = client.search(
            query=selection,
            include_answer="basic",
            include_domains=["bmsce.ac.in"]
            )
        x = response['answer']
        st.write(x)

                

    # Initialize session state for chat and feedback buttons
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thumbs_up" not in st.session_state:
        st.session_state.thumbs_up = 0
    if "thumbs_down" not in st.session_state:
        st.session_state.thumbs_down = 0
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    if "show_keyboard" not in st.session_state:
        st.session_state.show_keyboard = False

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
            if prompt.strip().lower() in ['hi', 'hello', 'hey']:
                client = InferenceClient(api_key=HF_API_KEY)

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
            elif "syllabus" in prompt.strip().lower():
                x = "Syllabus:\n"
                user_query = prompt.strip()
                syllabus_link = get_syllabus_by_query(page_url, user_query)
                ll = get_syllabus_links(syllabus_link)
                x += "\n"
                x += "\n".join(ll)

            else:
                TAVILY_KEY = random.choice(tavkey)
                client = TavilyClient(api_key=TAVILY_KEY)
                x = ""
                response = client.search(
                    query=prompt,
                    include_answer="basic",
                    include_domains=["bmsce.ac.in"]
                )
                x = response['answer']
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

    st.markdown(f"""
        <div class="thumbs-buttons">
            <button onclick="document.getElementById('thumbs-up-count').innerText++">👍 {st.session_state.thumbs_up}</button>
            <button onclick="document.getElementById('thumbs-down-count').innerText++">👎 {st.session_state.thumbs_down}</button>
        </div>
    """, unsafe_allow_html=True)

    # Button functionality
    col1, col2, col3 = st.columns([0.25, 1, 0.5])
    flag = 0
    with col1:
        if st.button("👍", key="up"):
            st.session_state.thumbs_up += 1
            flag = 1
    with col2:
        if st.button("👎", key="down"):
            st.session_state.thumbs_down += 1
            flag = 2
    with col3:
        if flag == 1:
            st.write(f"👍: {st.session_state.thumbs_up}")
        if flag == 2:
            st.write(f"👎: {st.session_state.thumbs_down}")
        print(st.session_state.thumbs_up, st.session_state.thumbs_down)


if __name__ == "__main__":
    main()


