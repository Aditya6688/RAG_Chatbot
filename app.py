#Final code
import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import os
import google.generativeai as genai
from tempfile import NamedTemporaryFile

# Initialize Gemini API
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Initialize session state
if "current_summary" not in st.session_state:
    st.session_state.current_summary = ""
if "recent_interaction" not in st.session_state:
    st.session_state.recent_interaction = {"question": "", "answer": ""}

def transcribe_audio(audio_file):
    """Transcribe audio file using speech_recognition."""
    r = sr.Recognizer()

    # Create a temporary file for the audio
    with NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio_path = temp_audio.name
        if audio_file.name.endswith(".mp3"):
            audio = AudioSegment.from_mp3(audio_file)
            audio.export(temp_audio_path, format="wav")
        else:
            temp_audio.write(audio_file.getbuffer())

    try:
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
    except Exception as e:
        text = None
        st.error(f"Error in transcription: {str(e)}")
    finally:
        os.unlink(temp_audio_path)  # Clean up temp file after use

    return text

def generate_summary(text):
    """Generate summary using Gemini API."""
    prompt = f"Please provide a concise summary and key points of the following text:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

def get_chatbot_response(query, context):
    """Get response from Gemini using RAG approach."""
    prompt = f"""Context: {context}

User Query: {query}

Please provide a relevant response based on the context above. If the query cannot be answered using the given context, please say so. Also rember the previosly asked question and answers for that particular file"""
    response = model.generate_content(prompt)
    return response.text

# Streamlit UI
st.title("Audio Summary and Chat Assistant")

# File upload
uploaded_file = st.file_uploader("Upload an audio file (WAV or MP3)", type=["wav", "mp3"])

if uploaded_file:
    if st.button("Process Audio"):
        # Clear previous summary and interaction when processing a new audio file
        st.session_state.current_summary = ""
        st.session_state.recent_interaction = {"question": "", "answer": ""}

        with st.spinner("Transcribing audio..."):
            transcription = transcribe_audio(uploaded_file)
            if transcription:
                with st.spinner("Generating summary..."):
                    summary = generate_summary(transcription)
                    st.session_state.current_summary = summary
                    st.success("Summary generated successfully!")

# Display the summary (persist until a new file is uploaded)
if st.session_state.current_summary:
    st.subheader("Summary and Key Points:")
    st.write(st.session_state.current_summary)

# Chat interface
if st.session_state.current_summary:
    st.subheader("Chat with the Assistant")
    user_input = st.text_input("Ask a question about the audio content:")

    if user_input:
        # Get chatbot response
        response = get_chatbot_response(user_input, st.session_state.current_summary) 

        # Store the most recent interaction
        st.session_state.recent_interaction["question"] = user_input
        st.session_state.recent_interaction["answer"] = response

    # Display the most recent interaction
    if st.session_state.recent_interaction["question"]:
        st.markdown(f"**You:** {st.session_state.recent_interaction['question']}")
        st.markdown(f"**Assistant:** {st.session_state.recent_interaction['answer']}")
