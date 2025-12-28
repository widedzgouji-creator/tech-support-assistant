"""Logging system for tracking queries, chunks, and confidence scores."""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class SupportLogger:
    """Logger for the support assistant system."""
    
    def __init__(self):
        """Initialize the logger."""
        log_file = os.getenv("LOG_FILE", "logs/support_assistant.log")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("SupportAssistant")
        self.json_log_file = log_path.parent / f"{log_path.stem}_structured.jsonl"
    
    def log_query(
        self,
        query: str,
        collection: str,
        retrieved_chunks: List[Dict],
        confidence: float,
        is_uncertain: bool,
        escalated: bool,
        response: str,
        error: Optional[str] = None
    ):
        """
        Log a complete query interaction.
        
        Args:
            query: The user's question
            collection: Collection name used
            retrieved_chunks: List of retrieved chunk data
            confidence: Confidence score (0-1)
            is_uncertain: Whether uncertainty was detected
            escalated: Whether human escalation was suggested
            response: The generated response
            error: Any error that occurred
        """
        # Log to standard logger
        self.logger.info(
            f"Query: '{query[:50]}...' | Collection: {collection} | "
            f"Confidence: {confidence:.3f} | Uncertain: {is_uncertain} | "
            f"Escalated: {escalated}"
        )
        
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "collection": collection,
            "retrieved_chunks": [
                {
                    "chunk_id": chunk.get("id"),
                    "filename": chunk.get("metadata", {}).get("filename"),
                    "chunk_index": chunk.get("metadata", {}).get("chunk_index"),
                    "distance": chunk.get("distance"),
                    "preview": chunk.get("document", "")[:100]
                }
                for chunk in retrieved_chunks
            ],
            "confidence": confidence,
            "is_uncertain": is_uncertain,
            "escalated": escalated,
            "response": response,
            "error": error
        }
        
        # Append to JSONL file
        with open(self.json_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_error(self, error_msg: str, context: Optional[Dict] = None):
        """Log an error with optional context."""
        self.logger.error(f"Error: {error_msg} | Context: {context}")
    
    def get_stats(self) -> Dict:
        """
        Get statistics from the log file.
        
        Returns:
            Dictionary with statistics
        """
        if not self.json_log_file.exists():
            return {
                "total_queries": 0,
                "uncertain_count": 0,
                "escalated_count": 0,
                "avg_confidence": 0.0
            }
        
        total = 0
        uncertain = 0
        escalated = 0
        confidences = []
        
        with open(self.json_log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    total += 1
                    if entry.get("is_uncertain"):
                        uncertain += 1
                    if entry.get("escalated"):
                        escalated += 1
                    if entry.get("confidence") is not None:
                        confidences.append(entry["confidence"])
                except json.JSONDecodeError:
                    continue
        
        return {
            "total_queries": total,
            "uncertain_count": uncertain,
            "escalated_count": escalated,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "uncertain_percentage": (uncertain / total * 100) if total > 0 else 0.0,
            "escalated_percentage": (escalated / total * 100) if total > 0 else 0.0
        }


# Global logger instance
_logger = None

def get_logger() -> SupportLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = SupportLogger()
    return _logger
