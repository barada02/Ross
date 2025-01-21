# Project Commands Reference

This document lists all the commands used throughout the project's lifecycle, from environment setup to deployment.

## Environment Setup Commands

### Conda Environment
```bash
# Create new conda environment
conda create -n snowflake-rag python=3.8

# Activate the environment
conda activate snowflake-rag

# Deactivate environment (when needed)
conda deactivate
```

### Virtual Environment (Alternative to Conda)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
.\venv\Scripts\activate

# On Unix/MacOS
source venv/bin/activate
```

## Package Installation Commands

### Initial Setup
```bash
# Install required packages
pip install -r requirements.txt

# If you need to update pip first
python -m pip install --upgrade pip

# Individual package installations (if needed)
pip install snowflake-connector-python>=2.8.0
pip install snowflake-snowpark-python<2.0.0
pip install streamlit>=1.28.0
pip install pandas>=1.3.0
pip install snowflake-core==0.9.0
```

### Package Management
```bash
# Generate requirements.txt from current environment
pip freeze > requirements.txt

# Update specific package
pip install --upgrade package_name

# Check installed packages
pip list
```

## Git Commands

### Initial Git Setup
```bash
# Initialize git repository
git init

# Configure git (if needed)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Basic Git Operations
```bash
# Check repository status
git status

# Add files to staging
git add .                    # Add all files
git add filename            # Add specific file

# Commit changes
git commit -m "Your commit message"

# Push changes to remote
git push origin master      # or main, depending on your default branch
```

### Git Branch Operations
```bash
# Create and switch to new branch
git checkout -b branch-name

# Switch branches
git checkout branch-name

# List branches
git branch

# Delete branch
git branch -d branch-name
```

### Git Remote Operations
```bash
# Add remote repository
git remote add origin https://github.com/yourusername/your-repo-name.git

# Check remote repositories
git remote -v

# Pull latest changes
git pull origin master

# Fetch updates
git fetch
```

## Streamlit Commands

### Running the Application
```bash
# Run the Streamlit app
streamlit run app.py

# Run with specific port (if needed)
streamlit run app.py --server.port 8501

# Run in debug mode
streamlit run app.py --logger.level=debug
```

### Streamlit Configuration
```bash
# Create Streamlit configuration
mkdir -p .streamlit

# View Streamlit version
streamlit --version
```

## Snowflake CLI Commands (if used)

```bash
# Login to Snowflake
snowsql -a <account> -u <user> -d <database> -s <schema> -r <role>

# Execute Snowflake script
snowsql -f script.sql
```

## Utility Commands

### Directory Operations
```bash
# Create directory
mkdir directory_name

# List directory contents
dir                  # Windows
ls                   # Unix/MacOS

# Change directory
cd directory_name
```

### File Operations
```bash
# Create empty file
type nul > filename  # Windows
touch filename       # Unix/MacOS

# Copy files
copy source destination  # Windows
cp source destination   # Unix/MacOS
```

## Deployment Commands

### Stop Application
```bash
# Windows
taskkill /F /IM streamlit.exe

# Unix/MacOS
pkill -f streamlit
```

## Common Troubleshooting Commands

```bash
# Check Python version
python --version

# Check pip version
pip --version

# Clear pip cache
pip cache purge

# Check port usage
netstat -ano | findstr :8501    # Windows
lsof -i :8501                   # Unix/MacOS
```

## Environment Variables (if needed)
```bash
# Windows
set VARIABLE_NAME=value

# Unix/MacOS
export VARIABLE_NAME=value
```

Remember to:
1. Always activate your virtual environment before running commands
2. Check the current directory before running git commands
3. Ensure proper permissions when running deployment commands
4. Keep your credentials secure and never commit them to git
