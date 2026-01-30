"""
Chat Skill Integration Module

This module provides a chat interface for modifying skills through natural language
requests, integrated with action execution capabilities.

Example usage (standalone):
    from chat_skill_integration import ChatSkillIntegration

    integration = ChatSkillIntegration()
    response = integration.process_message("Adicionar a skill de análise de dados")
    print(response)

Example usage (with Claude):
    from chat_skill_integration import ClaudeSkillIntegration

    claude = ClaudeSkillIntegration(api_key="sua-api-key")
    response = claude.chat("Cria uma skill de machine learning")
    print(response)
"""

from .skills_manager import Skill, SkillsManager, SkillCategory, SkillStatus
from .intent_parser import IntentParser, Intent, IntentType
from .action_executor import ActionExecutor, ExecutionResult, ActionResult
from .integration import ChatSkillIntegration

# Claude integration (optional - requires anthropic package)
try:
    from .claude_integration import ClaudeSkillIntegration, ToolResult
    _CLAUDE_AVAILABLE = True
except ImportError:
    _CLAUDE_AVAILABLE = False
    ClaudeSkillIntegration = None
    ToolResult = None

__all__ = [
    # Core
    'Skill',
    'SkillsManager',
    'SkillCategory',
    'SkillStatus',
    # Intent parsing
    'IntentParser',
    'Intent',
    'IntentType',
    # Action execution
    'ActionExecutor',
    'ExecutionResult',
    'ActionResult',
    # Main integration
    'ChatSkillIntegration',
    # Claude integration
    'ClaudeSkillIntegration',
    'ToolResult',
]

__version__ = '1.1.0'

def is_claude_available() -> bool:
    """Check if Claude integration is available (anthropic package installed)."""
    return _CLAUDE_AVAILABLE
