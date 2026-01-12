import streamlit as st
from streamlit_option_menu import option_menu
from pypdf import PdfReader, PdfWriter
import pdfplumber
import ollama
import io
import zipfile
import base64
import time
import random
import re
import json
import pandas as pd
import fitz  # PyMuPDF
import difflib
import os
import subprocess
import spacy
import numpy as np
from pptx import Presentation
from pptx.util import Inches, Pt
from streamlit_agraph import agraph, Node, Edge, Config
from streamlit_timeline import timeline
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from docx import Document
from pdf2docx import Converter as DocxConverter

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Journey Through Pages", layout="wide", page_icon="📜")

# --- 2. ETHEREAL UI ARCHITECTURE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background: radial-gradient(circle at 10% 20%, rgb(242, 246, 255) 0%, rgb(219, 234, 254) 90%); font-family: 'Inter', sans-serif; }
    @keyframes fadeInUp { from { opacity: 0; transform: translate3d(0, 20px, 0); } to { opacity: 1; transform: translate3d(0, 0, 0); } }
    @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
    .animate-enter { animation: fadeInUp 0.6s ease-out; }
    .glass-card { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.5); box-shadow: 0 10px 40px -10px rgba(0,0,0,0.05); border-radius: 24px; padding: 30px; margin-bottom: 25px; transition: all 0.3s; }
    .glass-card:hover { transform: translateY(-5px) scale(1.01); box-shadow: 0 20px 50px -10px rgba(37, 99, 235, 0.15); border: 1px solid rgba(37, 99, 235, 0.2); }
    h1 { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; letter-spacing: -1px; text-align: center; padding-bottom: 10px; }
    .quote-box { text-align: center; font-size: 1.1rem; font-style: italic; color: #64748b; margin-bottom: 40px; padding: 15px; border-left: 4px solid #3b82f6; background: rgba(255,255,255,0.5); border-radius: 0 12px 12px 0; }
    div.stButton > button { background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%); color: white; border: none; border-radius: 12px; padding: 0.75rem 1.5rem; font-weight: 600; transition: all 0.2s; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); width: 100%; }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 15px -3px rgba(37, 99, 235, 0.4); }
    .skeleton-box { height: 100px; width: 100%; background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%); background-size: 200% 100%; border-radius: 12px; animation: pulse 1.5s infinite; margin-bottom: 15px; }
    .confidence-badge { display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px); text-align: center; padding: 15px; border-top: 1px solid rgba(255,255,255,0.3); color: #64748b; font-size: 0.85rem; font-weight: 500; z-index: 999; }
    .book-item { padding: 12px; background: rgba(255,255,255,0.8); border-radius: 12px; margin-bottom: 8px; border-left: 4px solid #3b82f6; font-size: 0.9rem; color: #1e293b; display: flex; justify-content: space-between; align-items: center; transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .book-item:hover { transform: translateX(5px); }
    .diff-add { background-color: #dcfce7; color: #166534; padding: 8px; border-radius: 8px; margin: 4px 0; border-left: 4px solid #22c55e; }
    .diff-rem { background-color: #fee2e2; color: #991b1b; padding: 8px; border-radius: 8px; margin: 4px 0; border-left: 4px solid #ef4444; }

    /* === HOME PAGE GRID FIX === */
.home-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  margin-bottom: 40px;
}

.home-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 340px;
}

.home-card.large {
  min-height: 420px;
}

.card-footer {
  margin-top: auto;
}

.card-btn {
  width: 100%;
  padding: 12px;
  margin-top: 20px;x
  border-radius: 14px;
  border: none;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.35);
}

.card-btn:hover {
  transform: translateY(-2px);
}

