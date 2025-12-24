import streamlit as st
from streamlit_option_menu import option_menu
from pypdf import PdfReader, PdfWriter
import pdfplumber
import ollama
import io
import zipfile
import base64
import time
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Journey Through Pages", layout="wide", page_icon="⚡")

# --- 2. MAGICAL CSS STYLING ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #fdfbf7; }
    
    /* Ensure Footer stays at bottom by forcing main content to fill screen */
    .main .block-container {
        min-height: 85vh;
        display: flex;
        flex-direction: column;
    }
    
    /* Headers */
    h1, h2, h3 { font-family: 'Georgia', serif; color: #2c0e37; }
    
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white; border-radius: 12px; border: none;
        padding: 0.6rem 1rem; font-weight: 600; width: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div.stButton > button:hover { 
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(106, 17, 203, 0.4);
    }

    /* Uniform Feature Cards */
    .feature-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        transition: 0.3s;
        border-top: 5px solid #6a11cb;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .feature-card:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        border-top: 5px solid #ff0080; /* Hover color pop */
    }
    .feature-card h3 { font-size: 1.1rem; margin-bottom: 10px; font-weight: bold; }
    .feature-card p { font-size: 0.85rem; color: #666; }
    
    /* Footer Styling */
    .footer {
        width: 100%;
        background-color: transparent; 
        color: #555;
        text-align: center; 
        padding: 30px;
        margin-top: auto; /* Pushes footer to bottom */
        font-family: 'Arial', sans-serif; 
        font-size: 0.9rem;
        border-top: 1px solid #eaeaea;
    }
    .footer a { color: #6a11cb; text-decoration: none; font-weight: bold; margin: 0 10px; }
    .footer a:hover { text-decoration: underline; }

    /* Insight & Summary Boxes */
    .insight-box {
        background-color: #f3e8ff; border-left: 5px solid #9333ea;
        padding: 20px; border-radius: 8px; margin-bottom: 20px;
    }
    .summary-box {
        background-color: #fffbeb; border: 1px solid #fcd34d; color: #92400e;
        padding: 20px; border-radius: 8px; font-style: italic; line-height: 1.6;
    }
    
    /* Chat Spacer */
    .spacer { height: 50px; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def custom_badge(label, color_bg, color_text):
    st.markdown(f"""
    <span style="background-color: {color_bg}; color: {color_text}; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600; font-size: 0.9rem; display: inline-block; margin-right: 10px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
    {label}
    </span>
    """, unsafe_allow_html=True)

@st.cache_data
def extract_text_with_references(file):
    pages_data = []
    with pdfplumber.open(file) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text: pages_data.append({"page": i + 1, "text": text})
    return pages_data

def run_ml_pipeline(text):
    # HP Easter Egg prompts
    prompt_cls = f"Classify this text into [Resume, Legal Contract, Research Paper, Invoice, Financial Report, General Article]. Reply ONLY category name. Text: {text[:1000]}"
    try: doc_type = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt_cls}])['message']['content'].strip()
    except: doc_type = "General Scroll"
    
    prompt_sum = f"Write a 3-sentence Executive Summary. Text: {text[:4000]}"
    try: summary = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt_sum}])['message']['content']
    except: summary = "The ink is too faded to read."
    
    prompt_ins = f"Extract: 1. Key Sentences 2. Dates 3. Money. Format as bullets. Text: {text[:4000]}"
    try: insights = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt_ins}])['message']['content']
    except: insights = "No magical signatures found."
    
    return doc_type, summary, insights

# --- CONVERSION LOGIC ---
def images_to_pdf(images):
    pdf_buffer = io.BytesIO()
    if images:
        first = Image.open(images[0]).convert('RGB')
        others = [Image.open(img).convert('RGB') for img in images[1:]]
        first.save(pdf_buffer, save_all=True, append_images=others, format='PDF')
    return pdf_buffer

def word_to_pdf(docx_file):
    doc = Document(docx_file)
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    text_obj = c.beginText(40, 750)
    text_obj.setFont("Helvetica", 12)
    for para in doc.paragraphs:
        if para.text:
            text_obj.textLine(para.text[:90])
            if text_obj.getY() < 40:
                c.drawText(text_obj); c.showPage(); text_obj = c.beginText(40, 750); text_obj.setFont("Helvetica", 12)
    c.drawText(text_obj); c.save()
    return pdf_buffer

