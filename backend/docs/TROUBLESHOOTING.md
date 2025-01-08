# AGENTZ Troubleshooting Guide

## Table of Contents
1. [Environment Issues](#environment-issues)
2. [Import Problems](#import-problems)
3. [Database Issues](#database-issues)
4. [Authentication Problems](#authentication-problems)
5. [Performance Issues](#performance-issues)
6. [Common Errors](#common-errors)

## Environment Issues

### Python Version Mismatch
**Problem**: Wrong Python version or multiple Python versions causing conflicts.

**Solution**:
1. Check Python version:
```bash
python --version
```

2. Ensure using Python 3.12:
```bash
pyenv install 3.12.8
pyenv global 3.12.8
```

3. Create new virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

### Virtual Environment Issues
**Problem**: Dependencies installed in wrong environment.

**Solution**:
1. Verify active environment:
```bash
which python
pip -V
```

2. Recreate environment if needed:
```bash
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Import Problems

### Module Not Found Errors
**Problem**: Python can't find imported modules.

**Solution**:
1. Check Python path:
```python
import sys
print(sys.path)
```

2. Verify package installation:
```bash
pip list | grep package-name
```

3. Install in development mode:
```bash
pip install -e .
```

### CrewAI Import Issues
**Problem**: CrewAI V1/V2 model mixing warning.

**Solution**:
1. This warning is expected and non-critical:
```
UserWarning: Mixing V1 models and V2 models is not supported
```

2. If needed, pin specific versions:
```bash
pip uninstall crewai
pip install crewai==0.11.0
```

## Database Issues

### Supabase Connection Problems
**Problem**: Can't connect to Supabase.

**Solution**:
1. Verify environment variables:
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

2. Check connection:
```python
from app.core.database import get_db
async with get_db() as db:
    result = await db.execute("SELECT 1")
```

3. Verify credentials in `.env`:
```env
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-api-key
```

### Migration Issues
**Problem**: Database migrations failing.

**Solution**:
1. Reset migrations:
```bash
alembic downgrade base
alembic upgrade head
```

2. Check migration history:
```bash
alembic history
alembic current
```

## Authentication Problems

### Clerk Authentication Issues
**Problem**: JWT verification failing.

**Solution**:
1. Verify Clerk keys:
```env
CLERK_SECRET_KEY=your-clerk-secret
CLERK_JWT_VERIFICATION_KEY=your-jwt-key
```

2. Test JWT verification:
```python
from app.core.auth import verify_token
is_valid = await verify_token(token)
```

### Token Expiration
**Problem**: Tokens expiring too quickly.

**Solution**:
1. Check token expiration in headers
2. Implement token refresh
3. Adjust token lifetime in Clerk settings

## Performance Issues

### Slow Response Times
**Problem**: API endpoints responding slowly.

**Solution**:
1. Enable logging:
```python
from loguru import logger
logger.debug(f"Request time: {end_time - start_time}")
```

2. Profile code:
```python
import cProfile
cProfile.run('function_to_profile()')
```

3. Check database queries:
```python
from app.core.database import log_queries
log_queries(True)
```

### Memory Leaks
**Problem**: Application using too much memory.

**Solution**:
1. Monitor memory usage:
```python
import psutil
process = psutil.Process()
print(process.memory_info().rss)
```

2. Use memory profiler:
```bash
pip install memory_profiler
python -m memory_profiler your_script.py
```

## Common Errors

### 1. Import Error: No module named 'app'
**Problem**: Python can't find the app package.

**Solution**:
1. Check directory structure
2. Install package in development mode:
```bash
pip install -e .
```
3. Verify `pyproject.toml`:
```toml
[tool.setuptools]
packages = ["app"]
```

### 2. WebSocket Connection Failed
**Problem**: Can't establish WebSocket connection.

**Solution**:
1. Check WebSocket URL
2. Verify CORS settings:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Database Pool Exhaustion
**Problem**: Too many database connections.

**Solution**:
1. Configure connection pooling:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10
)
```

2. Monitor active connections:
```sql
SELECT count(*) FROM pg_stat_activity;
```

### 4. Rate Limiting Errors
**Problem**: Too many requests.

**Solution**:
1. Check rate limit settings
2. Implement backoff:
```python
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
async def make_request():
    pass
```

## Debugging Tips

### 1. Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Use FastAPI Debug Mode
```bash
uvicorn app.main:app --reload --log-level debug
```

### 3. Database Query Logging
```python
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 4. Test Environment
```bash
# Run specific test with detailed output
pytest tests/test_file.py -v -s

# Debug with PDB
pytest tests/test_file.py --pdb
```

## Getting Help

1. Check the logs:
```bash
tail -f logs/agentz.log
```

2. Enable detailed error responses:
```python
app = FastAPI(debug=True)
```

3. Use the test script:
```bash
python test_imports.py
```

4. Contact support:
- Open an issue on GitHub
- Join the Discord community
- Check the documentation 