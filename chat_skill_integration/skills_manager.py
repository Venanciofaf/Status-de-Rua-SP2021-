"""
Skills Manager Module

Handles skill definitions, storage, and management operations.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum


class SkillStatus(Enum):
    """Status of a skill."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"


class SkillCategory(Enum):
    """Categories for skills."""
    DATA_ANALYSIS = "data_analysis"
    MACHINE_LEARNING = "machine_learning"
    VISUALIZATION = "visualization"
    DATA_PROCESSING = "data_processing"
    REPORTING = "reporting"
    CUSTOM = "custom"


@dataclass
class Skill:
    """
    Represents a skill that can be modified through chat.

    Attributes:
        id: Unique identifier for the skill
        name: Display name of the skill
        description: What the skill does
        category: Category the skill belongs to
        parameters: Configuration parameters for the skill
        status: Current status of the skill
        created_at: When the skill was created
        modified_at: When the skill was last modified
        handler: Optional callable that executes the skill
    """
    id: str
    name: str
    description: str
    category: SkillCategory = SkillCategory.CUSTOM
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: SkillStatus = SkillStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    handler: Optional[Callable] = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary (excluding handler)."""
        data = asdict(self)
        data['category'] = self.category.value
        data['status'] = self.status.value
        del data['handler']
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Skill':
        """Create skill from dictionary."""
        data['category'] = SkillCategory(data.get('category', 'custom'))
        data['status'] = SkillStatus(data.get('status', 'active'))
        return cls(**data)


class SkillsManager:
    """
    Manages a collection of skills with CRUD operations.

    Provides methods to add, modify, remove, enable/disable skills,
    and persist them to storage.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the skills manager.

        Args:
            storage_path: Path to JSON file for persisting skills.
                         If None, skills are only stored in memory.
        """
        self._skills: Dict[str, Skill] = {}
        self._storage_path = storage_path
        self._handlers: Dict[str, Callable] = {}

        if storage_path and os.path.exists(storage_path):
            self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Load skills from storage file."""
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for skill_data in data.get('skills', []):
                    skill = Skill.from_dict(skill_data)
                    self._skills[skill.id] = skill
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load skills from storage: {e}")

    def _save_to_storage(self) -> None:
        """Save skills to storage file."""
        if not self._storage_path:
            return

        try:
            data = {
                'skills': [skill.to_dict() for skill in self._skills.values()],
                'last_updated': datetime.now().isoformat()
            }
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save skills to storage: {e}")

    def add_skill(self, skill: Skill) -> bool:
        """
        Add a new skill.

        Args:
            skill: The skill to add

        Returns:
            True if added successfully, False if skill ID already exists
        """
        if skill.id in self._skills:
            return False

        self._skills[skill.id] = skill
        self._save_to_storage()
        return True

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """
        Get a skill by ID.

        Args:
            skill_id: The ID of the skill to retrieve

        Returns:
            The skill if found, None otherwise
        """
        return self._skills.get(skill_id)

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name (case-insensitive).

        Args:
            name: The name of the skill to retrieve

        Returns:
            The skill if found, None otherwise
        """
        name_lower = name.lower()
        for skill in self._skills.values():
            if skill.name.lower() == name_lower:
                return skill
        return None

    def update_skill(self, skill_id: str, **updates) -> bool:
        """
        Update a skill's attributes.

        Args:
            skill_id: The ID of the skill to update
            **updates: Keyword arguments with attributes to update

        Returns:
            True if updated successfully, False if skill not found
        """
        if skill_id not in self._skills:
            return False

        skill = self._skills[skill_id]

        for key, value in updates.items():
            if hasattr(skill, key) and key not in ('id', 'created_at'):
                if key == 'parameters' and isinstance(value, dict):
                    skill.parameters.update(value)
                else:
                    setattr(skill, key, value)

        skill.modified_at = datetime.now().isoformat()
        self._save_to_storage()
        return True

    def remove_skill(self, skill_id: str) -> bool:
        """
        Remove a skill.

        Args:
            skill_id: The ID of the skill to remove

        Returns:
            True if removed successfully, False if skill not found
        """
        if skill_id not in self._skills:
            return False

        del self._skills[skill_id]
        self._save_to_storage()
        return True

    def enable_skill(self, skill_id: str) -> bool:
        """Enable a skill (set status to active)."""
        return self.update_skill(skill_id, status=SkillStatus.ACTIVE)

    def disable_skill(self, skill_id: str) -> bool:
        """Disable a skill (set status to disabled)."""
        return self.update_skill(skill_id, status=SkillStatus.DISABLED)

    def list_skills(self,
                    category: Optional[SkillCategory] = None,
                    status: Optional[SkillStatus] = None) -> List[Skill]:
        """
        List skills with optional filtering.

        Args:
            category: Filter by category
            status: Filter by status

        Returns:
            List of matching skills
        """
        skills = list(self._skills.values())

        if category:
            skills = [s for s in skills if s.category == category]
        if status:
            skills = [s for s in skills if s.status == status]

        return skills

    def search_skills(self, query: str) -> List[Skill]:
        """
        Search skills by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching skills
        """
        query_lower = query.lower()
        return [
            skill for skill in self._skills.values()
            if query_lower in skill.name.lower()
            or query_lower in skill.description.lower()
        ]

    def register_handler(self, skill_id: str, handler: Callable) -> bool:
        """
        Register a handler function for a skill.

        Args:
            skill_id: The ID of the skill
            handler: Callable that executes the skill logic

        Returns:
            True if registered successfully
        """
        if skill_id in self._skills:
            self._skills[skill_id].handler = handler
        self._handlers[skill_id] = handler
        return True

    def execute_skill(self, skill_id: str, **kwargs) -> Any:
        """
        Execute a skill's handler.

        Args:
            skill_id: The ID of the skill to execute
            **kwargs: Arguments to pass to the handler

        Returns:
            Result of the handler execution

        Raises:
            ValueError: If skill not found or has no handler
        """
        skill = self.get_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill '{skill_id}' not found")

        if skill.status != SkillStatus.ACTIVE:
            raise ValueError(f"Skill '{skill_id}' is not active")

        handler = skill.handler or self._handlers.get(skill_id)
        if not handler:
            raise ValueError(f"Skill '{skill_id}' has no registered handler")

        return handler(**kwargs)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about managed skills."""
        skills = list(self._skills.values())
        return {
            'total': len(skills),
            'by_status': {
                status.value: len([s for s in skills if s.status == status])
                for status in SkillStatus
            },
            'by_category': {
                category.value: len([s for s in skills if s.category == category])
                for category in SkillCategory
            }
        }
