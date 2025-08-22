import json
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd

import file_parser
import embed_and_store
from answer_with_rag import answer
from gdrive_uploader import find_or_create_folder, upload_or_update_file

# ──────────────────────────────────
# Constants
# ──────────────────────────────────
HIST_PATH = Path("chat_history.json")
REFRESH_PATH = Path("last_refresh.txt")
UPLOAD_DIR = Path("docs")
UPLOAD_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────
# Helper Functions
# ──────────────────────────────────
def load_history():
    if HIST_PATH.exists():
        return json.loads(HIST_PATH.read_text(encoding="utf-8"))
    return []

def save_history(history):
    HIST_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

def reset_chat():
    if HIST_PATH.exists():
        HIST_PATH.unlink()

def save_refresh_time():
    REFRESH_PATH.write_text(datetime.now().strftime('%b-%d-%Y %I:%M %p'))

def load_refresh_time():
    if REFRESH_PATH.exists():
        return REFRESH_PATH.read_text()
    return "Never"

def export_history_to_csv(history: list) -> bytes:
    df = pd.DataFrame(history)
    return df.to_csv(index=False).encode('utf-8')

# ──────────────────────────────────
# Page & Sidebar
# ──────────────────────────────────
st.set_page_config(page_title="AI CEO Assistant", page_icon="🧠", layout="wide")

st.sidebar.title("🧠 AI CEO Panel")
mode = st.sidebar.radio("Navigation", ["💬 New Chat", "📜 View History", "🔁 Refresh Data"])

# ──────────────────────────────────
# Mode: Refresh Embeddings from Drive
# ──────────────────────────────────
if mode == "🔁 Refresh Data":
    st.title("🔁 Refresh AI Knowledge Base")
    st.caption("This will re-parse documents and re-embed knowledge vectors.")
    st.markdown(f"🕓 **Last Refreshed:** {load_refresh_time()}")

    if st.button("🚀 Run File Parser + Embedder"):
        with st.spinner("Refreshing knowledge base..."):
            try:
                file_parser.main()
                embed_and_store.main()
                save_refresh_time()
                st.success("✅ Data refreshed and embedded successfully.")
                st.markdown(f"🕓 **Last Refreshed:** {load_refresh_time()}")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

# ──────────────────────────────────
# Mode: View Chat History
# ──────────────────────────────────
elif mode == "📜 View History":
    st.title("📜 Chat History")
    history = load_history()

    if not history:
        st.info("No chat history found.")
    else:
        for turn in history:
            role = "👤 You" if turn.get("role") == "user" else "🧠 Assistant"
            timestamp = turn.get("timestamp", "N/A")
            st.markdown(f"**{role} | [{timestamp}]**  \n{turn.get('content', '')}")

        st.markdown("---")
        st.download_button(
            label="⬇️ Download Chat History as CSV",
            data=export_history_to_csv(history),
            file_name="chat_history.csv",
            mime="text/csv"
        )

        if st.button("🗑️ Clear Chat History"):
            reset_chat()
            st.success("History cleared.")

# ──────────────────────────────────
# Mode: New Chat Interface
# ──────────────────────────────────
elif mode == "💬 New Chat":
    st.title("🧠 AI CEO Assistant")
    st.caption("Ask about meetings, projects, hiring, finances, and research. Answers cite your documents.")
    st.markdown(f"🕓 **Last Refreshed:** {load_refresh_time()}")

    history = load_history()

    for turn in history:
        with st.chat_message(turn.get("role", "assistant")):
            st.markdown(f"**[{turn.get('timestamp', 'N/A')}]**  \n{turn.get('content', '')}")

    user_msg = st.chat_input("Type your question…")
    if user_msg:
        now = datetime.now().strftime('%b-%d-%Y %I:%M%p')
        history.append({
            "role": "user",
            "content": user_msg,
            "timestamp": now
        })

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    reply = answer(user_msg, k=7, chat_history=history)
                except Exception as e:
                    reply = f"Error: {e}"
            st.markdown(f"**[{datetime.now().strftime('%b-%d-%Y %I:%M%p')}]**  \n{reply}")

        history.append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().strftime('%b-%d-%Y %I:%M%p')
        })

        save_history(history)

        try:
            from gdrive_uploader import service  # directly use service object
            root_folder_id = find_or_create_folder(service, "AI_CEO_KnowledgeBase", parent_id=st.secrets["shared_drive_id"])
            chat_folder_id = find_or_create_folder(service, "Chat_History", parent_id=root_folder_id)
            upload_or_update_file(service, "chat_history.json", chat_folder_id)
        except Exception as e:
            st.warning(f"⚠️ Failed to upload chat history to Google Drive: {e}")

