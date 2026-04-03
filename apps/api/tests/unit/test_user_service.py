import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from quant_cover_api.services.user_service import UserService


def test_create_user_normalizes_email(session: Session) -> None:
    service = UserService(session)

    user = service.create_user(email="  Matt@Example.com ", display_name="Matt")

    assert user.email == "matt@example.com"
    assert user.display_name == "Matt"


def test_create_user_rejects_duplicate_email(session: Session) -> None:
    service = UserService(session)
    service.create_user(email="matt@example.com", display_name="Matt")

    with pytest.raises(HTTPException, match="User already exists") as exc_info:
        service.create_user(email="Matt@Example.com", display_name=None)

    assert exc_info.value.status_code == 409
