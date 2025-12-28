# Tech Support Assistant - AI-Powered RAG System

An intelligent technical support chatbot for Laravel documentation using Retrieval-Augmented Generation (RAG). The system combines vector search with LLM generation to provide accurate, context-aware answers with confidence scoring and uncertainty detection.

## 🌟 Features

- **RAG Pipeline**: Complete retrieval-augmented generation with ChromaDB vector storage
- **Confidence Scoring**: Automatic confidence calculation based on retrieval quality
- **Uncertainty Detection**: Flags uncertain answers and suggests human escalation
- **Modern Web UI**: Clean HTML/CSS/JavaScript interface with markdown rendering
- **Debug Panel**: Real-time metrics, retrieved sources, and confidence visualization
- **Structured Logging**: JSONL logs for query analysis and evaluation
- **Clickable Sources**: View full chunk content with markdown formatting

## 📋 Prerequisites

- **Python 3.11+**
- **Docker** (for ChromaDB)
- **uv** package manager ([install](https://docs.astral.sh/uv/))
- **GitHub Token** (for LLM API access)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd tech-support
```

### 2. Start ChromaDB

```bash
make docker-up
```

This starts ChromaDB on port 8000.

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your GitHub token:

```bash
GITHUB_TOKEN=your_github_token_here
```

Get a token at: https://github.com/settings/tokens (with `read:org` scope)

### 4. Install Dependencies

```bash
uv sync
```

### 5. Ingest Documentation

```bash
make ingest FOLDER=assets/laravel
```

This processes all markdown files in the folder and creates embeddings.

### 6. Run the Web Interface

```bash
make web
```

Open http://localhost:5000 in your browser.

## 📖 Usage

### Web Interface

1. **Select Collection**: Choose "laravel" from the dropdown
2. **Toggle Debug**: Click 🐛 to show/hide debug panel
3. **Ask Questions**: Type in the input field at bottom
4. **View Sources**: Click on any source in debug panel to see full content
5. **Monitor Confidence**: Check confidence scores and escalation flags

### Command Line Tools

```bash
# Search the collection
make search COLLECTION=laravel Q="how to use blade templates"

# View collection info
make info COLLECTION=laravel

# Clear a collection
make clear COLLECTION=laravel

# Stop ChromaDB
make docker-down
```

## 🏗️ Architecture

### Pipeline Flow

```
User Query → Embedding → Vector Search (ChromaDB) 
→ Top-5 Chunks → LLM (GPT-4) → Response + Confidence
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Package Manager | uv |
| Vector DB | ChromaDB |
| Embeddings | BAAI/bge-small-en-v1.5 (384 dim) |
| LLM | GitHub Models API (GPT-4.1) |
| Web Framework | Flask |
| Frontend | HTML/CSS/JS + Marked.js |
| Container | Docker |

### Project Structure

```
tech-support/
├── tech_support/
│   ├── agent.py           # RAG agent with LLM integration
│   ├── rag.py             # Vector search and ingestion
│   ├── embedding.py       # Embedding model wrapper
│   ├── logger.py          # Structured logging system
│   ├── web_app.py         # Flask web server
│   ├── cli.py             # CLI commands
│   └── templates/
│       └── index.html     # Web interface
├── assets/
│   └── laravel/           # Documentation markdown files
├── logs/                  # Query logs (JSONL format)
├── docker-compose.yml     # ChromaDB configuration
├── Makefile               # Command shortcuts
├── pyproject.toml         # Python dependencies
├── .env.example           # Environment template
├── report.tex             # LaTeX project report
└── README.md              # This file
```

## ⚙️ Configuration

### Environment Variables

Edit `.env` to customize:

```bash
# Required
GITHUB_TOKEN=your_token_here

# ChromaDB
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Embeddings
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Confidence Thresholds
CONFIDENCE_THRESHOLD=0.5        # Below this = escalated
UNCERTAIN_DISTANCE_THRESHOLD=0.8  # Above this = uncertain

# Logging
LOG_FILE=logs/support_assistant.log
LOG_LEVEL=INFO

# LLM
GITHUB_MODEL=openai/gpt-4.1
```

## 📊 Confidence Scoring

The system calculates confidence from retrieval distance:

- **Confidence = 1 - min_distance** (range: 0-1)
- **Uncertain**: distance > 0.8
- **Escalated**: confidence < 0.5

### UI Indicators

- 🟢 **Confident**: High confidence (>80%)
- 🔵 **Uncertain**: Medium confidence (50-80%)
- 🟡 **Escalated**: Low confidence (<50%) - suggests human expert

## 📝 Logging

All queries are logged to `logs/support_assistant.log` in JSONL format:

```json
{
  "timestamp": "2025-12-07T10:30:45",
  "query": "How do I use Eloquent relationships?",
  "collection": "laravel",
  "retrieved_chunks": [...],
  "confidence": 0.82,
  "is_uncertain": false,
  "escalated": false,
  "response": "To use Eloquent relationships..."
}
```

## 🧪 Testing

### Sample Queries

Try these queries to test the system:

1. "How do I define routes in Laravel?"
2. "What is Eloquent ORM?"
3. "How to use middleware?"
4. "Explain Blade templates"
5. "How does authentication work?"
6. "Configure database connections"

### Expected Performance

- **Accuracy**: ~80% on well-documented topics
- **Response Time**: <3 seconds average
- **Retrieval Precision@5**: ~0.84
- **Escalation Rate**: ~20% (appropriate for uncertainty)

## 🛠️ Development

### Adding New Collections

1. Place markdown files in a folder (e.g., `assets/python-docs/`)
2. Ingest: `make ingest FOLDER=assets/python-docs`
3. Select the new collection in the web UI

### Customizing Chunking

Edit in `.env`:

```bash
CHUNK_SIZE=1000      # Characters per chunk
CHUNK_OVERLAP=200    # Overlap between chunks
```

Then re-ingest documents.

### Adjusting Confidence Thresholds

Fine-tune in `.env`:

```bash
CONFIDENCE_THRESHOLD=0.5        # Lower = more escalations
UNCERTAIN_DISTANCE_THRESHOLD=0.8  # Lower = more uncertain flags
```

## 🐛 Troubleshooting

### ChromaDB Connection Error

```bash
# Check if ChromaDB is running
docker ps

# Restart ChromaDB
make docker-down
make docker-up
```

### Embedding Model Not Found

The model downloads automatically on first use. If it fails:

```bash
# Manually download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
```

### GitHub Token Invalid

Get a new token at https://github.com/settings/tokens with `read:org` scope.

### Port 5000 Already in Use

Change Flask port in `tech_support/web_app.py`:

```python
app.run(debug=True, port=5001)
```

## 📚 Additional Resources

- [ChromaDB Docs](https://docs.trychroma.com/)
- [BGE Embeddings](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [GitHub Models](https://github.com/marketplace/models)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Laravel Docs](https://laravel.com/docs)

## 📄 License

MIT License - See project documentation for details.

## 🤝 Contributing

This is an academic project. For issues or suggestions, please refer to the project report.

## 📧 Contact

For questions about this implementation, refer to the LaTeX report (`report.tex`) for detailed technical documentation.

---

**Note**: This system is designed for educational purposes to demonstrate RAG pipeline implementation. For production use, consider adding authentication, rate limiting, and advanced security measures.
