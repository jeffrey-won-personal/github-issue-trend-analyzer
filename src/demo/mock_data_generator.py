"""
Mock data generator for demo mode.
Creates realistic GitHub repository and issues data for demonstration purposes.
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..core.state import GitHubIssue


class MockDataGenerator:
    """
    Generates realistic mock data for GitHub repositories and issues.
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        
        # Realistic issue templates
        self.issue_templates = [
            # Bug reports
            {
                "title_template": "Bug: {feature} not working properly in {component}",
                "labels": ["bug", "needs-investigation"],
                "comments_range": (0, 8),
                "probability": 0.35
            },
            {
                "title_template": "Critical: {error_type} causing application crash",
                "labels": ["bug", "critical", "urgent"],
                "comments_range": (3, 15),
                "probability": 0.05
            },
            # Feature requests
            {
                "title_template": "Feature Request: Add {feature} to {component}",
                "labels": ["enhancement", "feature-request"],
                "comments_range": (1, 12),
                "probability": 0.25
            },
            {
                "title_template": "Enhancement: Improve {feature} performance",
                "labels": ["enhancement", "performance"],
                "comments_range": (0, 6),
                "probability": 0.15
            },
            # Documentation
            {
                "title_template": "Documentation: Update {component} documentation",
                "labels": ["documentation"],
                "comments_range": (0, 4),
                "probability": 0.08
            },
            # Security
            {
                "title_template": "Security: {security_issue} in {component}",
                "labels": ["security", "urgent"],
                "comments_range": (2, 10),
                "probability": 0.03
            },
            # Questions/Help
            {
                "title_template": "Question: How to {action} with {feature}?",
                "labels": ["question", "help wanted"],
                "comments_range": (1, 8),
                "probability": 0.09
            }
        ]
        
        # Component/feature names for realistic titles
        self.components = [
            "authentication system", "user interface", "API endpoints", "database layer",
            "file manager", "search functionality", "notification system", "user dashboard",
            "settings panel", "data export", "reporting module", "plugin system",
            "theme engine", "code editor", "terminal", "debugger", "extension marketplace"
        ]
        
        self.features = [
            "dark mode", "auto-save", "syntax highlighting", "multi-language support",
            "real-time collaboration", "version control", "backup system", "search filters",
            "keyboard shortcuts", "drag and drop", "mobile support", "accessibility",
            "performance monitoring", "error logging", "user preferences", "data validation"
        ]
        
        self.error_types = [
            "NullPointerException", "memory leak", "infinite loop", "timeout error",
            "authentication failure", "database connection error", "file system error",
            "network timeout", "parsing error", "validation error"
        ]
        
        self.security_issues = [
            "potential XSS vulnerability", "SQL injection risk", "authentication bypass",
            "unauthorized access", "data exposure", "insecure API endpoint",
            "weak encryption", "session hijacking risk"
        ]
        
        self.actions = [
            "configure", "implement", "integrate", "optimize", "customize",
            "troubleshoot", "deploy", "migrate", "backup", "restore"
        ]
        
        # Realistic usernames
        self.usernames = [
            "dev_sarah", "mike_coder", "alex_frontend", "backend_ninja", "data_scientist_jane",
            "ui_designer_tom", "security_expert", "qa_tester_lisa", "devops_guru", "ml_engineer",
            "product_manager_kim", "tech_lead_john", "junior_dev_emma", "senior_architect",
            "open_source_contributor", "community_moderator", "bug_hunter_pro", "feature_requester",
            "documentation_writer", "performance_optimizer"
        ]
    
    def generate_repository_metadata(self, repo_url: str) -> Dict[str, Any]:
        """Generate realistic repository metadata."""
        repo_name = repo_url.split('/')[-1] if '/' in repo_url else repo_url
        
        # Base stats on repository name for consistency
        name_hash = hash(repo_name) % 1000000
        
        return {
            "name": repo_name,
            "full_name": repo_url,
            "description": f"A comprehensive {repo_name} project with advanced features and community support",
            "stars": 1000 + (name_hash % 50000),
            "forks": 100 + (name_hash % 5000),
            "open_issues": 50 + (name_hash % 200),
            "language": random.choice(["TypeScript", "Python", "JavaScript", "Java", "Go", "Rust"]),
            "created_at": datetime.now() - timedelta(days=365 + (name_hash % 1000)),
            "updated_at": datetime.now() - timedelta(days=name_hash % 30)
        }
    
    def generate_issues(self, repo_url: str, days_back: int = 90, include_closed: bool = True) -> List[GitHubIssue]:
        """Generate realistic issues for a repository."""
        repo_name = repo_url.split('/')[-1] if '/' in repo_url else repo_url
        
        # Determine number of issues based on repository name (for consistency)
        name_hash = hash(repo_name)
        base_issues = 50 + (abs(name_hash) % 200)
        
        # Adjust for time period
        issues_count = int(base_issues * (days_back / 90))
        
        issues = []
        current_date = datetime.now()
        
        # Generate issues with realistic temporal distribution
        for i in range(issues_count):
            # Create temporal clustering (some periods with more activity)
            if random.random() < 0.3:  # 30% chance of burst activity
                days_ago = random.randint(0, min(30, days_back))
            else:
                days_ago = random.randint(0, days_back)
            
            created_at = current_date - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Select issue template based on probability
            template = self._select_template()
            
            # Generate issue content
            title = self._generate_title(template["title_template"])
            labels = template["labels"].copy()
            
            # Add random additional labels
            additional_labels = ["good first issue", "help wanted", "duplicate", "wontfix", "invalid"]
            if random.random() < 0.2:
                labels.append(random.choice(additional_labels))
            
            # Determine if issue is closed
            is_closed = False
            closed_at = None
            
            if include_closed and random.random() < 0.6:  # 60% of issues are closed
                is_closed = True
                # Issues are typically closed after some time
                close_delay = random.randint(1, max(1, days_back - days_ago))
                closed_at = created_at + timedelta(days=close_delay)
                if closed_at > current_date:
                    closed_at = current_date - timedelta(days=random.randint(0, 5))
            
            # Generate comments count
            min_comments, max_comments = template["comments_range"]
            comments_count = random.randint(min_comments, max_comments)
            
            # More comments on older issues and critical issues
            if "critical" in labels or "urgent" in labels:
                comments_count += random.randint(2, 8)
            if days_ago > 30:
                comments_count += random.randint(0, 5)
            
            # Generate issue
            issue = GitHubIssue(
                id=100000 + i,
                number=i + 1,
                title=title,
                body=self._generate_issue_body(title, template),
                state="closed" if is_closed else "open",
                created_at=created_at,
                updated_at=closed_at or created_at + timedelta(days=random.randint(0, min(7, days_ago))),
                closed_at=closed_at,
                labels=labels,
                assignees=self._generate_assignees(),
                author=random.choice(self.usernames),
                comments_count=comments_count,
                reactions_count=random.randint(0, min(10, comments_count + 2))
            )
            
            issues.append(issue)
        
        # Sort by creation date
        issues.sort(key=lambda x: x.created_at)
        
        return issues
    
    def _select_template(self) -> Dict[str, Any]:
        """Select an issue template based on probability."""
        rand = random.random()
        cumulative_prob = 0
        
        for template in self.issue_templates:
            cumulative_prob += template["probability"]
            if rand <= cumulative_prob:
                return template
        
        return self.issue_templates[0]  # Fallback
    
    def _generate_title(self, title_template: str) -> str:
        """Generate a realistic issue title from template."""
        replacements = {
            "{feature}": random.choice(self.features),
            "{component}": random.choice(self.components),
            "{error_type}": random.choice(self.error_types),
            "{security_issue}": random.choice(self.security_issues),
            "{action}": random.choice(self.actions)
        }
        
        title = title_template
        for placeholder, replacement in replacements.items():
            title = title.replace(placeholder, replacement)
        
        return title
    
    def _generate_issue_body(self, title: str, template: Dict[str, Any]) -> str:
        """Generate realistic issue body content."""
        if "bug" in template["labels"]:
            return f"""## Description
{title}

## Steps to Reproduce
1. Navigate to the {random.choice(self.components)}
2. Attempt to {random.choice(self.actions)} the {random.choice(self.features)}
3. Observe the error

## Expected Behavior
The {random.choice(self.features)} should work as intended without errors.

## Actual Behavior
{random.choice(self.error_types)} occurs, preventing normal operation.

## Environment
- Version: {random.choice(['v1.2.3', 'v2.1.0', 'v3.0.0-beta'])}
- Browser: {random.choice(['Chrome 120', 'Firefox 119', 'Safari 17'])}
- OS: {random.choice(['Windows 11', 'macOS 14', 'Ubuntu 22.04'])}
"""
        
        elif "enhancement" in template["labels"]:
            return f"""## Feature Description
{title}

## Use Case
This enhancement would improve user experience by providing better {random.choice(self.features)} functionality.

## Proposed Solution
Implement {random.choice(self.features)} in the {random.choice(self.components)} to allow users to {random.choice(self.actions)} more efficiently.

## Alternatives Considered
- Alternative approach using {random.choice(self.features)}
- Integration with existing {random.choice(self.components)}

## Additional Context
This feature has been requested by multiple users and would significantly improve workflow efficiency.
"""
        
        elif "security" in template["labels"]:
            return f"""## Security Issue
{title}

## Risk Level
{random.choice(['High', 'Medium', 'Critical'])}

## Description
Potential security vulnerability identified in {random.choice(self.components)}.

## Impact
Could allow unauthorized access or data exposure.

## Recommendation
Immediate review and patching required.

**Note: Please handle this issue privately until resolved.**
"""
        
        else:
            return f"""## Issue Description
{title}

## Additional Information
Please provide more details about this {random.choice(['request', 'question', 'issue'])}.

## Context
Related to {random.choice(self.components)} functionality.
"""
    
    def _generate_assignees(self) -> List[str]:
        """Generate realistic assignees."""
        if random.random() < 0.3:  # 30% of issues have assignees
            num_assignees = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            return random.sample(self.usernames[:10], num_assignees)  # Use maintainer names
        return []
    
    def generate_demo_repositories(self) -> List[Dict[str, Any]]:
        """Generate a list of demo repositories for the frontend."""
        return [
            {
                "url": "microsoft/vscode-demo",
                "name": "VS Code Demo",
                "description": "Popular code editor with extensive features",
                "stars": 45000,
                "language": "TypeScript"
            },
            {
                "url": "facebook/react-demo", 
                "name": "React Demo",
                "description": "JavaScript library for building user interfaces",
                "stars": 38000,
                "language": "JavaScript"
            },
            {
                "url": "tensorflow/tensorflow-demo",
                "name": "TensorFlow Demo", 
                "description": "Machine learning platform",
                "stars": 55000,
                "language": "Python"
            },
            {
                "url": "kubernetes/kubernetes-demo",
                "name": "Kubernetes Demo",
                "description": "Container orchestration platform",
                "stars": 42000,
                "language": "Go"
            }
        ]


# Global instance for consistent demo data
demo_generator = MockDataGenerator()


