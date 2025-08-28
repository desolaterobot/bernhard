import os, json
import streamlit as st
from dotenv import load_dotenv
import boto3

from vector import store_content, query_content, DOCUMENT_FOLDER
# ---------- config ----------------- 
load_dotenv()  #aws_credentials put in .env file
LLM_MODEL = os.getenv("BEDROCK_LLM_MODEL")
brt = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))

# ---------- helpers ----------
def ingest_pdf(file_bytes: bytes, filename: str, title: str | None = None):
    """
    call dimas function to store document, if user want to add on documents
    """
    os.makedirs(DOCUMENT_FOLDER, exist_ok=True)
    saved_path = os.path.join(DOCUMENT_FOLDER, filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # Dimas store_content
    store_content(saved_path)

    # Return something simple for the UI
    paper_id = os.path.splitext(filename)[0]
    # If you want to keep "number of chunks", you can let store_content() return it,
    
    return paper_id, 0


def keyword_boost(query: str, text: str):
    """
    Not sure what this for,  apparently adds a small boost when query words appear in a chunk 
    For re-ranking
    """
    q = {w.lower() for w in query.split() if len(w) > 2}
    t = {w.lower() for w in text.split()}
    return len(q & t)


def search(query: str, k=5):
    """
    Retrieval search call dimas query_content(query, N=5)
    """
    try:
        results_list = query_content(query, N=k)  # returns a list of dicts
        # Expected keys
        # 'Source', 'Page', 'Chunk', 'Distance', 'Content'
    except Exception as e:
        return [], {"sim_mean": 0.0}

    hits = []
    for result in results_list:
        filename = result.get("Source", "")
        paper_id = os.path.splitext(os.path.basename(filename))[0]
        page = result.get("Page")
        chunk = result.get("Chunk")
        text = result.get("Content", "")
        dist = float(result.get("Distance", 1.0))
        sim = 1.0 - dist  # similarity score

        hit = {
            "id": f"{paper_id}:{page}:{chunk}",
            "text": text,
            "meta": {
                "paper_id": paper_id,
                "title": filename,
                "page": page,
            },
            "sim": sim,
        }
        hit["kw"] = keyword_boost(query, text) 
        hit["fused"] = hit["sim"] + 0.05 * hit["kw"] # I added keyword boost, fused is the overall score
        hits.append(hit)

    hits.sort(key=lambda x: x["fused"], reverse=True)
    hits_list = hits[:k]
    sim_mean = sum(hit["sim"] for hit in hits_list)/len(hits_list) if hits_list else 0.0
    return hits_list, {"sim_mean": sim_mean}  # Currently use mean as stats for LLM to decide whether DB is good enough?


def rag_prompt(query: str, chunks: list[dict]):
    """
    Build the rag prompt before calling Claude 
    """
    context = "\n\n".join(
      [f"[paper_id:{c['meta']['paper_id']} title:{c['meta']['title']} page:{c['meta']['page']} chunk_id:{c['id']}]\n{c['text']}"
       for c in chunks]
    )
    
    #this the full prompt with query and context to send the LLM
    return ( 
      "You are a research paper assistant.\n"
      "Use ONLY the CONTEXT. If missing, write 'insufficient_context'. "
      "Return VALID JSON exactly matching:\n"
      "{ \"mode\":\"RAG\", \"tldr\":\"...\", \"answer\":\"...\",\n"
      "  \"bullets\":[{\"text\":\"...\",\"cite\":{\"paper_id\":\"...\",\"page\":1,\"chunk_id\":\"...\"}}],\n"
      "  \"sources\":[{\"paper_id\":\"...\",\"title\":\"...\",\"pages\":[1,2]}] }\n\n"
      f"QUESTION:\n{query}\n\nCONTEXT:\n{context}"
    )

def open_prompt(query: str):
    """
    If database cannot find
    """
    return (
      "Return JSON: {\"mode\":\"OPEN\",\"answer\":\"short general explanation\",\"disclaimer\":\"This answer is not grounded in your database.\"}\n\n"
      f"QUESTION:\n{query}"
    )

def bedrock_generate(prompt: str, max_tokens=1100):
    """
    Should call Claude using API, not tested yet dk if it works
    """
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role":"user","content":[{"type":"text","text":prompt}]}],
        "temperature": 0 #not sure this one how
    }
    resp = brt.invoke_model(modelId=LLM_MODEL, body=json.dumps(body))
    data = json.loads(resp["body"].read())
    # extract text from Claude, model will consume the json and return data
    pieces = data["output"]["message"]["content"]
    return "".join([p.get("text","") for p in pieces])

def route_and_answer(query: str, debug: bool = False):
    """
    From user query: 
        if debug mode will format the search data
        if rag mode will check sim score first
    """
    hits_list, stats = search(query, k=5)
    sim_mean = stats["sim_mean"]
    is_background = any(w in query.lower() for w in ["what is", "explain", "overview", "definition"])

    # If debug: always show what retrieval from database produced; skip Bedrock calls
    if debug:
        data = dry_run_response(query, hits_list)
        data["stats"] = stats | {"debug": True}
        data["retrieved"] = [
            {   
                "id": hit["id"], "sim": round(hit["sim"], 4), "kw": hit["kw"],
                "paper_id": hit["meta"].get("paper_id"),
                "title": hit["meta"].get("title"),
                "page": hit["meta"].get("page"),
                "preview": hit["text"][:600].replace("\n", " ") #preview will show part of the text
            } for hit in hits_list
        ]
        return data

    # normal routing below, tweak thresholds here
    if sim_mean >= 0.32 and len(hits_list) >= 3:
        raw = bedrock_generate(rag_prompt(query, hits_list[:6]))
        try:
            data = json.loads(raw)
        except Exception:
            data = {"mode":"RAG","answer":raw}
        data["stats"] = stats
        return data

    if is_background:
        raw = bedrock_generate(open_prompt(query))
        try:
            data = json.loads(raw)
        except Exception:
            data = {"mode":"OPEN","answer":raw,"disclaimer":"Not grounded."}
        data["stats"] = stats
        return data

    return {"mode":"ABSTAIN","reason":"No sufficient evidence found in your local library.","stats":stats}


