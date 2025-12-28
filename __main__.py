"""Main entry point for CLI commands."""
import sys
from tech_support.cli import ingest_command, clear_collection_command, collection_info_command, search_command


def ingest():
    """Entry point for the ingest command."""
    if len(sys.argv) < 2:
        print("Usage: uv run ingest <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    ingest_command(folder_path)


def clear_collection():
    """Entry point for the clear collection command."""
    if len(sys.argv) < 2:
        print("Usage: uv run clear <collection_name>")
        sys.exit(1)
    
    collection_name = sys.argv[1]
    clear_collection_command(collection_name)


def info():
    """Entry point for the collection info command."""
    collection_name = sys.argv[1] if len(sys.argv) > 1 else None
    collection_info_command(collection_name)


def search():
    """Entry point for the search command."""
    if len(sys.argv) < 3:
        print("Usage: uv run search <collection_name> <query>")
        sys.exit(1)
    
    collection_name = sys.argv[1]
    query = " ".join(sys.argv[2:])  # Join all remaining args as query
    search_command(collection_name, query)


if __name__ == "__main__":
    ingest()
