# Security Hardening Guide

This document outlines the security measures implemented in the B2B Supplier-Wholesale Exchange Platform.

## 🔐 Authentication & Authorization

### JWT Tokens

- **Access Token Expiry**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token Expiry**: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_MINUTES`)
- **Token Rotation**: Refresh endpoint (`/api/v1/auth/refresh`) allows secure token rotation
- **Algorithm**: HS256 (HMAC-SHA256) - configurable via `ALGORITHM` setting
- **Secret Key**: Must be changed in production (use strong, randomly generated key)

### Password Security

- **Hashing**: bcrypt with configurable cost factor (default: 12 rounds)
- **Cost Factor**: Set via `BCRYPT_ROUNDS` (12 is recommended for 2024+)
  - Higher rounds = more secure but slower (exponential cost)
  - 12 rounds provides good balance between security and performance
- **Password Policy**:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - Special characters optional (configurable)

## 🛡️ Input Validation & Size Limits

### Request Size Limits

- **Max Request Body**: 10MB (configurable via `MAX_REQUEST_SIZE`)
- **Max String Length**: 10,000 characters (configurable via `MAX_STRING_LENGTH`)
- **Password Max Length**: 128 characters
- **Chat Message Max Length**: 10,000 characters

### File Uploads

- **No Direct File Uploads**: Chat messages only accept file URLs (not direct uploads)
- **File URL Validation**: Max length 500 characters, must be valid URL format
- **Future Enhancement**: If file uploads are added, implement:
  - File type validation (whitelist allowed MIME types)
  - File size limits per file type
  - Virus scanning
  - Secure storage (S3, etc.)

## 📚 API Documentation

### OpenAPI Docs Protection

- **Production**: Disabled by default (`ENABLE_DOCS_IN_PROD=False`)
- **Development/Staging**: Enabled for convenience
- **To Enable in Production**: Set `ENABLE_DOCS_IN_PROD=True` and protect with authentication

### Endpoints

- `/docs` - Swagger UI (disabled in production)
- `/redoc` - ReDoc (disabled in production)
- `/openapi.json` - OpenAPI schema (consider rate limiting in production)

## 🗄️ Database Security

### Database User Requirements

The application should use a database user with **least privilege**:

#### Required Permissions

```sql
-- Create application user (run as postgres superuser)
CREATE USER app_user WITH PASSWORD 'strong_password_here';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE mydb TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;

-- Grant table permissions (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Grant permissions on future tables (for migrations)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_user;
```

#### Prohibited Permissions

- ❌ `CREATE DATABASE` - Not needed
- ❌ `CREATE SCHEMA` - Not needed (use public schema)
- ❌ `DROP TABLE` - Not needed (use migrations)
- ❌ `TRUNCATE` - Not needed (use DELETE)
- ❌ `ALTER TABLE` - Not needed (use migrations)
- ❌ Superuser privileges - Never grant

### Connection String

Use the least-privilege user in production:

```env
DATABASE_URL=postgresql+asyncpg://app_user:strong_password@db_host:5432/mydb
```

## 🔍 Security Linting

### Bandit

Security linting is performed using [Bandit](https://bandit.readthedocs.io/):

```bash
# Run security checks
make security

# Or directly
bandit -r app -ll
```

### Common Security Patterns Checked

- SQL injection risks
- Hardcoded passwords/secrets
- Insecure random number generation
- Use of insecure hash functions
- Shell injection risks
- SSL/TLS issues
- Insecure deserialization

## ✅ Security Checklist

Before deploying to production, verify:

- [ ] `SECRET_KEY` is changed from default and is strong (32+ random characters)
- [ ] `ENV=production` is set
- [ ] `ENABLE_DOCS_IN_PROD=False` (or protected with auth)
- [ ] Database user has least privilege (not superuser)
- [ ] `BCRYPT_ROUNDS` is set to 12 or higher
- [ ] CORS origins are restricted to actual frontend domains
- [ ] Rate limiting is enabled (`RATE_LIMIT_ENABLED=True`)
- [ ] All dependencies are up to date (check for vulnerabilities)
- [ ] Security linting passes (`make security`)
- [ ] No secrets are committed to version control
- [ ] Environment variables are properly secured
- [ ] HTTPS is enforced in production
- [ ] Security headers are configured (via reverse proxy/CDN)

## 🚨 Security Incident Response

If you discover a security vulnerability:

1. **Do NOT** create a public issue
2. Contact the security team directly
3. Provide details of the vulnerability
4. Allow time for patching before disclosure

## 📖 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security.html)
