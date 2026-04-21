"""Minimal admin-mode gate.

No user accounts, no sessions. A single passphrase is read from the
`GGPT_ADMIN_KEY` env var (defaulting to `admin123` for local dev) and
compared to the `X-Admin-Key` header on every admin-gated request.
"""
import os

from fastapi import Header, HTTPException, status

ADMIN_KEY = os.environ.get("GGPT_ADMIN_KEY", "admin123")


def require_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin key required",
        )
