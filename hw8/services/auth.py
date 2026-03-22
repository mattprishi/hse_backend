from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import jwt
from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from models.entities import Account
from repositories.accounts import AccountRepository


@dataclass(frozen=True)
class AuthService:
    account_repository: AccountRepository = AccountRepository()

    async def authenticate_user(self, login: str, password: str) -> Optional[Account]:
        account = await self.account_repository.get_by_login_and_password(login, password)
        if not account or account.is_blocked:
            return None
        return account

    def create_access_token(self, user_id: int) -> str:
        payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)}
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> int:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])