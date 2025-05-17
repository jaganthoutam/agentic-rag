#!/usr/bin/env python3
"""
PDF File Adder for Agentic RAG

This script helps users add PDF files to the data folder for processing by the Agentic RAG system.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


def setup_data_folder():
    """Create the data folder if it doesn't exist."""
    data_folder = Path("./data")
    if not data_folder.exists():
        data_folder.mkdir(parents=True)
        print(f"Created data folder at {data_folder.absolute()}")
    return data_folder


def copy_pdf_files(source_paths, data_folder):
    """
    Copy PDF files to the data folder.
    
    Args:
        source_paths: List of paths to PDF files or directories
        data_folder: Path to the data folder
    """
    copied_files = []
    
    for source_path in source_paths:
        source_path = Path(source_path)
        
        if not source_path.exists():
            print(f"Warning: {source_path} does not exist, skipping")
            continue
        
        if source_path.is_file():
            # Copy a single file
            if source_path.suffix.lower() == '.pdf':
                dest_path = data_folder / source_path.name
                
                # Check if source and destination are the same file
                if source_path.samefile(dest_path):
                    print(f"File {source_path} is already in the data folder, skipping")
                    copied_files.append(dest_path)  # Still count it as processed
                    continue
                
                shutil.copy2(source_path, dest_path)
                copied_files.append(dest_path)
                print(f"Copied {source_path} to {dest_path}")
            else:
                print(f"Warning: {source_path} is not a PDF file, skipping")
        
        elif source_path.is_dir():
            # Copy all PDF files from a directory
            for pdf_file in source_path.glob("**/*.pdf"):
                dest_path = data_folder / pdf_file.name
                
                # Check if source and destination are the same file
                if pdf_file.samefile(dest_path):
                    print(f"File {pdf_file} is already in the data folder, skipping")
                    copied_files.append(dest_path)  # Still count it as processed
                    continue
                
                shutil.copy2(pdf_file, dest_path)
                copied_files.append(dest_path)
                print(f"Copied {pdf_file} to {dest_path}")
    
    return copied_files


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Add PDF files to the Agentic RAG data folder"
    )
    parser.add_argument(
        "paths", 
        nargs="+", 
        help="Paths to PDF files or directories containing PDF files"
    )
    parser.add_argument(
        "--data-folder", 
        default="./data", 
        help="Path to the data folder (default: ./data)"
    )
    
    args = parser.parse_args()
    
    # Setup data folder
    data_folder = Path(args.data_folder)
    if not data_folder.exists():
        data_folder.mkdir(parents=True)
        print(f"Created data folder at {data_folder.absolute()}")
    
    # Copy PDF files
    copied_files = copy_pdf_files(args.paths, data_folder)
    
    # Print summary
    if copied_files:
        print(f"\nSuccessfully processed {len(copied_files)} PDF files:")
        for file in copied_files:
            print(f"  - {file.name}")
        print("\nYou can now query the Agentic RAG system about these PDF files.")
    else:
        print("\nNo PDF files were added to the data folder.")
        print("Make sure the paths you provided contain PDF files.")


if __name__ == "__main__":
    main() 