#!/usr/bin/env python3
"""
Environment setup script for Agentic RAG.

This script helps users set up their environment variables for the Agentic RAG system.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file with placeholders for required API keys."""
    env_path = Path('.env')
    
    if env_path.exists():
        print("A .env file already exists. Do you want to overwrite it? (y/n)")
        response = input().strip().lower()
        if response != 'y':
            print("Keeping existing .env file.")
            return
    
    # Get API keys from user
    print("\n=== Agentic RAG Environment Setup ===\n")
    print("Please enter your API keys (or press Enter to skip):\n")
    
    groq_api_key = input("GROQ API Key: ").strip()
    openai_api_key = input("OpenAI API Key: ").strip()
    search_api_key = input("Search API Key (optional): ").strip()
    
    # Create .env file content
    env_content = "# Environment variables for Agentic RAG\n\n"
    
    if groq_api_key:
        env_content += f"GROQ_API_KEY={groq_api_key}\n"
    else:
        env_content += "# GROQ_API_KEY=your_groq_api_key_here\n"
    
    if openai_api_key:
        env_content += f"OPENAI_API_KEY={openai_api_key}\n"
    else:
        env_content += "# OPENAI_API_KEY=your_openai_api_key_here\n"
    
    if search_api_key:
        env_content += f"SEARCH_API_KEY={search_api_key}\n"
    else:
        env_content += "# SEARCH_API_KEY=your_search_api_key_here\n"
    
    # Write to .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n.env file created at {env_path.absolute()}")
    print("You can edit this file later to update your API keys.")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import dotenv
        print("python-dotenv is installed.")
    except ImportError:
        print("python-dotenv is not installed. Installing...")
        os.system(f"{sys.executable} -m pip install python-dotenv")
        print("python-dotenv installed successfully.")

def main():
    """Main function."""
    print("Setting up environment for Agentic RAG...")
    
    # Check dependencies
    check_dependencies()
    
    # Create .env file
    create_env_file()
    
    print("\nEnvironment setup complete!")
    print("You can now run the Agentic RAG system.")

if __name__ == "__main__":
    main() 