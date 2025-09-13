"""
GitHub API tools for retrieving repository data.
Implements rate limiting, error handling, and structured data extraction.
"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from github import Github
from github.Repository import Repository
from github.Issue import Issue
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from ..core.state import GitHubIssue


class GitHubRepoInput(BaseModel):
    """Input schema for GitHub repository analysis."""
    repository_url: str = Field(description="GitHub repository URL (e.g., 'owner/repo' or full URL)")
    days_back: int = Field(default=90, description="Number of days to look back for issues")
    include_closed: bool = Field(default=True, description="Whether to include closed issues")
    max_issues: int = Field(default=1000, description="Maximum number of issues to retrieve")


class GitHubIssuesTool(BaseTool):
    """
    Advanced GitHub issues retrieval tool with rate limiting and error handling.
    """
    name: str = "github_issues_retriever"
    description: str = """
    Retrieve GitHub issues from a repository with advanced filtering and data quality assurance.
    Handles rate limiting, authentication, and provides structured issue data.
    """
    args_schema = GitHubRepoInput
    
    def __init__(self):
        super().__init__()
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.github_client = Github(self.github_token)
        self.session = self._create_session_with_retries()
    
    def _create_session_with_retries(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _parse_repository_url(self, repo_url: str) -> str:
        """Parse repository URL to extract owner/repo format."""
        if repo_url.startswith("https://github.com/"):
            return repo_url.replace("https://github.com/", "").rstrip("/")
        elif repo_url.startswith("http://github.com/"):
            return repo_url.replace("http://github.com/", "").rstrip("/")
        elif "/" in repo_url and not repo_url.startswith("http"):
            return repo_url.rstrip("/")
        else:
            raise ValueError(f"Invalid repository URL format: {repo_url}")
    
    def _convert_issue_to_structured(self, issue: Issue) -> GitHubIssue:
        """Convert PyGithub Issue to our structured format."""
        return GitHubIssue(
            id=issue.id,
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            state=issue.state,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            closed_at=issue.closed_at,
            labels=[label.name for label in issue.labels],
            assignees=[assignee.login for assignee in issue.assignees],
            author=issue.user.login if issue.user else "unknown",
            comments_count=issue.comments,
            reactions_count=sum([
                issue.get_reactions().get_page(0).__len__() if hasattr(issue, 'get_reactions') else 0
            ])
        )
    
    def _check_rate_limit(self) -> Dict[str, Any]:
        """Check GitHub API rate limit status."""
        rate_limit = self.github_client.get_rate_limit()
        return {
            "remaining": rate_limit.core.remaining,
            "limit": rate_limit.core.limit,
            "reset_time": rate_limit.core.reset,
            "seconds_until_reset": (rate_limit.core.reset - datetime.now()).total_seconds()
        }
    
    def _wait_for_rate_limit_if_needed(self):
        """Wait if we're approaching rate limits."""
        rate_limit_info = self._check_rate_limit()
        
        if rate_limit_info["remaining"] < 10:  # Conservative threshold
            wait_time = max(1, rate_limit_info["seconds_until_reset"])
            print(f"Rate limit approaching. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    def _run(self, repository_url: str, days_back: int = 90, include_closed: bool = True, max_issues: int = 1000) -> Dict[str, Any]:
        """Execute the GitHub issues retrieval."""
        try:
            # Parse repository URL
            repo_path = self._parse_repository_url(repository_url)
            
            # Get repository
            repo = self.github_client.get_repo(repo_path)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Retrieve issues with filtering
            issues_data = []
            issues_processed = 0
            
            # Get issues (includes pull requests by default, we'll filter them)
            states = ["open", "closed"] if include_closed else ["open"]
            
            for state in states:
                if issues_processed >= max_issues:
                    break
                    
                self._wait_for_rate_limit_if_needed()
                
                issues = repo.get_issues(
                    state=state,
                    since=start_date,
                    sort="created",
                    direction="desc"
                )
                
                for issue in issues:
                    if issues_processed >= max_issues:
                        break
                    
                    # Skip pull requests (they're returned as issues by GitHub API)
                    if issue.pull_request is not None:
                        continue
                    
                    # Check if issue is within our date range
                    if issue.created_at < start_date:
                        continue
                    
                    # Convert to structured format
                    structured_issue = self._convert_issue_to_structured(issue)
                    issues_data.append(structured_issue)
                    issues_processed += 1
                    
                    # Rate limiting check every 10 issues
                    if issues_processed % 10 == 0:
                        self._wait_for_rate_limit_if_needed()
            
            # Get repository metadata
            repo_metadata = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "language": repo.language,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at
            }
            
            # Final rate limit check
            final_rate_limit = self._check_rate_limit()
            
            return {
                "success": True,
                "repository": repo_metadata,
                "issues": [issue.dict() for issue in issues_data],
                "total_issues_retrieved": len(issues_data),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days_back
                },
                "rate_limit_info": final_rate_limit,
                "processing_stats": {
                    "issues_processed": issues_processed,
                    "max_requested": max_issues,
                    "states_included": states
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "rate_limit_info": self._check_rate_limit() if hasattr(self, 'github_client') else None
            }
    
    async def _arun(self, repository_url: str, days_back: int = 90, include_closed: bool = True, max_issues: int = 1000) -> Dict[str, Any]:
        """Async version of the tool execution."""
        # For now, we'll run the sync version in a thread pool
        # In a production system, you'd want to use async GitHub libraries
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._run, 
            repository_url, 
            days_back, 
            include_closed, 
            max_issues
        )


# Tool instances for easy import
github_issues_tool = GitHubIssuesTool()

