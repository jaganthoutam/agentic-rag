# Configuration Guide

Agentic RAG uses a flexible configuration system that allows you to customize various aspects of the system. This guide explains how to configure the system to your needs.

## Configuration File

The primary configuration method is through a JSON file, typically named `config.json`. This file contains settings for all components of the system.

### Basic Structure

```json
{
  "version": "1.0.0",
  "app": {
    "name": "agentic-rag",
    "environment": "development",
    "debug": true
  },
  "logging": {
    "level": "info",
    "format": "json",
    "output": "console",
    "file_path": "logs/agentic-rag.log"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "timeout": 30,
    "cors_origins": ["*"]
  },
  "memory": {
    // Memory configuration
  },
  "planning": {
    // Planning configuration
  },
  "agents": {
    // Agents configuration
  }
}
```

## App Configuration

The `app` section contains general settings for the application:

```json
"app": {
  "name": "agentic-rag",
  "environment": "development",
  "debug": true
}
```

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `name` | string | Name of the application | `"agentic-rag"` |
| `environment` | string | Environment (`"development"`, `"production"`, `"test"`) | `"development"` |
| `debug` | boolean | Enable debug mode | `false` |

## Logging Configuration

The `logging` section controls logging behavior:

```json
"logging": {
  "level": "info",
  "format": "json",
  "output": "console",
  "file_path": "logs/agentic-rag.log"
}
```

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `level` | string | Log level (`"debug"`, `"info"`, `"warning"`, `"error"`, `"critical"`) | `"info"` |
| `format` | string | Log format (`"text"`, `"json"`) | `"text"` |
| `output` | string | Log output destination (`"console"`, `"file"`, `"both"`) | `"console"` |
| `file_path` | string | Path to log file (when `output` is `"file"` or `"both"`) | `"logs/agentic-rag.log"` |

## API Configuration

The `api` section configures the REST API:

```json
"api": {
  "host": "0.0.0.0",
  "port": 8000,
  "timeout": 30,
  "cors_origins": ["*"]
}
```

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `host` | string | Host to bind to | `"0.0.0.0"` |
| `port` | number | Port to listen on | `8000` |
| `timeout` | number | Request timeout in seconds | `30` |
| `cors_origins` | array | CORS allowed origins | `["*"]` |

## Memory Configuration

The `memory` section configures memory components:

```json
"memory": {
  "short_term": {
    "enabled": true,
    "capacity": 1000,
    "ttl": 3600
  },
  "long_term": {
    "enabled": true,
    "connection_string": "postgresql://user:password@localhost:5432/memory_db",
    "table_name": "long_term_memory"
  }
}
```

### Short-Term Memory

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable short-term memory | `true` |
| `capacity` | number | Maximum number of entries | `1000` |
| `ttl` | number | Time-to-live in seconds (0 for no expiration) | `3600` |

### Long-Term Memory

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable long-term memory | `true` |
| `connection_string` | string | Database connection string | `"postgresql://user:password@localhost:5432/memory_db"` |
| `table_name` | string | Base name for memory tables | `"long_term_memory"` |

## Planning Configuration

The `planning` section configures planning components:

```json
"planning": {
  "react": {
    "enabled": true,
    "max_steps": 10,
    "timeout": 60
  },
  "cot": {
    "enabled": true,
    "max_depth": 5
  }
}
```

### ReAct Planner

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable ReAct planner | `true` |
| `max_steps` | number | Maximum number of steps in a plan | `10` |
| `timeout` | number | Timeout in seconds for plan creation | `60` |

### Chain of Thought Planner

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable Chain of Thought planner | `true` |
| `max_depth` | number | Maximum depth of reasoning steps | `5` |

## Agents Configuration

The `agents` section configures agent components:

