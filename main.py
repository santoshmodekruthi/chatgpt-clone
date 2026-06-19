import streamlit as st
import sys
import traceback
import markdown
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.units import inch

from services.get_models_list import get_ollama_models_list
from services.get_title import get_chat_title
from services.chat_utilities import get_answer
from db.conversations import (
    create_new_conversation,
    add_message,
    get_conversation,
    get_all_conversations,
    rename_conversation,
    delete_conversation,
    update_message_like,
    update_message_content,
)

# ------------------- Page Config -------------------
st.set_page_config(
    page_title="Local ChatGPT Clone",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- Custom CSS -------------------
st.markdown("""
    <style>
        /* Light mode variables */
        :root {
            --bg-color: #ffffff;
            --text-color: #111827;
            --sidebar-bg: #f9fafb;
            --sidebar-hover: #e5e7eb;
            --user-bg: #f3f4f6;
            --assistant-bg: #ffffff;
            --border-color: #e5e7eb;
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
        }

        /* Dark mode variables */
        [data-theme="dark"] {
            --bg-color: #0f172a;
            --text-color: #f1f5f9;
            --sidebar-bg: #1e293b;
            --sidebar-hover: #334155;
            --user-bg: #1e293b;
            --assistant-bg: #0f172a;
            --border-color: #334155;
            --primary-color: #3b82f6;
            --primary-hover: #2563eb;
        }

        /* Global styles */
        .stApp {
            background-color: var(--bg-color);
            color: var(--text-color);
        }

        /* Sidebar styles */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
        }

        /* Chat messages */
        .chat-message {
            padding: 1rem;
            border-radius: 0.75rem;
            margin-bottom: 0.5rem;
            max-width: 85%;
        }

        .user-message {
            background-color: var(--user-bg);
            margin-left: auto;
        }

        .assistant-message {
            background-color: var(--assistant-bg);
            border: 1px solid var(--border-color);
            margin-right: auto;
        }

        /* Code block styling */
        pre {
            background-color: #1f2937;
            color: #e5e7eb;
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------- Session State Initialization -------------------
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "GROQ_MODELS" not in st.session_state:
    st.session_state.GROQ_MODELS = get_ollama_models_list()
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "conversation_title" not in st.session_state:
    st.session_state.conversation_title = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# ------------------- Theme Toggle Function -------------------
def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# ------------------- Export Functions -------------------
def export_to_txt():
    """Export current conversation to TXT file"""
    if not st.session_state.chat_history:
        st.warning("No messages to export!")
        return
    
    content = f"# Chat: {st.session_state.conversation_title or 'Untitled'}\n\n"
    for msg in st.session_state.chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        content += f"## {role}:\n{msg['content']}\n\n"
    
    buffer = BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    
    return buffer


def export_to_pdf():
    """Export current conversation to PDF file"""
    if not st.session_state.chat_history:
        st.warning("No messages to export!")
        return
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"Chat: {st.session_state.conversation_title or 'Untitled'}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.25*inch))
    
    for msg in st.session_state.chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        role_para = Paragraph(f"<b>{role}:</b>", styles['Heading3'])
        story.append(role_para)
        story.append(Spacer(1, 0.1*inch))
        
        # Handle content
        content_lines = msg['content'].split('\n')
        for line in content_lines:
            if line.startswith('    ') or line.startswith('\t'):
                pre = Preformatted(line, styles['Code'])
                story.append(pre)
            else:
                para = Paragraph(line, styles['BodyText'])
                story.append(para)
        story.append(Spacer(1, 0.2*inch))
    
    doc.build(story)
    buffer.seek(0)
    
    return buffer

# ------------------- Main UI -------------------
# Apply theme
st._config.set_option("theme.base", st.session_state.theme)

# Sidebar
with st.sidebar:
    # Header with logo and new chat button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("🤖 Local ChatGPT")
    with col2:
        if st.button("🌙" if st.session_state.theme == "light" else "☀️", help="Toggle theme"):
            toggle_theme()
            st.rerun()
    
    # New Chat button
    if st.button("➕ New Chat", type="primary", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.conversation_title = None
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    # Search
    st.text_input("🔍 Search conversations", key="search_query", placeholder="Search...")
    
    # Conversation history
    st.subheader("Recent Chats")
    conversations = get_all_conversations(st.session_state.search_query)
    
    for conv_id, conv_title in conversations.items():
        is_current = conv_id == st.session_state.conversation_id
        
        with st.container():
            if is_current:
                st.markdown(f"**{conv_title}**")
            else:
                if st.button(conv_title, key=f"conv_{conv_id}", use_container_width=True):
                    doc = get_conversation(conv_id) or {}
                    st.session_state.conversation_id = conv_id
                    st.session_state.conversation_title = doc.get("title", "Untitled")
                    st.session_state.chat_history = [
                        {"role": m["role"], "content": m["content"], "liked": m.get("liked", None)}
                        for m in doc.get("messages", [])
                    ]
                    st.rerun()
            
            # Conversation actions (rename/delete)
            if is_current:
                col_rename, col_delete = st.columns([1, 1])
                with col_rename:
                    if st.button("✏️ Rename", key=f"rename_{conv_id}", use_container_width=True):
                        new_title = st.text_input("New title", value=conv_title, key=f"new_title_{conv_id}")
                        if st.button("Save", key=f"save_{conv_id}", use_container_width=True):
                            rename_conversation(conv_id, new_title)
                            st.session_state.conversation_title = new_title
                            st.rerun()
                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_{conv_id}", use_container_width=True):
                        delete_conversation(conv_id)
                        st.session_state.conversation_id = None
                        st.session_state.conversation_title = None
                        st.session_state.chat_history = []
                        st.rerun()
    
    st.divider()
    
    # Export buttons
    st.subheader("Export")
    col_txt, col_pdf = st.columns([1, 1])
    with col_txt:
        txt_buffer = export_to_txt()
        if txt_buffer:
            st.download_button(
                "📄 TXT",
                txt_buffer,
                file_name=f"{st.session_state.conversation_title or 'chat'}.txt",
                mime="text/plain",
                use_container_width=True
            )
    with col_pdf:
        pdf_buffer = export_to_pdf()
        if pdf_buffer:
            st.download_button(
                "📕 PDF",
                pdf_buffer,
                file_name=f"{st.session_state.conversation_title or 'chat'}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    st.divider()
    
    # Footer
    st.markdown("---")
    st.markdown("Developed by Santosh Modekruthi")

# Main chat area
st.title("💬 Local ChatGPT Clone")

# Model selector
selected_model = st.selectbox(
    "Select Model",
    st.session_state.GROQ_MODELS,
    help="Choose which Groq model to use"
)
st.info(f"Current model: **{selected_model}**")

# Chat messages container
chat_container = st.container()

# Display chat history
with chat_container:
    for i, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            # Render markdown
            st.markdown(markdown.markdown(msg["content"], extensions=['fenced_code', 'tables']), unsafe_allow_html=True)
            
            # Only show actions for assistant messages
            if msg["role"] == "assistant":
                col_copy, col_regenerate, col_like, col_dislike = st.columns([1, 1, 1, 1])
                
                with col_copy:
                    if st.button("📋 Copy", key=f"copy_{i}"):
                        st.write("Content copied!")
                        st.code(msg["content"], language=None)
                
                with col_regenerate:
                    if st.button("🔄 Regenerate", key=f"regenerate_{i}") and not st.session_state.is_generating:
                        # Remove last message and regenerate
                        if i > 0 and i < len(st.session_state.chat_history):
                            st.session_state.chat_history = st.session_state.chat_history[:i]
                            if st.session_state.conversation_id:
                                doc = get_conversation(st.session_state.conversation_id)
                                if doc and len(doc["messages"]) > i:
                                    doc["messages"] = doc["messages"][:i]
                                    from db.mongo import get_collection
                                    conversations_col = get_collection("conversations")
                                    conversations_col.update_one(
                                        {"_id": st.session_state.conversation_id},
                                        {"$set": {"messages": doc["messages"]}}
                                    )
                        st.rerun()
                
                with col_like:
                    liked = msg.get("liked", None)
                    if st.button("👍" if liked else "👍", key=f"like_{i}"):
                        if st.session_state.conversation_id:
                            update_message_like(st.session_state.conversation_id, i, True if liked is None or liked is False else None)
                        st.rerun()
                
                with col_dislike:
                    liked = msg.get("liked", None)
                    if st.button("👎" if not liked and liked is not None else "👎", key=f"dislike_{i}"):
                        if st.session_state.conversation_id:
                            update_message_like(st.session_state.conversation_id, i, False if liked is None or liked is True else None)
                        st.rerun()

# Chat input
if prompt := st.chat_input("Ask AI something...", disabled=st.session_state.is_generating):
    print("\n===== New Chat Input Received =====", file=sys.stderr)
    print(f"User input: {prompt}", file=sys.stderr)
    
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(markdown.markdown(prompt), unsafe_allow_html=True)
    
    # Handle conversation
    if st.session_state.conversation_id is None:
        print("  Creating new conversation...", file=sys.stderr)
        # Create new conversation
        conv_id = create_new_conversation(title="New Chat", role="user", content=prompt)
        st.session_state.conversation_id = conv_id
        st.session_state.conversation_title = "New Chat"
        print(f"  ✅ New conversation created, ID: {conv_id}", file=sys.stderr)
        
        # Try to generate better title in background
        try:
            print("  Generating conversation title...", file=sys.stderr)
            generated_title = get_chat_title(selected_model, prompt)
            if generated_title:
                print(f"  Renaming conversation to: {generated_title.strip()}", file=sys.stderr)
                rename_conversation(conv_id, generated_title.strip())
                st.session_state.conversation_title = generated_title.strip()
        except Exception as e:
            print(f"[DEBUG] Title generation error: {e}", file=sys.stderr)
            traceback.print_exc()
    else:
        print(f"  Adding user message to existing conversation: {st.session_state.conversation_id}", file=sys.stderr)
        add_message(st.session_state.conversation_id, "user", prompt)
    
    # Generate assistant response
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            st.session_state.is_generating = True
            
            full_response = ""
            try:
                print("  Calling Groq for AI response...", file=sys.stderr)
                full_response = get_answer(selected_model, st.session_state.chat_history)
                print(f"  Received AI response, length: {len(full_response)}", file=sys.stderr)
                message_placeholder.markdown(markdown.markdown(full_response, extensions=['fenced_code', 'tables']), unsafe_allow_html=True)
            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                message_placeholder.error(error_msg)
                full_response = error_msg
                print(f"[DEBUG] Error in chat: {e}", file=sys.stderr)
                traceback.print_exc()
            
            st.session_state.is_generating = False
    
    # Add assistant message to history and DB
    print("  Adding AI response to conversation...", file=sys.stderr)
    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
    if st.session_state.conversation_id:
        add_message(st.session_state.conversation_id, "assistant", full_response)
    
    print("===== Chat Input Processing Complete =====", file=sys.stderr)
    
    # Rerun to update UI
    st.rerun()
