"""
Chat Skill Integration Module

Main integration class that connects chat messages with skill modifications.
"""

import os
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime

from .skills_manager import SkillsManager, Skill, SkillCategory, SkillStatus
from .intent_parser import IntentParser, Intent, IntentType
from .action_executor import ActionExecutor, ExecutionResult, ActionResult


@dataclass
class ConversationContext:
    """
    Maintains context across conversation turns.

    Attributes:
        last_skill_id: The last skill that was referenced
        last_intent: The last intent that was processed
        history: List of previous messages and results
        variables: Custom variables set during conversation
    """
    last_skill_id: Optional[str] = None
    last_intent: Optional[Intent] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)

    def add_to_history(self, message: str, result: ExecutionResult) -> None:
        """Add an interaction to history."""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'result': result.to_dict()
        })
        if result.intent and result.intent.skill_id:
            self.last_skill_id = result.intent.skill_id
            self.last_intent = result.intent


class ChatSkillIntegration:
    """
    Main integration class for chat-based skill modifications.

    Provides a unified interface for:
    - Processing natural language messages
    - Executing skill modifications
    - Maintaining conversation context
    - Formatting responses

    Example:
        >>> integration = ChatSkillIntegration()
        >>> response = integration.process_message("Adicionar skill de análise")
        >>> print(response)
        Skill 'análise' adicionada com sucesso.

        >>> response = integration.process_message("Listar skills")
        >>> print(response)
        Encontradas 1 skill(s).
    """

    def __init__(self,
                 storage_path: Optional[str] = None,
                 language: str = 'pt',
                 verbose: bool = False):
        """
        Initialize the chat skill integration.

        Args:
            storage_path: Path to persist skills (JSON file)
            language: Default language ('pt' for Portuguese, 'en' for English)
            verbose: Whether to include detailed information in responses
        """
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(__file__),
                'skills_data.json'
            )

        self._skills_manager = SkillsManager(storage_path)
        self._intent_parser = IntentParser()
        self._action_executor = ActionExecutor(self._skills_manager)
        self._context = ConversationContext()
        self._language = language
        self._verbose = verbose
        self._response_formatters: Dict[IntentType, Callable] = {}

        # Register default skills
        self._register_default_skills()

    def _register_default_skills(self) -> None:
        """Register default built-in skills."""
        default_skills = [
            Skill(
                id='data_analysis',
                name='Análise de Dados',
                description='Executa análise exploratória de dados',
                category=SkillCategory.DATA_ANALYSIS,
                parameters={'output_format': 'summary'}
            ),
            Skill(
                id='data_visualization',
                name='Visualização de Dados',
                description='Cria gráficos e visualizações',
                category=SkillCategory.VISUALIZATION,
                parameters={'chart_type': 'auto', 'theme': 'default'}
            ),
            Skill(
                id='model_training',
                name='Treinamento de Modelo',
                description='Treina modelos de machine learning',
                category=SkillCategory.MACHINE_LEARNING,
                parameters={'model_type': 'auto', 'cv_folds': 5}
            ),
            Skill(
                id='data_cleaning',
                name='Limpeza de Dados',
                description='Limpa e preprocessa dados',
                category=SkillCategory.DATA_PROCESSING,
                parameters={'handle_missing': 'drop', 'remove_duplicates': True}
            ),
            Skill(
                id='report_generation',
                name='Geração de Relatório',
                description='Gera relatórios de análise',
                category=SkillCategory.REPORTING,
                parameters={'format': 'html', 'include_charts': True}
            ),
        ]

        for skill in default_skills:
            if not self._skills_manager.get_skill(skill.id):
                self._skills_manager.add_skill(skill)

    def process_message(self, message: str) -> str:
        """
        Process a chat message and execute the corresponding action.

        Args:
            message: The user's chat message

        Returns:
            A formatted response string
        """
        # Parse the intent
        intent = self._intent_parser.parse(message)

        # Handle context-dependent references
        intent = self._resolve_context(intent)

        # Execute the action
        result = self._action_executor.execute(intent)

        # Update context
        self._context.add_to_history(message, result)

        # Format and return response
        return self._format_response(result)

    def _resolve_context(self, intent: Intent) -> Intent:
        """
        Resolve context-dependent references in the intent.

        Handles cases like "essa skill", "a mesma", etc.
        """
        if not intent.skill_id and self._context.last_skill_id:
            # Check for context references
            context_refs = [
                'essa', 'este', 'esta', 'mesmo', 'mesma',
                'it', 'this', 'that', 'same'
            ]
            message_lower = intent.original_message.lower()

            for ref in context_refs:
                if ref in message_lower:
                    intent.skill_id = self._context.last_skill_id
                    skill = self._skills_manager.get_skill(intent.skill_id)
                    if skill:
                        intent.skill_name = skill.name
                    break

        return intent

    def _format_response(self, result: ExecutionResult) -> str:
        """
        Format the execution result into a human-readable response.

        Args:
            result: The execution result to format

        Returns:
            Formatted response string
        """
        # Check for custom formatter
        if result.intent and result.intent.type in self._response_formatters:
            return self._response_formatters[result.intent.type](result)

        response = result.message

        if self._verbose and result.data:
            if 'skill' in result.data:
                skill_data = result.data['skill']
                response += f"\n\n📋 Detalhes:\n"
                response += f"   ID: {skill_data['id']}\n"
                response += f"   Nome: {skill_data['name']}\n"
                response += f"   Categoria: {skill_data['category']}\n"
                response += f"   Status: {skill_data['status']}\n"
                if skill_data.get('parameters'):
                    response += f"   Parâmetros: {skill_data['parameters']}\n"

            if 'skills' in result.data and result.data['skills']:
                response += "\n\n📋 Skills:\n"
                for skill in result.data['skills']:
                    status_icon = "✅" if skill['status'] == 'active' else "⏸️"
                    response += f"   {status_icon} {skill['name']} ({skill['id']})\n"

            if 'statistics' in result.data:
                stats = result.data['statistics']
                response += f"\n📊 Estatísticas:\n"
                response += f"   Total: {stats['total']}\n"

        return response

    def register_response_formatter(self,
                                     intent_type: IntentType,
                                     formatter: Callable[[ExecutionResult], str]) -> None:
        """
        Register a custom response formatter for an intent type.

        Args:
            intent_type: The intent type to format
            formatter: Function that takes ExecutionResult and returns string
        """
        self._response_formatters[intent_type] = formatter

    def register_skill_handler(self, skill_id: str, handler: Callable) -> None:
        """
        Register a handler function for a skill.

        Args:
            skill_id: The skill ID
            handler: The handler function to execute
        """
        self._skills_manager.register_handler(skill_id, handler)

    def register_default_handler(self, handler: Callable) -> None:
        """
        Register a default handler for all new skills.

        Args:
            handler: The default handler function
        """
        self._action_executor.register_default_handler('*', handler)

    def add_skill(self, skill: Skill) -> bool:
        """
        Programmatically add a skill.

        Args:
            skill: The skill to add

        Returns:
            True if successful
        """
        return self._skills_manager.add_skill(skill)

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        return self._skills_manager.get_skill(skill_id)

    def list_skills(self) -> List[Skill]:
        """List all skills."""
        return self._skills_manager.list_skills()

    def get_context(self) -> ConversationContext:
        """Get the current conversation context."""
        return self._context

    def clear_context(self) -> None:
        """Clear the conversation context."""
        self._context = ConversationContext()

    def get_help(self) -> str:
        """Get help text in the configured language."""
        return self._intent_parser.get_supported_commands(self._language)

    def set_language(self, language: str) -> None:
        """
        Set the response language.

        Args:
            language: 'pt' for Portuguese, 'en' for English
        """
        self._language = language

    def set_verbose(self, verbose: bool) -> None:
        """
        Set verbose mode.

        Args:
            verbose: Whether to include detailed information
        """
        self._verbose = verbose

    def interactive_mode(self) -> None:
        """
        Start an interactive chat session.

        Reads messages from stdin and prints responses.
        Type 'sair' or 'exit' to quit.
        """
        print("=" * 50)
        print("Chat Skill Integration - Modo Interativo")
        print("=" * 50)
        print("Digite seus comandos ou 'ajuda' para ver opções.")
        print("Digite 'sair' ou 'exit' para encerrar.\n")

        while True:
            try:
                message = input("Você: ").strip()

                if not message:
                    continue

                if message.lower() in ('sair', 'exit', 'quit', 'q'):
                    print("\nAté logo! 👋")
                    break

                response = self.process_message(message)
                print(f"\nAssistente: {response}\n")

            except KeyboardInterrupt:
                print("\n\nSessão encerrada.")
                break
            except EOFError:
                break

    def batch_process(self, messages: List[str]) -> List[str]:
        """
        Process multiple messages in batch.

        Args:
            messages: List of messages to process

        Returns:
            List of responses
        """
        return [self.process_message(msg) for msg in messages]

    def export_skills(self, filepath: str) -> bool:
        """
        Export skills to a JSON file.

        Args:
            filepath: Path to export to

        Returns:
            True if successful
        """
        import json
        try:
            skills = [s.to_dict() for s in self._skills_manager.list_skills()]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({'skills': skills}, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def import_skills(self, filepath: str) -> int:
        """
        Import skills from a JSON file.

        Args:
            filepath: Path to import from

        Returns:
            Number of skills imported
        """
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for skill_data in data.get('skills', []):
                skill = Skill.from_dict(skill_data)
                if self._skills_manager.add_skill(skill):
                    count += 1
            return count
        except (IOError, json.JSONDecodeError):
            return 0


def create_integration(storage_path: Optional[str] = None,
                       language: str = 'pt',
                       verbose: bool = False) -> ChatSkillIntegration:
    """
    Factory function to create a ChatSkillIntegration instance.

    Args:
        storage_path: Path to persist skills
        language: Default language
        verbose: Verbose mode

    Returns:
        Configured ChatSkillIntegration instance
    """
    return ChatSkillIntegration(
        storage_path=storage_path,
        language=language,
        verbose=verbose
    )
