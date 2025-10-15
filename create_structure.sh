#!/bin/bash

# Script to create empty file and folder structure
# Usage: ./create_structure.sh [project_name]

PROJECT_NAME=${1:-"distributed-job-queue"}

echo "Creating project structure: $PROJECT_NAME"
echo "=========================================="

# Create main project directory
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Create directories
echo "Creating directories..."
mkdir -p tests
mkdir -p scripts
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Create main Python files
echo "Creating Python files..."
touch app.py
touch tasks.py
touch worker.py
touch requirements.txt

# Create Docker files
echo "Creating Docker files..."
touch Dockerfile
touch Dockerfile.worker
touch docker-compose.yml

# Create test files
echo "Creating test files..."
touch tests/__init__.py
touch tests/test_app.py
touch tests/test_integration.py

# Create scripts
echo "Creating scripts..."
touch scripts/benchmark.py

# Create monitoring configs
echo "Creating monitoring configs..."
touch monitoring/prometheus.yml
touch monitoring/grafana/datasources/datasource.yml
touch monitoring/grafana/dashboards/dashboard.yml
touch monitoring/grafana/dashboards/job-queue.json

# Create configuration files
echo "Creating configuration files..."
touch pytest.ini
touch Makefile
touch .gitignore
touch .env.example
touch README.md
touch setup.sh

# Make shell scripts executable
chmod +x setup.sh

echo ""
echo "=========================================="
echo "Project structure created successfully!"
echo "=========================================="
echo ""
echo "Directory: $PROJECT_NAME/"
echo ""
echo "Files created:"
echo "  - app.py"
echo "  - tasks.py"
echo "  - worker.py"
echo "  - requirements.txt"
echo "  - Dockerfile"
echo "  - Dockerfile.worker"
echo "  - docker-compose.yml"
echo "  - pytest.ini"
echo "  - Makefile"
echo "  - .gitignore"
echo "  - .env.example"
echo "  - README.md"
echo "  - setup.sh"
echo "  - tests/__init__.py"
echo "  - tests/test_app.py"
echo "  - tests/test_integration.py"
echo "  - scripts/benchmark.py"
echo "  - monitoring/prometheus.yml"
echo "  - monitoring/grafana/datasources/datasource.yml"
echo "  - monitoring/grafana/dashboards/dashboard.yml"
echo "  - monitoring/grafana/dashboards/job-queue.json"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. Add your code to the empty files"
echo "  3. Run: docker-compose up -d"
echo ""