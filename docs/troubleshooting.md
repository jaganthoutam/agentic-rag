# Troubleshooting Guide

This guide provides solutions for common issues you might encounter when working with the Agentic RAG system.

## Installation Issues

### Dependency Conflicts

**Problem**: Dependency conflicts when installing requirements.

**Solution**:
- Use a virtual environment to isolate dependencies
- Try installing dependencies one by one to identify conflicts
- Update your Python version
- Check for incompatible package versions

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies one by one
pip install pydantic
pip install sqlalchemy
# ...
```

### Database Connection Issues

**Problem**: Cannot connect to the database for long-term memory.

**Solution**:
- Verify database server is running
- Check connection string in `config.json`
- Ensure database user has appropriate permissions
- Check for network issues or firewall rules

```python
# Test database connection
import sqlalchemy
engine = sqlalchemy.create_engine("postgresql://user:password@localhost:5432/memory_db")
try:
    connection = engine.connect()
    print("Connection successful")
    connection.close()
except Exception as e:
    print(f"Connection error: {str(e)}")
```

## Configuration Issues

### Invalid Configuration

**Problem**: System fails to start due to configuration errors.

**Solution**:
- Validate JSON syntax in `config.json`
- Check for missing required fields
- Ensure environment variables are set correctly
- Use a JSON validator

```bash
# Validate JSON syntax
python -c "import json; json.load(open('config.json'))"
```

### Environment Variables

**Problem**: Environment variables not being recognized.

**Solution**:
- Check that `.env` file is in the correct location
- Verify environment variable names match those in `config.json`
- Ensure environment variables are properly exported in your shell
- Use `python-dotenv` to load environment variables

```python
# Check environment variables
import os
from dotenv import load_dotenv

load_dotenv()
print(f"SEARCH_API_KEY: {os.getenv('SEARCH_API_KEY')}")
```

## Runtime Issues

### Memory Leaks

**Problem**: System memory usage grows over time.

**Solution**:
- Check for memory leaks in custom components
- Ensure all database connections are properly closed
- Monitor memory usage with tools like `psutil`
- Implement memory limits for short-term memory

```python
# Monitor memory usage
import psutil
import time

while True:
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"Memory usage: {memory_info.rss / (1024 * 1024):.2f} MB")
    time.sleep(60)
```

### High CPU Usage

**Problem**: System CPU usage is consistently high.

**Solution**:
- Profile the application to identify bottlenecks
- Optimize expensive operations
- Consider caching frequently accessed data
- Increase hardware resources

```python
# Profile a function
import cProfile

def main():
    # Your code here
    pass

cProfile.run('main()')
```

### Slow Queries

**Problem**: Some queries take too long to process.

**Solution**:
- Add logging to identify slow components
- Optimize memory retrieval
- Improve agent processing efficiency
- Consider parallel processing for independent steps
- Add timeouts for external API calls

```python
# Add timing logs
import time

def process_function():
    start_time = time.time()
    # Function code
    end_time = time.time()
    print(f"Function took {end_time - start_time:.2f} seconds")
```

## API Issues

### API Connection Refused

**Problem**: Cannot connect to the API server.

**Solution**:
- Verify the API server is running
- Check the host and port configuration
- Ensure firewall rules allow connections
- Test with a simple curl command

```bash
# Test API connection
curl http://localhost:8000/health
```

### API Timeouts

**Problem**: API requests timeout.

**Solution**:
- Increase the timeout value in `config.json`
- Optimize the processing pipeline
- Consider asynchronous processing for long-running tasks
- Add a request queue for high-load scenarios

```bash
# Test with increased timeout
curl --max-time 60 -X POST \
  http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What are the latest developments in AI research?"}'
```

## Agent Issues

### Search Agent Failures

**Problem**: Search agent fails to retrieve results.

**Solution**:
- Check the search engine API key
- Verify internet connectivity
- Ensure search engine service is available
- Check for rate limiting or quotas

```python
# Test search engine API
import requests

def test_search_api(api_key, query):
    url = f"https://api.example.com/search?q={query}&key={api_key}"
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