</style>
""", unsafe_allow_html=True)

# --- 3. UI HELPER COMPONENTS ---
def ui_spacer(height=20): st.markdown(f"<div style='height: {height}px;'></div>", unsafe_allow_html=True)
def ui_skeleton(): return st.empty().markdown("""<div class="skeleton-box" style="height: 20px; width: 40%;"></div><div class="skeleton-box" style="height: 120px;"></div><div class="skeleton-box" style="height: 120px;"></div>""", unsafe_allow_html=True)
def ui_confidence_badge(score="High"):
    c = {"High": "#dcfce7", "Medium": "#fef9c3", "Low": "#fee2e2"}
    st.markdown(f"<div class='confidence-badge' style='background-color: {c.get(score)}; color: #374151;'>⚡ AI Confidence: {score}</div>", unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'page_selection' not in st.session_state: st.session_state.page_selection = 0 
if 'highlights' not in st.session_state: st.session_state.highlights = []
if 'preview_pdf_bytes' not in st.session_state: st.session_state.preview_pdf_bytes = None
if 'bookshelf' not in st.session_state: st.session_state.bookshelf = []

def set_page(index): st.session_state.page_selection = index

# --- 5. BOOKSHELF LOGIC ---
def add_to_bookshelf(filename, file_bytes):
    for book in st.session_state.bookshelf:
        if book['name'] == filename: return 
    st.session_state.bookshelf.insert(0, {'name': filename, 'data': file_bytes}) 
    if len(st.session_state.bookshelf) > 5: st.session_state.bookshelf.pop()

def get_file_from_shelf(filename):
    for book in st.session_state.bookshelf:
        if book['name'] == filename: return io.BytesIO(book['data'])
    return None

def remove_from_shelf(filename):
    st.session_state.bookshelf = [b for b in st.session_state.bookshelf if b['name'] != filename]

# --- 6. CORE FUNCTIONS ---
def get_daily_quote():
    return random.choice(["“Data is the new oil.” — Clive Humby", "“Simplicity is the ultimate sophistication.” — Leonardo da Vinci", "“Technology is best when it brings people together.” — Matt Mullenweg", "“The best way to predict the future is to invent it.” — Alan Kay"])

def extract_text_with_references(file):
    pages_data = []
    with pdfplumber.open(file) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text: pages_data.append({"page": i + 1, "text": text})
    return pages_data

def text_to_audio_mac(text):
    output_file = "podcast.wav"
    safe_text = text.replace('"', '').replace("'", "").replace("\n", " ")[:5000]
    try:
        subprocess.run(["say", "-o", output_file, "--data-format=LEI16@44100", safe_text], check=True)
        if os.path.exists(output_file):
            with open(output_file, "rb") as f: return f.read()
    except: return None

# --- ML FUNCTIONS ---
def extract_timeline_data(text):
    prompt = f"Extract key events. Return STRICT JSON: {{'events': [{{'start_date': {{'year': 'YYYY', 'month': 'MM', 'day': 'DD'}}, 'text': {{'headline': 'Title', 'text': 'Desc'}}}}]}}. Text: {text[:4000]}"
    try:
        res = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        match = re.search(r'\{.*\}', res['message']['content'], re.DOTALL)
        return json.loads(match.group()) if match else None
    except: return None

def generate_ppt_from_text(text):
    prompt = f"Create 5-slide PPT. Format: TITLE: [T]\nCONTENT: [B1, B2]. Text: {text[:4000]}"
    try:
        res = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        prs = Presentation(); prs.slides.add_slide(prs.slide_layouts[0]).shapes.title.text = "Generated Presentation"
        for t, c in re.findall(r'TITLE: (.*?)\nCONTENT: (.*?)(?=\nTITLE:|$)', res['message']['content'], re.DOTALL):
            s = prs.slides.add_slide(prs.slide_layouts[1]); s.shapes.title.text = t.strip()
            tf = s.shapes.placeholders[1].text_frame
            for b in c.split(','): tf.add_paragraph().text = b.strip()
        out = io.BytesIO(); prs.save(out); return out
    except: return None

def get_embedding(text):
    try: return ollama.embeddings(model='llama3.2', prompt=text)["embedding"]
    except: return []

def semantic_search_pdf(file_bytes, query):
    doc = fitz.open(stream=file_bytes, filetype="pdf"); qv = get_embedding(query)
    if not qv: return None, 0
    best_score = -1; best_page = None; best_sent = None
    for p in doc:
        for s in p.get_text().replace('\n',' ').split('. '):
            if len(s) > 20:
                v = get_embedding(s)
                if v:
                    score = np.dot(qv, v) / (np.linalg.norm(qv) * np.linalg.norm(v))
                    if score > best_score: best_score = score; best_sent = s; best_page = p
    if best_score > 0.35 and best_page:
        for i in best_page.search_for(best_sent[:50]): best_page.add_highlight_annot(i).set_colors(stroke=(0,1,0)); best_page.add_highlight_annot(i).update()
    out = io.BytesIO(); doc.save(out); return out, best_score

def run_audit(text):
    try: return ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Audit Risk Score 0-100. 3 Risks. Format: SCORE: X. RISKS: -. Text: {text[:4000]}"}])['message']['content']
    except: return "Audit Failed."

def analyze_contradictions(text):
    try: return ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Find contradictions. Text: {text[:4000]}"}])['message']['content']
    except: return "Analysis Failed."

def extract_ledger_data(text):
    try:
        res = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Extract invoice JSON: {{'vendor': '', 'total': '', 'items': []}}. Text: {text[:3000]}"}])
        match = re.search(r'\{.*\}', res['message']['content'], re.DOTALL)
        return json.loads(match.group()) if match else None
    except: return None

def generate_flashcards(text):
    try:
        res = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"5 Flashcards 'Term|Definition'. No headers. Text: {text[:3000]}"}])
        return [{'Question': l.split('|')[0], 'Answer': l.split('|')[1]} for l in res['message']['content'].split('\n') if '|' in l]
    except: return []

# --- STANDARD UTILS ---
# MISSING FUNCTIONS RESTORED BELOW
def apply_redaction(file_bytes, search_text):
    doc = fitz.open(stream=file_bytes, filetype="pdf"); count = 0
    for page in doc:
        for inst in page.search_for(search_text): page.add_redact_annot(inst, fill=(0, 0, 0)); page.apply_redactions(); count += 1
    out = io.BytesIO(); doc.save(out); doc.close(); return out, count

def apply_highlights_to_pdf(file_bytes, highlights_list):
    doc = fitz.open(stream=file_bytes, filetype="pdf"); 
    for h in highlights_list:
        for page in doc:
            for inst in page.search_for(h['text']): page.add_highlight_annot(inst).update()
    out = io.BytesIO(); doc.save(out); doc.close(); return out, []

def detect_pii(text):
    return list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text) + re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)))

def df_to_pdf(df):
    buffer = io.BytesIO(); doc = SimpleDocTemplate(buffer, pagesize=letter); elements = []
    data = [df.columns.to_list()] + df.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('BOTTOMPADDING',(0,0),(-1,0),12),('BACKGROUND',(0,1),(-1,-1),colors.beige),('GRID',(0,0),(-1,-1),1,colors.black)]))
    elements.append(table); doc.build(elements); return buffer

def pdf_to_docx(f):
    out = io.BytesIO(); open("t.pdf", "wb").write(f.getvalue())
    cv = DocxConverter("t.pdf"); cv.convert("t.docx"); cv.close()
    out.write(open("t.docx", "rb").read()); return out

def images_to_pdf(imgs):
    out = io.BytesIO(); i1 = Image.open(imgs[0]).convert('RGB'); i1.save(out, save_all=True, append_images=[Image.open(i).convert('RGB') for i in imgs[1:]], format='PDF'); return out

def word_to_pdf(d):
    doc = Document(d); out = io.BytesIO(); c = canvas.Canvas(out, pagesize=letter); t = c.beginText(40, 750); t.setFont("Helvetica", 12)
    for p in doc.paragraphs: t.textLine(p.text[:90]); c.drawText(t) if t.getY() > 40 else (c.showPage(), t.setTextOrigin(40, 750))
    c.save(); return out

def split_pdf(file):
    r = PdfReader(file); z = io.BytesIO()
    with zipfile.ZipFile(z, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for i, p in enumerate(r.pages):
            w = PdfWriter(); w.add_page(p); b = io.BytesIO(); w.write(b); zf.writestr(f"p_{i+1}.pdf", b.getvalue())
    return z

def merge_pdfs(files):
    w = PdfWriter(); [w.add_page(p) for f in files for p in PdfReader(f).pages]; out = io.BytesIO(); w.write(out); return out

def compress_pdf(file):
    doc = fitz.open(stream=file.getvalue(), filetype="pdf"); out = io.BytesIO(); doc.save(out, deflate=True, garbage=4); return out

def add_watermark(file, text):
    packet = io.BytesIO(); c = canvas.Canvas(packet, pagesize=letter); c.setFont("Helvetica", 50); c.setFillColorRGB(0.5,0.5,0.5,0.3); c.translate(300,400); c.rotate(45); c.drawCentredString(0,0,text); c.save(); packet.seek(0)
    wm = PdfReader(packet).pages[0]; r = PdfReader(file); w = PdfWriter()
    for p in r.pages: p.merge_page(wm); w.add_page(p)
    out = io.BytesIO(); w.write(out); return out

def rotate_pdf(file, angle):
    r = PdfReader(file); w = PdfWriter()
    for p in r.pages: p.rotate(angle); w.add_page(p)
    out = io.BytesIO(); w.write(out); return out

def delete_page(file, p_num):
    r = PdfReader(file); w = PdfWriter()
    for i, p in enumerate(r.pages):
        if i != (p_num-1): w.add_page(p)
    out = io.BytesIO(); w.write(out); return out

def run_ml_pipeline(text):
    try: doc_type = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Classify into [Resume, Contract, Invoice, Report]. Only name. Text: {text[:1000]}"}])['message']['content'].strip()
    except: doc_type = "Document"
    try: summary = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"3-sentence summary. Text: {text[:4000]}"}])['message']['content']
    except: summary = "Unavailable."
    try: insights = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Extract key points. Bullets. Text: {text[:4000]}"}])['message']['content']
    except: insights = "Unavailable."
    return doc_type, summary, insights

def chat_with_bookshelf(query, bookshelf):
    context = ""
    for book in bookshelf[:3]:
        try:
            with pdfplumber.open(io.BytesIO(book['data'])) as pdf:
                context += f"\n--- {book['name']} ---\n{''.join([p.extract_text() or '' for p in pdf.pages])[:2000]}..."
        except: pass
    try: return ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Context: {context}\nQ: {query}"}])['message']['content']
    except: return "Error."

def pdf_page_to_image(file_bytes, page_num=0):
    doc = fitz.open(stream=file_bytes, filetype="pdf"); page = doc.load_page(page_num); return page.get_pixmap().tobytes("png")

def analyze_image_with_vision(image_bytes):
    try: return ollama.chat(model='llama3.2-vision', messages=[{'role': 'user', 'content': 'Describe this image.', 'images': [image_bytes]}])['message']['content']
    except: return "Vision Model Missing."

def compare_pdfs_enhanced(text1, text2):
    diff = list(difflib.Differ().compare(text1.splitlines(), text2.splitlines()))
    structured = []; raw = []
    for l in diff:
        if l.startswith('+ '): structured.append(('add', l[2:])); raw.append(f"ADDED: {l[2:]}")
        elif l.startswith('- '): structured.append(('rem', l[2:])); raw.append(f"REMOVED: {l[2:]}")
    return structured, "\n".join(raw)

# --- 7. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9912/9912328.png", width=30)
    st.markdown("## Journey Through Pages")
    st.caption("v1.2 Stable")
    ui_spacer(10)
    
    selected = option_menu(menu_title=None, options=["Home", "Viewer", "Converter", "Editor", "AI Analyst", "Compare"], 
        icons=["house", "eye", "arrow-repeat", "tools", "stars", "arrow-left-right"], 
        default_index=st.session_state.page_selection, manual_select=st.session_state.page_selection,
        styles={"nav-link-selected": {"background-color": "#2563eb", "color": "white"}})
    
    st.divider()
    with st.expander("📚 Active Bookshelf", expanded=True):
        if st.session_state.bookshelf:
            for i, b in enumerate(st.session_state.bookshelf):
                c1, c2 = st.columns([4, 1])
                with c1: st.markdown(f"<div class='book-item'>📄 {b['name'][:15]}...</div>", unsafe_allow_html=True)
                with c2: 
                    if st.button("✖", key=f"d_{i}"): remove_from_shelf(b['name']); st.rerun()
        else: st.caption("Library is empty.")

# --- 8. PAGE LOGIC (WITH ANIMATIONS) ---
st.markdown("<div class='animate-enter'>", unsafe_allow_html=True)

if selected == "Home":
    # --- HERO ---
    st.markdown(
        f"""
        <h1>Journey Through Pages</h1>
        <div class='quote-box'>{get_daily_quote()}</div>
        """,
        unsafe_allow_html=True
    )

    ui_spacer(30)

    # --- FEATURE CARDS ---
    r1c1, r1c2, r1c3 = st.columns(3)

    # 👀 VIEWER
    with r1c1:
        st.markdown("""
        <div class="glass-card">
            <h3>👀 Viewer</h3>
            <ul>
                <li>Highlight Text</li>
                <li>Redaction</li>
                <li>PII Detection & Shield</li>
                <li>Semantic Search</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Viewer"):
            set_page(1)
            st.rerun()

    # 🔄 CONVERTER
    with r1c2:
        st.markdown("""
        <div class="glass-card">
            <h3>🔄 Converter</h3>
            <ul>
                <li>Images → PDF</li>
                <li>Word → PDF</li>
                <li>PDF → Word</li>
                <li>PDF → Excel</li>
                <li>CSV / Excel → PDF</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Converter"):
            set_page(2)
            st.rerun()

    # ✂️ EDITOR
    with r1c3:
        st.markdown("""
        <div class="glass-card">
            <h3>✂️ Editor</h3>
            <ul>
                <li>Split PDF</li>
                <li>Merge PDFs</li>
                <li>Compress PDF</li>
                <li>Add Watermark</li>
                <li>Rotate Pages</li>
                <li>Delete Pages</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Editor"):
            set_page(3)
            st.rerun()

    ui_spacer(30)

    # --- AI ANALYST FEATURES ---
    r2c1, r2c2 = st.columns([2, 1])

    with r2c1:
        st.markdown("""
        <div class="glass-card">
            <h3>🧠 AI Analyst</h3>
            <ul>
                <li>AI Summary</li>
                <li>Vision Analysis (Image PDFs)</li>
                <li>Flashcards Generator</li>
                <li>Knowledge Graph</li>
                <li>Audit & Risk Analysis</li>
                <li>Ledger / Invoice Extraction</li>
                <li>Chronos – Timeline Builder</li>
                <li>Contradiction Detection</li>
                <li>Document Comparison</li>
                <li>Slide / Deck Generator</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open AI Analyst"):
            set_page(4)
            st.rerun()

    # 📚 BOOKSHELF
    with r2c2:
        st.markdown("""
        <div class="glass-card">
            <h3>📚 Book Shelf</h3>
            <p>
                Your recently accessed documents are stored securely
                for cross-document intelligence and omniscient AI queries.
            </p>
            <ul>
                <li>Auto-saved PDFs</li>
                <li>Cross-document chat</li>
                <li>Quick re-access</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    ui_spacer(40)

    st.caption("⚡ One platform. Every document. Infinite intelligence.")

elif selected == "Viewer":
    st.markdown("<h1>👀 Ethereal Viewer</h1>", unsafe_allow_html=True)
    c_tools, c_view = st.columns([1, 3])
    with c_tools:
        bk = [b['name'] for b in st.session_state.bookshelf]
        sel = st.selectbox("Library", ["None"] + bk)
        up = st.file_uploader("Upload", type="pdf")
        
        target = None; name = None
        if up: target = up.getvalue(); name = up.name
        elif sel != "None": target = get_file_from_shelf(sel).getvalue(); name = sel
        
        if target:
            if "curr_view" not in st.session_state or st.session_state.curr_view != name:
                st.session_state.curr_view = name; st.session_state.highlights = []; st.session_state.view_bytes = target; st.session_state.orig_bytes = target; add_to_bookshelf(name, target)
            
            ui_spacer(10)
            t1, t2, t3, t4 = st.tabs(["Highlight", "Redact", "Shield", "Search"])
            
            with t1:
                hl = st.text_input("Text to Mark")
                if st.button("Highlight"):
                    st.session_state.highlights.append({'text': hl})
                    res, _ = apply_highlights_to_pdf(st.session_state.orig_bytes, st.session_state.highlights)
                    st.session_state.view_bytes = res.getvalue(); st.rerun()
                if st.button("Reset View"): st.session_state.highlights = []; st.session_state.view_bytes = st.session_state.orig_bytes; st.rerun()
            with t2:
                rd = st.text_input("Blackout Text")
                if st.button("Apply Redaction"):
                    res, c = apply_redaction(st.session_state.view_bytes, rd)
                    st.session_state.view_bytes = res.getvalue(); st.session_state.orig_bytes = res.getvalue(); st.success(f"Redacted {c}."); st.rerun()
            with t3:
                if st.button("🛡️ Scan & Redact"):
                    txt = extract_text_with_references(io.BytesIO(st.session_state.view_bytes)); ft = " ".join([p['text'] for p in txt])
                    pii = detect_pii(ft)
                    if pii:
                        tb = st.session_state.view_bytes; tot = 0
                        for i in pii: rb, c = apply_redaction(tb, i); tb = rb.getvalue(); tot += c
                        st.session_state.view_bytes = tb; st.session_state.orig_bytes = tb; st.success(f"Redacted {tot} items."); st.rerun()
                    else: st.success("No PII found.")
            with t4:
                sq = st.text_input("Semantic Query")
                if st.button("🧠 Deep Search"):
                    sk = ui_skeleton()
                    res, sc = semantic_search_pdf(st.session_state.view_bytes, sq)
                    sk.empty()
                    if res and sc > 0.3: 
                        st.session_state.view_bytes = res.getvalue(); ui_confidence_badge("High"); st.rerun()
                    else: st.error("No matches found.")
            
            ui_spacer(20)
            st.download_button("💾 Save PDF", st.session_state.view_bytes, "doc.pdf", "application/pdf")

    with c_view:
        if target:
            b64 = base64.b64encode(st.session_state.view_bytes).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}#t={time.time()}" width="100%" height="800" style="border-radius:15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);"></iframe>', unsafe_allow_html=True)

elif selected == "AI Analyst":
    st.markdown("<h1>🧠 The AI Analyst</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📄 Text", "👁️ Vision", "🎓 Study", "🕸️ Graph", "⚖️ Auditor", "🎞️ Deck", "📊 Ledger", "⏳ Chronos", "🕵️ Truth"])
    
    with tabs[0]:
        up = st.file_uploader("Upload Document", type="pdf", key="ai")
        if up:
            if "curr_ai" not in st.session_state or st.session_state.curr_ai != up.name:
                st.session_state.curr_ai = up.name; sk = ui_skeleton()
                pgs = extract_text_with_references(up)
                ft = "\n".join([p['text'] for p in pgs])
                dt, sm, ins = run_ml_pipeline(ft)
                st.session_state.dt = dt; st.session_state.sm = sm; st.session_state.ins = ins; st.session_state.ft = ft
                sk.empty(); st.rerun()
            
            st.write(f"**Type:** {st.session_state.dt}")
            st.info(st.session_state.sm)
            if st.button("🎧 Generate Podcast"):
                with st.spinner("Recording..."):
                    ad = text_to_audio_mac(st.session_state.ft[:1000]) # Shorten for demo
                    if ad: st.audio(ad, format="audio/wav")
            
            st.divider()
            use_shelf = st.checkbox("📚 Omniscient Mode (All Docs)")
            if p := st.chat_input("Ask..."):
                if use_shelf:
                    sk = ui_skeleton(); ans = chat_with_bookshelf(p, st.session_state.bookshelf); sk.empty(); st.write(f"**AI:** {ans}")
                else:
                    sk = ui_skeleton(); res = ollama.chat(model='llama3.2', messages=[{'role':'user','content':f"Context: {st.session_state.ft[:10000]} Q: {p}"}]); sk.empty()
                    st.write(f"**AI:** {res['message']['content']}")

    with tabs[1]:
        v_up = st.file_uploader("Upload Image PDF", type="pdf", key="vis")
        if v_up:
            img = pdf_page_to_image(v_up.getvalue(), 0); st.image(img, width=400)
            if st.button("Analyze Visuals"):
                sk = ui_skeleton(); desc = analyze_image_with_vision(img); sk.empty()
                st.success("Analysis Complete"); st.write(desc)

    with tabs[2]:
        if "ft" in st.session_state and st.button("Generate Flashcards"):
            sk = ui_skeleton(); cards = generate_flashcards(st.session_state.ft); sk.empty()
            if cards: st.table(pd.DataFrame(cards)); ui_confidence_badge("High")

    with tabs[3]:
        if "ft" in st.session_state and st.button("Build Graph"):
            nlp = spacy.load("en_core_web_sm"); doc = nlp(st.session_state.ft[:5000])
            nodes = []; edges = []; names = set()
            for e in doc.ents:
                if e.label_ in ["ORG","PERSON"] and e.text not in names:
                    nodes.append(Node(id=e.text, label=e.text, size=20)); names.add(e.text)
            for s in doc.sents:
                en = [x.text for x in s.ents if x.text in names]
                for i in range(len(en)-1): edges.append(Edge(source=en[i], target=en[i+1]))
            agraph(nodes, edges, Config(height=500, width=700))

    with tabs[4]:
        if "ft" in st.session_state and st.button("Run Audit"):
            sk = ui_skeleton(); res = run_audit(st.session_state.ft); sk.empty()
            st.markdown(f"<div class='glass-card'>{res}</div>", unsafe_allow_html=True)

    with tabs[5]:
        if "ft" in st.session_state and st.button("Generate Slides"):
            sk = ui_skeleton(); ppt = generate_ppt_from_text(st.session_state.ft); sk.empty()
            if ppt: st.download_button("Download PPT", ppt.getvalue(), "pres.pptx"); ui_confidence_badge("High")

    with tabs[6]:
        if "ft" in st.session_state and st.button("Extract Data"):
            sk = ui_skeleton(); data = extract_ledger_data(st.session_state.ft); sk.empty()
            if data: st.json(data); ui_confidence_badge("High")

    with tabs[7]: # Chronos (FIXED)
        if "ft" in st.session_state and st.button("Build Timeline"):
            sk = ui_skeleton(); data = extract_timeline_data(st.session_state.ft); sk.empty()
            if data and "events" in data:
                timeline(data, height=400)
                ui_confidence_badge("Medium")
            else: st.warning("No timeline data found or JSON error.")

    with tabs[8]:
        if "ft" in st.session_state and st.button("Find Contradictions"):
            sk = ui_skeleton(); res = analyze_contradictions(st.session_state.ft); sk.empty()
            st.markdown(f"<div class='glass-card'>{res}</div>", unsafe_allow_html=True)

