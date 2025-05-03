"""
Example usage of the Agentic RAG system.

This script demonstrates how to use the Agentic RAG system for query processing.
"""

import argparse
import json
import logging
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import Query
from app import AgenticRag


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def process_query(rag, query_text):
    """
    Process a query and print the results.
    
    Args:
        rag: Initialized AgenticRag instance
        query_text: Text of the query to process
    """
    print(f"\n=== Processing Query: '{query_text}' ===\n")
    
    start_time = time.time()
    query = Query(text=query_text)
    result = rag.process_query(query.text)
    
    print(f"Query ID: {result.query_id}")
    print(f"Processing Time: {result.processing_time:.2f}s")
    print(f"Confidence: {result.confidence:.2f}")
    print("\nResponse:")
    print("-" * 80)
    print(result.response)
    print("-" * 80)
    
    print("\nMetadata:")
    print(json.dumps(result.metadata, indent=2))
    
    if result.documents:
        print(f"\nSupporting Documents: {len(result.documents)}")
        for i, doc in enumerate(result.documents[:3]):  # Show only first 3
            print(f"\nDocument {i+1}: {doc.source}")
            print(doc.content[:200] + "..." if len(doc.content) > 200 else doc.content)
        
        if len(result.documents) > 3:
            print(f"\n... and {len(result.documents) - 3} more documents")
    
    total_time = time.time() - start_time
    print(f"\nTotal execution time: {total_time:.2f}s")


def test_search_agent():
    """Test the search agent with Kagi API."""
    # Import the search agent
    from agents.search import SearchAgent
    from core import Query
    
    # Get API key from environment
    api_key = os.environ.get("SEARCH_API_KEY")
    if not api_key:
        print("WARNING: SEARCH_API_KEY environment variable not set")
        print("Using mock search instead")
    
    # Create a search agent
    search_agent = SearchAgent(
        engine="kagi",
        api_key=api_key,
        max_results=5
    )
    
    # Create a test query
    query = Query(text="What is retrieval-augmented generation?")
    
    # Process the query
    print("Testing search agent...")
    result = search_agent.process(query)
    
    # Print results
    print(f"\nSearch results (confidence: {result.confidence:.2f}):")
    for i, doc in enumerate(result.documents):
        print(f"\n[{i+1}] {doc.metadata.get('title', 'No title')}")
        print(f"URL: {doc.source}")
        print(doc.content[:200] + "..." if len(doc.content) > 200 else doc.content)


def run_example_queries(config_path):
    """
    Run example queries through the Agentic RAG system.
    
    Args:
        config_path: Path to the configuration file
    """
    # Initialize the RAG system
    print(f"Initializing Agentic RAG system with config: {config_path}")
    rag = AgenticRag(config_path=config_path)
    
    try:
        # Example queries
        example_queries = [
            "What are the latest developments in AI research?",
            "How do I optimize AWS S3 storage costs?",
            "Summarize the sales data from the last quarter.",
            "What is retrieval-augmented generation?",
            "Compare the performance of different memory models."
        ]
        
        for query in example_queries:
            process_query(rag, query)
            print("\n" + "=" * 80 + "\n")
        
        # Interactive mode
        print("Enter 'quit' or 'exit' to end the session.")
        print("Enter 'test-search' to test the search agent directly.")
        
        while True:
            user_input = input("\nEnter your query: ")
            
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if user_input.lower() == 'test-search':
                test_search_agent()
                continue
            
            process_query(rag, user_input)
    
    finally:
        # Clean up
        rag.shutdown()
        print("Agentic RAG system shut down.")


if __name__ == "__main__":
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Agentic RAG Example")
    parser.add_argument("--config", default="../config.json", help="Path to configuration file")
    parser.add_argument("--test-search", action="store_true", help="Test search agent directly")
    args = parser.parse_args()
    
    if args.test_search:
        test_search_agent()
    else:
        run_example_queries(args.config)