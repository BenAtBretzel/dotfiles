# dotfiles

Dotfiles shared across development machines.

## AGENTS.md Setup

### [Antigravity](https://antigravity.google/)
```bash
ln -s "$PWD/AGENTS.md" ~/.gemini/AGENTS.md
```

### [Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md)
```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}"
ln -s "$PWD/AGENTS.md" "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
```

### [Mistral Vibe](https://github.com/mistralai/vibe)
```bash
mkdir -p "${VIBE_HOME:-$HOME/.vibe}"
ln -s "$PWD/AGENTS.md" "${VIBE_HOME:-$HOME/.vibe}/AGENTS.md"
```

## License
[GPL-2.0](LICENSE)
