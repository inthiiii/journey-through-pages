# Journey Through Pages ⚡🦄
### *v1.2: The Ethereal Edition*

**Journey Through Pages** is an enterprise-grade, privacy-first Document Intelligence Platform. It runs entirely **offline** on your device using **Local LLMs (Llama 3.2 & Vision)**, bridging the gap between raw AI power and professional productivity.

Designed with a Silicon Valley-grade **Glassmorphism UI**, it replaces multiple paid SaaS tools (Acrobat Pro, Jasper, ChatPDF, Otter.ai) with one free, open-source solution.

---

## 🚀 Features

### 🧠 **The AI Analyst (Powerhouse)**
* **🤖 Private Chat:** Chat with documents using Citation-Aware RAG.
* **📚 Omniscient Mode:** Chat with your entire "Bookshelf" (multiple docs) at once.
* **🕸️ The Connector:** Visualizes hidden relationships (People, Orgs) as an interactive **Knowledge Graph**.
* **🎞️ Deck Builder:** Converts PDF reports into editable **PowerPoint Slides (.pptx)** instantly.
* **⚖️ The Auditor:** Assigns a "Risk Score" (0-100) to contracts and flags dangerous clauses.
* **📊 The Ledger:** Extracts table data from Invoices/Receipts into structured **JSON**.
* **⏳ Chronos:** Plots events on an interactive **Visual Timeline**.
* **🕵️ Truth Serum:** Detects logical contradictions and conflicting statements in long texts.
* **👁️ Vision Analyst:** Uses Multimodal AI to describe charts, graphs, and images.
* **🎧 Podcast Mode:** Converts summaries into lifelike Audio (WAV) for listening on the go.
* **🎓 Study Tools:** Generates concept-based Flashcards (CSV) for students.

### 👀 **Advanced Viewer & Privacy Shield**
* **🧠 Semantic Search:** Find information by *meaning*, not just keywords (e.g., "money" finds "revenue").
* **🛡️ Auto-PII Shield:** Automatically scans and detects Emails & Phone numbers for redaction.
* **🖍️ Markup Tools:** Real-time Highlighting and Blackout Redaction.

### ✂️ **Professional Editor**
* **Universal Toolset:** Split, Merge, Compress, Rotate, and Delete pages.
* **Watermarker:** Stamp documents with custom text (e.g., "CONFIDENTIAL").

### 🔄 **Universal Converter**
* **Any-to-Any:** Images → PDF, Word → PDF, PDF → Word, PDF → Excel.
* **Data-to-Report:** Converts CSV/Excel data into formatted PDF reports.

### ⚖️ **Cross-Comparison**
* **Diff Viewer:** Upload two versions of a document and see exactly what changed (Added/Removed text).

---

## 🛠️ Installation

### Prerequisites
* Python 3.10+
* [Ollama](https://ollama.com) installed and running.

### 1. Clone the Repository
```bash
git clone [https://github.com/YourUsername/journey-through-pages-ai.git](https://github.com/YourUsername/journey-through-pages-ai.git)
cd journey-through-pages-ai

---
### Setup Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

### Install Local Models

# The Main Brain (Text)
ollama pull llama3.2

# The Vision Brain (Images)
ollama pull llama3.2-vision

# The NLP Brain (Graphing)
python -m spacy download en_core_web_sm


### Run the App

streamlit run app.py