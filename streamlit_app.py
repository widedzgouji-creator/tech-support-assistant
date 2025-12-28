"""Streamlit web interface for the technical support assistant."""
import streamlit as st
from tech_support.agent import Agent
from tech_support.rag import RAG
import asyncio


def get_collections():
    """Get list of available collections."""
    try:
        rag = RAG()
        client = rag._get_client()
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        st.error(f"Could not connect to ChromaDB: {e}")
        return []


def main():
    st.set_page_config(
        page_title="Tech Support Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for modern UI
    st.markdown("""
        <style>
        /* Hide default sidebar */
        section[data-testid="stSidebar"] {
            display: none;
        }
        
        /* Main container adjustments */
        .main .block-container {
            padding: 0;
            max-width: 100%;
        }
        
        /* Sticky header bar */
        .header-container {
            position: sticky;
            top: 0;
            background: white;
            z-index: 999;
            padding: 1rem 2rem;
            border-bottom: 2px solid #e9ecef;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Content area with padding */
        .content-area {
            padding: 2rem;
        }
        
        /* Chat messages styling */
        .stChatMessage {
            padding: 1.25rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            border: 1px solid #e9ecef;
        }
        
        /* User message */
        .stChatMessage[data-testid*="user"] {
            background-color: #f8f9fa;
        }
        
        /* Assistant message */
        .stChatMessage[data-testid*="assistant"] {
            background-color: white;
        }
        
        /* Debug panel styling */
        .debug-panel {
            background-color: #f8f9fa;
            border-left: 3px solid #6c757d;
            border-radius: 0.5rem;
            padding: 1rem;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.85rem;
            max-height: calc(100vh - 180px);
            overflow-y: auto;
            position: sticky;
            top: 140px;
        }
        
        /* Input area styling */
        section[data-testid="stChatInput"] {
            padding: 1rem 2rem;
            background: white;
            border-top: 1px solid #e9ecef;
        }
        
        /* Hide expanders and badges */
        .stExpander, .confidence-badge {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Sticky header with input at top
    with st.container():
        st.markdown('<div class="header-container">', unsafe_allow_html=True)
        
        # Header row
        header_col1, header_col2, header_col3 = st.columns([3, 2, 1])
        
        with header_col1:
            st.markdown("# 🤖 Tech Support Assistant")
        
        with header_col2:
            collections = get_collections()
            
            if not collections:
                st.error("No collections found. Please ingest documents first.")
                st.code("make ingest FOLDER=path/to/docs")
                st.stop()
            
            selected_collection = st.selectbox(
                "Knowledge Base",
                collections,
                label_visibility="collapsed"
            )
        
        with header_col3:
            debug_mode = st.toggle("🐛 Debug", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "msg_counter" not in st.session_state:
        st.session_state.msg_counter = 0
    
    if "last_debug_info" not in st.session_state:
        st.session_state.last_debug_info = None
    
    if "agent" not in st.session_state or st.session_state.get("collection") != selected_collection:
        st.session_state.agent = Agent(collection_name=selected_collection)
        st.session_state.rag = RAG(collection_name=selected_collection)
        st.session_state.collection = selected_collection
    
    # Input area at top
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    prompt = st.chat_input("💬 Ask a question about the documentation...", key="chat_input_top")
    
    if prompt:
        # Increment message counter for unique keys
        st.session_state.msg_counter += 1
        
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "msg_id": st.session_state.msg_counter
        })
        
        # Get agent response
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            st.session_state.agent.message(prompt)
        )
        loop.close()
        
        # Extract response data
        response = result['response']
        references = result['references']
        confidence = result['confidence']
        is_uncertain = result['is_uncertain']
        escalated = result['escalated']
        
        # Store debug info
        st.session_state.last_debug_info = {
            'query': prompt,
            'confidence': confidence,
            'is_uncertain': is_uncertain,
            'escalated': escalated,
            'num_references': len(references),
            'references': references
        }
        
        # Add assistant message to history
        st.session_state.msg_counter += 1
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "references": references,
            "confidence": confidence,
            "is_uncertain": is_uncertain,
            "escalated": escalated,
            "msg_id": st.session_state.msg_counter
        })
        
        st.rerun()
    
    # Main layout: conversation on left, debug on right
    if debug_mode:
        col1, col2 = st.columns([2.5, 1.5])
    else:
        col1 = st.container()
        col2 = None
    
    with col1:
        # Display chat messages (clean, no confidence or references)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Debug panel on the right
    if col2 is not None:
        with col2:
            st.markdown("### 🐛 Debug Information")
            
            # Collection statistics
            with st.expander("📊 Collection Stats", expanded=True):
                try:
                    rag = RAG(collection_name=selected_collection)
                    collection = rag._get_collection()
                    count = collection.count()
                    
                    st.metric("Total Chunks", f"{count:,}")
                    st.caption(f"Collection: `{selected_collection}`")
                    
                    # Get unique files
                    sample = collection.get(limit=min(count, 500), include=["metadatas"])
                    files = {}
                    for meta in sample['metadatas']:
                        filename = meta.get('filename', 'unknown')
                        files[filename] = files.get(filename, 0) + 1
                    
                    st.metric("Unique Files", len(files))
                    
                    with st.expander("📁 File List", expanded=False):
                        for filename, chunk_count in sorted(files.items()):
                            st.text(f"• {filename} ({chunk_count})")
                            
                except Exception as e:
                    st.error(f"Error: {e}")
            
            # Last query debug info
            if st.session_state.last_debug_info:
                with st.expander("🔍 Last Query Analysis", expanded=True):
                    info = st.session_state.last_debug_info
                    
                    st.markdown("**Query:**")
                    st.code(info['query'], language=None)
                    
                    st.markdown("**Metrics:**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Confidence", f"{info['confidence']:.1%}")
                    with col_b:
                        st.metric("Sources", info['num_references'])
                    
                    st.markdown("**Flags:**")
                    st.text(f"• Uncertain: {'Yes' if info['is_uncertain'] else 'No'}")
                    st.text(f"• Escalated: {'Yes' if info['escalated'] else 'No'}")
                    
                    if info['references']:
                        st.markdown("**Retrieved Chunks:**")
                        for i, ref in enumerate(info['references'], 1):
                            title, chunk_id, filename, preview = ref
                            with st.expander(f"{i}. {filename}", expanded=False):
                                st.caption(f"Chunk ID: `{chunk_id}`")
                                st.text(preview)
            else:
                st.info("Send a query to see debug information")
            
            # Configuration
            with st.expander("⚙️ Configuration", expanded=False):
                st.markdown("**Thresholds:**")
                st.text(f"• Confidence: {st.session_state.agent.confidence_threshold}")
                st.text(f"• Uncertainty: {st.session_state.agent.uncertain_distance_threshold}")
                
                st.markdown("**Model:**")
                st.text(f"• LLM: {st.session_state.agent.model}")
                st.text(f"• Embeddings: BAAI/bge-small-en-v1.5")


if __name__ == "__main__":
    main()
