import os, json
import streamlit as st

from vector import store_content, DOCUMENT_FOLDER, delete_all_vectors
from agent_core import agent  # Strands Agent instance created in here

# ---------- helpers ----------
def ingest_pdf(file_bytes: bytes, filename: str):
    """
    call dimas function to store document, if user want to add on documents
    """
    os.makedirs(DOCUMENT_FOLDER, exist_ok=True)
    saved_path = os.path.join(DOCUMENT_FOLDER, filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # Dimas store_content
    numchunks = store_content(saved_path)

    # Return something simple for the UI
    paper_id = os.path.splitext(filename)[0]
    # If you want to keep "number of chunks", you can let store_content() return it, ok!
    
    return paper_id, numchunks
    

def render_sources(sources):
    """
    Render citations if search_result == LOCAL, meaning agent searched locally 
    """
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
        
        

#-------streamlit UI----------------------------

st.set_page_config(page_title="Strands Paper Assistant 🤖", layout="wide")
st.title("Strands Paper Assistant  🤖")
    
if "history" not in st.session_state:
    st.session_state.history = []
    
# ---- sidebar UI --------------------
with st.sidebar: 
    st.header("Upload & Ingest")
    pdf = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])
    title = st.text_input("Paper title (optional)")
    if pdf and st.button("Ingest"):
        with st.spinner("Indexing..."):
            # if the user enters a title, we will use that as the stored filename instead
            pid, n = ingest_pdf(pdf.read(), f"{title}.pdf" if title.strip() != "" else pdf.name)
        if n == None:
            st.error("Duplicate file, already ingested before.")
        else:
            st.success(f"Ingested `{pid}` with {n} chunks")

    st.header("Ingested Papers")
    if not os.listdir(DOCUMENT_FOLDER):
        st.info("No papers ingested yet!")
    else:
        for fn in os.listdir(DOCUMENT_FOLDER):
            if fn.lower().endswith(('.txt')):
                if st.button(f"📄 {fn}", key=fn):
                    with st.modal(fn):
                        with open(f"{DOCUMENT_FOLDER}/{fn}", "r") as f:
                            st.markdown(f.read())
                        st.button("Close")
            elif fn.lower().endswith(('.pdf')):
                if st.button(f"📄 {fn}", key=fn):
                    os.startfile(os.path.abspath(f"{DOCUMENT_FOLDER}/{fn}"))

    st.header("Created Documents")
    if not os.listdir('created_documents'):
        st.info("No created docs yet!")
    else:
        for fn in os.listdir('created_documents'):
            if fn.lower().endswith(('.md')):
                if st.button(f"📜 {fn}", key=fn):
                    with st.modal(fn):
                        with open(f"created_documents/{fn}", "r") as f:
                            st.markdown(f.read())
                        st.button("Close")
            elif fn.lower().endswith(('.pdf', '.docx')):
                if st.button(f"📄 {fn}", key=fn):
                    os.startfile(os.path.abspath(f"created_documents/{fn}"))
    
    if st.button("⚠ DELETE ALL VECTORS & FILES"):
        delete_all_vectors()
        for filename in os.listdir(DOCUMENT_FOLDER):
            file_path = os.path.join(DOCUMENT_FOLDER, filename)
            if os.path.isfile(file_path):
                print(f"Deleting file: {file_path}")
                os.remove(file_path)
        for filename in os.listdir('created_documents'):
            file_path = os.path.join('created_documents', filename)
            if os.path.isfile(file_path):
                print(f"Deleting file: {file_path}")
                os.remove(file_path)
    

#---------Main UI: Query and answer-------------------------------------------------------
query = st.text_input("Ask anything about your papers.")
col_run, col_clear = st.columns([1,1])

if col_run.button("Ask") and query:
    with st.spinner("Agent thinking..."):
        raw_result = agent(query) #call agent, agent returns an object AgentResult, but the response inside we ask for JSON already
        result = json.loads(str(raw_result))
    st.session_state.history.append((query, result))
    st.rerun()

if col_clear.button("Clear history"):
    st.session_state.history = []
    
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