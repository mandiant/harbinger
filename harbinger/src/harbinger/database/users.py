# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid
from typing import Optional

from harbinger.config import get_settings
from harbinger.crud import get_user_db
from harbinger.database.redis_pool import redis
from harbinger.models import User
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.authentication import RedisStrategy

settings = get_settings()


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_max_age=settings.lifetime_seconds,
    cookie_samesite=settings.cookie_samesite,  # type: ignore
    cookie_httponly=True,
    cookie_secure=True,
)

bearer_transport = BearerTransport(tokenUrl="auth/redis/login")


def get_redis_strategy() -> RedisStrategy:
    return RedisStrategy(redis)


auth_backend_cookie = AuthenticationBackend(
    name="redis_cookie",
    transport=cookie_transport,
    get_strategy=get_redis_strategy,
)

auth_backend_bearer = AuthenticationBackend(
    name="redis_bearer",
    transport=bearer_transport,
    get_strategy=get_redis_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager, [auth_backend_cookie, auth_backend_bearer]
)

current_active_user = fastapi_users.current_user(active=True)
