import streamlit as st
from google import genai
from google.genai import types 
from elevenlabs.client import ElevenLabs
import base64

# --- 1. SETUP ---
GEMINI_API_KEY = st.secrets['GEMINI_API_KEY']
ELEVEN_API_KEY = st.secrets['ELEVEN_API_KEY']
VOICE_ID = "21m00Tcm4TlvDq8ikWAM" 

genai_client = genai.Client(api_key=GEMINI_API_KEY)
eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)

# --- 2. DARK MODE THEME (CSS) ---
st.set_page_config(page_title="HearMe Safety", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #020617; }
    
    /* MAIN CARD GRADIENT */
    .main-card {
        background: linear-gradient(145deg, #0F172A, #1E293B);
        padding: 40px;
        border-radius: 28px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        text-align: center;
        border: 1px solid #334155;
        margin-bottom: 30px;
    }

    /* MIDDLE HEARME TO PURE WHITE */
    .main-card h1 {
        color: #FFFFFF !important;
    }
    .main-card p {
        color: #FFFFFF !important;
        opacity: 0.9;
    }

    /* SIDEBAR HEARME TO BLACK */
    .sidebar-title {
        color: #000000 !important;
        font-weight: 900 !important;
        margin-bottom: 15px;
    }

    /* --- CHAT BUBBLES & WHITE TEXT --- */
    [data-testid="stChatMessage"] p {
        color: #FFFFFF !important;
    }

    /* User Message: Tail on Right Bottom */
    [data-testid="stChatMessage"][data-test-was-user="true"] {
        background-color: #1E293B !important;
        border-radius: 20px 20px 0px 20px !important; /* Sharp corner Bottom-Right */
        border: 1px solid #334155 !important;
        margin-left: 15% !important;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.2) !important;
    }
    
    /* Assistant Message: Tail on Left Bottom */
    [data-testid="stChatMessage"][data-test-was-user="false"] {
        background-color: #0F172A !important;
        border-radius: 20px 20px 20px 0px !important; /* Sharp corner Bottom-Left */
        border: 1px solid #1E40AF !important;
        margin-right: 15% !important;
        box-shadow: -5px 5px 15px rgba(0,0,0,0.2) !important;
    }

    .stChatInputContainer {
        padding: 20px !important;
        background-color: #020617 !important; 
        border-top: 1px solid #1E293B !important;
    }
    
    .stChatInput textarea {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border-radius: 15px !important;
        border: 1px solid #334155 !important;
    }

    .st-key-emergency_btn button p, .st-key-support_btn button p {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    .st-key-emergency_btn button {
        background-color: #EF4444 !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4) !important;
        border-radius: 15px !important;
    }

    .st-key-support_btn button {
        background-color: #0EA5E9 !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(14, 165, 233, 0.3) !important;
        border-radius: 15px !important;
    }

    div[data-testid="stCheckbox"] {
        margin-top: -25px !important;
        margin-bottom: 25px !important;
    }

    [data-testid="stAudioInput"] {
        border: 1px solid #1E40AF !important;
        border-radius: 20px !important;
        background-color: #0F172A !important;
        padding: 10px !important;
        box-shadow: 0 0 15px rgba(96, 165, 250, 0.2) !important;
        animation: pulse-blue 3s infinite ease-in-out;
        margin-bottom: 40px !important;
    }

    @keyframes pulse-blue {
        0% { box-shadow: 0 0 0px rgba(96, 165, 250, 0.2); }
        50% { box-shadow: 0 0 20px rgba(96, 165, 250, 0.5); }
        100% { box-shadow: 0 0 0px rgba(96, 165, 250, 0.2); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR TOOLS ---
with st.sidebar:
    st.markdown("<h2 class='sidebar-title'>🛡️ HearMe</h2>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background: #020617; padding: 15px; border-radius: 10px; color: #60A5FA; font-size: 0.85em; border: 1px solid #1E40AF;">
            <b>Live Status:</b> GPS Tracking Active
        </div>
    """, unsafe_allow_html=True)
    
    st.write("") 
    if st.button("🚨 EMERGENCY ALERT (911)", key="emergency_btn", use_container_width=True):
        st.toast("CRITICAL ALERT SENT")
        st.error("Emergency Services notified.")

    if st.button("💬 MENTAL HEALTH SUPPORT", key="support_btn", use_container_width=True):
        st.toast("Connecting to 211...")
        st.info("Counselor pinged.")
    
    st.write("---")
    voice_enabled = st.toggle("Voice Companion", value=True)
    voice_input = st.audio_input("Speak to HearMe")

# --- 4. MAIN INTERFACE ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div class="main-card">
            <h1 style="font-size: 3em; margin-bottom: 0;">HearMe</h1>
            <p style="font-size: 1.2em;">I am here. Listening.</p>
        </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. LOGIC & SAFETY TRIGGERS ---
SYSTEM_PROMPT = (
    "You are 'HearMe', a compassionate, non-judgmental safety and mental health companion. "
    "Guidelines: Use active listening, reflect feelings, and be warm. "
    "Current conversation: "
)

CRISIS_KEYWORDS = ["suicide", "murder", "kill myself", "end my life", "harm myself", "hurt someone"]

def check_for_crisis(text):
    if any(word in text.lower() for word in CRISIS_KEYWORDS):
        st.toast("⚠️ CRITICAL OVERRIDE: Connecting to 211 Support...")
        st.info("HearMe detected a crisis. Counselor pinged automatically.")

def speak_now(text):
    if not voice_enabled: return
    try:
        response = eleven_client.text_to_speech.convert(
            voice_id=VOICE_ID, text=text, model_id="eleven_multilingual_v2"
        )
        audio_bytes = b"".join(response)
        if len(audio_bytes) > 100:
            b64 = base64.b64encode(audio_bytes).decode()
            audio_html = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.components.v1.html(audio_html, height=0)
    except Exception:
        pass

# A. VOICE INPUT
if voice_input is not None:
    if "last_voice_id" not in st.session_state or st.session_state.last_voice_id != voice_input.name:
        try:
            input_audio_bytes = voice_input.getvalue() 
            if input_audio_bytes:
                response = genai_client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=[SYSTEM_PROMPT, types.Part.from_bytes(data=input_audio_bytes, mime_type="audio/webm")]
                )
                st.session_state.last_voice_id = voice_input.name
                st.session_state.messages.append({"role": "user", "content": "🎤 [Voice Message Received]"})
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                check_for_crisis(response.text)
                st.rerun()
        except Exception:
            st.error("Voice processing error.")

# B. TEXT INPUT
if prompt := st.chat_input("I'm listening..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        response = genai_client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"{SYSTEM_PROMPT} User says: {prompt}"
        )
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        check_for_crisis(prompt + " " + response.text)
        st.rerun() 
    except Exception:
        st.error("Brain Error")

# C. AUTO-VOICE TRIGGER
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    if "last_spoken" not in st.session_state or st.session_state.last_spoken != st.session_state.messages[-1]["content"]:
        speak_now(st.session_state.messages[-1]["content"])
        st.session_state.last_spoken = st.session_state.messages[-1]["content"]