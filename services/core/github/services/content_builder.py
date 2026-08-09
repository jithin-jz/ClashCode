"""
Content builders — generates README.md and PROGRESS.md content.
"""

from datetime import datetime

from ..models import GitHubConnection, GitHubPushLog

LANGUAGE_EXTENSIONS = {
    "python": "py",
    "javascript": "js",
    "typescript": "ts",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "go": "go",
    "rust": "rs",
    "ruby": "rb",
    "csharp": "cs",
    "kotlin": "kt",
    "swift": "swift",
}


def language_extension(language: str) -> str:
    """Map language name to file extension."""
    return LANGUAGE_EXTENSIONS.get(language.lower(), "txt")


class ContentBuilder:
    """Generates all markdown content for the GitHub repo."""

    def __init__(self, connection: GitHubConnection):
        self.connection = connection
        self.username = connection.github_username

    def repo_readme(self) -> str:
        """Professional root README.md."""
        date = datetime.now().strftime("%B %d, %Y")

        return f"""<div align="center">

# ⚡ CLASHCODE Solutions

**Coding challenge solutions — auto-synced from [clashcode.com](https://clashcode.com)**

[![CLASHCODE](https://img.shields.io/badge/Platform-CLASHCODE-000000?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTMgMTBWM0w0IDE0aDdWMjFMMjAgMTBoLTd6IiBmaWxsPSIjMTBiOTgxIi8+PC9zdmc+)](https://clashcode.com)
[![Auto-Sync](https://img.shields.io/badge/Sync-Automated-10b981?style=for-the-badge&logo=github&logoColor=white)](https://clashcode.com)
[![Profile](https://img.shields.io/badge/Coder-@{self.username}-1a1a1a?style=for-the-badge&logo=github&logoColor=white)](https://github.com/{self.username})

---

*Every time I complete a challenge, my solution is automatically pushed here.*

</div>

## 🗂️ Repository Structure

```
{self.connection.repo_name}/
│
├── level-01-challenge-slug/
│   ├── README.md          ← Problem description & metadata
│   └── solution.py        ← My solution
│
├── level-02-challenge-slug/
│   ├── README.md
│   └── solution.py
│
├── PROGRESS.md            ← Full progress tracker
└── README.md              ← You are here
```

## 📊 Progress

Track my journey → **[PROGRESS.md](./PROGRESS.md)**

## 🛠️ Tech

| | |
|---|---|
| **Platform** | [CLASHCODE](https://clashcode.com) |
| **Language** | Python |
| **Sync** | Automated via GitHub API |

## 🔗 Links

- 🌐 **Platform**: [clashcode.com](https://clashcode.com)
- 👤 **Profile**: [@{self.username}](https://github.com/{self.username})

---

<div align="center">

<sub>🤖 This repository is automatically maintained by <a href="https://clashcode.com">CLASHCODE</a> · Generated on {date}</sub>

</div>
"""

    def problem_readme(self, push_log: GitHubPushLog) -> str:
        """README.md for an individual challenge folder."""
        ext = language_extension(push_log.language)
        date = push_log.created_at.strftime("%B %d, %Y") if push_log.created_at else "N/A"

        parts = [
            f"# Level {push_log.challenge_order} — {push_log.challenge_title}\n",
            "",
            "| | |",
            "|---|---|",
            "| **Platform** | [CLASHCODE](https://clashcode.com) |",
            f"| **Language** | {push_log.language.capitalize()} |",
            f"| **Solved by** | [@{self.username}](https://github.com/{self.username}) |",
            f"| **Date** | {date} |",
            "",
        ]

        if self.connection.include_problem_description and push_log.challenge_description:
            parts.append("---\n")
            parts.append("## 📋 Problem\n")
            parts.append(push_log.challenge_description)
            parts.append("\n")

        parts.append("---\n")
        parts.append("## 💡 Solution\n")
        parts.append(f"→ [`solution.{ext}`](./solution.{ext})\n")
        parts.append("---\n")
        parts.append("<sub>Auto-synced from [CLASHCODE](https://clashcode.com)</sub>\n")

        return "\n".join(parts)

    def progress_tracker(self, logs) -> str:
        """PROGRESS.md with visual progress bar and table."""
        from django.utils import timezone

        count = logs.count()
        last_updated = timezone.now().strftime("%B %d, %Y at %H:%M UTC")

        total_levels = max(count, 10)
        progress_pct = min(int((count / total_levels) * 100), 100)
        filled = int(progress_pct / 5)
        bar = "█" * filled + "░" * (20 - filled)

        content = f"""<div align="center">

# 📊 Progress Tracker

**[@{self.username}](https://github.com/{self.username})** · CLASHCODE Solutions

`{bar}` **{count}** challenges solved

<sub>Last updated: {last_updated}</sub>

</div>

---

## Completed Challenges

| # | Challenge | Language | Date | Solution |
|:---:|-----------|:--------:|:----:|:--------:|
"""

        for log in logs:
            date_str = log.pushed_at.strftime("%b %d") if log.pushed_at else "—"
            folder = f"level-{log.challenge_order:02d}-{log.challenge_slug}"
            ext = language_extension(log.language)
            content += f"| {log.challenge_order} | [{log.challenge_title}](./{folder}) | `{log.language}` | {date_str} | [→](./{folder}/solution.{ext}) |\n"

        content += """
---

<div align="center">

<sub>⚡ Auto-tracked by <a href="https://clashcode.com">CLASHCODE</a></sub>

</div>
"""
        return content
