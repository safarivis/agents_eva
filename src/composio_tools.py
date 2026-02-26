"""Composio tools wrapper for Eva."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup
from composio import ComposioToolSet, Action

# GitHub API configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"


def _get_toolset() -> ComposioToolSet:
    """Get configured Composio toolset."""
    return ComposioToolSet(api_key=os.environ.get("COMPOSIO_API_KEY"))


def fetch_emails(
    max_results: int = 10,
    query: str = "is:unread",
) -> list[dict]:
    """Fetch emails from Gmail via Composio.

    Args:
        max_results: Maximum number of emails to fetch
        query: Gmail search query

    Returns:
        List of email dicts with id, subject, from, snippet
    """
    toolset = _get_toolset()
    result = toolset.execute_action(
        action=Action.GMAIL_FETCH_EMAILS,
        params={
            "max_results": max_results,
            "q": query,
            "user_id": "me",
        },
    )
    messages = result.get("data", {}).get("messages", [])
    return messages


def fetch_calendar_events(
    hours_ahead: int = 24,
) -> list[dict]:
    """Fetch upcoming calendar events via Composio.

    Args:
        hours_ahead: How many hours ahead to look

    Returns:
        List of event dicts with id, summary, start, end
    """
    toolset = _get_toolset()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    time_max = now + timedelta(hours=hours_ahead)

    result = toolset.execute_action(
        action=Action.GOOGLECALENDAR_FIND_EVENT,
        params={
            "time_min": now.isoformat() + "Z",
            "time_max": time_max.isoformat() + "Z",
            "max_results": 10,
        },
    )
    events = result.get("data", {}).get("items", [])
    return events


def send_email(
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    """Send email via Gmail/Composio.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body text

    Returns:
        True if sent successfully
    """
    toolset = _get_toolset()
    result = toolset.execute_action(
        action=Action.GMAIL_SEND_EMAIL,
        params={
            "recipient_email": to_email,
            "subject": subject,
            "body": body,
            "user_id": "me",
        },
    )
    return bool(result.get("data", {}).get("id"))


# ============================================================================
# GitHub API Tools (Direct API - more reliable than Composio for GitHub)
# ============================================================================

def _github_headers() -> dict:
    """Get GitHub API headers with auth."""
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set in environment")
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def github_get_repo(owner: str, repo: str) -> dict:
    """Get repository information.
    
    Args:
        owner: Repository owner (username or org)
        repo: Repository name
        
    Returns:
        Repo info dict with name, description, stars, forks, open_issues, etc.
    """
    resp = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
        headers=_github_headers(),
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data["description"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "language": data["language"],
        "default_branch": data["default_branch"],
        "html_url": data["html_url"],
    }


def github_list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> list[dict]:
    """List issues in a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Filter by state (open, closed, all)
        limit: Max issues to return
        
    Returns:
        List of issue dicts with number, title, state, created_at, url
    """
    resp = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
        headers=_github_headers(),
        params={"state": state, "per_page": limit},
    )
    resp.raise_for_status()
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"],
            "created_at": i["created_at"],
            "url": i["html_url"],
            "author": i["user"]["login"],
        }
        for i in resp.json()
    ]


def github_create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
) -> dict:
    """Create a new issue.
    
    Args:
        owner: Repository owner
        repo: Repository name
        title: Issue title
        body: Issue body/description
        labels: List of label names
        
    Returns:
        Created issue dict with number, url
    """
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
        
    resp = requests.post(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
        headers=_github_headers(),
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"number": data["number"], "url": data["html_url"]}


def github_create_pull_request(
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str = "",
) -> dict:
    """Create a pull request.
    
    Args:
        owner: Repository owner
        repo: Repository name
        title: PR title
        head: Branch with changes
        base: Branch to merge into
        body: PR description
        
    Returns:
        Created PR dict with number, url
    """
    resp = requests.post(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
        headers=_github_headers(),
        json={"title": title, "head": head, "base": base, "body": body},
    )
    resp.raise_for_status()
    data = resp.json()
    return {"number": data["number"], "url": data["html_url"]}


def github_get_file_contents(owner: str, repo: str, path: str, ref: str = "main") -> str:
    """Get contents of a file from a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        path: File path in repo (case-sensitive!)
        ref: Branch or commit sha
        
    Returns:
        File content as string
    """
    # Try exact path first
    resp = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}",
        headers=_github_headers(),
        params={"ref": ref},
    )
    # If 404, try case variations (e.g., CLAUDE.md, claude.md)
    if resp.status_code == 404:
        import os
        base = os.path.basename(path)
        dir_path = os.path.dirname(path)
        # Common patterns: all caps name (CLAUDE.md), all lower (claude.md)
        name, ext = os.path.splitext(base)
        variations = [
            f"{name.upper()}{ext.lower()}",  # CLAUDE.md
            f"{name.lower()}{ext.lower()}",  # claude.md
        ]
        for var in variations:
            if var == base:
                continue
            test_path = f"{dir_path}/{var}" if dir_path else var
            resp = requests.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{test_path}",
                headers=_github_headers(),
                params={"ref": ref},
            )
            if resp.status_code == 200:
                break
    
    resp.raise_for_status()
    import base64
    content_b64 = resp.json()["content"]
    return base64.b64decode(content_b64).decode("utf-8")


# ============================================================================
# Web Browsing Tools
# ============================================================================

def fetch_webpage(url: str, max_chars: int = 3000) -> str:
    """Fetch and extract text content from a webpage.
    
    Args:
        url: Full URL to fetch
        max_chars: Maximum characters to return
        
    Returns:
        Extracted text content from the page
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text with better formatting
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace but preserve paragraph breaks
        lines = []
        prev_empty = False
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
                prev_empty = False
            elif not prev_empty:
                lines.append('')  # Keep one empty line between paragraphs
                prev_empty = True
        
        cleaned = '\n'.join(lines)
        
        # Truncate if too long
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "\n\n[...truncated]"
        
        return cleaned
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"
