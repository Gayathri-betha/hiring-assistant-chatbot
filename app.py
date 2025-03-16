import os
import json
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from textblob import TextBlob
from googletrans import Translator

# Load API Key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GEMINI_API_KEY)

# Translator for multilingual support
translator = Translator()

# JSON file path
DATA_FILE = "candidate_data.json"

# Function to load existing data from JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to save data to JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Streamlit UI Configuration
st.set_page_config(page_title="TalentScout - Hiring Assistant", layout="centered")
st.title("🤖 TalentScout - AI Hiring Assistant")
st.write("Welcome! I'll help screen candidates based on their tech stack.")

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "questions" not in st.session_state:
    st.session_state.questions = []
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = {}
if "preferred_language" not in st.session_state:
    st.session_state.preferred_language = "en"
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "current_answer" not in st.session_state:
    st.session_state.current_answer = ""

# Language Selection (Added Tamil)
lang_options = {"English": "en", "Telugu": "te", "Hindi": "hi", "Tamil": "ta"}
selected_lang = st.selectbox("🌍 Select your preferred language:", list(lang_options.keys()))
st.session_state.preferred_language = lang_options[selected_lang]

# Translation Function
def translate_text(text, target_lang="en"):
    if target_lang == "en":
        return text
    try:
        translated = translator.translate(text, dest=target_lang)
        return translated.text
    except Exception:
        return text

# Sentiment Analysis Function
def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0:
        return "🙂 Positive"
    elif polarity < 0:
        return "☹️ Negative"
    else:
        return "😐 Neutral"

# Tech Stack Validation
def validate_tech_stack(stack):
    valid_tech_keywords = ["python", "java", "c++", "tensorflow", "react", "node.js", "pandas", "sql"]
    stack_lower = stack.lower()
    return any(tech in stack_lower for tech in valid_tech_keywords)

# Function to generate interview questions based on tech stack
def generate_questions(tech_stack):
    if not validate_tech_stack(tech_stack):
        return [translate_text("Please enter a valid tech stack!", st.session_state.preferred_language)]
    
    prompt = f"Generate 5 interview questions for a candidate skilled in {tech_stack}."
    response = llm.invoke(prompt)
    questions = [q.strip() for q in response.content.split("\n") if q.strip()]
    return questions[:5] if questions else [translate_text("Unable to generate questions.", st.session_state.preferred_language)]

# Step 1: Gather Candidate Info
if not st.session_state.interview_started:
    with st.form("candidate_info_form"):
        st.subheader("📋 " + translate_text("Candidate Information", st.session_state.preferred_language))
        full_name = st.text_input(translate_text("Full Name", st.session_state.preferred_language))
        email = st.text_input(translate_text("Email", st.session_state.preferred_language))
        phone = st.text_input(translate_text("Phone Number", st.session_state.preferred_language))
        experience = st.number_input(translate_text("Years of Experience", st.session_state.preferred_language), min_value=0, max_value=50, step=1)
        position = st.text_input(translate_text("Desired Position", st.session_state.preferred_language))
        location = st.text_input(translate_text("Current Location", st.session_state.preferred_language))
        tech_stack = st.text_area(translate_text("Tech Stack (e.g., Python, TensorFlow, PostgreSQL)", st.session_state.preferred_language))

        submit_info = st.form_submit_button(translate_text("Proceed to Interview", st.session_state.preferred_language))

    if submit_info:
        if not full_name or not email or not phone or not tech_stack:
            st.warning(translate_text("Please fill in all required fields.", st.session_state.preferred_language))
        else:
            st.session_state.candidate_info = {
                "name": full_name,
                "email": email,
                "phone": phone,
                "experience": experience,
                "position": position,
                "location": location,
                "tech_stack": tech_stack,
            }
            st.session_state.questions = generate_questions(tech_stack)
            st.session_state.question_index = 0
            st.session_state.conversation = []
            st.session_state.interview_started = True
            st.session_state.current_answer = ""
            st.success(translate_text(f"Thank you, {full_name}! Let's start your interview.", st.session_state.preferred_language))
            st.rerun()

# Step 2: Interview Process
if st.session_state.interview_started and st.session_state.questions:
    index = st.session_state.question_index

    if index < len(st.session_state.questions):
        question = translate_text(st.session_state.questions[index], st.session_state.preferred_language)
        
        st.subheader(f"📝 {translate_text('Question', st.session_state.preferred_language)} {index + 1} of {len(st.session_state.questions)}:")
        st.write(question)

        # Single answer input tied to session state
        st.session_state.current_answer = st.text_area(
            translate_text("Your Answer:", st.session_state.preferred_language),
            value=st.session_state.current_answer,
            key=f"answer_{index}"
        )

        # Submit button
        if st.button(translate_text("Submit Answer", st.session_state.preferred_language), key=f"submit_{index}"):
            if not st.session_state.current_answer.strip():
                st.warning(translate_text("Please enter a valid answer before proceeding.", st.session_state.preferred_language))
            else:
                translated_answer = translate_text(st.session_state.current_answer, "en")
                sentiment = analyze_sentiment(translated_answer)

                st.session_state.conversation.append({
                    "question": st.session_state.questions[index],
                    "answer": translated_answer,
                    "sentiment": sentiment
                })
                st.session_state.question_index += 1
                st.session_state.current_answer = ""
                st.rerun()
    else:
        # Interview completed - Save to JSON
        candidate_data = load_data()
        candidate_id = st.session_state.candidate_info["email"]  # Using email as unique identifier
        candidate_data[candidate_id] = {
            "info": st.session_state.candidate_info,
            "interview": st.session_state.conversation,
            "completed_date": "March 16, 2025"  # Current date as per your instruction
        }
        save_data(candidate_data)

        st.success(translate_text("✅ Interview completed! Your responses have been saved. We will contact you for further steps.", st.session_state.preferred_language))
        st.subheader(translate_text("Your Responses:", st.session_state.preferred_language))
        
        for idx, qa in enumerate(st.session_state.conversation):
            st.write(f"**Q{idx+1}:** {translate_text(qa['question'], st.session_state.preferred_language)}")
            st.write(f"**A{idx+1}:** {translate_text(qa['answer'], st.session_state.preferred_language)}")
            st.write(f"**Sentiment:** {qa['sentiment']}")
            st.write("---")

        # Option to restart
        if st.button(translate_text("Start New Interview", st.session_state.preferred_language)):
            st.session_state.interview_started = False
            st.session_state.conversation = []
            st.session_state.questions = []
            st.session_state.question_index = 0
            st.session_state.candidate_info = {}
            st.session_state.current_answer = ""
            st.rerun()

# Optional: Display all saved candidates (for admin view)
if st.checkbox(translate_text("Show all saved candidates (Admin View)", st.session_state.preferred_language)):
    candidate_data = load_data()
    if candidate_data:
        st.subheader(translate_text("Saved Candidate Data:", st.session_state.preferred_language))
        for email, data in candidate_data.items():
            st.write(f"**Candidate:** {data['info']['name']} ({email})")
            st.write(f"**Position:** {data['info']['position']}")
            st.write(f"**Tech Stack:** {data['info']['tech_stack']}")
            st.write(f"**Completed:** {data['completed_date']}")
            st.write("---")
    else:
        st.write(translate_text("No candidate data available yet.", st.session_state.preferred_language))