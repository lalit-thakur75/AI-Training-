import streamlit as st
import requests
import json

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Assistant AI Playground", page_icon="🧪", layout="wide")

st.title("🧪 Multimodal Assistant Backend & AI Playground")
st.caption("Minimal developer testing interface for backend APIs, RAG, and AI features.")

# Sidebar Health Check
with st.sidebar:
    st.header("Backend Health")
    if st.button("Check /health"):
        try:
            res = requests.get(f"{BACKEND_URL}/health", timeout=3)
            st.json(res.json())
        except Exception as e:
            st.error(f"Backend offline: {e}")

tab1, tab2, tab3 = st.tabs(["💬 Chat Test", "🌐 Web Search Test", "📄 Document RAG Test"])

with tab1:
    st.subheader("Test /chat Endpoint")
    msg = st.text_input("Test Message", value="Hello, what can you do?")
    mode = st.selectbox("Mode", ["standard", "emotional", "rag"])
    search_on = st.checkbox("Web Search Enabled", value=False)
    voice_on = st.checkbox("Voice (TTS) Response", value=False)
    
    if st.button("Send to /chat"):
        payload = {
            "message": msg,
            "mode": mode,
            "search_enabled": search_on,
            "voice_response": voice_on
        }
        with st.spinner("Calling /chat..."):
            try:
                res = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
                st.write("**HTTP Status:**", res.status_code)
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.subheader("Test /search Endpoint")
    query = st.text_input("Search Query", value="latest space discoveries")
    max_res = st.slider("Max Results", 1, 10, 4)
    if st.button("Execute Search"):
        with st.spinner("Searching..."):
            try:
                res = requests.post(f"{BACKEND_URL}/search", json={"query": query, "max_results": max_res}, timeout=15)
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.subheader("Test Document Upload & Indexing")
    uploaded_file = st.file_uploader("Upload TXT, PDF, DOCX", type=["txt", "pdf", "docx"])
    if uploaded_file and st.button("Upload to Backend"):
        with st.spinner("Uploading and indexing..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                res = requests.post(f"{BACKEND_URL}/documents/upload", files=files, timeout=30)
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")
