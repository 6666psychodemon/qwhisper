import streamlit as st
from groq import Groq
import streamlit.components.v1 as components
import json
import os

st.set_page_config(page_title="whisperfleet", page_icon="🎙️")

st.markdown("""
    <style>
    /* Убираем гигантский отступ сверху */
    .block-container { 
        padding-top: 3rem; 
        max-width: 800px; 
    }

    /* Чистим загрузчик */
    [data-testid="stFileUploader"] section button { display: none; }
    [data-testid="stFileUploader"] section div[data-testid="stMarkdownContainer"] { display: none; }
    [data-testid="stFileUploader"] small { display: none !important; } /* Прячем дефолтный текст про 200MB */
    
    [data-testid="stFileUploader"] section { 
        padding: 0;
        background-color: transparent;
        border: 1px dashed #444;
        transition: border 0.2s ease;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: #ff4b4b;
    }

    [data-testid="stFileUploader"] section::before {
        content: "Кидай файл сюда или нажми для выбора";
        display: block;
        text-align: center;
        color: #888;
        font-size: 1rem;
        padding: 40px 20px;
        cursor: pointer;
    }

    .stApp { background-color: #0E1117; }
    
    .small-info {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 24px;
        margin-top: -10px;
    }
    
    [data-testid="stTextArea"] label { display: none !important; }
    
    .stTextArea textarea {
        font-size: 1rem;
        line-height: 1.5;
        background-color: #1a1c23;
        border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎙️ whisperfleet")
st.markdown('<p class="small-info">mp3, wav, m4a, flac до 25MB</p>', unsafe_allow_html=True)

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
    edited_text = st.text_area("", value=st.session_state.transcript, height=350)
    
    # st.columns добавляет свой gap, мы его учитываем для ровной сетки
    col1, col2 = st.columns(2)
    
    with col1:
        safe_text = json.dumps(edited_text)
        
        # Обнуляем margin у body внутри iframe и мимикрируем под стили кнопок Streamlit
        copy_code = f"""
        <style>
        body {{ 
            margin: 0; 
            padding: 0; 
            display: flex; 
            align-items: center; 
            height: 100%; 
        }}
        .copy-btn {{
            width: 100%;
            background-color: #0E1117;
            color: #fafafa;
            border: 1px solid rgba(250, 250, 250, 0.2);
            padding: 0.5rem 0.75rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 400;
            font-family: "Source Sans Pro", sans-serif;
            font-size: 1rem;
            height: 42px; /* Стандартная высота кнопки Streamlit */
            transition: all 0.2s ease;
        }}
        .copy-btn:hover {{
            border-color: #ff4b4b;
            color: #ff4b4b;
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
        # Высота 42 пикселя точно совпадает с нативной кнопкой, без лишних полей
        components.html(copy_code, height=42)

    with col2:
        base_name = os.path.splitext(uploaded_file.name)[0]
        st.download_button(
            label="Скачать .txt", 
            data=edited_text, 
            file_name=f"{base_name}_transcript.txt",
            use_container_width=True
        )
