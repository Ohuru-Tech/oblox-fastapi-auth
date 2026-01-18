"""
Sample FastAPI application using oblox-fastapi-auth package.

This example demonstrates:
- Basic FastAPI app setup
- Authentication routes integration
- Protected routes with RBAC
- CORS configuration
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_auth import auth_router, get_engine, get_settings
from fastapi_auth.models.user import User
from fastapi_auth.services.rbac import (
    required_admin,
    required_permissions,
    required_role,
)
from fastapi_auth.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting application...")
    try:
        yield
    finally:
        logger.info("Shutting down application...")
        await get_engine().dispose()


# Create FastAPI app
app = FastAPI(
    title="Sample FastAPI Auth App",
    description="A sample application demonstrating oblox-fastapi-auth integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # React/Vue dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)


# Public route
@app.get("/")
async def root():
    """Public endpoint - no authentication required."""
    return {
        "message": "Welcome to the Sample FastAPI Auth App",
        "version": "1.0.0",
        "endpoints": {
            "public": "/",
            "auth": {
                "signup": "POST /auth/signup",
                "social_login": "POST /auth/social/{provider}/login",
            },
            "protected": {
                "user_profile": "GET /user/profile",
                "admin_dashboard": "GET /admin/dashboard",
                "users_list": "GET /users",
            },
        },
    }


# Protected route - requires authentication (any authenticated user)
@app.get("/user/profile")
async def get_user_profile(current_user: User = Depends(required_role("user"))):
    """Get current user's profile - requires 'user' role."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "profile_pic": current_user.profile_pic,
        "is_staff": current_user.is_staff,
        "created_at": current_user.created_at.isoformat()
        if current_user.created_at
        else None,
    }


# Protected route - requires admin role
@app.get("/admin/dashboard")
async def admin_dashboard(current_user: User = Depends(required_admin)):
    """Admin dashboard - requires admin role."""
    return {
        "message": f"Welcome to the admin dashboard, {current_user.email}!",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
        },
        "stats": {
            "total_users": "N/A",  # Implement actual stats
            "active_sessions": "N/A",
        },
    }


# Protected route - requires specific permissions
@app.get("/users")
async def list_users(
    current_user: User = Depends(required_permissions(["users:read"])),
):
    """List all users - requires 'users:read' permission."""
    # In a real app, you would fetch users from the database
    # This is just a placeholder
    return {
        "message": "Users list endpoint",
        "note": "Implement actual user listing logic here",
        "current_user": current_user.email,
    }


# Protected route - requires multiple permissions
@app.post("/users")
async def create_user(
    current_user: User = Depends(required_permissions(["users:create", "users:write"])),
):
    """Create a new user - requires 'users:create' and 'users:write' permissions."""
    return {
        "message": "User creation endpoint",
        "note": "Implement actual user creation logic here",
        "current_user": current_user.email,
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "database": "connected",  # Implement actual health check
        "settings": {
            "project_name": settings.project_name,
            "timezone": settings.timezone,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
