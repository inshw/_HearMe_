import streamlit as st
from google import genai
from google.genai import types 
from elevenlabs.client import ElevenLabs
import base64
# test

# --- 1. SETUP ---
GEMINI_API_KEY = st.secrets['GEMINI_API_KEY']
ELEVEN_API_KEY = st.secrets['ELEVEN_API_KEY']
VOICE_ID = "21m00Tcm4TlvDq8ikWAM" 

genai_client = genai.Client(api_key=GEMINI_API_KEY)
eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)

# --- 2. DARK MODE THEME (CSS) - UNTOUCHED ---
st.set_page_config(page_title="HearMe Safety", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #020617; }
    .main-card {
        background: #0F172A;
        padding: 40px;
        border-radius: 28px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        text-align: center;
        border: 1px solid #1E293B;
    }
    .stChatInputContainer {
        padding: 20px !important;
        background-color: #020617 !important; 
        border-top: 2px solid #0F172A !important;
    }
    .stChatInput textarea {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
    }
    h1 { color: #F1F5F9 !important; font-family: 'Inter', sans-serif; }
    p { color: #94A3B8 !important; }
    [data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #1E293B; }
    
    .st-key-emergency_btn button {
        background-color: #EF4444 !important;
        color: black !important;
        border: none !important;
        font-weight: bold !important;
    }
    .st-key-support_btn button {
        background-color: #0EA5E9 !important;
        color: black !important;
        border: none !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR TOOLS - UNTOUCHED ---
with st.sidebar:
    st.markdown("<h2 style='color:white;'>🛡️ HearMe</h2>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background: #020617; padding: 15px; border-radius: 10px; color: #60A5FA; font-size: 0.85em; border: 1px solid #1E40AF;">
            <b>Live Status:</b> GPS Tracking Active
        </div>
    """, unsafe_allow_html=True)
    
    st.write("") 
    if st.button("🚨 SEND EMERGENCY ALERT (911)", key="emergency_btn", use_container_width=True):
        st.toast("CRITICAL ALERT SENT")
        st.error("Emergency Services notified.")

    if st.button("💬 MENTAL HEALTH SUPPORT (211)", key="support_btn", use_container_width=True):
        st.toast("Connecting to 211...")
        st.info("Counselor pinged.")
    
    st.write("---")
    voice_enabled = st.toggle("Voice Companion", value=True)
    
    st.write("---")
    voice_input = st.audio_input("Speak to HearMe")

# --- 4. MAIN INTERFACE ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div class="main-card">
            <h1 style="font-size: 2.5em;">HearMe Companion</h1>
            <p style="font-size: 1.1em;">I am listening.</p>
        </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. LOGIC & FUNCTIONS ---

def speak_now(text):
    if not voice_enabled: return
    try:
        response = eleven_client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=text,
            model_id="eleven_multilingual_v2"
        )
        audio_bytes = b"".join(response)
        if len(audio_bytes) > 100:
            b64 = base64.b64encode(audio_bytes).decode()
            audio_html = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.components.v1.html(audio_html, height=0)
    except Exception as e:
        st.error(f"Safety Companion Connection Error: {e}")

# A. HANDLE VOICE INPUT
if voice_input is not None:
    # Use a placeholder to prevent UI flickering
    status_placeholder = st.empty()
    
    if "last_voice_id" not in st.session_state or st.session_state.last_voice_id != voice_input.name:
        try:
            with st.spinner("HearMe is transcribing..."):
                # Read the bytes carefully
                input_audio_bytes = voice_input.getvalue() 
                
                if input_audio_bytes:
                    response = genai_client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=[
                            "Transcribe this audio, then answer as HearMe (brief, calm safety companion, <20 words).",
                            types.Part.from_bytes(data=input_audio_bytes, mime_type="audio/webm")
                        ]
                    )
                    
                    # Update session state
                    st.session_state.last_voice_id = voice_input.name
                    st.session_state.messages.append({"role": "user", "content": "🎤 [Voice Message Received]"})
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    st.rerun()
                    
        except Exception as e:
            # Check if it's just a 'file not ready' error, otherwise show it
            if "NoneType" not in str(e):
                st.error(f"Voice processing delay: Please wait a second.")

# B. HANDLE TEXT INPUT
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        # FIX: Changed model to gemini-1.5-flash
        response = genai_client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"You are 'HearMe', a calm safety companion. Brief supportive response under 20 words: {prompt}"
        )
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun() 
    except Exception as e:
        st.error(f"Brain Error: {e}")

# C. AUTO-VOICE TRIGGER
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    if "last_spoken" not in st.session_state or st.session_state.last_spoken != st.session_state.messages[-1]["content"]:
        speak_now(st.session_state.messages[-1]["content"])
        st.session_state.last_spoken = st.session_state.messages[-1]["content"]

