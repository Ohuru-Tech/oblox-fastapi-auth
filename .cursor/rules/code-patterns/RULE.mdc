---
description: FastAPI development standards and best practices for async, dependency injection, MVC pattern, and SQLAlchemy ORM
globs:
  - "**/*fastapi*.py"
  - "**/main.py"
  - "**/app.py"
  - "**/api/**/*.py"
  - "**/routers/**/*.py"
  - "**/controllers/**/*.py"
  - "**/services/**/*.py"
  - "**/models/**/*.py"
alwaysApply: true
---

# FastAPI Development Standards

Follow these standards when developing FastAPI applications.

## Architecture Pattern: MVC

Organize code following the Model-View-Controller (MVC) pattern:

- **Models**: SQLAlchemy ORM models in `models/` directory
- **Views**: FastAPI route handlers in `routers/` or `api/` directory
- **Controllers**: Business logic in `controllers/` or `services/` directory

### Directory Structure

```text
app/
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic schemas for request/response validation
├── routers/         # API route handlers (views)
├── services/        # Business logic (controllers)
└── main.py          # FastAPI app initialization
```

## Dependency Injection

Always use FastAPI's dependency injection system:

- **Prefer `Depends()`**: Use `Depends()` for all dependencies (database sessions, services, authentication, etc.)
- **Co-locate dependencies**: Define dependency functions in the same file where they're used, not in a separate `dependencies.py` file
- **Avoid global state**: Never use global variables for shared resources
- **Dependency chains**: Build dependency chains for complex scenarios (e.g., auth → user → permissions)

### Dependency Injection Examples

```python
# routers/users.py
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.services import UserService
from app.database import async_session

router = APIRouter()

# Dependency function defined in the same file
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_user_service() -> UserService:
    return UserService()

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_user(db, user_id)
```

## Async Execution

Always use async/await patterns:

- **Async route handlers**: All route handlers must be `async def`
- **Async database operations**: Use async SQLAlchemy for all database operations
- **Async HTTP clients**: Use `httpx.AsyncClient` or `aiohttp` for external API calls
- **Async context managers**: Use `async with` for resource management
- **Avoid blocking operations**: Never use synchronous I/O operations in async handlers

### Async Execution Examples

```python
# ✅ Good: Async route handler
# Dependency defined in same file
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# ❌ Bad: Synchronous handler
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

## SQLAlchemy Async ORM

Use async SQLAlchemy for all database operations:

- **AsyncSession**: Always use `AsyncSession` from `sqlalchemy.ext.asyncio`
- **Async engine**: Use `create_async_engine()` with async database URLs
- **Async queries**: Use `await db.execute()` and `await db.scalar()` instead of synchronous methods
- **Session management**: Use dependency injection for session management with proper cleanup
- **Transactions**: Use `async with db.begin()` for explicit transactions

### SQLAlchemy Async ORM Examples

```python
# ✅ Good: Async SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

engine = create_async_engine("postgresql+asyncpg://...")
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# ❌ Bad: Synchronous SQLAlchemy
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
```

## Pydantic Schemas

Use Pydantic for request/response validation:

- **Separate schemas**: Create separate schemas for requests (`*Create`, `*Update`) and responses (`*Response`, `*Detail`)
- **Model validation**: Use Pydantic models for all API inputs and outputs
- **Field validation**: Leverage Pydantic validators for complex validation logic
- **Response models**: Always specify `response_model` in route decorators

### Pydantic Schema Examples

```python
# schemas/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    
    class Config:
        from_attributes = True

# routers/users.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.database import async_session

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # Implementation
    pass
```

## Error Handling

Implement consistent error handling:

- **HTTPException**: Use FastAPI's `HTTPException` for HTTP errors
- **Custom exceptions**: Create custom exception classes for domain-specific errors
- **Exception handlers**: Register exception handlers using `app.add_exception_handler()`
- **Status codes**: Use appropriate HTTP status codes (400, 401, 403, 404, 422, 500)

### Error Handling Examples

```python
from fastapi import HTTPException, status

# Dependency defined in same file
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return user
```

## Best Practices

### Route Organization

- **Router modules**: Group related routes in separate router modules
- **Prefix and tags**: Use `APIRouter(prefix="/api/v1", tags=["users"])` for organization
- **Include routers**: Use `app.include_router()` to register routers

### Database Migrations

- **Alembic**: Use Alembic for database migrations
- **Async migrations**: Configure Alembic to work with async SQLAlchemy
- **Migration scripts**: Keep migrations focused and reversible

### Testing

- **TestClient**: Use `TestClient` from `fastapi.testing` for integration tests
- **Async test fixtures**: Use `pytest-asyncio` for async test functions
- **Dependency overrides**: Use `app.dependency_overrides` to mock dependencies in tests

### Security

- **Password hashing**: Use `passlib` with bcrypt for password hashing
- **JWT tokens**: Use `python-jose` for JWT token handling
- **CORS**: Configure CORS middleware appropriately
- **Environment variables**: Use `pydantic-settings` for configuration management

### Performance

- **Response models**: Always use `response_model` to optimize serialization
- **Background tasks**: Use `BackgroundTasks` for non-blocking operations
- **Connection pooling**: Configure appropriate connection pool settings for async engines
- **Query optimization**: Use `selectinload()` or `joinedload()` for eager loading relationships

## Code Examples

### Complete Service Pattern

```python
# services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User
from app.schemas import UserCreate

class UserService:
    async def get_user(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def create_user(self, db: AsyncSession, user_data: UserCreate) -> User:
        user = User(**user_data.model_dump())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

# routers/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.services import UserService
from app.schemas import UserCreate, UserResponse
from app.database import async_session

router = APIRouter(prefix="/users", tags=["users"])

# Dependencies defined in the same file
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_user_service() -> UserService:
    return UserService()

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.create_user(db, user_data)
```
