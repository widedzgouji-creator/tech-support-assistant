"""Agent class for handling conversations."""
import os
import asyncio
from typing import Optional, Tuple, List, Dict
from tech_support.rag import RAG
from tech_support.logger import get_logger
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Agent:
    """AI agent that responds to user messages with RAG-based references."""
    
    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize the agent with optional RAG collection.
        
        Args:
            collection_name: Name of the ChromaDB collection to use for RAG
        """
        self.collection_name = collection_name
        self.rag = RAG(collection_name=collection_name) if collection_name else None
        self.logger = get_logger()
        
        # Load thresholds from environment
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
        self.uncertain_distance_threshold = float(os.getenv("UNCERTAIN_DISTANCE_THRESHOLD", "0.8"))
        
        # Initialize GitHub Models client
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.model = os.getenv("GITHUB_MODEL", "openai/gpt-4.1")
        self.endpoint = "https://models.github.ai/inference"
        
        if self.github_token:
            self.client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.github_token),
            )
        else:
            print("WARNING: GITHUB_TOKEN not found. Agent will not be able to generate responses.")
            self.client = None
    
    async def message(self, user_input: str) -> Dict:
        """
        Process a user message and return a response with references and confidence metrics.
        
        Args:
            user_input: The user's question or message
            
        Returns:
            A dictionary with:
            - response: The generated response text
            - references: List of (title, chunk_id, filename, document_preview) tuples
            - confidence: Confidence score (0-1)
            - is_uncertain: Whether the answer is uncertain
            - escalated: Whether this should be escalated to a human
        """
        references = []
        context_docs = []
        retrieved_chunks = []
        confidence = 0.0
        min_distance = 1.0
        
        # Perform RAG search if available
        if self.rag and self.collection_name:
            try:
                results = self.rag.search(user_input, n_results=5)
                print(f"DEBUG Agent: RAG search returned {len(results)} results")
                
                for result in results:
                    metadata = result['metadata']
                    chunk_id = result['id']
                    filename = metadata.get('filename', 'Unknown')
                    chunk_index = metadata.get('chunk_index', 0)
                    document = result['document']
                    distance = result['distance']
                    
                    # Track minimum distance for confidence calculation
                    if distance < min_distance:
                        min_distance = distance
                    
                    # Create a preview of the document
                    doc_preview = document[:100] + "..." if len(document) > 100 else document
                    
                    # Title format: filename (chunk X)
                    title = f"{filename} (chunk {chunk_index + 1})"
                    
                    references.append((title, chunk_id, filename, doc_preview))
                    context_docs.append(f"[{filename} - chunk {chunk_index + 1}]\n{document}")
                    retrieved_chunks.append({
                        'chunk_id': chunk_id,
                        'filename': filename,
                        'distance': distance
                    })
                    
            except Exception as e:
                print(f"RAG search error: {e}")
                import traceback
                traceback.print_exc()
                self.logger.log_query(
                    query=user_input,
                    collection=self.collection_name,
                    retrieved_chunks=[],
                    confidence=0.0,
                    is_uncertain=True,
                    escalated=True,
                    response="",
                    error=str(e)
                )
        
        # Calculate confidence based on retrieval distance
        # Lower distance = higher confidence
        # Convert distance (0-2 for cosine) to confidence (0-1)
        if retrieved_chunks:
            confidence = max(0.0, 1.0 - min_distance)
        
        # Determine uncertainty and escalation
        is_uncertain = min_distance > self.uncertain_distance_threshold
        escalated = confidence < self.confidence_threshold
        
        # Generate response using LLM
        if not self.client:
            response = "Error: GITHUB_TOKEN not configured. Please set your GitHub token in .env file."
        else:
            try:
                # Build context from retrieved documents
                if context_docs:
                    context = "\n\n---\n\n".join(context_docs)
                    system_prompt = f"""You are a helpful technical support assistant. Answer the user's question based on the following documentation excerpts. If the answer is not in the documentation, say so.

Documentation:
{context}"""
                else:
                    system_prompt = "You are a helpful technical support assistant. Answer the user's question to the best of your ability."
                
                # Call GitHub Models API
                result = self.client.complete(
                    messages=[
                        SystemMessage(system_prompt),
                        UserMessage(user_input),
                    ],
                    temperature=0.7,
                    top_p=0.95,
                    max_tokens=500,
                    model=self.model
                )
                
                response = result.choices[0].message.content
                
            except Exception as e:
                print(f"LLM error: {e}")
                import traceback
                traceback.print_exc()
                response = f"Error generating response: {str(e)}"
                self.logger.log_query(
                    query=user_input,
                    collection=self.collection_name,
                    retrieved_chunks=retrieved_chunks,
                    confidence=confidence,
                    is_uncertain=is_uncertain,
                    escalated=escalated,
                    response="",
                    error=str(e)
                )
        
        # Log the query
        self.logger.log_query(
            query=user_input,
            collection=self.collection_name,
            retrieved_chunks=retrieved_chunks,
            confidence=confidence,
            is_uncertain=is_uncertain,
            escalated=escalated,
            response=response
        )
        
        return {
            'response': response,
            'references': references,
            'confidence': confidence,
            'is_uncertain': is_uncertain,
            'escalated': escalated
        }