```json
"agents": {
  "aggregator": {
    "enabled": true,
    "timeout": 30,
    "max_agents": 5
  },
  "search": {
    "enabled": true,
    "engine": "kogi",
    "api_key": "${SEARCH_API_KEY}",
    "max_results": 10
  },
  "local_data": {
    "enabled": true,
    "data_path": "./data",
    "formats": ["csv", "json", "pdf"]
  },
  "cloud": {
    "enabled": true,
    "provider": "aws",
    "region": "us-west-2",
    "credentials": {
      "access_key": "${AWS_ACCESS_KEY}",
      "secret_key": "${AWS_SECRET_KEY}"
    }
  },
  "generative": {
    "enabled": true,
    "model": "claude-3-opus-20240229",
    "api_key": "${CLAUDE_API_KEY}",
    "max_tokens": 4000,
    "temperature": 0.7
  },
  "memory_agent": {
    "enabled": true
  }
}
```

### Aggregator Agent

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable aggregator agent | `true` |
| `timeout` | number | Timeout in seconds for aggregation | `30` |
| `max_agents` | number | Maximum number of agent results to aggregate | `5` |

### Search Agent

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable search agent | `true` |
| `engine` | string | Search engine to use | `"kogi"` |
| `api_key` | string | API key for the search engine | `""` |
| `max_results` | number | Maximum number of results to return | `10` |

### Local Data Agent

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable local data agent | `true` |
| `data_path` | string | Path to the local data directory | `"./data"` |
| `formats` | array | List of supported file formats | `["csv", "json", "pdf"]` |

### Cloud Agent

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable cloud agent | `true` |
| `provider` | string | Cloud provider (`"aws"`, `"azure"`, `"gcp"`) | `"aws"` |
| `region` | string | Cloud region | `"us-west-2"` |
| `credentials` | object | Credentials for cloud access | See below |

#### Cloud Credentials

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `access_key` | string | Access key for the cloud provider | `""` |
| `secret_key` | string | Secret key for the cloud provider | `""` |

### Generative Agent

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable generative agent | `true` |
| `model` | string | Language model to use | `"claude-3-opus-20240229"` |
| `api_key` | string | API key for the language model service | `""` |
| `max_tokens` | number | Maximum number of tokens in generated responses | `4000` |
| `temperature` | number | Temperature parameter for generation (0.0-1.0) | `0.7` |

### Memory Agent

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `enabled` | boolean | Enable memory agent | `true` |

## Environment Variables

You can use environment variables in the configuration file by using the `${VARIABLE_NAME}` syntax. For example:

```json
"api_key": "${SEARCH_API_KEY}"
```

This will be replaced with the value of the `SEARCH_API_KEY` environment variable at runtime.

## Configuration Precedence

The system follows this order of precedence for configuration (from highest to lowest):

1. Command-line arguments
2. Environment variables
3. Configuration file
4. Default values

## Using .env Files

You can also use a `.env` file to set environment variables. See `.env.example` for a template.

Example `.env` file:

```
SEARCH_API_KEY=your_api_key_here
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
CLAUDE_API_KEY=your_claude_api_key
```

## Advanced Configuration

### Custom Agent Configuration

To add a custom agent, add a new section to the `agents` object with your agent's configuration:

```json
"my_custom_agent": {
  "enabled": true,
  "custom_param1": "value1",
  "custom_param2": "value2"
}
```

Then register your agent in the system by adding it to the agent initialization in `app.py`.

### Database Options

For long-term memory, you can use different database backends by changing the connection string:

- PostgreSQL: `"postgresql://user:password@localhost:5432/memory_db"`
- SQLite: `"sqlite:///memory.db"`
- MySQL: `"mysql://user:password@localhost:3306/memory_db"`

## Troubleshooting

If you encounter issues with your configuration:

1. Check the logs for error messages
2. Validate your JSON syntax
3. Ensure all required fields are present
4. Verify that environment variables are set correctly
5. Check file paths and permissions

For more help, see the [Troubleshooting Guide](troubleshooting.md).