# backend/models/repository.py
from typing import Dict, List, Optional

class Repository:
    """Represents a code repository."""

    def __init__(self, name: str, owner: str, url: str, language: Optional[str] = None):
        self.name = name
        self.owner = owner
        self.url = url
        self.language = language

    def __repr__(self):
        return f"Repository(name='{self.name}', owner='{self.owner}', url='{self.url}', language='{self.language}')"

    def to_dict(self):
        return {
            "name": self.name,
            "owner": self.owner,
            "url": self.url,
            "language": self.language
        }