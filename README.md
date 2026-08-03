# dotfiles

**TL;DR**: Dotfiles shared across development machines.

## Antigravity

Link guidelines for [Antigravity](https://antigravity.google/):
```bash
ln -s "$PWD/AGENTS.md" ~/.gemini/AGENTS.md
```

## Codex

Codex reads `AGENTS.md` from the repository automatically when launched in this
checkout. To install the same guidance globally for Codex, link it into the
Codex home directory. `CODEX_HOME` defaults to `~/.codex`.

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}"
ln -s "$PWD/AGENTS.md" "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
```

Reference: [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md), retrieved August 3, 2026.

[GPL-2.0](LICENSE)
