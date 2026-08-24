# dotfiles

Dotfiles, utility scripts, and agent configurations shared across development machines.

## Setup & Symlink Management

Use [`manage-link.sh`](manage-link.sh) to manage symbolic links for scripts and agent skills:

```bash
./manage-link.sh                   # Link scripts to $HOME/bin and skills to all agents
./manage-link.sh --scripts         # Link only scripts to $HOME/bin
./manage-link.sh --skills          # Link skills to all agents (default: all)
./manage-link.sh --skills=agy      # Link skills to a specific agent (aider|agy|codex|vibe)
./manage-link.sh --unlink          # Remove managed symlinks for scripts and skills
./manage-link.sh --help            # Display help and usage information
```

## Agent Setup

Run from the repository root to symlink `AGENTS.md` and repository skills:

* **[Antigravity CLI](https://antigravity.google/docs/cli/cli-plugins)**:
  * Instructions: `mkdir -p "$HOME/.gemini" && ln -s "$PWD/AGENTS.md" "$HOME/.gemini/AGENTS.md"`
  * Skills: `./manage-link.sh --skills=agy`
* **[Codex](https://learn.chatgpt.com/docs/build-skills)**:
  * Instructions: `mkdir -p "${CODEX_HOME:-$HOME/.codex}" && ln -s "$PWD/AGENTS.md" "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"`
  * Skills: `./manage-link.sh --skills=codex`
* **[Mistral Vibe](https://github.com/mistralai/mistral-vibe#skills-system)**:
  * Instructions: `mkdir -p "${VIBE_HOME:-$HOME/.vibe}" && ln -s "$PWD/AGENTS.md" "${VIBE_HOME:-$HOME/.vibe}/AGENTS.md"`
  * Skills: `./manage-link.sh --skills=vibe`
* **[Aider](https://aider.chat)**:
  * Skills: `./manage-link.sh --skills=aider`

## Configuration

Copy [`config.toml.sample`](config.toml.sample) to `$HOME/.config/sdlcbot/config.toml` (or custom path specified by `SDLCBOT_CONFIG`) and update it with your Git email, optional signing key, and GitHub username:

```bash
mkdir -p "$HOME/.config/sdlcbot"
cp config.toml.sample "${SDLCBOT_CONFIG:-$HOME/.config/sdlcbot/config.toml}"
```

Example configuration (`$HOME/.config/sdlcbot/config.toml` or `$SDLCBOT_CONFIG`):

```toml
[git]
email = "user@example.com"
signingkey = ""

[github]
user = "YourGithubUserName"
```

Agents extract these values using `yq` to set command-scoped Git flags (`git -c user.name="$(yq '.github.user' "${SDLCBOT_CONFIG:-$HOME/.config/sdlcbot/config.toml}")" -c user.email="$(yq '.git.email' "${SDLCBOT_CONFIG:-$HOME/.config/sdlcbot/config.toml}")" -c user.signingkey="$(yq '.git.signingkey' "${SDLCBOT_CONFIG:-$HOME/.config/sdlcbot/config.toml}")"`) and GitHub authentication tokens (`GH_TOKEN="$(gh auth token --user "$(yq '.github.user' "${SDLCBOT_CONFIG:-$HOME/.config/sdlcbot/config.toml}")")"`).

Validate configuration sanity without leaking secrets using [`scripts/verify-config`](scripts/verify-config):

```bash
./scripts/verify-config            # Validate $SDLCBOT_CONFIG (default: $HOME/.config/sdlcbot/config.toml)
./scripts/verify-config /path/to/custom.toml
```

## Scripts

### Directory of Scripts

* [`glowt`](scripts/glowt): Run [Glow](https://github.com/charmbracelet/glow) formatted markdown output in TUI mode with smart dynamic resizing (`glow --tui "$@"`).
* [`verify-config`](scripts/verify-config): Validate configuration file (`$SDLCBOT_CONFIG` or `$HOME/.config/sdlcbot/config.toml`) structure, syntax, and required fields without leaking secrets.

## License

[GPL-2.0](LICENSE)