test_search_api("your_api_key", "test query")
```

### Generative Agent Issues

**Problem**: Generative agent produces low-quality responses.

**Solution**:
- Check the language model API key
- Adjust temperature and max tokens settings
- Improve prompt engineering
- Consider using a more capable model

```python
# Test language model API
import requests

def test_llm_api(api_key, prompt):
    url = "https://api.example.com/generate"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "prompt": prompt,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

test_llm_api("your_api_key", "Write a short paragraph about AI.")
```

## Memory Issues

### Memory Retrieval Failures

**Problem**: Memory component fails to retrieve relevant information.

**Solution**:
- Check memory configuration
- Verify database connectivity
- Improve retrieval algorithms
- Add more logging to identify the issue

```python
# Test memory retrieval
from core import Query
from memory import ShortTermMemory

memory = ShortTermMemory(capacity=1000, ttl=3600)
query = Query(text="Test query")
result = memory.retrieve(query)
print(f"Result: {result}")
```

### Long-Term Memory Issues

**Problem**: Long-term memory database errors.

**Solution**:
- Check database connection string
- Ensure tables are created correctly
- Verify database permissions
- Check for database schema changes

```python
# Check database schema
import sqlalchemy
from sqlalchemy import inspect

engine = sqlalchemy.create_engine("postgresql://user:password@localhost:5432/memory_db")
inspector = inspect(engine)

for table_name in inspector.get_table_names():
    print(f"Table: {table_name}")
    for column in inspector.get_columns(table_name):
        print(f"  Column: {column['name']}, Type: {column['type']}")
```

## Planning Issues

### Invalid Plans

**Problem**: Planners create invalid or inefficient plans.

**Solution**:
- Check planner configuration
- Add validation logic to the planner
- Improve the planning algorithm
- Add more logging to identify the issue

```python
# Validate a plan
from core import Plan

def validate_plan(plan):
    if not plan.steps:
        print("Warning: Plan has no steps")
        return False
    
    # Check for common issues
    for i, step in enumerate(plan.steps):
        print(f"Step {i+1}: {step.agent_type.value} - {step.description}")
    
    return True
```

## Docker Issues

### Container Startup Failures

**Problem**: Docker container fails to start.

**Solution**:
- Check Docker logs for error messages
- Verify configuration files are mounted correctly
- Ensure environment variables are set
- Check for port conflicts

```bash
# Check Docker logs
docker logs agentic-rag

# Run with interactive shell for debugging
docker run -it --entrypoint /bin/bash agentic-rag
```

### Container Resource Limits

**Problem**: Container runs out of resources.

**Solution**:
- Increase memory and CPU limits
- Optimize the application for lower resource usage
- Monitor resource usage with Docker stats
- Consider scaling horizontally

```bash
# Increase memory limit
docker run -m 4g agentic-rag

# Monitor resource usage
docker stats agentic-rag
```

## Performance Optimization

### Slow Memory Retrieval

**Problem**: Memory retrieval is too slow.

**Solution**:
- Implement more efficient retrieval algorithms
- Add indexes to the database
- Use caching for frequent queries
- Optimize database queries

```sql
-- Add index to long-term memory table
CREATE INDEX idx_memory_query_id ON long_term_memory_entries (query_id);
CREATE INDEX idx_memory_relevance ON long_term_memory_entries (relevance_score DESC);
```

### High Latency

**Problem**: System has high latency for query processing.

**Solution**:
- Identify bottlenecks with profiling
- Optimize the slowest components
- Implement concurrent processing where possible
- Use asynchronous API for external services

```python
# Implement async processing
import asyncio
import aiohttp

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    tasks = [
        fetch_data("https://api1.example.com"),
        fetch_data("https://api2.example.com")
    ]
    results = await asyncio.gather(*tasks)
    return results