def dry_run_response(query: str, hits_list: list[dict]):
    """
    Return a mock JSON payload shaped like the real RAG response, without model calls.
    Its just to show how the answer should look, i just pass back with RAG Mode
    
    So 'bullets' and 'sources' is fake
    """
    bullets = []
    sources_map = {}
    for hit in hits_list[:6]:
        meta = hit["meta"]
        bullets.append({
            "text": f"(debug) Relevant snippet from p.{meta.get('page')} of {meta.get('title')}",
            "cite": {
                "paper_id": meta.get("paper_id"),
                "page": meta.get("page"),
                "chunk_id": hit["id"]
            }
        })
        pid = meta.get("paper_id")
        sources_map.setdefault(pid, {"paper_id": pid, "title": meta.get("title"), "pages": set()})
        sources_map[pid]["pages"].add(meta.get("page"))

    sources = []
    for s in sources_map.values():
        s["pages"] = sorted(list(s["pages"]))
        sources.append(s)

    return {
        "mode": "RAG", 
        "tldr": "(debug) Skipping model call. Showing retrieval results only.",
        "answer": "(debug-disclaimer) This is a dry-run. No Bedrock tokens used.",
        "bullets": bullets,
        "sources": sources
    }


# ---------- streamlit UI ---------------------------------------
st.set_page_config(page_title="RAG Paper Assistant", page_icon="📚", layout="wide")
st.title("📚 RAG Paper Assistant")

#--Sidebar to upload a new file to add into database--------------------
# maybe can use it as a in case you want to specifically summarise a file 
with st.sidebar: 
    st.header("Upload & Ingest")
    pdf = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])
    title = st.text_input("Paper title (optional)")
    if pdf and st.button("Ingest"):
        with st.spinner("Indexing..."):
            pid, n = ingest_pdf(pdf.read(), pdf.name, title or pdf.name)
        st.success(f"Ingested `{pid}` with {n} chunks")
    st.markdown("---")  
    st.caption("All vectors of PDF and txt files are stored locally in ChromaDB.")
    st.markdown("---")
    DEBUG = st.checkbox("🔍 Debug / Dry-run (skip LLM call)", value=True)
    SHOW_PROMPT = st.checkbox("Show prompt/context preview", value=False)


if "history" not in st.session_state:
    st.session_state.history = []

#--Query------------------------------------------------------------
query = st.text_input("Ask a question (e.g., 'Summarize contributions and results of <paper>')")

col_run, col_clear = st.columns([1,1])
if col_run.button("Ask") and query:
    with st.spinner("Thinking..."):
        res = route_and_answer(query, debug=DEBUG)
    st.session_state.history.append((query, res))

if col_clear.button("Clear history"):
    st.session_state.history = []

#--Render history--------------------------------------- 
for q, res in reversed(st.session_state.history):
    st.markdown(f"### ❓ {q}")
    badge = {"RAG":"✅ Grounded","OPEN":"ℹ️ Open (not grounded)","ABSTAIN":"⚠️ No answer"}
    st.markdown(f"**Mode:** {badge.get(res.get('mode','?'))}")
    stats = res.get("stats", {})
    st.caption(f"sim_mean={stats.get('sim_mean',0):.3f}")

#---Populate base on what the LLM return------------------
    if res.get("mode") == "RAG":
        if res.get("tldr"): st.success(f"TLDR: {res['tldr']}")
        if res.get("answer"): st.write(f"Answer: {res['answer']}")
        st.markdown("**Bulletpoints**")
        for b in res.get("bullets", []):
            cite = b.get("cite", {})
            st.markdown(
                f"- {b.get('text','')}\n  "
                f"<sub>📄 {cite.get('paper_id','?')} · p.{cite.get('page','?')} · {cite.get('chunk_id','?')}</sub>",
                unsafe_allow_html=True
            )
        st.markdown("**Sources**")
        for s in res.get("sources", []):
            pages = ", ".join(map(str, s.get("pages", []))) if s.get("pages") else "—"
            st.write(f"- **{s.get('title','')}** (id: {s.get('paper_id','')}) — pages {pages}")

    elif res.get("mode") == "OPEN":
        st.info(res.get("disclaimer","This answer is not grounded in your library."))
        st.write(res.get("answer",""))
    else:
        st.warning(res.get("reason",""))
    st.markdown("---")

    #------Debug mode extra UI------------------------------------------------------------------
    if res.get("stats", {}).get("debug"):
        with st.expander("🔎 Top matches from DB search (DEBUG)", expanded=True):
            for i, h in enumerate(res.get("retrieved", []), start=1):
                st.markdown(
                    f"{i}. **{h['title']}** (id: `{h['paper_id']}`) — "
                    f"p.{h['page']}  "
                    f"· sim={h['sim']} · kw={h['kw']}"
                )
                st.caption(h["preview"])

        if SHOW_PROMPT:
            # The prompt that was built, what we sent to the model
            hits_for_prompt = res.get("retrieved", [])[:6]
            context_preview = "\n\n".join(
                [f"[paper_id:{h['paper_id']} title:{h['title']} page:{h['page']} chunk_id:{h['id']}]\n"
                f"{h['preview']}…" for h in hits_for_prompt]
            )
            with st.expander("🧾 Context to be sent to LLM"):
                st.text(context_preview)
