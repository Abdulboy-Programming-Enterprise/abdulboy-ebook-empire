"""
Authentication Routes
=====================
User registration, login, token refresh, and password management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_reset_token,
    verify_reset_token,
)
from app.models.user import User, AccountType, SubscriptionStatus
from app.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
    TokenRefresh,
    ChangePassword,
    ForgotPassword,
    ResetPassword,
    UserResponse,
)
from app.schemas.response import StandardResponse
from app.api.deps import get_current_user
from app.utils.validators import validate_email
from app.core.logger import logger
from app.tasks.email_jobs import send_welcome_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[UserResponse])
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    """
    # Check if user already exists
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == user_data.email.lower()))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email.lower(),
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        account_type=AccountType.NORMAL,
        subscription_status=SubscriptionStatus.FREE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Send welcome email in background
    send_welcome_email.delay(
        user_id=str(new_user.id),
        user_email=new_user.email,
        user_name=new_user.full_name
    )
    
    logger.info(f"New user registered: {new_user.email}")
    
    return StandardResponse(
        success=True,
        message="Registration successful. Please verify your email.",
        data=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            account_type=new_user.account_type.value,
            subscription_status=new_user.subscription_status.value,
            total_points=new_user.total_points,
            reading_streak=new_user.reading_streak,
            email_verified=new_user.email_verified_at is not None,
            created_at=new_user.created_at,
        )
    )


@router.post("/login", response_model=StandardResponse[Token])
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return access tokens.
    """
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == login_data.email.lower()))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated",
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info(f"User logged in: {user.email}")
    
    return StandardResponse(
        success=True,
        message="Login successful",
        data=Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    )


@router.post("/refresh", response_model=StandardResponse[Token])
async def refresh_token(
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    payload = verify_reset_token(refresh_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return StandardResponse(
        success=True,
        data=Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout current user (client-side token removal).
    """
    # Token revocation would be implemented with a token blacklist
    return StandardResponse(
        success=True,
        message="Logged out successfully"
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user's password.
    """
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Password changed for user: {current_user.email}")
    
    return StandardResponse(
        success=True,
        message="Password changed successfully"
    )


@router.post("/forgot-password")
async def forgot_password(
    forgot_data: ForgotPassword,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset email.
    """
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == forgot_data.email.lower()))
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if user:
        reset_token = generate_reset_token(str(user.id))
        send_password_reset_email.delay(
            user_email=user.email,
            user_name=user.full_name,
            reset_token=reset_token,
        )
        logger.info(f"Password reset requested for: {user.email}")
    
    return StandardResponse(
        success=True,
        message="If an account exists with this email, you will receive a password reset link"
    )


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPassword,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using token from email.
    """
    user_id = verify_reset_token(reset_data.token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.password_hash = get_password_hash(reset_data.new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Password reset for user: {user.email}")
    
    return StandardResponse(
        success=True,
        message="Password reset successfully. Please login with your new password."
    )