elif selected == "Converter":
    st.markdown("<h1>🔄 Universal Converter</h1>", unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["Images to PDF", "Word to PDF", "PDF to Word", "PDF to Excel", "Data to PDF"])
    with t1:
        i = st.file_uploader("Images", type=["png","jpg"], accept_multiple_files=True)
        if i and st.button("Convert"): st.download_button("Download PDF", images_to_pdf(i).getvalue(), "img.pdf")
    with t2:
        d = st.file_uploader("Docx", type=["docx"])
        if d and st.button("Convert"): st.download_button("Download PDF", word_to_pdf(d).getvalue(), "doc.pdf")
    with t3:
        p = st.file_uploader("PDF", type="pdf")
        if p and st.button("To Word"): 
            sk = ui_skeleton(); doc = pdf_to_docx(p); sk.empty()
            st.download_button("Download Docx", doc.getvalue(), "doc.docx")
    with t4:
        p2 = st.file_uploader("PDF", type="pdf", key="p2e")
        if p2 and st.button("To Excel"):
            sk = ui_skeleton(); xl = pdf_to_excel(p2); sk.empty()
            if xl: st.download_button("Download Excel", xl.getvalue(), "tab.xlsx")
    with t5:
        d = st.file_uploader("CSV/Excel", type=["csv","xlsx"])
        if d and st.button("Convert to PDF"):
            sk = ui_skeleton()
            if d.name.endswith("csv"): df = pd.read_csv(d)
            else: df = pd.read_excel(d)
            pdf = df_to_pdf(df)
            sk.empty()
            st.download_button("Download PDF", pdf.getvalue(), "data.pdf")

