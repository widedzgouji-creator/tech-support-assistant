# **1. Project Overview**

The goal is to build an **AI-powered technical support assistant** capable of answering questions about a chosen software/product using:

* a **Retrieval-Augmented Generation (RAG)** pipeline
* **embeddings + vector database**
* **LLM generation**
* optional **re-ranking**
* a simple **support-style chat interface**

The chatbot should provide clear, accurate, and user-friendly explanations, and gracefully handle cases where it is uncertain.

You must select a technical domain (e.g., Python, Linux commands, HuggingFace Transformers, a specific tool, open-source project, etc.) and build a support bot around its documentation.

---

# **2. Objectives**

### **2.1 Pedagogical Objectives**

You must demonstrate the ability to:

* Build a complete RAG pipeline from scratch.
* Extract and preprocess technical documentation.
* Apply multi-passage retrieval and optionally re-ranking (cross-encoder).
* Manage uncertainty (scores, “I’m not sure”, escalate to human).
* Produce well-structured and easy-to-read answers.
* Design and evaluate a real support-use-case system.

---

# **3. Functional Requirements**

### **3.1 Core Features**

The system must provide:

#### **1) Technical Q&A**

* Accept user questions related to the chosen product/software.
* Retrieve relevant documentation passages.
* Generate accurate explanations or troubleshooting steps.

#### **2) Multi-Passage Retrieval**

* Retrieve several text chunks per query.
* Include re-ranking (optional but recommended) to select the best passages.

#### **3) Uncertainty Detection**

When the bot is unsure:

* Provide a message such as:
  *“I’m not fully confident about this answer. You may need to contact an expert.”*
* Show a **confidence score** or threshold logic.

#### **4) Human Escalation Option**

If confidence < threshold:

* Suggest contacting a human expert.
* The system does NOT need to route to a real human — only suggest.

#### **5) Support Chat Interface**

At minimum:

* CLI or Terminal chat OR
* Streamlit / Gradio web UI
  with:
* chat history
* formatted answers
* retrieved snippets display (optional but recommended)

---

# **4. Technical Requirements**

### **4.1 Data Collection**

Use technical documentation such as:

* HuggingFace documentation
* Python official docs
* Linux man pages
* GitHub Issues (open-source projects)
* FAQs or internal knowledge bases

Formats allowed: PDF, HTML, Markdown, text.

You must preprocess and clean the text.

---

### **4.2 Preprocessing & Chunking**

Pipeline must include:

* text extraction
* cleaning (remove menus, navigation, irrelevant sections)
* segmentation into chunks (150–500 tokens recommended)
* optional metadata (title, URL, section header)

---

### **4.3 Embeddings & Vector Database**

Use one of:

✔ Sentence-BERT
✔ e5-base / e5-large
✔ Llama embeddings
✔ Instructor-xl
✔ Any modern embedding model

Vector stores allowed:

* FAISS
* Chroma
* Milvus
* Qdrant

---

### **4.4 Retrieval**

Implement:

* **Top-k retrieval** (k = 3–10)
* Optionally: **Re-ranking** with a cross-encoder (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`).

You must justify:

* chunk size
* embedding choice
* retrieval strategy

---

### **4.5 RAG Generation**

LLM can be:

* GPT
* Llama 3
* Mistral
* any local model

LLM must generate answers based only on retrieved contexts.

---

### **4.6 Logging & Evaluation**

The system must log:

* user queries
* selected chunks
* confidence scores
* whether the bot escalated or not

This will be used for analysis in the report.

---

# **5. Deliverables**

### **5.1 Mandatory Deliverables**

1. **PDF Report**
   Contains:

   * project description
   * full pipeline architecture
   * datasets used
   * diagrams (retrieval flow, system architecture)
   * technical justifications
   * experimental results
   * examples of conversations
   * limitations & improvements
   * GitHub link

2. **GitHub Repository**
   Must include:

   * clean, modular code
   * README with:

     * setup instructions
     * how to run the app
     * dependencies
     * optional demo script

3. **Functioning Chatbot**
   (CLI or web interface)

---

### **5.2 Specific Deliverables for Project 3**

* A set of test questions + analysis of:

  * success cases
  * failure cases
* Simple metrics:

  * accuracy
  * percentage of “uncertain” answers
  * retrieval precision (optional)

---

# **6. Evaluation Criteria**

### **Technical (50%)**

* Quality of retrieval and re-ranking
* Quality of technical answers
* Handling of uncertainty
* RAG architecture coherence

### **Code (20%)**

* Organization
* Modularity
* Documentation

### **Report (20%)**

* Clarity
* Diagrams
* Critical analysis

### **Originality & Extras (10%)**

* Additional UI features
* More advanced metrics
* Fine-tuning a model
* Deploying the bot online