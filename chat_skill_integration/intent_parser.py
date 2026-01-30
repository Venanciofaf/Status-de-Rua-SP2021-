"""
Intent Parser Module

Parses natural language chat messages to extract skill modification intents.
Supports both Portuguese and English commands.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class IntentType(Enum):
    """Types of intents that can be parsed from chat messages."""
    ADD_SKILL = "add_skill"
    REMOVE_SKILL = "remove_skill"
    MODIFY_SKILL = "modify_skill"
    ENABLE_SKILL = "enable_skill"
    DISABLE_SKILL = "disable_skill"
    LIST_SKILLS = "list_skills"
    GET_SKILL_INFO = "get_skill_info"
    EXECUTE_SKILL = "execute_skill"
    SET_PARAMETER = "set_parameter"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """
    Represents a parsed intent from a chat message.

    Attributes:
        type: The type of intent detected
        skill_name: Name of the skill (if applicable)
        skill_id: ID of the skill (if applicable)
        parameters: Additional parameters extracted
        confidence: Confidence score (0-1) of the parsing
        original_message: The original chat message
    """
    type: IntentType
    skill_name: Optional[str] = None
    skill_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    original_message: str = ""

    def is_valid(self) -> bool:
        """Check if the intent has enough information to be actionable."""
        if self.type == IntentType.UNKNOWN:
            return False
        if self.type in (IntentType.LIST_SKILLS, IntentType.HELP):
            return True
        return bool(self.skill_name or self.skill_id)


class IntentParser:
    """
    Parses natural language messages to extract skill modification intents.

    Supports commands in Portuguese and English.
    """

    # Pattern definitions for intent detection
    PATTERNS = {
        IntentType.ADD_SKILL: [
            # Portuguese
            r'(?:adicionar?|criar?|nova?|incluir?)\s+(?:a\s+)?(?:skill|habilidade|capacidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            r'(?:quero|gostaria\s+de|preciso)\s+(?:adicionar?|criar?)\s+(?:uma?\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            # English
            r'(?:add|create|new)\s+(?:a\s+)?skill\s+(?:for\s+|called\s+)?["\']?(.+?)["\']?$',
            r'(?:i\s+want\s+to|please)\s+(?:add|create)\s+(?:a\s+)?skill\s+(?:for\s+)?["\']?(.+?)["\']?$',
        ],
        IntentType.REMOVE_SKILL: [
            # Portuguese
            r'(?:remover?|deletar?|excluir?|apagar?)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            # English
            r'(?:remove|delete|drop)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?$',
        ],
        IntentType.MODIFY_SKILL: [
            # Portuguese
            r'(?:modificar?|alterar?|mudar?|atualizar?|editar?)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            r'(?:quero|gostaria\s+de)\s+(?:modificar?|alterar?)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            # English
            r'(?:modify|change|update|edit)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?$',
        ],
        IntentType.ENABLE_SKILL: [
            # Portuguese
            r'(?:ativar?|habilitar?|ligar?)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            # English
            r'(?:enable|activate|turn\s+on)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?$',
        ],
        IntentType.DISABLE_SKILL: [
            # Portuguese
            r'(?:desativar?|desabilitar?|desligar?)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            # English
            r'(?:disable|deactivate|turn\s+off)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?$',
        ],
        IntentType.LIST_SKILLS: [
            # Portuguese
            r'(?:listar?|mostrar?|exibir?|ver)\s+(?:as\s+|todas\s+(?:as\s+)?)?(?:skills|habilidades)',
            r'(?:quais|que)\s+(?:skills|habilidades)\s+(?:eu\s+)?(?:tenho|existem)',
            # English
            r'(?:list|show|display|get)\s+(?:all\s+)?skills',
            r'what\s+skills\s+(?:do\s+i\s+have|are\s+available)',
        ],
        IntentType.GET_SKILL_INFO: [
            # Portuguese
            r'(?:info(?:rmação)?|detalhes?|sobre)\s+(?:da?\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            r'(?:como|o\s+que)\s+(?:é|funciona)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            # English
            r'(?:info|information|details)\s+(?:about|on)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?$',
            r'(?:what\s+is|how\s+does)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?\s*(?:work)?$',
        ],
        IntentType.EXECUTE_SKILL: [
            # Portuguese
            r'(?:executar?|rodar?|usar?|aplicar?)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            r'(?:quero|preciso)\s+(?:executar?|usar?)\s+(?:a\s+)?(?:skill|habilidade)\s+(?:de\s+)?["\']?(.+?)["\']?$',
            # English
            r'(?:execute|run|use|apply)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?$',
        ],
        IntentType.SET_PARAMETER: [
            # Portuguese
            r'(?:definir?|configurar?|setar?)\s+(?:o\s+)?(?:parâmetro|parametro|param)\s+["\']?(\w+)["\']?\s+(?:para|como|=)\s+["\']?(.+?)["\']?(?:\s+(?:na|da)\s+(?:skill|habilidade)\s+["\']?(.+?)["\']?)?$',
            # English
            r'set\s+(?:the\s+)?(?:parameter|param)\s+["\']?(\w+)["\']?\s+(?:to|=)\s+["\']?(.+?)["\']?(?:\s+(?:for|on|in)\s+(?:the\s+)?skill\s+["\']?(.+?)["\']?)?$',
        ],
        IntentType.HELP: [
            # Portuguese
            r'^(?:ajuda|help|socorro|\?)$',
            r'(?:como|o\s+que)\s+(?:eu\s+)?(?:posso|consigo)\s+(?:fazer|usar)',
            # English
            r'(?:what\s+can\s+(?:i|you)\s+do|how\s+(?:do\s+i|to)\s+use)',
        ],
    }

    # Keywords for category detection
    CATEGORY_KEYWORDS = {
        'data_analysis': [
            'análise', 'analise', 'analysis', 'estatística', 'estatistica',
            'statistics', 'dados', 'data', 'exploratória', 'exploratoria'
        ],
        'machine_learning': [
            'ml', 'machine learning', 'aprendizado', 'modelo', 'model',
            'classificação', 'classificacao', 'regressão', 'regressao',
            'predição', 'predicao', 'prediction', 'treinamento', 'training'
        ],
        'visualization': [
            'visualização', 'visualizacao', 'visualization', 'gráfico',
            'grafico', 'chart', 'plot', 'mapa', 'map', 'dashboard'
        ],
        'data_processing': [
            'processamento', 'processing', 'limpeza', 'cleaning',
            'transformação', 'transformacao', 'transformation', 'etl'
        ],
        'reporting': [
            'relatório', 'relatorio', 'report', 'resumo', 'summary',
            'exportação', 'exportacao', 'export'
        ]
    }

    def __init__(self):
        """Initialize the intent parser."""
        self._compiled_patterns: Dict[IntentType, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficiency."""
        for intent_type, patterns in self.PATTERNS.items():
            self._compiled_patterns[intent_type] = [
                re.compile(pattern, re.IGNORECASE | re.UNICODE)
                for pattern in patterns
            ]

    def parse(self, message: str) -> Intent:
        """
        Parse a chat message to extract the intent.

        Args:
            message: The chat message to parse

        Returns:
            An Intent object with the parsed information
        """
        message = message.strip()

        if not message:
            return Intent(
                type=IntentType.UNKNOWN,
                original_message=message,
                confidence=0.0
            )

        # Try each intent type
        for intent_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(message)
                if match:
                    return self._create_intent(intent_type, match, message)

        # If no pattern matched, try fuzzy matching
        return self._fuzzy_match(message)

    def _create_intent(self, intent_type: IntentType,
                       match: re.Match, message: str) -> Intent:
        """Create an Intent object from a regex match."""
        groups = match.groups()

        intent = Intent(
            type=intent_type,
            original_message=message,
            confidence=0.9
        )

        # Extract skill name from first capturing group
        if groups and groups[0]:
            skill_name = groups[0].strip()
            intent.skill_name = skill_name
            intent.skill_id = self._name_to_id(skill_name)

        # Handle SET_PARAMETER specially - has param_name, value, optional skill
        if intent_type == IntentType.SET_PARAMETER and len(groups) >= 2:
            intent.parameters['param_name'] = groups[0]
            intent.parameters['param_value'] = self._parse_value(groups[1])
            if len(groups) >= 3 and groups[2]:
                intent.skill_name = groups[2].strip()
                intent.skill_id = self._name_to_id(groups[2])

        # Detect category from message
        category = self._detect_category(message)
        if category:
            intent.parameters['category'] = category

        return intent

    def _fuzzy_match(self, message: str) -> Intent:
        """
        Attempt fuzzy matching for messages that don't match exact patterns.

        Args:
            message: The message to match

        Returns:
            An Intent with lower confidence or UNKNOWN type
        """
        message_lower = message.lower()

        # Keyword-based detection
        keyword_mapping = {
            IntentType.ADD_SKILL: ['adicionar', 'criar', 'nova', 'add', 'create', 'new'],
            IntentType.REMOVE_SKILL: ['remover', 'deletar', 'excluir', 'remove', 'delete'],
            IntentType.MODIFY_SKILL: ['modificar', 'alterar', 'mudar', 'modify', 'change', 'update'],
            IntentType.ENABLE_SKILL: ['ativar', 'habilitar', 'enable', 'activate'],
            IntentType.DISABLE_SKILL: ['desativar', 'desabilitar', 'disable', 'deactivate'],
            IntentType.LIST_SKILLS: ['listar', 'mostrar', 'list', 'show'],
            IntentType.EXECUTE_SKILL: ['executar', 'rodar', 'execute', 'run'],
            IntentType.HELP: ['ajuda', 'help', 'como', 'how'],
        }

        for intent_type, keywords in keyword_mapping.items():
            for keyword in keywords:
                if keyword in message_lower:
                    skill_name = self._extract_skill_name_fuzzy(message)
                    return Intent(
                        type=intent_type,
                        skill_name=skill_name,
                        skill_id=self._name_to_id(skill_name) if skill_name else None,
                        original_message=message,
                        confidence=0.6
                    )

        return Intent(
            type=IntentType.UNKNOWN,
            original_message=message,
            confidence=0.0
        )

    def _extract_skill_name_fuzzy(self, message: str) -> Optional[str]:
        """Extract a potential skill name from the message using heuristics."""
        # Try to find quoted text
        quoted = re.search(r'["\'](.+?)["\']', message)
        if quoted:
            return quoted.group(1)

        # Try to find text after common prepositions
        for prep in ['de ', 'para ', 'skill ', 'habilidade ', 'for ', 'called ']:
            idx = message.lower().find(prep)
            if idx != -1:
                remainder = message[idx + len(prep):].strip()
                # Take up to the next preposition or punctuation
                match = re.match(r'^[\w\s]+', remainder)
                if match:
                    return match.group(0).strip()

        return None

    def _name_to_id(self, name: str) -> str:
        """Convert a skill name to a valid ID."""
        if not name:
            return ""
        # Convert to lowercase, replace spaces with underscores, remove special chars
        skill_id = name.lower()
        skill_id = re.sub(r'\s+', '_', skill_id)
        skill_id = re.sub(r'[^\w_]', '', skill_id)
        return skill_id

    def _detect_category(self, message: str) -> Optional[str]:
        """Detect the skill category from the message."""
        message_lower = message.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return category

        return None

    def _parse_value(self, value: str) -> Any:
        """Parse a string value into the appropriate type."""
        value = value.strip()

        # Try boolean
        if value.lower() in ('true', 'verdadeiro', 'sim', 'yes'):
            return True
        if value.lower() in ('false', 'falso', 'não', 'nao', 'no'):
            return False

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def get_supported_commands(self, language: str = 'pt') -> List[str]:
        """
        Get a list of supported commands.

        Args:
            language: 'pt' for Portuguese, 'en' for English

        Returns:
            List of example commands
        """
        if language == 'pt':
            return [
                "Adicionar skill de <nome>",
                "Remover skill <nome>",
                "Modificar skill <nome>",
                "Ativar skill <nome>",
                "Desativar skill <nome>",
                "Listar skills",
                "Info sobre skill <nome>",
                "Executar skill <nome>",
                "Definir parâmetro <param> para <valor> na skill <nome>",
                "Ajuda",
            ]
        else:
            return [
                "Add skill <name>",
                "Remove skill <name>",
                "Modify skill <name>",
                "Enable skill <name>",
                "Disable skill <name>",
                "List skills",
                "Info about skill <name>",
                "Execute skill <name>",
                "Set parameter <param> to <value> for skill <name>",
                "Help",
            ]
