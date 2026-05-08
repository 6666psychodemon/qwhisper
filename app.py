import streamlit as st
from groq import Groq
import streamlit.components.v1 as components
import json
import os
import re

st.set_page_config(page_title="qwhisper", page_icon="🎙️")

st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        display: none !important;
    }

    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 1rem !important;
        max-width: 800px; 
    }

    [data-testid="stFileUploader"] section button { display: none; }
    [data-testid="stFileUploader"] section div[data-testid="stMarkdownContainer"] { display: none; }
    [data-testid="stFileUploader"] small { display: none !important; }
    
    [data-testid="stFileUploader"] section { 
        padding: 1.25rem 1.5rem !important;
        background-color: #16181f; 
        border: 1px solid #2e323e;
        border-radius: 0.75rem;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: flex-start; 
        min-height: 72px;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: #5c627a;
    }

    [data-testid="stFileUploader"] section:not(:has([data-testid="stUploadedFile"]))::before {
        content: "Drop file here or click to browse \\A0\\A0 • \\A0\\A0 mp3, wav, m4a, flac up to 25MB";
        display: block;
        text-align: left;
        color: #8b8f9e;
        font-size: 0.95rem;
        width: 100%;
        cursor: pointer;
    }

    [data-testid="stUploadedFile"] {
        margin: 0 !important; 
        background-color: #1a1c23 !important;
        border: 1px solid #3b3f4f !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem 1rem !important;
        width: auto !important; 
        max-width: 70%; 
    }

    [data-testid="stUploadedFile"] svg {
        display: none !important;
    }
    
    [data-testid="stUploadedFile"] > div:first-child::before {
        content: "∿"; 
        color: #a8b1c4;
        font-size: 1.4rem;
        line-height: 0;
        margin-right: 12px;
        position: relative;
        top: 2px;
    }

    .stApp { background-color: #0E1117; }
    
    [data-testid="stTextArea"] label { display: none !important; }
    
    .stTextArea textarea {
        font-size: 1rem;
        line-height: 1.6;
        background-color: #16181f;
        border: 1px solid #2e323e;
        border-radius: 0.5rem;
        padding: 1rem;
        color: #e2e4e9;
        overflow-y: hidden !important; /* Force kills the scrollbar */
        padding-bottom: 24px !important; /* Bakes in the extra space below */
    }
    
    .stTextArea textarea:focus {
        border-color: #5c627a;
        box-shadow: none;
    }

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
        
        with st.spinner("Transcribing..."):
            try:
                transcription = client.audio.transcriptions.create(
                    file=(uploaded_file.name, uploaded_file.read()),
                    model="whisper-large-v3",
                    language="en", 
                    response_format="text"
                )
                st.session_state.transcript = transcription
                st.rerun() 
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

if "transcript" in st.session_state:
    text_content = st.session_state.transcript
    
    # Calculate lines per paragraph to account for actual line breaks
    # Assume a very conservative 65 characters per line before word wrap
    num_lines = sum((len(paragraph) // 65) + 1 for paragraph in text_content.split('\n'))
    
    # Base height per line (approx 26px) + overhead for padding
    dynamic_height = max(100, (num_lines * 26) + 40)

    edited_text = st.text_area("", value=text_content, height=dynamic_height)
    
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
        <button id="copyBtn" class="copy-btn" onclick="copyToClipboard()">Copy</button>
        
        <script>
        function copyToClipboard() {{
            const text = {safe_text};
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById("copyBtn");
                btn.innerText = "✓ Copied";
                btn.classList.add("success");
                
                setTimeout(() => {{
                    btn.innerText = "Copy";
                    btn.classList.remove("success");
                }}, 2000);
            }});
        }}
        </script>
        """
        components.html(copy_code, height=42)

    with col2:
        clean_text = re.sub(r'[^\w\s]', '', edited_text)
        words = clean_text.split()
        file_name_prefix = "-".join(words[:3]) if words else "transcript"
        
        st.download_button(
            label="Download .txt", 
            data=edited_text, 
            file_name=f"{file_name_prefix}.txt",
            use_container_width=True
        )
