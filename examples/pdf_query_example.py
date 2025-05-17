#!/usr/bin/env python3
"""
PDF Query Example for Agentic RAG

This script demonstrates how to query the Agentic RAG system about PDF content.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests


def query_rag_api(query_text, api_url="http://localhost:8000"):
    """
    Send a query to the Agentic RAG API.
    
    Args:
        query_text: The query text
        api_url: The API URL
        
    Returns:
        The API response
    """
    url = f"{api_url}/query"
    payload = {"text": query_text}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying API: {e}")
        return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Query Agentic RAG about PDF content"
    )
    parser.add_argument(
        "query", 
        help="The query text"
    )
    parser.add_argument(
        "--api-url", 
        default="http://localhost:8000", 
        help="The API URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    print(f"Querying Agentic RAG about: {args.query}")
    print(f"API URL: {args.api_url}")
    print("-" * 50)
    
    # Send the query
    start_time = time.time()
    response = query_rag_api(args.query, args.api_url)
    elapsed_time = time.time() - start_time
    
    if not response:
        print("Failed to get a response from the API.")
        return
    
    # Print the response
    print(f"\nResponse (confidence: {response.get('confidence', 0):.2f}):")
    print("-" * 50)
    print(response.get("response", "No response"))
    print("-" * 50)
    
    # Print metadata
    metadata = response.get("metadata", {})
    if metadata:
        print("\nMetadata:")
        print(f"  Memory hit: {metadata.get('memory_hit', False)}")
        
        agent_counts = metadata.get("agent_counts", {})
        if agent_counts:
            print("  Agents used:")
            for agent_type, count in agent_counts.items():
                print(f"    - {agent_type}: {count}")
    
    print(f"\nProcessing time: {response.get('processing_time', elapsed_time):.2f}s")
    print(f"Total time: {elapsed_time:.2f}s")


if __name__ == "__main__":
    main() 