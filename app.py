"""Main TUI application for the technical support assistant."""
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Input, RichLog, Label, LoadingIndicator, Markdown
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
from rich.text import Text
from rich.markdown import Markdown as RichMarkdown

from tech_support.agent import Agent
from tech_support.rag import RAG


class ReferencesList(Static):
    """Widget to display clickable references."""
    
    references = reactive([])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "References"
        self._reference_map = {}  # Store chunk_id mapping
        
    def watch_references(self, references):
        """Update the display when references change."""
        if not references:
            self.update("[dim]No references yet[/dim]")
            self._reference_map = {}
            return
        
        content = []
        self._reference_map = {}
        
        for i, ref in enumerate(references, 1):
            # Unpack based on tuple size (old format: 3, new format: 4)
            if len(ref) == 4:
                title, chunk_id, filename, preview = ref
                self._reference_map[i] = chunk_id
                # Use @click action with proper syntax
                content.append(f"[b cyan][@click='show_chunk({i})']{i}. {title}[/][/b cyan]\n[dim]{preview}[/dim]")
            else:
                # Fallback for old format
                title, url, filename = ref
                content.append(f"[b]{i}. {title}[/b]")
        
        self.update("\n\n".join(content))
    
    def on_click(self, event):
        """Handle clicks on references."""
        # Clicks are handled via action_show_chunk now
        pass


