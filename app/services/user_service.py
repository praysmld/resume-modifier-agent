import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from app.models.schemas import UserRegistration, UserLogin, UserProfile, AuthToken
from app.auth.jwt_handler import verify_password, get_password_hash, create_access_token


# In-memory storage (replace with database in production)
users_db: Dict[str, Dict[str, Any]] = {}
users_by_email: Dict[str, str] = {}


class UserService:
    """Service for user management operations"""
    
    @staticmethod
    async def register_user(user_data: UserRegistration) -> AuthToken:
        """Register a new user"""
        # Check if user already exists
        if user_data.email in users_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        
        user_record = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        users_db[user_id] = user_record
        users_by_email[user_data.email] = user_id
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id, "email": user_data.email})
        
        user_profile = UserProfile(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            created_at=user_record["created_at"],
            updated_at=user_record["updated_at"],
            is_active=True
        )
        
        return AuthToken(
            access_token=access_token,
            expires_in=86400,  # 24 hours
            user=user_profile
        )
    
    @staticmethod
    async def login_user(login_data: UserLogin) -> AuthToken:
        """Login user and return access token"""
        # Find user by email
        if login_data.email not in users_by_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_id = users_by_email[login_data.email]
        user_record = users_db[user_id]
        
        # Verify password
        if not verify_password(login_data.password, user_record["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user_record.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_id, "email": login_data.email}
        )
        
        user_profile = UserProfile(
            id=user_id,
            email=user_record["email"],
            full_name=user_record["full_name"],
            created_at=user_record["created_at"],
            updated_at=user_record["updated_at"],
            is_active=user_record["is_active"]
        )
        
        return AuthToken(
            access_token=access_token,
            expires_in=86400,  # 24 hours
            user=user_profile
        )
    
    @staticmethod
    async def get_user_profile(user_id: str) -> UserProfile:
        """Get user profile by ID"""
        if user_id not in users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_record = users_db[user_id]
        return UserProfile(
            id=user_id,
            email=user_record["email"],
            full_name=user_record["full_name"],
            created_at=user_record["created_at"],
            updated_at=user_record["updated_at"],
            is_active=user_record["is_active"]
        )
    
    @staticmethod
    async def update_user_profile(user_id: str, update_data: Dict[str, Any]) -> UserProfile:
        """Update user profile"""
        if user_id not in users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_record = users_db[user_id]
        
        # Update allowed fields
        if "full_name" in update_data:
            user_record["full_name"] = update_data["full_name"]
        
        user_record["updated_at"] = datetime.utcnow()
        
        return UserProfile(
            id=user_id,
            email=user_record["email"],
            full_name=user_record["full_name"],
            created_at=user_record["created_at"],
            updated_at=user_record["updated_at"],
            is_active=user_record["is_active"]
        ) 