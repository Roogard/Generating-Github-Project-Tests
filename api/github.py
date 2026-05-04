"""GitHub App webhook entrypoint.

Parallel to /api/runs: instead of the React webapp posting a RunRequest,
GitHub sends a webhook when a tracked label is applied to an issue, and
the same pipeline runs end-to-end. After a successful run, the generated
test is pushed back as a PR.

The runner deletes `output_dir/_repo` after each run (it preserves only
`tests/`), so we can't reuse the on-disk clone. Instead, after the agent
finishes, we mint an installation token, do a fresh shallow clone, copy
the test in, branch + commit + push, and open the PR via REST.

Setup:
  1. Register a new GitHub App at https://github.com/settings/apps/new
       Webhook URL:    https://<your-host>/api/github/webhook
       Webhook secret: <strong random string>
       Permissions (Repository):
         - Issues:        Read & write
         - Pull requests: Read & write
         - Contents:      Read & write
         - Metadata:      Read
       Subscribe to events: Issues
  2. From the App settings page, generate a private key (.pem) and store
     it somewhere readable by the API process.
  3. Install the App on the target repo(s).
  4. Set env vars (see src/config.py for the full list):
       GITHUB_WEBHOOK_SECRET     <secret you chose>
       GITHUB_APP_ID             <numeric ID from the App settings page>
       GITHUB_PRIVATE_KEY_PATH   <path to the PEM file>
       GITHUB_TRIGGER_LABEL      ggpt    (default; override if you like)
  5. Expose api.app:app on a public URL (ngrok / cloud).
  6. On a tracked repo: open an issue describing a bug, then add the
     `ggpt` label. A Run row appears in the DB; on success a PR opens
     against the default branch with the generated test.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from api import store
from api.db import get_db
from api.models import RunStatus
from src import config
from src.inputs.base import force_rmtree
from src.logging import get_logger


logger = get_logger(__name__)

github_router = APIRouter(prefix="/api/github", tags=["github"])


@dataclass
class GhCtx:
    installation_id: int
    full_name: str       # "owner/repo"
    owner: str
    repo: str
    issue_number: int
    default_branch: str


# ── signature + trigger ─────────────────────────────────────────────────────

def _verify_signature(body: bytes, header: str | None) -> bool:
    if not config.GITHUB_WEBHOOK_SECRET or not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        config.GITHUB_WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, header)


def _should_trigger(event_type: str, payload: dict) -> bool:
    if event_type != "issues" or payload.get("action") != "labeled":
        return False
    label = (payload.get("label") or {}).get("name", "")
    return label == config.GITHUB_TRIGGER_LABEL


# ── installation auth ───────────────────────────────────────────────────────

def _make_app_jwt() -> str:
    if not config.GITHUB_APP_ID or not config.GITHUB_PRIVATE_KEY_PATH:
        raise RuntimeError("GITHUB_APP_ID and GITHUB_PRIVATE_KEY_PATH must be set for PR-back")
    with open(config.GITHUB_PRIVATE_KEY_PATH, "rb") as f:
        key = f.read()
    now = int(time.time())
    # 60s clock-skew slack on iat; 9-minute exp (max is 10).
    payload = {"iat": now - 60, "exp": now + 540, "iss": config.GITHUB_APP_ID}
    return jwt.encode(payload, key, algorithm="RS256")


def _gh_request(method: str, url: str, *, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def _get_installation_token(installation_id: int) -> str:
    app_jwt = _make_app_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    resp = _gh_request("POST", url, token=app_jwt)
    return resp["token"]


# ── PR-back ─────────────────────────────────────────────────────────────────

def _run_git(args: list[str], cwd: str) -> None:
    # capture_output keeps tokenized push URLs out of the parent log stream.
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _push_and_open_pr(run_id: int, gh_ctx: GhCtx) -> None:
    with store.session_scope() as db:
        run = store.get_run(db, run_id)
        output_dir = run.output_dir if run else None

    if not output_dir:
        logger.warning("github.pr_skip", reason="no output_dir", run_id=run_id)
        return
    src_test = os.path.join(output_dir, "tests", "test_agent.py")
    if not os.path.isfile(src_test):
        logger.warning("github.pr_skip", reason="no test file", run_id=run_id, path=src_test)
        return

    token = _get_installation_token(gh_ctx.installation_id)
    branch = f"ggpt/issue-{gh_ctx.issue_number}-run-{run_id}"
    test_filename = f"test_ggpt_issue_{gh_ctx.issue_number}_run_{run_id}.py"

    tmp_root = tempfile.mkdtemp(prefix=f"ggpt-pr-{run_id}-")
    clone_dir = os.path.join(tmp_root, "repo")
    try:
        push_url = f"https://x-access-token:{token}@github.com/{gh_ctx.full_name}.git"
        _run_git(["clone", "--depth=1", "--branch", gh_ctx.default_branch, push_url, clone_dir], cwd=tmp_root)

        _run_git(["checkout", "-b", branch], cwd=clone_dir)
        _run_git(["config", "user.email", "ggpt-bot@users.noreply.github.com"], cwd=clone_dir)
        _run_git(["config", "user.name", "GGPT Bot"], cwd=clone_dir)

        dst_rel = os.path.join("tests", test_filename)
        dst_abs = os.path.join(clone_dir, dst_rel)
        os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
        shutil.copyfile(src_test, dst_abs)

        _run_git(["add", dst_rel], cwd=clone_dir)
        _run_git(["commit", "-m", f"Add regression test for #{gh_ctx.issue_number}"], cwd=clone_dir)
        _run_git(["push", push_url, branch], cwd=clone_dir)

        pr = _gh_request(
            "POST",
            f"https://api.github.com/repos/{gh_ctx.full_name}/pulls",
            token=token,
            body={
                "title": f"GGPT: regression test for #{gh_ctx.issue_number}",
                "head": branch,
                "base": gh_ctx.default_branch,
                "body": (
                    f"Closes #{gh_ctx.issue_number}\n\n"
                    f"Auto-generated regression test by GGPT (run {run_id})."
                ),
            },
        )
        logger.info("github.pr_opened", run_id=run_id, pr_url=pr.get("html_url"),
                    pr_number=pr.get("number"))
    finally:
        force_rmtree(tmp_root)


# ── background task ─────────────────────────────────────────────────────────

def _execute_github_run(run_id: int, body, gh_ctx: GhCtx) -> None:
    # Imported lazily to avoid a circular import at module load
    # (api.routes imports things that pull this module in transitively).
    from api.routes import _execute_run

    _execute_run(run_id, body)

    with store.session_scope() as db:
        run = store.get_run(db, run_id)
        status = run.status if run else None

    if status != RunStatus.DONE:
        logger.info("github.pr_skip", reason=f"run status {status}", run_id=run_id)
        return

    try:
        _push_and_open_pr(run_id, gh_ctx)
    except subprocess.CalledProcessError as e:
        logger.error("github.pr_failed", run_id=run_id, cmd=e.cmd[0:2],
                     returncode=e.returncode,
                     stderr=(e.stderr or b"").decode("utf-8", errors="replace")[-500:])
    except urllib.error.HTTPError as e:
        logger.error("github.pr_failed", run_id=run_id, http_status=e.code,
                     body=e.read().decode("utf-8", errors="replace")[:500])
    except Exception as e:
        logger.error("github.pr_failed", run_id=run_id,
                     err_type=type(e).__name__, err=str(e))


# ── webhook route ───────────────────────────────────────────────────────────

@github_router.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")
    if not _verify_signature(body, sig):
        raise HTTPException(status_code=401, detail="invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    if event_type == "ping":
        return {"ok": True}
    if event_type != "issues":
        return {"ok": True, "ignored": event_type}

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid JSON")

    if not _should_trigger(event_type, payload):
        return {"ok": True, "ignored": "not a triggering label event"}

    repo = payload.get("repository") or {}
    issue = payload.get("issue") or {}
    install = payload.get("installation") or {}
    if not repo.get("clone_url") or not install.get("id") or "number" not in issue:
        raise HTTPException(status_code=400, detail="payload missing required fields")

    gh_ctx = GhCtx(
        installation_id=int(install["id"]),
        full_name=repo.get("full_name", ""),
        owner=(repo.get("owner") or {}).get("login", ""),
        repo=repo.get("name", ""),
        issue_number=int(issue["number"]),
        default_branch=repo.get("default_branch", "main"),
    )

    # Defer the import: api.routes is what RunRequest lives on, and lazy
    # importing here avoids a top-level cycle if anything in routes ever
    # imports github.py.
    from api.routes import RunRequest

    run_request = RunRequest(
        source="repo",
        repo_url=repo["clone_url"],
        issue_text=issue.get("body") or "",
        issue_title=issue.get("title") or "",
        provider=config.GITHUB_DEFAULT_PROVIDER,
        model=config.GITHUB_DEFAULT_MODEL,
        preset="default",
    )
    if not run_request.issue_text.strip():
        raise HTTPException(status_code=400, detail="issue body is empty — cannot run agent")

    run = store.create_run(
        db,
        repo_url=repo["clone_url"],
        mode="repo",
        provider=config.GITHUB_DEFAULT_PROVIDER,
        model=config.GITHUB_DEFAULT_MODEL,
        preset="default",
        status=RunStatus.PENDING,
    )
    db.commit()
    db.refresh(run)

    background_tasks.add_task(_execute_github_run, run.id, run_request, gh_ctx)
    logger.info("github.run_queued", run_id=run.id, issue=gh_ctx.issue_number,
                repo=gh_ctx.full_name)
    return {"ok": True, "run_id": run.id}
