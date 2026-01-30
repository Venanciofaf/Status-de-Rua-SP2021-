"""
Exemplo de Integração com Claude via Tool Use

Este script demonstra como usar o ClaudeSkillIntegration para
gerenciar skills através de conversas naturais com o Claude.

Requisitos:
    pip install anthropic

Uso:
    export ANTHROPIC_API_KEY="sua-chave-api"
    python exemplo_claude_integration.py
"""

import os


def exemplo_basico():
    """Exemplo básico de uso da integração com Claude."""
    from chat_skill_integration import ClaudeSkillIntegration

    # Inicializa a integração
    # A API key pode ser passada diretamente ou via variável de ambiente
    claude = ClaudeSkillIntegration(
        # api_key="sk-ant-...",  # Ou usa ANTHROPIC_API_KEY env var
        model="claude-sonnet-4-20250514"
    )

    print("=" * 60)
    print("Exemplo de Integração Claude + Skills")
    print("=" * 60)

    # Exemplos de conversas
    conversas = [
        "Quais skills eu tenho disponíveis?",
        "Cria uma skill de previsão de vendas para mim",
        "Me dá mais informações sobre essa skill de previsão",
        "Agora desativa ela",
        "Lista as skills novamente",
    ]

    for msg in conversas:
        print(f"\n👤 Você: {msg}")
        resposta = claude.chat(msg)
        print(f"🤖 Claude: {resposta}")
        print("-" * 40)


def exemplo_interativo():
    """Inicia modo interativo de chat."""
    from chat_skill_integration import ClaudeSkillIntegration

    claude = ClaudeSkillIntegration()
    claude.interactive_mode()


def exemplo_com_tratamento_erros():
    """Exemplo com tratamento de erros."""
    try:
        from chat_skill_integration import ClaudeSkillIntegration, is_claude_available

        # Verifica se o pacote anthropic está instalado
        if not is_claude_available():
            print("❌ Pacote 'anthropic' não está instalado.")
            print("   Instale com: pip install anthropic")
            return

        # Verifica se a API key está configurada
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("❌ ANTHROPIC_API_KEY não está definida.")
            print("   Configure com: export ANTHROPIC_API_KEY='sua-chave'")
            return

        claude = ClaudeSkillIntegration()

        resposta = claude.chat("Liste todas as minhas skills")
        print(f"✅ Resposta: {resposta}")

    except Exception as e:
        print(f"❌ Erro: {e}")


def exemplo_programatico():
    """
    Exemplo de uso programático - útil para integrar em outros sistemas.
    """
    from chat_skill_integration import ClaudeSkillIntegration

    claude = ClaudeSkillIntegration()

    # Processa uma lista de comandos
    comandos = [
        "Adiciona skill de análise de sentimentos",
        "Adiciona skill de extração de entidades",
        "Adiciona skill de sumarização de texto",
    ]

    print("Criando skills de NLP...")
    for cmd in comandos:
        resposta = claude.chat(cmd)
        print(f"  → {resposta[:80]}...")

    # Obtém lista de skills diretamente
    skills = claude.get_skills()
    print(f"\nTotal de skills: {len(skills)}")

    for skill in skills:
        print(f"  - {skill.name} ({skill.status.value})")


if __name__ == "__main__":
    import sys

    print("""
╔═══════════════════════════════════════════════════════════╗
║     Integração Claude + Sistema de Skills                ║
╠═══════════════════════════════════════════════════════════╣
║  1. Exemplo básico (demonstração automática)             ║
║  2. Modo interativo (chat livre)                         ║
║  3. Exemplo programático (para integração)               ║
╚═══════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) > 1:
        opcao = sys.argv[1]
    else:
        opcao = input("Escolha uma opção (1/2/3): ").strip()

    if opcao == "1":
        exemplo_basico()
    elif opcao == "2":
        exemplo_interativo()
    elif opcao == "3":
        exemplo_programatico()
    else:
        print("Opção inválida. Executando exemplo básico...")
        exemplo_basico()
