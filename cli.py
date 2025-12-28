"""CLI commands for the technical support assistant."""
import asyncio
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm

from tech_support.rag import RAG


def clear_collection_command(collection_name: str):
    """
    Clear (delete) a collection from ChromaDB.
    
    Args:
        collection_name: Name of the collection to clear
    """
    console = Console()
    
    # Confirm deletion
    confirmed = Confirm.ask(
        f"[bold yellow]⚠ Warning:[/bold yellow] This will permanently delete collection '{collection_name}'. Continue?",
        default=False,
        console=console
    )
    
    if not confirmed:
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    try:
        rag = RAG(collection_name=collection_name)
        client = rag._get_client()
        
        # Check if collection exists
        try:
            client.get_collection(collection_name)
        except Exception:
            console.print(f"[yellow]Collection '{collection_name}' does not exist.[/yellow]")
            return
        
        # Delete the collection
        client.delete_collection(collection_name)
        console.print(f"[bold green]✓[/bold green] Successfully deleted collection '{collection_name}'")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


def collection_info_command(collection_name: str = None):
    """
    Display information about collections.
    
    Args:
        collection_name: Optional specific collection name to inspect
    """
    console = Console()
    
    try:
        rag = RAG(collection_name=collection_name)
        client = rag._get_client()
        
        if collection_name:
            # Show info for specific collection
            try:
                collection = client.get_collection(collection_name)
                count = collection.count()
                metadata = collection.metadata
                
                console.print(f"\n[bold cyan]Collection: {collection_name}[/bold cyan]")
                console.print(f"[bold]Total chunks:[/bold] {count}")
                console.print(f"[bold]Metadata:[/bold] {metadata}")
                
                # Get sample documents to show file info
                if count > 0:
                    sample = collection.get(limit=min(count, 100), include=["metadatas"])
                    
                    # Count unique files
                    files = {}
                    for meta in sample['metadatas']:
                        filename = meta.get('filename', 'unknown')
                        if filename not in files:
                            files[filename] = 0
                        files[filename] += 1
                    
                    console.print(f"\n[bold]Files ({len(files)} total):[/bold]")
                    for filename, chunk_count in sorted(files.items()):
                        console.print(f"  • {filename} ({chunk_count} chunks)")
                
            except Exception as e:
                console.print(f"[yellow]Collection '{collection_name}' not found.[/yellow]")
                return
        else:
            # List all collections
            collections = client.list_collections()
            
            if not collections:
                console.print("[yellow]No collections found.[/yellow]")
                console.print("[dim]Use 'uv run ingest <folder>' to create one.[/dim]")
                return
            
            console.print(f"\n[bold cyan]Available Collections ({len(collections)}):[/bold cyan]\n")
            
            for col in collections:
                count = col.count()
                console.print(f"[bold]{col.name}[/bold]")
                console.print(f"  Chunks: {count}")
                console.print(f"  Metadata: {col.metadata}")
                console.print()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


def search_command(collection_name: str, query: str):
    """
    Search a collection with a query.
    
    Args:
        collection_name: Name of the collection to search
        query: The search query
    """
    console = Console()
    
    try:
        console.print(f"[bold cyan]Searching collection '{collection_name}'...[/bold cyan]\n")
        
        rag = RAG(collection_name=collection_name)
        results = rag.search(query, n_results=5)
        
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return
        
        console.print(f"[bold green]Found {len(results)} results:[/bold green]\n")
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            distance = result['distance']
            document = result['document']
            
            console.print(f"[bold]{i}. {metadata.get('filename', 'Unknown')} (chunk {metadata.get('chunk_index', 0) + 1})[/bold]")
            console.print(f"[dim]Distance: {distance:.4f}[/dim]")
            console.print(f"[dim]ID: {result['id']}[/dim]")
            
            # Show preview
            preview = document[:200] + "..." if len(document) > 200 else document
            console.print(f"\n{preview}\n")
            console.print("─" * 80)
            console.print()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        import traceback
        traceback.print_exc()


def ingest_command(folder_path: str):
    """
    Ingest documents from a folder into the RAG system.
    
    Args:
        folder_path: Path to the folder containing documents to ingest
    """
    console = Console()
    
    # Get folder name as default collection name
    path = Path(folder_path)
    default_collection_name = path.name
    
    # Prompt user for collection name
    collection_name = Prompt.ask(
        "[bold cyan]Enter collection name[/bold cyan]",
        default=default_collection_name,
        console=console
    )
    
    # Sanitize collection name (ChromaDB requirements)
    collection_name = collection_name.replace(" ", "_").replace("-", "_").lower()
    
    console.print(f"[bold green]Collection:[/bold green] {collection_name}")
    console.print(f"[bold green]Ingesting documents from:[/bold green] {folder_path}")
    
    rag = RAG(collection_name=collection_name)
    
    console.print(f"[bold green]Ingesting documents from:[/bold green] {folder_path}")
    
    if not path.exists():
        console.print(f"[bold red]Error:[/bold red] Path does not exist: {folder_path}")
        return
    
    async def run_ingest():
        try:
            console.print("[cyan]Starting ingestion...[/cyan]\n")
            
            def update_progress(current, total, filename, status):
                if status.startswith("REJECTED:"):
                    console.print(f"  [yellow]⊘[/yellow] {filename}: [dim]{status}[/dim]")
                elif status.startswith("ERROR:"):
                    console.print(f"  [red]✗[/red] {filename}: [red]{status}[/red]")
                elif "Done" in status:
                    console.print(f"  [green]✓[/green] {filename}: [dim]{status}[/dim]")
                elif total > 0 and current == total and "Completed" in status:
                    console.print(f"\n[bold green]{status}[/bold green]")
                # Skip intermediate progress updates for cleaner output
            
            await rag.ingest(folder_path, progress_callback=update_progress)
            
            console.print(f"\n[bold green]✓[/bold green] Successfully ingested documents into collection '{collection_name}'!")
            console.print(f"[dim]Use 'make info COLLECTION={collection_name}' to view details[/dim]")
            
        except ValueError as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        except Exception as e:
            console.print(f"\n[bold red]Unexpected error during ingestion:[/bold red] {str(e)}")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    asyncio.run(run_ingest())
