import streamlit as st
from groq import Groq
import streamlit.components.v1 as components
import json
import os

st.set_page_config(page_title="whisperfleet", page_icon="🎙️")

st.markdown("""
    <style>
    /* 1. Nuke the invisible Streamlit header menu that eats top space */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 1rem !important;
        max-width: 800px; 
    }

    /* 2. Clean up native uploader garbage */
    [data-testid="stFileUploader"] section button { display: none; }
    [data-testid="stFileUploader"] section div[data-testid="stMarkdownContainer"] { display: none; }
    [data-testid="stFileUploader"] small { display: none !important; }
    
    /* 3. Modernize the Dropzone container */
    [data-testid="stFileUploader"] section { 
        padding: 1.25rem 1.5rem !important;
        background-color: #16181f; /* Slight contrast from deep black bg */
        border: 1px solid #2e323e;
        border-radius: 0.75rem;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: flex-start; /* Left alignment */
        min-height: 72px;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: #5c627a;
    }

    /* 4. Left-aligned empty state text (merged with file info) */
    [data-testid="stFileUploader"] section:not(:has([data-testid="stUploadedFile"]))::before {
        content: "Кидай файл сюда или нажми для выбора \\A0\\A0 • \\A0\\A0 mp3, wav, m4a, flac до 25MB";
        display: block;
        text-align: left;
        color: #8b8f9e;
        font-size: 0.95rem;
        width: 100%;
        cursor: pointer;
    }

    /* 5. Custom File Chip styling */
    [data-testid="stUploadedFile"] {
        margin: 0 !important; 
        background-color: #1a1c23 !important;
        border: 1px solid #3b3f4f !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem 1rem !important;
        width: auto !important; /* Stop it from sticking to the right */
        max-width: 70%; 
    }

    /* Hide ugly default icon and inject a modern one */
    [data-testid="stUploadedFile"] svg {
        display: none !important;
    }
    
    [data-testid="stUploadedFile"] > div:first-child::before {
        content: "∿"; /* Modern minimal wave symbol */
        color: #a8b1c4;
        font-size: 1.4rem;
        line-height: 0;
        margin-right: 12px;
        position: relative;
        top: 2px;
    }

    .stApp { background-color: #0E1117; }
    
    /* Hide text area label */
    [data-testid="stTextArea"] label { display: none !important; }
    
    /* 6. True Auto-Height for Text Area */
    .stTextArea textarea {
        font-size: 1rem;
        line-height: 1.6;
        background-color: #16181f;
        border: 1px solid #2e323e;
        border-radius: 0.5rem;
        padding: 1rem;
        field-sizing: content; /* Modern CSS: perfectly wraps the text volume */
        min-height: 64px !important; 
        color: #e2e4e9;
    }
    
    .stTextArea textarea:focus {
        border-color: #5c627a;
        box-shadow: none;
    }

    /* Button Height Synchronization */
    [data-testid="stDownloadButton"] button {
        height: 42px !important;
        min-height: 42px !important;
        line-height: 1.5 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin: 0 !important;
        background-color: #16181f;
        border: 1px solid #2e323e;
        color: #e2e4e9;
        border-radius: 0.5rem;
    }
    
    [data-testid="stDownloadButton"] button:hover {
        border-color: #5c627a;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

uploaded_file = st.file_uploader("", type=["mp3", "wav", "m4a", "flac"])

if uploaded_file:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if "last_file_id" not in st.session_state or st.session_state.last_file_id != file_id:
        st.session_state.pop("transcript", None) 
        st.session_state.last_file_id = file_id
        
        with st.spinner("Расшифровываю..."):
            try:
                transcription = client.audio.transcriptions.create(
                    file=(uploaded_file.name, uploaded_file.read()),
                    model="whisper-large-v3",
                    language="ru",
                    response_format="text"
                )
                st.session_state.transcript = transcription
                st.rerun() 
            except Exception as e:
                st.error(f"Ошибка: {e}")
                st.stop()

if "transcript" in st.session_state:
    edited_text = st.text_area("", value=st.session_state.transcript)
    
    col1, col2 = st.columns(2)
    
    with col1:
        safe_text = json.dumps(edited_text)
        
        copy_code = f"""
        <style>
        body {{ 
            margin: 0; 
            padding: 0; 
            display: flex; 
            align-items: flex-start;
            height: 100%; 
            background: transparent;
        }}
        .copy-btn {{
            width: 100%;
            background-color: #16181f;
            color: #e2e4e9;
            border: 1px solid #2e323e;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 400;
            font-family: "Source Sans Pro", sans-serif;
            font-size: 1rem;
            height: 42px;
            box-sizing: border-box;
            transition: all 0.2s ease;
            margin: 0;
        }}
        .copy-btn:hover {{
            border-color: #5c627a;
            color: #fff;
        }}
        .copy-btn.success {{
            border-color: #28a745;
            color: #28a745;
        }}
        </style>
        <button id="copyBtn" class="copy-btn" onclick="copyToClipboard()">В буфер</button>
        
        <script>
        function copyToClipboard() {{
            const text = {safe_text};
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById("copyBtn");
                btn.innerText = "✓ Скопировано";
                btn.classList.add("success");
                
                setTimeout(() => {{
                    btn.innerText = "В буфер";
                    btn.classList.remove("success");
                }}, 2000);
            }});
        }}
        </script>
        """
        components.html(copy_code, height=42)

    with col2:
        base_name = os.path.splitext(uploaded_file.name)[0]
        st.download_button(
            label="Скачать .txt", 
            data=edited_text, 
            file_name=f"{base_name}_transcript.txt",
            use_container_width=True
        )
