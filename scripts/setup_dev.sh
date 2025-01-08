#!/bin/bash

# Exit on error
set -e

echo "Setting up CrewAI Web development environment..."

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
cd ..
pip install pre-commit
pre-commit install

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p backend/logs
mkdir -p backend/backups

# Copy environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "Creating backend/.env from example..."
    cp backend/.env.example backend/.env
fi

if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp .env.example .env
fi

# Initialize git if not already initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Set up git hooks directory
if [ ! -d .git/hooks ]; then
    mkdir -p .git/hooks
fi

# Create git hooks
echo "Creating git hooks..."

# pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
echo "Running tests before push..."
cd backend
source .venv/bin/activate
pytest
EOF
chmod +x .git/hooks/pre-push

echo "Development environment setup complete!"
echo
echo "Next steps:"
echo "1. Update environment variables in backend/.env"
echo "2. Run 'cd backend && uvicorn app.main:app --reload' to start the development server"
echo "3. Visit http://localhost:8000/docs to view the API documentation" 