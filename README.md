# dotfiles

Dotfiles shared across development machines.

## Agent Setup

Run these commands from the repository root. Skills remain in this repository and are symlinked into each agent's global skills directory.

### [Antigravity CLI](https://antigravity.google/docs/cli/cli-plugins)

Install the shared agent instructions:

```bash
mkdir -p "$HOME/.gemini"
ln -s "$PWD/AGENTS.md" "$HOME/.gemini/AGENTS.md"
```

Install the repository skills:

```bash
mkdir -p "$HOME/.gemini/antigravity-cli/skills"
for skill_directory in "$PWD"/skills/*; do
  [ -f "$skill_directory/SKILL.md" ] || continue
  ln -s "$skill_directory" "$HOME/.gemini/antigravity-cli/skills/${skill_directory##*/}"
done
```

### [Codex](https://learn.chatgpt.com/docs/build-skills)

Install the shared agent instructions:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}"
ln -s "$PWD/AGENTS.md" "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
```

Install the repository skills:

```bash
mkdir -p "$HOME/.agents/skills"
for skill_directory in "$PWD"/skills/*; do
  [ -f "$skill_directory/SKILL.md" ] || continue
  ln -s "$skill_directory" "$HOME/.agents/skills/${skill_directory##*/}"
done
```

### [Mistral Vibe](https://github.com/mistralai/mistral-vibe#skills-system)

Install the shared agent instructions:

```bash
mkdir -p "${VIBE_HOME:-$HOME/.vibe}"
ln -s "$PWD/AGENTS.md" "${VIBE_HOME:-$HOME/.vibe}/AGENTS.md"
```

Install the repository skills:

```bash
mkdir -p "${VIBE_HOME:-$HOME/.vibe}/skills"
for skill_directory in "$PWD"/skills/*; do
  [ -f "$skill_directory/SKILL.md" ] || continue
  ln -s "$skill_directory" "${VIBE_HOME:-$HOME/.vibe}/skills/${skill_directory##*/}"
done
```

## License

[GPL-2.0](LICENSE)
