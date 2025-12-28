.PHONY: help docker-up docker-down ingest clear info search support streamlit clean

help:
	@echo "Tech Support AI Assistant - Available Commands:"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up      - Start ChromaDB and Admin UI containers"
	@echo "  make docker-down    - Stop all containers"
	@echo "  make docker-logs    - View ChromaDB logs"
	@echo "  make docker-clean   - Stop containers and remove volumes (deletes data)"
	@echo ""
	@echo "Data Management:"
	@echo "  make ingest FOLDER=<path>           - Ingest documents from folder"
	@echo "  make clear COLLECTION=<name>        - Delete a collection"
	@echo "  make info [COLLECTION=<name>]       - Show collection info"
	@echo "  make search COLLECTION=<name> Q='<query>' - Search a collection"
	@echo ""
	@echo "Run Application:"
	@echo "  make support [COLLECTION=<name>]    - Run TUI app"
	@echo "  make streamlit                      - Run Streamlit web app"
	@echo "  make web                            - Run Flask web app (NEW)"
	@echo ""
	@echo "Examples:"
	@echo "  make docker-up"
	@echo "  make ingest FOLDER=assets/laravel"
	@echo "  make info COLLECTION=laravel"
	@echo "  make search COLLECTION=laravel Q='how to use blade'"
	@echo "  make streamlit"

# Docker commands
docker-up:
	docker-compose up -d
	@echo ""
	@echo "✓ ChromaDB running at http://localhost:8000"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f chromadb

docker-clean:
	docker-compose down -v
	@echo "✓ All data deleted"

# Data management
ingest:
	@if [ -z "$(FOLDER)" ]; then \
		echo "Error: FOLDER is required. Usage: make ingest FOLDER=<path>"; \
		exit 1; \
	fi
	uv run ingest $(FOLDER)

clear:
	@if [ -z "$(COLLECTION)" ]; then \
		echo "Error: COLLECTION is required. Usage: make clear COLLECTION=<name>"; \
		exit 1; \
	fi
	uv run clear $(COLLECTION)

info:
	@if [ -z "$(COLLECTION)" ]; then \
		uv run info; \
	else \
		uv run info $(COLLECTION); \
	fi

search:
	@if [ -z "$(COLLECTION)" ] || [ -z "$(Q)" ]; then \
		echo "Error: COLLECTION and Q are required. Usage: make search COLLECTION=<name> Q='<query>'"; \
		exit 1; \
	fi
	uv run search $(COLLECTION) $(Q)

# Run application
support:
	@if [ -z "$(COLLECTION)" ]; then \
		uv run support; \
	else \
		uv run support $(COLLECTION); \
	fi

streamlit:
	uv run streamlit run tech_support/streamlit_app.py

web:
	uv run python tech_support/web_app.py

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Python cache cleaned"
