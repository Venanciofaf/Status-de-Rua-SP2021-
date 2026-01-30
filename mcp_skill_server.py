#!/usr/bin/env python3
"""
MCP Server para Gerenciamento de Skills

Este servidor MCP expõe as ferramentas de gerenciamento de skills
para uso com Claude Desktop ou Claude Web (com MCP habilitado).

Requisitos:
    pip install mcp

Uso:
    python mcp_skill_server.py

Configuração no Claude Desktop:
    Adicione ao arquivo claude_desktop_config.json
"""

import asyncio
import json
import os
import re
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

# Importa o sistema de skills
from chat_skill_integration import (
    SkillsManager,
    Skill,
    SkillCategory,
    SkillStatus
)


# Inicializa o servidor MCP
server = Server("skill-manager")

# Caminho para persistir skills
SKILLS_STORAGE = os.path.join(os.path.dirname(__file__), "mcp_skills_data.json")

# Inicializa o gerenciador de skills
skills_manager = SkillsManager(storage_path=SKILLS_STORAGE)


def name_to_id(name: str) -> str:
    """Converte nome para ID válido."""
    skill_id = name.lower()
    skill_id = re.sub(r'\s+', '_', skill_id)
    skill_id = re.sub(r'[^\w_]', '', skill_id)
    return skill_id


def init_default_skills():
    """Inicializa skills padrão se não existirem."""
    default_skills = [
        Skill(
            id='data_analysis',
            name='Análise de Dados',
            description='Executa análise exploratória de dados',
            category=SkillCategory.DATA_ANALYSIS,
        ),
        Skill(
            id='visualization',
            name='Visualização',
            description='Cria gráficos e visualizações',
            category=SkillCategory.VISUALIZATION,
        ),
        Skill(
            id='machine_learning',
            name='Machine Learning',
            description='Treina e avalia modelos de ML',
            category=SkillCategory.MACHINE_LEARNING,
        ),
    ]

    for skill in default_skills:
        if not skills_manager.get_skill(skill.id):
            skills_manager.add_skill(skill)


