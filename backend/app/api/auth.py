from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserAuthInfo
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token, summary="User login endpoint")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a staff or admin user and issue a JWT bearer token."""
    user = (
        db.query(User)
        .filter(
            (User.username == login_data.username) | (User.email == login_data.username)
        )
        .first()
    )

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    access_token = create_access_token(
        data={
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserAuthInfo(
            id=user.id,
            username=user.username,
            tenant_id=user.tenant_id,
            tenant_name=user.tenant.name if user.tenant else None,
            role=user.role,
        ),
    )


@router.get("/me", response_model=UserResponse, summary="Get current logged-in user profile")
def get_me(current_user: User = Depends(get_current_user)):
    """Return profile and tenant info for currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        tenant_name=current_user.tenant.name if current_user.tenant else None,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
