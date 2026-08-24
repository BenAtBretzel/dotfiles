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

Copy [`config.toml.sample`](config.toml.sample) to `config.toml` (ignored by Git) and update it with your Git email, optional signing key, and GitHub username:

```bash
cp config.toml.sample config.toml
```

Example configuration (`config.toml`):

```toml
[git]
email = "user@example.com"
signingkey = ""

[github]
user = "YourGithubUserName"
```

Agents extract these values using `yq` to set command-scoped Git flags (`git -c user.name="$(yq '.github.user' config.toml)" -c user.email="$(yq '.git.email' config.toml)" -c user.signingkey="$(yq '.git.signingkey' config.toml)"`) and GitHub authentication tokens (`GH_TOKEN="$(gh auth token --user "$(yq '.github.user' config.toml)")"`).

## Scripts

### Directory of Scripts

* [`glowt`](scripts/glowt): Run [Glow](https://github.com/charmbracelet/glow) formatted markdown output in TUI mode with smart dynamic resizing (`glow --tui "$@"`).

## License

[GPL-2.0](LICENSE)
