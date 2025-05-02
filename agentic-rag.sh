#!/bin/bash

# Setup script for Agentic RAG system - empty structure only
# This script creates all the necessary directories and files without content

set -e  # Exit on any error

echo "Creating Agentic RAG folder structure..."

# Create base directory
BASE_DIR="agentic-rag"
mkdir -p $BASE_DIR
cd $BASE_DIR

# Create directory structure
mkdir -p agents
mkdir -p docs
mkdir -p examples
mkdir -p memory
mkdir -p planning
mkdir -p tests
mkdir -p .github/workflows
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/dashboards
mkdir -p logs
mkdir -p data

echo "Directory structure created."

# Create __init__.py files
touch __init__.py
touch agents/__init__.py
touch memory/__init__.py
touch planning/__init__.py
touch docs/__init__.py
touch examples/__init__.py
touch tests/__init__.py

echo "Package initialization files created."

# Create empty core files
touch core.py
touch app.py
touch api.py
touch config.json
touch .env.example
touch Dockerfile
touch docker-compose.yml
touch requirements.txt
touch requirements-dev.txt
touch README.md
touch LICENSE
touch logging_config.py

# Create empty agent files
touch agents/base.py
touch agents/aggregator.py
touch agents/search.py
touch agents/local_data.py
touch agents/cloud.py
touch agents/generative.py
touch agents/memory.py

# Create empty memory files
touch memory/base.py
touch memory/short_term.py
touch memory/long_term.py

# Create empty planning files
touch planning/base.py
touch planning/react.py
touch planning/cot.py

# Create empty test files
touch tests/test_core.py
touch tests/test_memory.py
touch tests/test_planning.py
touch tests/test_agent.py
touch tests/test_api.py

# Create empty example files
touch examples/example_usage.py

# Create empty monitoring files
touch monitoring/prometheus.yml
touch monitoring/grafana/provisioning/datasources/datasource.yml
touch monitoring/grafana/dashboards/agentic_rag_dashboard.json

# Create empty CI/CD workflow file
touch .github/workflows/ci-cd.yml

# Create empty documentation files
touch docs/configuration.md
touch docs/developer_guide.md
touch docs/troubleshooting.md

echo "All empty files created successfully!"
echo ""
echo "Folder structure for Agentic RAG system is now ready."
echo "You can now copy your content into the files as needed."