elif selected == "Editor":
    st.markdown("<h1>✂️ Pro Editor</h1>", unsafe_allow_html=True)
    t1, t2, t3, t4, t5, t6 = st.tabs(["Split", "Merge", "Compress", "Watermark", "Rotate", "Delete"])
    with t1:
        f = st.file_uploader("PDF", type="pdf", key="sp")
        if f and st.button("Split"): 
            r = PdfReader(f); z = io.BytesIO()
            with zipfile.ZipFile(z,"a") as zf:
                for n, p in enumerate(r.pages):
                    w = PdfWriter(); w.add_page(p); b = io.BytesIO(); w.write(b); zf.writestr(f"p{n}.pdf", b.getvalue())
            st.download_button("Download ZIP", z.getvalue(), "pages.zip")
    with t2:
        fs = st.file_uploader("PDFs", accept_multiple_files=True, key="mg")
        if fs and st.button("Merge"): st.download_button("Download PDF", merge_pdfs(fs).getvalue(), "merged.pdf")
    with t3:
        fc = st.file_uploader("PDF", key="cp")
        if fc and st.button("Compress"): st.download_button("Download PDF", compress_pdf(fc).getvalue(), "comp.pdf")
    with t4:
        fw = st.file_uploader("PDF", key="wm"); txt = st.text_input("Text", "DRAFT")
        if fw and st.button("Apply"): st.download_button("Download PDF", add_watermark(fw, txt).getvalue(), "wm.pdf")
    with t5:
        fr = st.file_uploader("PDF", key="rt"); ang = st.radio("Angle", [90, 180, 270])
        if fr and st.button("Rotate"): st.download_button("Download PDF", rotate_pdf(fr, ang).getvalue(), "rot.pdf")
    with t6:
        fd = st.file_uploader("PDF", key="del"); pn = st.number_input("Page", 1)
        if fd and st.button("Delete"): st.download_button("Download PDF", delete_page(fd, pn).getvalue(), "mod.pdf")

elif selected == "Compare":
    st.markdown("<h1>⚖️ Cross-Comparison</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: f1 = st.file_uploader("Original", type="pdf", key="c1")
    with c2: f2 = st.file_uploader("Modified", type="pdf", key="c2")
    if f1 and f2 and st.button("Compare"):
        sk = ui_skeleton()
        t1 = "".join([p.extract_text() for p in PdfReader(f1).pages])
        t2 = "".join([p.extract_text() for p in PdfReader(f2).pages])
        d, raw = compare_pdfs_enhanced(t1, t2)
        
        st.subheader("📝 AI Summary")
        try: 
            s = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Summarize changes:\n{raw[:4000]}"}])['message']['content']
            st.info(s)
        except: st.warning("Summary unavailable.")
        
        sk.empty()
        for t, txt in d:
            if t == 'add': st.markdown(f"<div class='diff-add'>{txt}</div>", unsafe_allow_html=True)
            elif t == 'rem': st.markdown(f"<div class='diff-rem'>{txt}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # End Animation