# --- EDITOR LOGIC ---
def split_pdf(file):
    reader = PdfReader(file)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            page_buffer = io.BytesIO()
            writer.write(page_buffer)
            zip_file.writestr(f"page_{i+1}.pdf", page_buffer.getvalue())
    return zip_buffer

def merge_pdfs(files):
    writer = PdfWriter()
    for file in files:
        reader = PdfReader(file)
        for page in reader.pages: writer.add_page(page)
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    return output_buffer

# --- 4. APP LAYOUT ---

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2619/2619246.png", width=60) 
    st.markdown("<h2 style='text-align: center;'>Journey<br>Through Pages</h2>", unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["Home", "Viewer", "Converter", "Editor", "AI Analyst"],
        icons=["house-door", "eye-fill", "arrow-repeat", "magic", "stars"],
        default_index=0,
        styles={
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "5px"},
            "nav-link-selected": {"background-color": "#6a11cb"},
        }
    )
    st.divider()
    st.caption("⚡ Engine: Llama 3.2 (Local)")

# --- HOME PAGE ---
if selected == "Home":
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>⚡ Journey Through Pages</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555; margin-bottom: 30px;'><i>'The magical toolbox for your digital scrolls.'</i></p>", unsafe_allow_html=True)
    
    st.info("""
    **Welcome, Traveler!** Step into a workspace where productivity meets magic. I designed this application to take the stress out of document management. 
    Whether you need to transfigure images into PDFs, consult a digital oracle (AI) about your contracts, or simply organize your library, 
    **Journey Through Pages** does it all—securely, offline, and instanty.
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔮 Your Magical Capabilities")
    
    # ROW 1
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown("""<div class="feature-card"><h3>👀 Viewer</h3><p>Read scrolls with crystal clarity using the Pensieve interface.</p></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="feature-card"><h3>🔄 Converter</h3><p>Transfigure Images & Word Docs into professional PDFs instantly.</p></div>""", unsafe_allow_html=True)
    with c3: st.markdown("""<div class="feature-card"><h3>✂️ Splitter</h3><p>Cast 'Diffindo' to sever a document into individual pages.</p></div>""", unsafe_allow_html=True)
    with c4: st.markdown("""<div class="feature-card"><h3>🔗 Merger</h3><p>Cast 'Reparo' to bind multiple documents into one.</p></div>""", unsafe_allow_html=True)
    
    # ROW 2 (AI Features Split)
    c5, c6, c7, c8 = st.columns(4)
    with c5: st.markdown("""<div class="feature-card"><h3>📝 Summarizer</h3><p>Get the executive summary instantly without reading a word.</p></div>""", unsafe_allow_html=True)
    with c6: st.markdown("""<div class="feature-card"><h3>🔍 Revelio (Insights)</h3><p>Automatically extract hidden money values, dates, and secrets.</p></div>""", unsafe_allow_html=True)
    with c7: st.markdown("""<div class="feature-card"><h3>💬 Portrait Chat</h3><p>Talk to your document. Ask questions and get page citations.</p></div>""", unsafe_allow_html=True)
    with c8: st.markdown("""<div class="feature-card"><h3>🔒 Privacy</h3><p>Local AI Engine. Your secrets never leave your device.</p></div>""", unsafe_allow_html=True)

# --- VIEWER ---
elif selected == "Viewer":
    st.header("👀 The Marauder's Viewer")
    uploaded_file = st.file_uploader("Reveal your document...", type="pdf")
    if uploaded_file:
        base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="900" style="border: 2px solid #6a11cb; border-radius: 10px;"></iframe>', unsafe_allow_html=True)
        st.toast("Lumos Maxima! Document revealed.", icon="💡")

# --- CONVERTER ---
elif selected == "Converter":
    st.header("🔄 Transfiguration Class (Converter)")
    tab1, tab2 = st.tabs(["🖼️ Images to PDF", "📝 Word to PDF"])
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        img_files = st.file_uploader("Upload Images", type=["png", "jpg"], accept_multiple_files=True)
        name = st.text_input("Name your scroll", "photos.pdf")
        if img_files and st.button("Transfigure Images"):
            st.download_button("Download Scroll", images_to_pdf(img_files).getvalue(), name, "application/pdf")
            st.toast("Transfiguration successful!", icon="✨")
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        docx = st.file_uploader("Upload Word Doc", type=["docx"])
        name_w = st.text_input("Name your document", "doc.pdf")
        if docx and st.button("Transfigure Doc"):
            st.download_button("Download PDF", word_to_pdf(docx).getvalue(), name_w, "application/pdf")
            st.toast("Transfiguration successful!", icon="✨")

# --- EDITOR ---
elif selected == "Editor":
    st.header("🛠️ Charms Class (Editor)")
    tab1, tab2 = st.tabs(["✂️ Diffindo (Split)", "🔗 Reparo (Merge)"])
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        f = st.file_uploader("Upload PDF to Split", type="pdf")
        if f and st.button("Cast Diffindo"): 
            st.download_button("Download Pages (ZIP)", split_pdf(f).getvalue(), "split_pages.zip", "application/zip")
            st.toast("Diffindo successful!", icon="✂️")
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        fs = st.file_uploader("Upload PDFs to Merge", type="pdf", accept_multiple_files=True)
        if fs and st.button("Cast Reparo"): 
            st.download_button("Download Merged PDF", merge_pdfs(fs).getvalue(), "merged_doc.pdf", "application/pdf")
            st.toast("Reparo successful!", icon="🔗")

# --- AI ANALYST ---
elif selected == "AI Analyst":
    st.header("🧠 The Sorting Hat & Pensieve")
    
    uploaded_file = st.file_uploader("Upload Scroll (PDF) for Analysis", type="pdf")
    
    if uploaded_file:
        # PROCESSING PIPELINE
        if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
            st.session_state.current_file = uploaded_file.name
            
            progress_text = "Opening the Restricted Section..."
            my_bar = st.progress(0, text=progress_text)
            
            time.sleep(0.5)
            my_bar.progress(30, text="📜 Deciphering Ancient Runes...")
            st.session_state.pages_data = extract_text_with_references(uploaded_file)
            full_text = "\n".join([p['text'] for p in st.session_state.pages_data])
            
            my_bar.progress(60, text="🎩 Consulting the Sorting Hat...")
            doc_type, summary, insights = run_ml_pipeline(full_text)
            
            my_bar.progress(90, text="✨ Extracting Magical Properties...")
            st.session_state.doc_type = doc_type
            st.session_state.summary = summary
            st.session_state.insights = insights
            st.session_state.chat_history = []
            
            my_bar.progress(100, text="Mischief Managed!")
            time.sleep(1)
            my_bar.empty()
            st.rerun()

        # --- DASHBOARD ---
        st.markdown("<hr>", unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(f"📜 Analysis: {uploaded_file.name}")
        with col2:
            if st.button("🧹 Obliviate"):
                st.session_state.chat_history = []
                st.rerun()

        # BADGES
        st.markdown("<br>", unsafe_allow_html=True)
        dtype = st.session_state.doc_type
        if "Resume" in dtype: custom_badge("🧙‍♂️ Wizard Profile (Resume)", "#e0e7ff", "#3730a3")
        elif "Invoice" in dtype: custom_badge("💰 Gringotts Invoice", "#dcfce7", "#166534")
        elif "Legal" in dtype: custom_badge("📜 Ministry Decree (Legal)", "#fee2e2", "#991b1b")
        else: custom_badge(f"📑 {dtype}", "#f3f4f6", "#1f2937")
        custom_badge(f"{len(st.session_state.pages_data)} Pages", "#f3f4f6", "#374151")

        # SUMMARY & INSIGHTS
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("##### 📜 Executive Summary")
            st.markdown(f'<div class="summary-box">{st.session_state.summary}</div>', unsafe_allow_html=True)
        
        with st.expander("✨ Prophecies & Key Revelations", expanded=False):
            st.markdown(st.session_state.insights)

        st.divider()

        # CHAT
        st.subheader("💬 Consult the Portrait")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
        # Spacer
        st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

        if prompt := st.chat_input("Ask the document a question..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Consulting the library..."):
                    context = ""
                    for p in st.session_state.pages_data:
                        if len(context) < 25000: context += f"\n[Page {p['page']}]\n{p['text']}"
                    
                    full_prompt = f"Answer clearly. Cite pages like (Source: Page X). Context: {context}\nQuestion: {prompt}"
                    try:
                        resp = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': full_prompt}])
                        reply = resp['message']['content']
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- FOOTER (Always at Bottom) ---
st.markdown("""
<div class="footer">
    <p>Designed with ❤️ and ⚡ by <b>M. Ihthisham Irshad</b></p>
    <a href="https://www.instagram.com/inthi.ii?igsh=bW5tZXZ4dmpvYnli&utm_source=qr" target="_blank">Instagram</a> | 
    <a href="https://www.linkedin.com/in/ihthisham-irshad-296157234?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=ios_app" target="_blank">LinkedIn</a>
</div>
""", unsafe_allow_html=True)
