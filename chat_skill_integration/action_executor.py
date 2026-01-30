"""
Action Executor Module

Executes skill modification actions based on parsed intents.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, List
from enum import Enum

from .intent_parser import Intent, IntentType
from .skills_manager import SkillsManager, Skill, SkillStatus, SkillCategory


class ActionResult(Enum):
    """Result status of an action execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class ExecutionResult:
    """
    Result of executing an action.

    Attributes:
        status: The result status
        message: Human-readable message about the result
        data: Any data returned by the action
        intent: The original intent that was executed
    """
    status: ActionResult
    message: str
    data: Optional[Any] = None
    intent: Optional[Intent] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'status': self.status.value,
            'message': self.message,
            'data': self.data,
            'intent_type': self.intent.type.value if self.intent else None
        }


class ActionExecutor:
    """
    Executes skill modification actions based on intents.

    Bridges the gap between parsed intents and actual skill modifications.
    """

    def __init__(self, skills_manager: SkillsManager):
        """
        Initialize the action executor.

        Args:
            skills_manager: The skills manager to use for operations
        """
        self._skills_manager = skills_manager
        self._hooks: Dict[IntentType, List[Callable]] = {
            intent_type: [] for intent_type in IntentType
        }
        self._default_handlers: Dict[str, Callable] = {}

    def execute(self, intent: Intent) -> ExecutionResult:
        """
        Execute an action based on the parsed intent.

        Args:
            intent: The parsed intent to execute

        Returns:
            ExecutionResult with the outcome
        """
        if not intent.is_valid() and intent.type not in (IntentType.LIST_SKILLS, IntentType.HELP):
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message="Intent inválido ou informação insuficiente.",
                intent=intent
            )

        # Call pre-execution hooks
        for hook in self._hooks.get(intent.type, []):
            try:
                hook(intent, 'pre')
            except Exception as e:
                print(f"Warning: Pre-execution hook failed: {e}")

        # Execute based on intent type
        handler_map = {
            IntentType.ADD_SKILL: self._handle_add_skill,
            IntentType.REMOVE_SKILL: self._handle_remove_skill,
            IntentType.MODIFY_SKILL: self._handle_modify_skill,
            IntentType.ENABLE_SKILL: self._handle_enable_skill,
            IntentType.DISABLE_SKILL: self._handle_disable_skill,
            IntentType.LIST_SKILLS: self._handle_list_skills,
            IntentType.GET_SKILL_INFO: self._handle_get_skill_info,
            IntentType.EXECUTE_SKILL: self._handle_execute_skill,
            IntentType.SET_PARAMETER: self._handle_set_parameter,
            IntentType.HELP: self._handle_help,
            IntentType.UNKNOWN: self._handle_unknown,
        }

        handler = handler_map.get(intent.type, self._handle_unknown)
        result = handler(intent)

        # Call post-execution hooks
        for hook in self._hooks.get(intent.type, []):
            try:
                hook(intent, 'post', result)
            except Exception as e:
                print(f"Warning: Post-execution hook failed: {e}")

        return result

    def register_hook(self, intent_type: IntentType,
                      callback: Callable) -> None:
        """
        Register a hook to be called before/after action execution.

        Args:
            intent_type: The intent type to hook
            callback: Callable(intent, phase, result=None)
        """
        self._hooks[intent_type].append(callback)

    def register_default_handler(self, skill_id: str,
                                  handler: Callable) -> None:
        """
        Register a default handler for new skills.

        Args:
            skill_id: The skill ID pattern (supports wildcards)
            handler: The handler function
        """
        self._default_handlers[skill_id] = handler

    def _handle_add_skill(self, intent: Intent) -> ExecutionResult:
        """Handle adding a new skill."""
        skill_name = intent.skill_name
        skill_id = intent.skill_id

        # Check if skill already exists
        existing = self._skills_manager.get_skill(skill_id)
        if existing:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name}' já existe.",
                data={'existing_skill': existing.to_dict()},
                intent=intent
            )

        # Determine category
        category_str = intent.parameters.get('category', 'custom')
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.CUSTOM

        # Create the skill
        skill = Skill(
            id=skill_id,
            name=skill_name,
            description=f"Skill de {skill_name}",
            category=category,
            parameters=intent.parameters.get('skill_params', {}),
            status=SkillStatus.ACTIVE
        )

        # Register default handler if available
        for pattern, handler in self._default_handlers.items():
            if pattern == '*' or pattern in skill_id:
                self._skills_manager.register_handler(skill_id, handler)
                break

        success = self._skills_manager.add_skill(skill)

        if success:
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill_name}' adicionada com sucesso.",
                data={'skill': skill.to_dict()},
                intent=intent
            )
        else:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Falha ao adicionar skill '{skill_name}'.",
                intent=intent
            )

    def _handle_remove_skill(self, intent: Intent) -> ExecutionResult:
        """Handle removing a skill."""
        skill_id = intent.skill_id
        skill_name = intent.skill_name

        # Try to find by ID first, then by name
        skill = self._skills_manager.get_skill(skill_id)
        if not skill and skill_name:
            skill = self._skills_manager.get_skill_by_name(skill_name)
            if skill:
                skill_id = skill.id

        if not skill:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name or skill_id}' não encontrada.",
                intent=intent
            )

        success = self._skills_manager.remove_skill(skill_id)

        if success:
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill.name}' removida com sucesso.",
                data={'removed_skill_id': skill_id},
                intent=intent
            )
        else:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Falha ao remover skill '{skill_name}'.",
                intent=intent
            )

    def _handle_modify_skill(self, intent: Intent) -> ExecutionResult:
        """Handle modifying a skill."""
        skill_id = intent.skill_id
        skill_name = intent.skill_name

        # Find the skill
        skill = self._skills_manager.get_skill(skill_id)
        if not skill and skill_name:
            skill = self._skills_manager.get_skill_by_name(skill_name)
            if skill:
                skill_id = skill.id

        if not skill:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name or skill_id}' não encontrada.",
                intent=intent
            )

        # Get modification parameters
        updates = {}
        if 'new_name' in intent.parameters:
            updates['name'] = intent.parameters['new_name']
        if 'new_description' in intent.parameters:
            updates['description'] = intent.parameters['new_description']
        if 'category' in intent.parameters:
            try:
                updates['category'] = SkillCategory(intent.parameters['category'])
            except ValueError:
                pass
        if 'parameters' in intent.parameters:
            updates['parameters'] = intent.parameters['parameters']

        if not updates:
            return ExecutionResult(
                status=ActionResult.PARTIAL,
                message=f"Skill '{skill.name}' encontrada, mas nenhuma modificação especificada. "
                        f"Use parâmetros como 'new_name', 'new_description', ou 'parameters'.",
                data={'skill': skill.to_dict()},
                intent=intent
            )

        success = self._skills_manager.update_skill(skill_id, **updates)

        if success:
            updated_skill = self._skills_manager.get_skill(skill_id)
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill.name}' modificada com sucesso.",
                data={'skill': updated_skill.to_dict()},
                intent=intent
            )
        else:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Falha ao modificar skill '{skill_name}'.",
                intent=intent
            )

    def _handle_enable_skill(self, intent: Intent) -> ExecutionResult:
        """Handle enabling a skill."""
        skill_id = intent.skill_id
        skill_name = intent.skill_name

        skill = self._skills_manager.get_skill(skill_id)
        if not skill and skill_name:
            skill = self._skills_manager.get_skill_by_name(skill_name)
            if skill:
                skill_id = skill.id

        if not skill:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name or skill_id}' não encontrada.",
                intent=intent
            )

        if skill.status == SkillStatus.ACTIVE:
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill.name}' já está ativa.",
                data={'skill': skill.to_dict()},
                intent=intent
            )

        success = self._skills_manager.enable_skill(skill_id)

        if success:
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill.name}' ativada com sucesso.",
                data={'skill_id': skill_id},
                intent=intent
            )
        else:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Falha ao ativar skill '{skill_name}'.",
                intent=intent
            )

    def _handle_disable_skill(self, intent: Intent) -> ExecutionResult:
        """Handle disabling a skill."""
        skill_id = intent.skill_id
        skill_name = intent.skill_name

        skill = self._skills_manager.get_skill(skill_id)
        if not skill and skill_name:
            skill = self._skills_manager.get_skill_by_name(skill_name)
            if skill:
                skill_id = skill.id

        if not skill:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name or skill_id}' não encontrada.",
                intent=intent
            )

        if skill.status == SkillStatus.DISABLED:
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill.name}' já está desativada.",
                data={'skill': skill.to_dict()},
                intent=intent
            )

        success = self._skills_manager.disable_skill(skill_id)

        if success:
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill.name}' desativada com sucesso.",
                data={'skill_id': skill_id},
                intent=intent
            )
        else:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Falha ao desativar skill '{skill_name}'.",
                intent=intent
            )

    def _handle_list_skills(self, intent: Intent) -> ExecutionResult:
        """Handle listing skills."""
        category_str = intent.parameters.get('category')
        status_str = intent.parameters.get('status')

        category = None
        status = None

        if category_str:
            try:
                category = SkillCategory(category_str)
            except ValueError:
                pass

        if status_str:
            try:
                status = SkillStatus(status_str)
            except ValueError:
                pass

        skills = self._skills_manager.list_skills(category=category, status=status)

        if not skills:
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message="Nenhuma skill encontrada.",
                data={'skills': [], 'count': 0},
                intent=intent
            )

        skills_data = [skill.to_dict() for skill in skills]
        stats = self._skills_manager.get_statistics()

        return ExecutionResult(
            status=ActionResult.SUCCESS,
            message=f"Encontradas {len(skills)} skill(s).",
            data={
                'skills': skills_data,
                'count': len(skills),
                'statistics': stats
            },
            intent=intent
        )

    def _handle_get_skill_info(self, intent: Intent) -> ExecutionResult:
        """Handle getting information about a skill."""
        skill_id = intent.skill_id
        skill_name = intent.skill_name

        skill = self._skills_manager.get_skill(skill_id)
        if not skill and skill_name:
            skill = self._skills_manager.get_skill_by_name(skill_name)

        if not skill:
            # Try searching
            if skill_name:
                results = self._skills_manager.search_skills(skill_name)
                if results:
                    skill = results[0]

        if not skill:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name or skill_id}' não encontrada.",
                intent=intent
            )

        return ExecutionResult(
            status=ActionResult.SUCCESS,
            message=f"Informações da skill '{skill.name}'.",
            data={'skill': skill.to_dict()},
            intent=intent
        )

    def _handle_execute_skill(self, intent: Intent) -> ExecutionResult:
        """Handle executing a skill."""
        skill_id = intent.skill_id
        skill_name = intent.skill_name

        skill = self._skills_manager.get_skill(skill_id)
        if not skill and skill_name:
            skill = self._skills_manager.get_skill_by_name(skill_name)
            if skill:
                skill_id = skill.id

        if not skill:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name or skill_id}' não encontrada.",
                intent=intent
            )

        try:
            result = self._skills_manager.execute_skill(
                skill_id,
                **intent.parameters.get('execution_params', {})
            )
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Skill '{skill.name}' executada com sucesso.",
                data={'result': result},
                intent=intent
            )
        except ValueError as e:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=str(e),
                intent=intent
            )
        except Exception as e:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Erro ao executar skill '{skill.name}': {e}",
                intent=intent
            )

    def _handle_set_parameter(self, intent: Intent) -> ExecutionResult:
        """Handle setting a skill parameter."""
        skill_id = intent.skill_id
        skill_name = intent.skill_name
        param_name = intent.parameters.get('param_name')
        param_value = intent.parameters.get('param_value')

        if not param_name:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message="Nome do parâmetro não especificado.",
                intent=intent
            )

        skill = self._skills_manager.get_skill(skill_id)
        if not skill and skill_name:
            skill = self._skills_manager.get_skill_by_name(skill_name)
            if skill:
                skill_id = skill.id

        if not skill:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Skill '{skill_name or skill_id}' não encontrada.",
                intent=intent
            )

        # Update the parameter
        new_params = {param_name: param_value}
        success = self._skills_manager.update_skill(
            skill_id,
            parameters=new_params
        )

        if success:
            updated_skill = self._skills_manager.get_skill(skill_id)
            return ExecutionResult(
                status=ActionResult.SUCCESS,
                message=f"Parâmetro '{param_name}' definido como '{param_value}' "
                        f"na skill '{skill.name}'.",
                data={'skill': updated_skill.to_dict()},
                intent=intent
            )
        else:
            return ExecutionResult(
                status=ActionResult.FAILURE,
                message=f"Falha ao definir parâmetro na skill '{skill_name}'.",
                intent=intent
            )

    def _handle_help(self, intent: Intent) -> ExecutionResult:
        """Handle help request."""
        help_text = """
Comandos disponíveis:

📌 ADICIONAR SKILL
   - "Adicionar skill de análise de dados"
   - "Criar skill visualização"

📌 REMOVER SKILL
   - "Remover skill análise"
   - "Deletar skill processamento"

📌 MODIFICAR SKILL
   - "Modificar skill análise"
   - "Alterar skill visualização"

📌 ATIVAR/DESATIVAR
   - "Ativar skill análise"
   - "Desativar skill processamento"

📌 LISTAR SKILLS
   - "Listar skills"
   - "Mostrar todas as habilidades"

📌 INFORMAÇÕES
   - "Info sobre skill análise"
   - "Detalhes da skill visualização"

📌 EXECUTAR
   - "Executar skill análise"
   - "Rodar skill processamento"

📌 PARÂMETROS
   - "Definir parâmetro threshold para 0.5 na skill análise"
"""
        return ExecutionResult(
            status=ActionResult.SUCCESS,
            message=help_text,
            intent=intent
        )

    def _handle_unknown(self, intent: Intent) -> ExecutionResult:
        """Handle unknown intent."""
        return ExecutionResult(
            status=ActionResult.FAILURE,
            message="Não entendi o comando. Digite 'ajuda' para ver os comandos disponíveis.",
            intent=intent
        )
