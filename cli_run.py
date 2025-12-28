"""CLI wrapper to run the app with collection selection."""
import sys
from rich.console import Console
from rich.prompt import Prompt
from tech_support.app import run as app_run
from tech_support.rag import RAG


def main():
    """Main entry point for the tech-support CLI."""
    console = Console()
    
    # Check if collection name provided as argument
    if len(sys.argv) > 1:
        collection_name = sys.argv[1]
    else:
        # List available collections
        try:
            rag = RAG()
            client = rag._get_client()
            collections = client.list_collections()
            
            if not collections:
                console.print("[yellow]No collections found. Please ingest documents first.[/yellow]")
                console.print("[dim]Usage: uv run ingest <folder_path>[/dim]")
                sys.exit(1)
            
            console.print("[bold cyan]Available collections:[/bold cyan]")
            for i, col in enumerate(collections, 1):
                console.print(f"  {i}. {col.name}")
            
            if len(collections) == 1:
                collection_name = collections[0].name
                console.print(f"\n[dim]Using collection: {collection_name}[/dim]")
            else:
                collection_name = Prompt.ask(
                    "\n[bold cyan]Enter collection name[/bold cyan]",
                    default=collections[0].name if collections else "",
                    console=console
                )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not connect to ChromaDB: {e}[/yellow]")
            console.print("[dim]Starting without RAG support...[/dim]")
            collection_name = None
    
    # Run the app
    console.print(f"[dim]DEBUG: Passing collection_name='{collection_name}' to app[/dim]")
    app_run(collection_name=collection_name)


if __name__ == "__main__":
    main()