class ConversationHistory(RichLog):
    """Widget to display conversation history."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.border_title = "Conversation"
        self.can_focus = False
        
    def add_user_message(self, message: str):
        """Add a user message to the conversation."""
        self.write(Text(f"You: {message}", style="bold cyan"))
        
    def add_agent_message(self, message: str):
        """Add an agent response to the conversation."""
        self.write(Text(f"Assistant: {message}", style="bold green"))
    
    def remove_last_line(self):
        """Remove the last line from the log (for removing loading indicator)."""
        # RichLog doesn't support removal, so we'll just add a blank line to separate
        pass
        
    def add_loading(self):
        """Add a loading indicator."""
        self.write(Text("Assistant is thinking...", style="dim italic"))


class DocumentViewer(Container):
    """Widget to display markdown documents."""
    
    def __init__(self, rag: RAG, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rag = rag
        self.border_title = "Document Chunk"
        self.display = False
        
    def compose(self) -> ComposeResult:
        """Compose the document viewer."""
        yield Static("[dim]Click on a reference above to view the document chunk.[/dim]", id="doc-content")
        
    def show_chunk(self, chunk_id: str):
        """Show a specific document chunk."""
        content = self.rag.get_document_chunk(chunk_id)
        if content:
            # Format as markdown with the chunk content
            formatted = f"# Document Chunk\n\n```\n{content}\n```"
            self.query_one("#doc-content", Static).update(formatted)
        else:
            self.query_one("#doc-content", Static).update("[red]Failed to load document chunk[/red]")


class TechSupportApp(App):
    """Main application for the technical support assistant."""
    
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #left-panel {
        width: 30%;
        height: 100%;
        border: solid green;
    }
    
    #main-panel {
        width: 70%;
        height: 100%;
        layout: vertical;
    }
    
    #conversation {
        height: 80%;
        border: solid blue;
        padding: 1;
    }
    
    #input-container {
        height: auto;
        border: solid yellow;
        padding: 1;
    }
    
    #references {
        height: 50%;
        border: solid magenta;
        padding: 1;
        overflow-y: auto;
    }
    
    #doc-viewer {
        height: 50%;
        border: solid cyan;
        padding: 1;
        overflow-y: auto;
    }
    
    Input {
        width: 100%;
    }
    
    LoadingIndicator {
        height: auto;
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    def __init__(self, collection_name: str = None, **kwargs):
        super().__init__(**kwargs)
        self.collection_name = collection_name
        print(f"DEBUG TechSupportApp: Initializing with collection_name='{collection_name}'")
        self.agent = Agent(collection_name=collection_name)
        self.rag = RAG(collection_name=collection_name)
        self.is_loading = False
        
    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        
        with Horizontal():
            # Left panel for references and document viewer
            with Vertical(id="left-panel"):
                yield ReferencesList(id="references")
                yield DocumentViewer(self.rag, id="doc-viewer")
            
            # Main panel for conversation and input
            with Vertical(id="main-panel"):
                yield ConversationHistory(id="conversation")
                with Container(id="input-container"):
                    yield Label("Ask a question:")
                    yield Input(placeholder="Type your question here...", id="user-input")
                    yield LoadingIndicator(id="loading")
        
        yield Footer()
    
    def on_mount(self):
        """Initialize the app when mounted."""
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = False
        
        # Welcome message
        conv = self.query_one("#conversation", ConversationHistory)
        conv.write(Text("Welcome to the Technical Support Assistant!", style="bold magenta"))
        conv.write(Text("Ask any question and I'll help you find the answer.", style="dim"))
    
    async def on_input_submitted(self, event: Input.Submitted):
        """Handle user input submission."""
        if self.is_loading:
            return
            
        user_input = event.value.strip()
        if not user_input:
            return
        
        # Clear input and disable it
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""
        input_widget.disabled = True
        
        # Show loading indicator
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = True
        self.is_loading = True
        
        # Add user message to conversation
        conv = self.query_one("#conversation", ConversationHistory)
        conv.add_user_message(user_input)
        
        # Get response from agent (in background) - don't show loading text
        self.get_agent_response(user_input)
    
    @work(exclusive=True)
    async def get_agent_response(self, user_input: str):
        """Get response from the agent (runs in background)."""
        try:
            # Get response from agent
            response, references = await self.agent.message(user_input)
            
            # Update UI
            conv = self.query_one("#conversation", ConversationHistory)
            conv.add_agent_message(response)
            
            # Debug: Log what we got
            conv.write(Text(f"DEBUG: Got {len(references)} references", style="yellow"))
            for i, ref in enumerate(references[:2], 1):  # Show first 2
                conv.write(Text(f"  Ref {i}: {ref[0]}", style="dim"))
            
            # Update references
            refs = self.query_one("#references", ReferencesList)
            # Use call_after_refresh to ensure UI update happens on main thread
            self.call_after_refresh(self._update_references, refs, references)
            
        finally:
            # Re-enable input and hide loading
            input_widget = self.query_one("#user-input", Input)
            input_widget.disabled = False
            input_widget.focus()
            
            loading = self.query_one("#loading", LoadingIndicator)
            loading.display = False
            self.is_loading = False
    
    def _update_references(self, refs_widget, references):
        """Update references widget (called on main thread)."""
        refs_widget.references = references
    
    def action_show_chunk(self, ref_id: str):
        """Handle clicking a reference to show its chunk."""
        try:
            ref_num = int(ref_id)
            refs = self.query_one("#references", ReferencesList)
            
            if ref_num in refs._reference_map:
                chunk_id = refs._reference_map[ref_num]
                doc_viewer = self.query_one("#doc-viewer", DocumentViewer)
                doc_viewer.show_chunk(chunk_id)
        except (ValueError, KeyError) as e:
            # Log to conversation for debugging
            conv = self.query_one("#conversation", ConversationHistory)
            conv.write(Text(f"Error showing chunk: {e}", style="red"))


def run(collection_name: str = None):
    """Run the application in TUI mode."""
    app = TechSupportApp(collection_name=collection_name)
    app.run()


def serve():
    """Serve the application in web mode."""
    from rich.console import Console
    from rich.prompt import Prompt
    
    console = Console()
    console.print("[yellow]Note: textual-web requires cloud service setup.[/yellow]")
    console.print("[dim]For production web deployment, consider using textual-web CLI separately.[/dim]")
    
    # Ask for collection
    try:
        rag = RAG()
        client = rag._get_client()
        collections = client.list_collections()
        
        if not collections:
            console.print("[yellow]No collections found. Starting without RAG support.[/yellow]")
            collection_name = None
        else:
            console.print("\n[bold cyan]Available collections:[/bold cyan]")
            for i, col in enumerate(collections, 1):
                console.print(f"  {i}. {col.name}")
            
            collection_name = Prompt.ask(
                "\n[bold cyan]Enter collection name[/bold cyan]",
                default=collections[0].name if collections else "",
                console=console
            )
    except Exception as e:
        console.print(f"[yellow]Could not connect to ChromaDB: {e}[/yellow]")
        collection_name = None
    
    console.print("\n[green]Starting TUI mode...[/green]\n")
    app = TechSupportApp(collection_name=collection_name)
    app.run()
