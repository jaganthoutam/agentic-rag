# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0.0 | :x:                |

## Reporting a Vulnerability

We take the security of Agentic RAG seriously. If you believe you've found a security vulnerability, please follow these steps:

### How to Report

1. **Do not** disclose the vulnerability publicly.
2. **Email** us at security@example.com with details of the vulnerability.
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any potential mitigations you've identified

### What to Expect

- You will receive an acknowledgment within 48 hours.
- We will investigate and respond with our assessment within 7 days.
- We will keep you informed of our progress towards addressing the vulnerability.
- Once the vulnerability is fixed, we will publicly disclose it, giving credit to the reporter (unless you prefer to remain anonymous).

## Security Recommendations

When deploying Agentic RAG in production, we recommend the following security measures:

1. **API Authentication**: Always implement proper authentication for the API endpoints.
2. **Secure Database**: Ensure your database for long-term memory has appropriate access controls.
3. **API Keys**: Keep all external service API keys secure and use environment variables or a secure vault.
4. **Regular Updates**: Keep the system and its dependencies up to date.
5. **Restricted Network Access**: Limit network access to the system to only the necessary services.
6. **Content Filtering**: Implement input validation and content filtering to prevent injection attacks.
7. **Logging and Monitoring**: Set up comprehensive logging and monitoring to detect unusual behavior.

## Security Dependencies

Agentic RAG relies on several dependencies that have their own security considerations. Please also check the security advisories and updates for:

- Python and its standard library
- PostgreSQL
- SQLAlchemy
- FastAPI
- All other dependencies listed in requirements.txt

## Security-related Configuration

The following configuration settings in `config.json` can impact security:

- `api.cors_origins`: Restrict to only necessary origins
- `api.timeout`: Set to a reasonable value to prevent DoS attacks
- `memory.long_term.connection_string`: Ensure this contains no plaintext passwords in production

Thank you for helping us keep Agentic RAG secure!