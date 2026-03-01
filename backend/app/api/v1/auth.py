"""
Authentication endpoints
"""
from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.models.schemas import UserLogin, UserRegister, Token, User
from app.core.security import create_access_token, get_password_hash, verify_password

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user

    TODO: Implement database persistence
    """
    logger.info(f"Registering new user: {user_data.username}")

    # TODO: Check if user already exists
    # TODO: Hash password and store in database

    # Placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User registration not yet implemented - coming in Phase 2"
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login and receive JWT token

    For MVP, this is a simplified version.
    TODO: Implement proper database user lookup
    """
    logger.info(f"Login attempt for user: {credentials.username}")

    # For MVP: Simple demo authentication
    # TODO: Lookup user in database and verify password hash
    if credentials.username == "demo" and credentials.password == "demo":
        access_token = create_access_token(
            data={"sub": credentials.username, "username": credentials.username}
        )
        return Token(access_token=access_token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token: str):
    """
    Refresh an access token

    TODO: Implement token refresh logic
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented"
    )