```

## Debugging Techniques

### Enable Debug Logging

**Problem**: Need more detailed logs for debugging.

**Solution**:
- Set log level to "debug" in `config.json`
- Add more logging statements in custom components
- Use a log viewer tool
- Implement structured logging

```json
"logging": {
  "level": "debug",
  "format": "json",
  "output": "both",
  "file_path": "logs/agentic-rag.log"
}
```

### Remote Debugging

**Problem**: Need to debug in a production environment.

**Solution**:
- Use remote debugging tools
- Add endpoints for diagnostic information
- Implement health checks
- Set up monitoring and alerting

```python
# Add a diagnostic endpoint
@app.get("/diagnostic")
async def diagnostic():
    return {
        "system_health": "OK",
        "memory_stats": {
            "short_term": rag.memories.get("short_term", {}).get_stats(),
            "long_term": rag.memories.get("long_term", {}).get_stats()
        },
        "agent_stats": {
            agent_type.value: {"status": "active"}
            for agent_type in rag.agents
        }
    }
```

## Cloud Deployment Issues

### Connection Issues

**Problem**: Cloud agent cannot connect to cloud services.

**Solution**:
- Check network connectivity
- Verify credentials are correct
- Ensure proper IAM roles and permissions
- Check for service outages

```python
# Test AWS connectivity
import boto3

def test_aws_connection(access_key, secret_key, region):
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3 = session.client('s3')
        response = s3.list_buckets()
        print("Connection successful")
        print(f"Buckets: {response['Buckets']}")
    except Exception as e:
        print(f"Connection error: {str(e)}")

test_aws_connection("your_access_key", "your_secret_key", "us-west-2")
```

### Permission Issues

**Problem**: Cloud agent lacks permissions for required operations.

**Solution**:
- Check IAM roles and policies
- Verify service account permissions
- Use least privilege principle
- Add more specific error handling

```python
# Check S3 permissions
import boto3

def check_s3_permissions(bucket_name):
    s3 = boto3.client('s3')
    try:
        # Check read permissions
        s3.head_bucket(Bucket=bucket_name)
        print(f"Can access bucket: {bucket_name}")
        
        # Check write permissions
        s3.put_object(Bucket=bucket_name, Key="test.txt", Body="test")
        print(f"Can write to bucket: {bucket_name}")
        
        # Clean up
        s3.delete_object(Bucket=bucket_name, Key="test.txt")
        print(f"Can delete from bucket: {bucket_name}")
    except Exception as e:
        print(f"Permission error: {str(e)}")

check_s3_permissions("your-bucket-name")
```

## Common Error Messages

### "No module named X"

**Problem**: Missing Python module.

**Solution**:
- Install the missing package
- Check for typos in imports
- Verify virtual environment is activated
- Update requirements.txt

```bash
# Install missing package
pip install missing-package

# Update requirements
pip freeze > requirements.txt
```

### "Memory exceeds capacity"

**Problem**: Short-term memory capacity limit reached.

**Solution**:
- Increase capacity in configuration
- Implement better memory management
- Add more aggressive cleanup
- Consider upgrading to long-term memory

```json
"memory": {
  "short_term": {
    "enabled": true,
    "capacity": 5000,
    "ttl": 3600
  }
}
```

### "Database connection timeout"

**Problem**: Cannot connect to the database within the timeout period.

**Solution**:
- Check database server status
- Increase connection timeout
- Verify network connectivity
- Check for database overload

```python
# Increase connection timeout
engine = sqlalchemy.create_engine(
    "postgresql://user:password@localhost:5432/memory_db",
    connect_args={"connect_timeout": 60}
)
```

## Getting Help

If you've tried these solutions and still have issues:

1. Check the [GitHub Issues](https://github.com/yourusername/agentic-rag/issues) for similar problems
2. Review the documentation again for any missed steps
3. Post your question on [Stack Overflow](https://stackoverflow.com/) with the 'agentic-rag' tag
4. Create a new issue on GitHub with detailed information about your problem
5. Reach out to the maintainers for support

When reporting issues, include:

- System information (OS, Python version, package versions)
- Full error messages
- Configuration details (sanitized of any credentials)
- Steps to reproduce the issue
- What you've already tried