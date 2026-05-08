import streamlit as st
from groq import Groq
import streamlit.components.v1 as components
import json
import os
import re

st.set_page_config(page_title="whisperfleet", page_icon="🎙️")

st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        display: none !important;
    }

    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 1rem !important;
        max-width: 800px; 
        z-index: 10;
    }

    /* 1. Deep Animated Aurora Background */
    .stApp { 
        background: linear-gradient(-45deg, #090a0f, #1a1525, #0d1425, #050508);
        background-size: 400% 400%;
        animation: aurora 20s ease infinite;
    }
    
    @keyframes aurora {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 2. Glassmorphism Mixin for Uploader */
    [data-testid="stFileUploader"] section button { display: none; }
    [data-testid="stFileUploader"] section div[data-testid="stMarkdownContainer"] { display: none; }
    [data-testid="stFileUploader"] small { display: none !important; }
    
    [data-testid="stFileUploader"] section { 
        padding: 1.5rem !important;
        background: rgba(20, 24, 35, 0.45) !important;
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: flex-start; 
        min-height: 80px;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(255, 255, 255, 0.2);
        background: rgba(30, 35, 50, 0.5) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4), 0 0 20px rgba(255, 255, 255, 0.05);
    }

    [data-testid="stFileUploader"] section:not(:has([data-testid="stUploadedFile"]))::before {
        content: "Drop file here or click to browse \\A0\\A0 • \\A0\\A0 mp3, wav, m4a, flac up to 25MB";
        display: block;
        text-align: left;
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.95rem;
        width: 100%;
        cursor: pointer;
        letter-spacing: 0.3px;
    }

    /* 3. Glass File Chip */
    [data-testid="stUploadedFile"] {
        margin: 0 !important; 
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1rem !important;
        width: auto !important; 
        max-width: 70%; 
        color: #fff;
    }

    [data-testid="stUploadedFile"] svg { display: none !important; }
    
    [data-testid="stUploadedFile"] > div:first-child::before {
        content: "∿"; 
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.4rem;
        line-height: 0;
        margin-right: 12px;
        position: relative;
        top: 2px;
    }

    /* 4. Glass Text Area */
    [data-testid="stTextArea"] label { display: none !important; }
    
    .stTextArea textarea {
        font-size: 1rem;
        line-height: 1.7;
        background: rgba(20, 24, 35, 0.45);
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        box-shadow: inset 0 2px 15px rgba(0, 0, 0, 0.2);
        padding: 1.25rem;
        color: rgba(255, 255, 255, 0.9);
        overflow-y: hidden !important; 
        padding-bottom: 24px !important; 
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: rgba(255, 255, 255, 0.25);
        box-shadow: inset 0 2px 15px rgba(0, 0, 0, 0.2), 0 0 15px rgba(255, 255, 255, 0.05);
    }

    /* 5. Glass Buttons (Native Download Button) */
    [data-testid="stDownloadButton"] button {
        height: 46px !important;
        min-height: 46px !important;
        line-height: 1.5 !important;
        padding: 0 !important;
        margin: 0 !important;
        
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.75rem;
        color: rgba(255, 255, 255, 0.85);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        letter-spacing: 0.5px;
        font-weight: 400;
    }
    
    [data-testid="stDownloadButton"] button:hover {
        border-color: rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.08);
        color: #fff;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
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
                    response_format="text"
                )
                st.session_state.transcript = transcription
                st.rerun() 
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

if "transcript" in st.session_state:
    text_content = st.session_state.transcript
    
    num_lines = sum((len(paragraph) // 65) + 1 for paragraph in text_content.split('\n'))
    dynamic_height = max(120, (num_lines * 28) + 40)

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
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.75rem;
            color: rgba(255, 255, 255, 0.85);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            cursor: pointer;
            font-weight: 400;
            font-family: "Source Sans Pro", sans-serif;
            font-size: 1rem;
            height: 46px;
            box-sizing: border-box;
            transition: all 0.3s ease;
            margin: 0;
            letter-spacing: 0.5px;
        }}
        .copy-btn:hover {{
            border-color: rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.08);
            color: #fff;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }}
        .copy-btn.success {{
            border-color: rgba(40, 167, 69, 0.5);
            background: rgba(40, 167, 69, 0.1);
            color: #4ade80;
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
        # Height strictly locked to 46px to match native button
        components.html(copy_code, height=46)

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
