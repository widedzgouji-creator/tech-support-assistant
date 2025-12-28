"""Flask web interface for the technical support assistant."""
import os
import asyncio
from flask import Flask, render_template, request, jsonify
from tech_support.agent import Agent
from tech_support.rag import RAG
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Store agents per collection
agents = {}
rags = {}


def get_collections():
    """Get list of available collections."""
    try:
        rag = RAG()
        client = rag._get_client()
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        return []


def get_agent(collection_name):
    """Get or create an agent for a collection."""
    if collection_name not in agents:
        agents[collection_name] = Agent(collection_name=collection_name)
        rags[collection_name] = RAG(collection_name=collection_name)
    return agents[collection_name], rags[collection_name]


@app.route('/')
def index():
    collections = get_collections()
    return render_template('index.html', collections=collections)


@app.route('/api/query', methods=['POST'])
def query():
    """Handle user query."""
    data = request.json
    user_query = data.get('query', '')
    collection = data.get('collection', '')
    
    if not user_query or not collection:
        return jsonify({'error': 'Missing query or collection'}), 400
    
    try:
        agent, rag = get_agent(collection)
        
        # Run async query
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(agent.message(user_query))
        loop.close()
        
        # Format references
        references = []
        for title, chunk_id, filename, preview in result['references']:
            references.append({
                'title': title,
                'chunk_id': chunk_id,
                'filename': filename,
                'preview': preview
            })
        
        return jsonify({
            'response': result['response'],
            'confidence': result['confidence'],
            'is_uncertain': result['is_uncertain'],
            'escalated': result['escalated'],
            'references': references
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/collection-stats', methods=['POST'])
def collection_stats():
    """Get collection statistics."""
    data = request.json
    collection = data.get('collection', '')
    
    if not collection:
        return jsonify({'error': 'Missing collection'}), 400
    
    try:
        _, rag = get_agent(collection)
        coll = rag._get_collection()
        count = coll.count()
        
        # Get file statistics
        sample = coll.get(limit=min(count, 500), include=["metadatas"])
        files = {}
        for meta in sample['metadatas']:
            filename = meta.get('filename', 'unknown')
            files[filename] = files.get(filename, 0) + 1
        
        return jsonify({
            'total_chunks': count,
            'total_files': len(files),
            'files': [{'name': name, 'chunks': chunks} for name, chunks in sorted(files.items())]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chunk-content', methods=['POST'])
def chunk_content():
    """Get full content of a specific chunk."""
    data = request.json
    collection = data.get('collection', '')
    chunk_id = data.get('chunk_id', '')
    
    if not collection or not chunk_id:
        return jsonify({'error': 'Missing collection or chunk_id'}), 400
    
    try:
        _, rag = get_agent(collection)
        content = rag.get_document_chunk(chunk_id)
        
        if content:
            return jsonify({'content': content})
        else:
            return jsonify({'error': 'Chunk not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
