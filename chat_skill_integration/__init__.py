"""
Chat Skill Integration Module

This module provides a chat interface for modifying skills through natural language
requests, integrated with action execution capabilities.

Example usage:
    from chat_skill_integration import ChatSkillIntegration

    integration = ChatSkillIntegration()
    response = integration.process_message("Adicionar a skill de análise de dados")
    print(response)
"""

from .skills_manager import Skill, SkillsManager
from .intent_parser import IntentParser, Intent
from .action_executor import ActionExecutor
from .integration import ChatSkillIntegration

__all__ = [
    'Skill',
    'SkillsManager',
    'IntentParser',
    'Intent',
    'ActionExecutor',
    'ChatSkillIntegration'
]

__version__ = '1.0.0'
