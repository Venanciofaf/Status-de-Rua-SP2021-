"""
Claude Tool Use Integration Module

Integra o sistema de skills com o Claude via Tool Use,
permitindo que o Claude decida inteligentemente quando e como usar as skills.
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .integration import ChatSkillIntegration
from .skills_manager import Skill, SkillCategory, SkillStatus


@dataclass
class ToolResult:
    """Resultado da execução de uma tool."""
    tool_name: str
    result: str
    success: bool


class ClaudeSkillIntegration:
    """
    Integração do sistema de skills com Claude via Tool Use.

    O Claude atua como o "cérebro" que interpreta as mensagens do usuário
    e decide quais skills executar através do mecanismo de Tool Use.

    Exemplo:
        >>> claude_integration = ClaudeSkillIntegration()
        >>> response = claude_integration.chat("Cria uma skill de análise de dados")
        >>> print(response)
        "Criei a skill 'análise de dados' para você!"
    """

    # Definição das tools disponíveis para o Claude
    SKILL_TOOLS = [
        {
            "name": "adicionar_skill",
            "description": "Adiciona uma nova skill ao sistema. Use quando o usuário quiser criar/adicionar uma nova habilidade.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser criada"
                    },
                    "descricao": {
                        "type": "string",
                        "description": "Descrição do que a skill faz (opcional)"
                    },
                    "categoria": {
                        "type": "string",
                        "enum": ["data_analysis", "machine_learning", "visualization", "data_processing", "reporting", "custom"],
                        "description": "Categoria da skill (opcional, default: custom)"
                    }
                },
                "required": ["nome"]
            }
        },
        {
            "name": "remover_skill",
            "description": "Remove uma skill existente do sistema. Use quando o usuário quiser deletar/remover uma habilidade.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser removida"
                    }
                },
                "required": ["nome"]
            }
        },
        {
            "name": "listar_skills",
            "description": "Lista todas as skills disponíveis no sistema. Use quando o usuário quiser ver quais habilidades existem.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "enum": ["data_analysis", "machine_learning", "visualization", "data_processing", "reporting", "custom"],
                        "description": "Filtrar por categoria (opcional)"
                    },
                    "apenas_ativas": {
                        "type": "boolean",
                        "description": "Se true, lista apenas skills ativas (opcional)"
                    }
                }
            }
        },
        {
            "name": "ativar_skill",
            "description": "Ativa uma skill que estava desativada. Use quando o usuário quiser habilitar uma skill.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser ativada"
                    }
                },
                "required": ["nome"]
            }
        },
        {
            "name": "desativar_skill",
            "description": "Desativa uma skill sem removê-la. Use quando o usuário quiser desabilitar temporariamente uma skill.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser desativada"
                    }
                },
                "required": ["nome"]
            }
        },
        {
            "name": "info_skill",
            "description": "Obtém informações detalhadas sobre uma skill específica. Use quando o usuário quiser saber mais sobre uma skill.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill para obter informações"
                    }
                },
                "required": ["nome"]
            }
        },
        {
            "name": "modificar_skill",
            "description": "Modifica os parâmetros ou configurações de uma skill existente.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser modificada"
                    },
                    "novo_nome": {
                        "type": "string",
                        "description": "Novo nome para a skill (opcional)"
                    },
                    "nova_descricao": {
                        "type": "string",
                        "description": "Nova descrição para a skill (opcional)"
                    },
                    "parametros": {
                        "type": "object",
                        "description": "Parâmetros a serem atualizados (opcional)"
                    }
                },
                "required": ["nome"]
            }
        },
        {
            "name": "executar_skill",
            "description": "Executa uma skill específica. Use quando o usuário quiser rodar/usar uma skill.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser executada"
                    },
                    "parametros": {
                        "type": "object",
                        "description": "Parâmetros para a execução (opcional)"
                    }
                },
                "required": ["nome"]
            }
        }
    ]

    SYSTEM_PROMPT = """Você é um assistente que ajuda a gerenciar skills (habilidades) do sistema.

Você tem acesso a ferramentas para:
- Adicionar novas skills
- Remover skills existentes
- Listar skills disponíveis
- Ativar/desativar skills
- Obter informações sobre skills
- Modificar configurações de skills
- Executar skills

