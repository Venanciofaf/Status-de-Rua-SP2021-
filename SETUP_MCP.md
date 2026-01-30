# Configuração do MCP Server para Claude Desktop

Este guia explica como configurar o servidor MCP para usar o gerenciamento de skills diretamente no Claude Desktop.

## 1. Instalar dependências

```bash
pip install mcp
```

## 2. Configurar o Claude Desktop

### No macOS

Edite o arquivo:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### No Windows

Edite o arquivo:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### No Linux

Edite o arquivo:
```
~/.config/Claude/claude_desktop_config.json
```

## 3. Adicionar o servidor MCP

Adicione esta configuração ao arquivo `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "skill-manager": {
      "command": "python",
      "args": ["/CAMINHO/COMPLETO/PARA/mcp_skill_server.py"],
      "env": {}
    }
  }
}
```

**IMPORTANTE:** Substitua `/CAMINHO/COMPLETO/PARA/` pelo caminho real onde está o arquivo `mcp_skill_server.py`.

### Exemplo macOS/Linux:

```json
{
  "mcpServers": {
    "skill-manager": {
      "command": "python3",
      "args": ["/home/user/Status-de-Rua-SP2021-/mcp_skill_server.py"],
      "env": {}
    }
  }
}
```

### Exemplo Windows:

```json
{
  "mcpServers": {
    "skill-manager": {
      "command": "python",
      "args": ["C:\\Users\\SeuUsuario\\Status-de-Rua-SP2021-\\mcp_skill_server.py"],
      "env": {}
    }
  }
}
```

## 4. Reiniciar o Claude Desktop

Feche completamente o Claude Desktop e abra novamente.

## 5. Usar!

Agora você pode conversar naturalmente com o Claude Desktop:

- "Cria uma skill de análise de sentimentos"
- "Lista minhas skills"
- "Desativa a skill de machine learning"
- "Me dá informações sobre a skill de visualização"
- "Remove a skill de análise de sentimentos"

## Ferramentas disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `adicionar_skill` | Cria uma nova skill |
| `remover_skill` | Remove uma skill |
| `listar_skills` | Lista todas as skills |
| `ativar_skill` | Ativa uma skill desativada |
| `desativar_skill` | Desativa uma skill |
| `info_skill` | Mostra detalhes de uma skill |
| `modificar_skill` | Modifica nome/descrição/parâmetros |

## Solução de problemas

### O Claude não mostra as ferramentas

1. Verifique se o caminho no config está correto
2. Verifique se o Python está no PATH
3. Reinicie o Claude Desktop completamente

### Erro de importação

Certifique-se de que está usando o Python correto:

```bash
which python3
# Use esse caminho no config
```

### Verificar se o servidor funciona

Teste manualmente:

```bash
python mcp_skill_server.py
# Deve ficar aguardando (não mostra nada)
# Ctrl+C para sair
```

## Onde ficam as skills salvas?

As skills são salvas em:
```
mcp_skills_data.json
```

No mesmo diretório do `mcp_skill_server.py`.
