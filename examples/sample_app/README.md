# Sample FastAPI Application

This is a sample FastAPI application demonstrating how to use the `oblox-fastapi-auth` package.

## Features Demonstrated

- ✅ Basic FastAPI app setup
- ✅ Authentication routes integration
- ✅ Protected routes with RBAC
- ✅ CORS configuration
- ✅ Admin-only routes
- ✅ Permission-based access control

## Setup

### 1. Install Dependencies

```bash
# From the sample_app directory
cd examples/sample_app

# Install the package (if not already installed)
uv add oblox-fastapi-auth

# Or install from local source
uv add ../..
```

### 2. Configure Environment

Create a `.dev.env` file:

```env
AUTH_DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
AUTH_TIMEZONE=UTC
JWT_SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key-32-bytes-long!!
AUTH_EMAIL_BACKEND=console
AUTH_PROJECT_NAME=sample-app
```

Generate encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Run Database Migrations

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 4. Create Initial Users and Roles

```bash
# Create an admin user
oblox-fastapi-auth-cli create-user admin@example.com --name "Admin User" --password "admin123" --is-staff

# Create a regular user
oblox-fastapi-auth-cli create-user user@example.com --name "Regular User" --password "user123"

# Create admin role
oblox-fastapi-auth-cli create-role admin --description "Administrator role"

# Create user role
oblox-fastapi-auth-cli create-role user --description "Regular user role"

# Assign permissions to admin role
oblox-fastapi-auth-cli create-permission-for-role admin users:read users read "Read users"
oblox-fastapi-auth-cli create-permission-for-role admin users:create users create "Create users"
oblox-fastapi-auth-cli create-permission-for-role admin users:write users write "Write users"
```

### 5. Run the Application

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

The application will be available at `http://localhost:8000`

## API Endpoints

### Public Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `POST /auth/signup` - User registration
- `POST /auth/social/{provider}/login` - Social authentication

### Protected Endpoints

- `GET /user/profile` - Get current user's profile (requires 'user' role)
- `GET /admin/dashboard` - Admin dashboard (requires 'admin' role)
- `GET /users` - List users (requires 'users:read' permission)
- `POST /users` - Create user (requires 'users:create' and 'users:write' permissions)

## Testing the API

### 1. Sign Up

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "testpassword123"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. Access Protected Route

```bash
curl -X GET http://localhost:8000/user/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Access Admin Route

```bash
curl -X GET http://localhost:8000/admin/dashboard \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## Frontend Integration

See the [FRONTEND_INTEGRATION.md](../../FRONTEND_INTEGRATION.md) guide for detailed frontend integration examples.

## Next Steps

1. Implement actual user listing logic in `/users` endpoint
2. Add user update and delete endpoints
3. Implement token refresh endpoint
4. Add password reset functionality
5. Add email verification flow
6. Implement rate limiting
7. Add request logging and monitoring

## Project Structure

```
sample_app/
├── main.py              # Main application file
├── README.md            # This file
└── .dev.env            # Environment configuration (create this)
```

## Notes

- This is a minimal example. In production, add proper error handling, logging, and monitoring.
- Always use HTTPS in production.
- Store sensitive configuration in environment variables or secret management services.
- Implement proper database connection pooling and error recovery.
- Add comprehensive tests for all endpoints.