Quando o usuário pedir algo relacionado a skills, use a ferramenta apropriada.
Responda sempre em português de forma amigável e clara.
Após executar uma ação, explique o que foi feito de forma concisa."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        skill_storage_path: Optional[str] = None
    ):
        """
        Inicializa a integração com Claude.

        Args:
            api_key: Chave da API Anthropic (ou usa ANTHROPIC_API_KEY env var)
            model: Modelo do Claude a ser usado
            skill_storage_path: Caminho para persistir skills
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "O pacote 'anthropic' não está instalado. "
                "Instale com: pip install anthropic"
            )

        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError(
                "API key não fornecida. Passe como parâmetro ou "
                "defina a variável de ambiente ANTHROPIC_API_KEY"
            )

        self._client = anthropic.Anthropic(api_key=self._api_key)
        self._model = model
        self._skill_integration = ChatSkillIntegration(
            storage_path=skill_storage_path,
            verbose=False
        )
        self._conversation_history: List[Dict[str, Any]] = []

    def _process_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> ToolResult:
        """
        Processa uma chamada de tool e executa a ação correspondente.

        Args:
            tool_name: Nome da tool chamada pelo Claude
            tool_input: Parâmetros da tool

        Returns:
            ToolResult com o resultado da execução
        """
        try:
            if tool_name == "adicionar_skill":
                nome = tool_input["nome"]
                descricao = tool_input.get("descricao", f"Skill de {nome}")
                categoria = tool_input.get("categoria", "custom")

                # Cria a skill diretamente
                skill = Skill(
                    id=self._name_to_id(nome),
                    name=nome,
                    description=descricao,
                    category=SkillCategory(categoria)
                )
                success = self._skill_integration.add_skill(skill)

                if success:
                    result = f"Skill '{nome}' criada com sucesso! Categoria: {categoria}"
                else:
                    result = f"Skill '{nome}' já existe no sistema."
                return ToolResult(tool_name, result, success)

            elif tool_name == "remover_skill":
                nome = tool_input["nome"]
                result = self._skill_integration.process_message(f"Remover skill {nome}")
                success = "sucesso" in result.lower() or "removida" in result.lower()
                return ToolResult(tool_name, result, success)

            elif tool_name == "listar_skills":
                categoria = tool_input.get("categoria")
                apenas_ativas = tool_input.get("apenas_ativas", False)

                skills = self._skill_integration.list_skills()

                if categoria:
                    skills = [s for s in skills if s.category.value == categoria]
                if apenas_ativas:
                    skills = [s for s in skills if s.status == SkillStatus.ACTIVE]

                if not skills:
                    result = "Nenhuma skill encontrada com os filtros especificados."
                else:
                    lines = ["Skills disponíveis:"]
                    for s in skills:
                        status = "✅" if s.status == SkillStatus.ACTIVE else "⏸️"
                        lines.append(f"  {status} {s.name} ({s.category.value})")
                    result = "\n".join(lines)

                return ToolResult(tool_name, result, True)

            elif tool_name == "ativar_skill":
                nome = tool_input["nome"]
                result = self._skill_integration.process_message(f"Ativar skill {nome}")
                success = "sucesso" in result.lower() or "ativada" in result.lower()
                return ToolResult(tool_name, result, success)

            elif tool_name == "desativar_skill":
                nome = tool_input["nome"]
                result = self._skill_integration.process_message(f"Desativar skill {nome}")
                success = "sucesso" in result.lower() or "desativada" in result.lower()
                return ToolResult(tool_name, result, success)

            elif tool_name == "info_skill":
                nome = tool_input["nome"]
                skill = self._skill_integration.get_skill(self._name_to_id(nome))

                if not skill:
                    # Tenta buscar por nome
                    for s in self._skill_integration.list_skills():
                        if s.name.lower() == nome.lower():
                            skill = s
                            break

                if skill:
                    result = (
                        f"Informações da skill '{skill.name}':\n"
                        f"  ID: {skill.id}\n"
                        f"  Descrição: {skill.description}\n"
                        f"  Categoria: {skill.category.value}\n"
                        f"  Status: {skill.status.value}\n"
                        f"  Parâmetros: {skill.parameters or 'Nenhum'}"
                    )
                else:
                    result = f"Skill '{nome}' não encontrada."

                return ToolResult(tool_name, result, skill is not None)

            elif tool_name == "modificar_skill":
                nome = tool_input["nome"]
                novo_nome = tool_input.get("novo_nome")
                nova_descricao = tool_input.get("nova_descricao")
                parametros = tool_input.get("parametros")

                # Encontra a skill
                skill_id = self._name_to_id(nome)
                skill = self._skill_integration.get_skill(skill_id)

                if not skill:
                    for s in self._skill_integration.list_skills():
                        if s.name.lower() == nome.lower():
                            skill = s
                            skill_id = s.id
                            break

                if not skill:
                    return ToolResult(tool_name, f"Skill '{nome}' não encontrada.", False)

                # Aplica modificações
                updates = {}
                if novo_nome:
                    updates['name'] = novo_nome
                if nova_descricao:
                    updates['description'] = nova_descricao
                if parametros:
                    updates['parameters'] = parametros

                if updates:
                    self._skill_integration._skills_manager.update_skill(skill_id, **updates)
                    result = f"Skill '{nome}' atualizada com sucesso!"
                else:
                    result = "Nenhuma modificação especificada."

                return ToolResult(tool_name, result, bool(updates))

            elif tool_name == "executar_skill":
                nome = tool_input["nome"]
                parametros = tool_input.get("parametros", {})

                result = self._skill_integration.process_message(f"Executar skill {nome}")
                success = "sucesso" in result.lower() or "executada" in result.lower()
                return ToolResult(tool_name, result, success)

            else:
                return ToolResult(tool_name, f"Tool '{tool_name}' não reconhecida.", False)

        except Exception as e:
            return ToolResult(tool_name, f"Erro ao executar {tool_name}: {str(e)}", False)

    def _name_to_id(self, name: str) -> str:
        """Converte nome para ID válido."""
        import re
        skill_id = name.lower()
        skill_id = re.sub(r'\s+', '_', skill_id)
        skill_id = re.sub(r'[^\w_]', '', skill_id)
        return skill_id

    def chat(self, message: str) -> str:
        """
        Envia uma mensagem para o Claude e processa a resposta.

        O Claude pode decidir usar tools para executar ações de skills,
        ou responder diretamente se a mensagem não for relacionada a skills.

        Args:
            message: Mensagem do usuário

        Returns:
            Resposta do Claude (após executar tools se necessário)
        """
        # Adiciona mensagem do usuário ao histórico
        self._conversation_history.append({
            "role": "user",
            "content": message
        })

        # Faz a chamada para o Claude
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=self.SYSTEM_PROMPT,
            tools=self.SKILL_TOOLS,
            messages=self._conversation_history
        )

        # Processa a resposta
        final_response = ""

        while response.stop_reason == "tool_use":
            # Claude quer usar uma tool
            assistant_content = response.content

            # Adiciona resposta do assistente ao histórico
            self._conversation_history.append({
                "role": "assistant",
                "content": assistant_content
            })

            # Processa cada tool call
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    result = self._process_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result.result
                    })

            # Adiciona resultados das tools ao histórico
            self._conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # Continua a conversa para Claude processar os resultados
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=self.SYSTEM_PROMPT,
                tools=self.SKILL_TOOLS,
                messages=self._conversation_history
            )

        # Extrai resposta final de texto
        for block in response.content:
            if hasattr(block, "text"):
                final_response += block.text

        # Adiciona resposta final ao histórico
        self._conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        return final_response

    def clear_history(self) -> None:
        """Limpa o histórico da conversa."""
        self._conversation_history = []

    def get_skills(self) -> List[Skill]:
        """Retorna lista de skills disponíveis."""
        return self._skill_integration.list_skills()

    def interactive_mode(self) -> None:
        """
        Inicia modo interativo de chat com Claude.

        Digite 'sair' para encerrar.
        """
        print("=" * 50)
        print("Chat com Claude - Gerenciamento de Skills")
        print("=" * 50)
        print("Converse naturalmente para gerenciar suas skills.")
        print("Digite 'sair' para encerrar.\n")

        while True:
            try:
                user_input = input("Você: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ('sair', 'exit', 'quit'):
                    print("\nAté logo! 👋")
                    break

                response = self.chat(user_input)
                print(f"\nClaude: {response}\n")

            except KeyboardInterrupt:
                print("\n\nSessão encerrada.")
                break