# Inicializa skills padrão
init_default_skills()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas as ferramentas disponíveis."""
    return [
        Tool(
            name="adicionar_skill",
            description="Adiciona uma nova skill ao sistema. Use quando o usuário quiser criar uma nova habilidade.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser criada"
                    },
                    "descricao": {
                        "type": "string",
                        "description": "Descrição do que a skill faz"
                    },
                    "categoria": {
                        "type": "string",
                        "enum": ["data_analysis", "machine_learning", "visualization", "data_processing", "reporting", "custom"],
                        "description": "Categoria da skill"
                    }
                },
                "required": ["nome"]
            }
        ),
        Tool(
            name="remover_skill",
            description="Remove uma skill existente do sistema.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser removida"
                    }
                },
                "required": ["nome"]
            }
        ),
        Tool(
            name="listar_skills",
            description="Lista todas as skills disponíveis no sistema.",
            inputSchema={
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "enum": ["data_analysis", "machine_learning", "visualization", "data_processing", "reporting", "custom"],
                        "description": "Filtrar por categoria (opcional)"
                    },
                    "apenas_ativas": {
                        "type": "boolean",
                        "description": "Se true, lista apenas skills ativas"
                    }
                }
            }
        ),
        Tool(
            name="ativar_skill",
            description="Ativa uma skill que estava desativada.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser ativada"
                    }
                },
                "required": ["nome"]
            }
        ),
        Tool(
            name="desativar_skill",
            description="Desativa uma skill temporariamente.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill a ser desativada"
                    }
                },
                "required": ["nome"]
            }
        ),
        Tool(
            name="info_skill",
            description="Obtém informações detalhadas sobre uma skill.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da skill"
                    }
                },
                "required": ["nome"]
            }
        ),
        Tool(
            name="modificar_skill",
            description="Modifica uma skill existente (nome, descrição ou parâmetros).",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome atual da skill"
                    },
                    "novo_nome": {
                        "type": "string",
                        "description": "Novo nome (opcional)"
                    },
                    "nova_descricao": {
                        "type": "string",
                        "description": "Nova descrição (opcional)"
                    },
                    "parametros": {
                        "type": "object",
                        "description": "Parâmetros a atualizar (opcional)"
                    }
                },
                "required": ["nome"]
            }
        ),
    ]


def find_skill_by_name(nome: str) -> Skill | None:
    """Encontra uma skill pelo nome (case-insensitive)."""
    skill = skills_manager.get_skill(name_to_id(nome))
    if skill:
        return skill

    # Tenta buscar por nome exato
    for s in skills_manager.list_skills():
        if s.name.lower() == nome.lower():
            return s

    return None


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Executa uma ferramenta."""

    if name == "adicionar_skill":
        nome = arguments["nome"]
        descricao = arguments.get("descricao", f"Skill de {nome}")
        categoria = arguments.get("categoria", "custom")

        skill_id = name_to_id(nome)

        if skills_manager.get_skill(skill_id):
            return [TextContent(
                type="text",
                text=f"❌ Skill '{nome}' já existe no sistema."
            )]

        try:
            cat = SkillCategory(categoria)
        except ValueError:
            cat = SkillCategory.CUSTOM

        skill = Skill(
            id=skill_id,
            name=nome,
            description=descricao,
            category=cat,
            status=SkillStatus.ACTIVE
        )

        skills_manager.add_skill(skill)

        return [TextContent(
            type="text",
            text=f"✅ Skill '{nome}' criada com sucesso!\n"
                 f"   📁 Categoria: {categoria}\n"
                 f"   📝 Descrição: {descricao}"
        )]

    elif name == "remover_skill":
        nome = arguments["nome"]
        skill = find_skill_by_name(nome)

        if not skill:
            return [TextContent(
                type="text",
                text=f"❌ Skill '{nome}' não encontrada."
            )]

        skills_manager.remove_skill(skill.id)

        return [TextContent(
            type="text",
            text=f"✅ Skill '{skill.name}' removida com sucesso!"
        )]

    elif name == "listar_skills":
        categoria = arguments.get("categoria")
        apenas_ativas = arguments.get("apenas_ativas", False)

        skills = skills_manager.list_skills()

        if categoria:
            try:
                cat = SkillCategory(categoria)
                skills = [s for s in skills if s.category == cat]
            except ValueError:
                pass

        if apenas_ativas:
            skills = [s for s in skills if s.status == SkillStatus.ACTIVE]

        if not skills:
            return [TextContent(
                type="text",
                text="📋 Nenhuma skill encontrada com os filtros especificados."
            )]

        lines = ["📋 **Skills disponíveis:**\n"]
        for s in skills:
            status = "✅" if s.status == SkillStatus.ACTIVE else "⏸️"
            lines.append(f"  {status} **{s.name}**")
            lines.append(f"      Categoria: {s.category.value}")
            lines.append(f"      {s.description}\n")

        return [TextContent(
            type="text",
            text="\n".join(lines)
        )]

    elif name == "ativar_skill":
        nome = arguments["nome"]
        skill = find_skill_by_name(nome)

        if not skill:
            return [TextContent(
                type="text",
                text=f"❌ Skill '{nome}' não encontrada."
            )]

        if skill.status == SkillStatus.ACTIVE:
            return [TextContent(
                type="text",
                text=f"ℹ️ Skill '{skill.name}' já está ativa."
            )]

        skills_manager.enable_skill(skill.id)

        return [TextContent(
            type="text",
            text=f"✅ Skill '{skill.name}' ativada com sucesso!"
        )]

    elif name == "desativar_skill":
        nome = arguments["nome"]
        skill = find_skill_by_name(nome)

        if not skill:
            return [TextContent(
                type="text",
                text=f"❌ Skill '{nome}' não encontrada."
            )]

        if skill.status == SkillStatus.DISABLED:
            return [TextContent(
                type="text",
                text=f"ℹ️ Skill '{skill.name}' já está desativada."
            )]

        skills_manager.disable_skill(skill.id)

        return [TextContent(
            type="text",
            text=f"⏸️ Skill '{skill.name}' desativada com sucesso!"
        )]

    elif name == "info_skill":
        nome = arguments["nome"]
        skill = find_skill_by_name(nome)

        if not skill:
            return [TextContent(
                type="text",
                text=f"❌ Skill '{nome}' não encontrada."
            )]

        status_emoji = "✅" if skill.status == SkillStatus.ACTIVE else "⏸️"

        info = (
            f"📊 **Informações da Skill: {skill.name}**\n\n"
            f"  🔑 ID: `{skill.id}`\n"
            f"  📁 Categoria: {skill.category.value}\n"
            f"  {status_emoji} Status: {skill.status.value}\n"
            f"  📝 Descrição: {skill.description}\n"
            f"  📅 Criada em: {skill.created_at}\n"
            f"  🔄 Modificada em: {skill.modified_at}\n"
        )

        if skill.parameters:
            info += f"  ⚙️ Parâmetros: {json.dumps(skill.parameters, indent=2)}\n"

        return [TextContent(
            type="text",
            text=info
        )]

    elif name == "modificar_skill":
        nome = arguments["nome"]
        skill = find_skill_by_name(nome)

        if not skill:
            return [TextContent(
                type="text",
                text=f"❌ Skill '{nome}' não encontrada."
            )]

        updates = {}
        changes = []

        if "novo_nome" in arguments and arguments["novo_nome"]:
            updates["name"] = arguments["novo_nome"]
            changes.append(f"Nome: {skill.name} → {arguments['novo_nome']}")

        if "nova_descricao" in arguments and arguments["nova_descricao"]:
            updates["description"] = arguments["nova_descricao"]
            changes.append(f"Descrição atualizada")

        if "parametros" in arguments and arguments["parametros"]:
            updates["parameters"] = arguments["parametros"]
            changes.append(f"Parâmetros atualizados")

        if not updates:
            return [TextContent(
                type="text",
                text=f"ℹ️ Nenhuma modificação especificada para '{skill.name}'."
            )]

        skills_manager.update_skill(skill.id, **updates)

        return [TextContent(
            type="text",
            text=f"✅ Skill '{skill.name}' modificada!\n\n"
                 f"Alterações:\n  • " + "\n  • ".join(changes)
        )]

    else:
        return [TextContent(
            type="text",
            text=f"❌ Ferramenta '{name}' não reconhecida."
        )]


async def main():
    """Inicia o servidor MCP."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
