import os, json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
from vector import store_content, DOCUMENT_FOLDER
from agent_core import agent  # Strands Agent instance created in here

st.set_page_config(page_title="Strands Paper Assistant 🤖", layout="wide")
st.title("Strands Paper Assistant")
    
if "history" not in st.session_state:
    st.session_state.history = []

# ---- sidebar to upload pdf ------
with st.sidebar:
    st.header("Upload")
    pdf = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])
    title = st.text_input("Paper title")
    if pdf and st.button("Upload"):
        os.makedirs(DOCUMENT_FOLDER, exist_ok=True)
        path = os.path.join(DOCUMENT_FOLDER, pdf.name)
        with open(path, "wb") as f:
            f.write(pdf.read())
        store_content(path)
        st.success(f"Uploaded `{os.path.splitext(pdf.name)[0]}` into local vector store.")
    
#----Render citations if found in local-----------------------------------------------
def render_sources(sources):
    if not sources: return
    st.markdown("**Sources**")
    for s in sources:
        # expected keys: paper_id, title, page
        paper_id = s.get("paper_id", "")
        title = s.get("title", "")
        page = s.get("page", "")
        meta = []
        if paper_id: meta.append(f"id: `{paper_id}`")
        if page != "": meta.append(f"p.{page}")
        meta_str = f" — {' · '.join(meta)}" if meta else ""
        st.write(f"- **{title}**{meta_str}")
        
        

#-------Call agent and pass the query----------------------------


query = st.text_input("Ask anything about your papers.")
col_run, col_clear = st.columns([1,1])

if col_run.button("Ask") and query:
    with st.spinner("Agent thinking..."):
        raw_result = agent(query) #call agent
    st.session_state.history.append((query, raw_result))

if col_clear.button("Clear history"):
    st.session_state.history = []
    
# ----Render all answers-----------------------------------------------------------------

for q, res in reversed(st.session_state.history):
    st.markdown(f"### ❓ {q}")
    
    search_res = res.get("search_result", "MODEL")
    if search_res == "LOCAL":
        st.success("✅ Found in local DB")
    else:
        st.info("ℹ️ Model's answer")
    
    st.write(res.get("answer", ""))
    
    if search_res == "LOCAL":
        render_sources(res.get("sources"))
        
    # For debugging, to trace what the agent tool call
    if res.get("tool_used"):
        with st.expander("Tool trace"):
            tools = res.get("tool_used")
            if isinstance(tools,list):
                st.write("Tools used: " + ", ".join(tools))
            else:
                st.write(str(tools))
                
    st.markdown("---")