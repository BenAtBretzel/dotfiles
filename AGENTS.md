# Agent Coding Guidelines & Session Steering

Coding guidelines, standards, and steering rules for AI agents working in this repository.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174). The additional terms defined by [RFC 6919](https://www.rfc-editor.org/rfc/rfc6919) MAY be used for informal guidance, but MUST NOT replace the RFC 2119 keywords when stating repository requirements.

These instructions apply to this repository. More-specific `AGENTS.md` files, if present, MAY add or narrow these instructions for their subtree. Explicit user requests take precedence over recommendations, but MUST NOT override safety constraints.

---

## 1. Code Style & Design Principles
* **Early Exits & Short-Circuiting**: Code SHOULD check empty, missing, boundary, or short-circuit conditions early to minimize cognitive load and unnecessary allocations. Code SHOULD prefer early exits over nesting when doing so improves readability.
* **Detailed Error Handling**: Edge cases and unexpected calls MUST return useful, detailed errors. Tests SHOULD verify error types and, when stable and meaningful, error messages.
* **Purity of Functions**: Functions SHOULD be pure and SHOULD NOT mutate input arguments unless mutation is part of their documented contract. When input immutability is expected, tests MUST verify that the input remains unchanged.
* **Symbol Shadowing**: Code MUST NOT shadow symbols when distinct, descriptive names are practical.
* **Lexicographical Ordering & File Structure**: Code SHOULD use idiomatic file structures and alphabetical or lexicographical ordering to break ties, unless language-, project-, user-, or framework-specific conventions take precedence.
* **Best Practice & Deviations**: Deviations from these guidelines SHOULD be documented with a brief rationale when the reason is not self-evident.

### Language-Specific Standards
| Language | Standards & Best Practice Tooling |
| :--- | :--- |
| **Go** | New code SHOULD prefer the standard-library [`maps`](https://pkg.go.dev/maps), [`slices`](https://pkg.go.dev/slices), and [`cmp`](https://pkg.go.dev/cmp) packages where applicable. New dependencies MAY use [`samber/lo`](https://github.com/samber/lo), [`emirpasic/gods`](https://github.com/emirpasic/gods), or [`go-playground/validator`](https://github.com/go-playground/validator) when they provide a clear benefit and fit existing project dependencies. Unit tests MUST use `t.Context()` or another appropriate test context instead of `context.TODO()` or `context.Background()`. Code SHOULD avoid deprecated components. Error comparisons MUST prefer `errors.Is` and `errors.As`. |
| **Bash/Shell** | Shell scripts MUST pass [`shellcheck`](https://www.shellcheck.net/). |
| **JavaScript** | New JavaScript code SHOULD use [TypeScript](https://www.typescriptlang.org/). |
| **React** | React code SHOULD avoid unnecessary prop drilling. New shared state SHOULD use [`Zustand`](https://github.com/pmndrs/zustand) rather than Redux unless project requirements dictate otherwise. |
| **Python** | New Python code SHOULD use [Beartype](https://github.com/beartype/beartype) where runtime type checking is appropriate. |
| **Ruby** | New Ruby code SHOULD use [Sorbet](https://sorbet.org/) where static type checking is appropriate. |
| **GitHub Actions / CI** | Changed GitHub Actions, Dependabot, and pre-commit configuration MUST pass [`zizmor`](https://github.com/zizmorcore/zizmor). |

## 2. Code Quality & Verification Standards
* **Formatting**: When Go files change, they MUST be formatted with `gofmt`; `go fmt ./...` SHOULD be run before finalizing changes.
* **Linter**: When Go code changes, `golangci-lint run` MUST pass with zero issues. `gocognit` SHOULD be configured with a documented project threshold; a target of 15–20 is RECOMMENDED. When relevant, Bash/Shell scripts MUST pass `shellcheck`, and CI/CD configuration MUST pass `zizmor`. Project-specific linters MUST pass before finalizing changes.
* **Coverage**: Tests SHOULD use table-driven cases where appropriate and SHOULD cover edge cases, boundary values, and meaningful input variations. Projects MAY define a specific coverage threshold elsewhere.
* **Verification**: Before a task is marked complete, relevant build, test, formatting, and lint commands MUST be run. If a required tool or library cannot be installed as described below, agents MUST prompt the user and report that the code style could not be fully applied.

## 3. Writing & Communication Style
* **Factual & Objective**: Comments, documentation, and explanations MUST be factual and objective.
* **Terse & Concise**: Communication SHOULD be concise and professional. Unnecessary conversational filler SHOULD be avoided.
* **Citations & Links**: References to external definitions or tools SHOULD link to original or authoritative sources. Permalinks or retrieval dates MAY be included when useful.
* **Code Documentation & Comments**: Public functions SHOULD have documentation. Inline comments SHOULD be limited to explaining complexity, constants, or non-obvious behavior.
* **Emojis**: Emojis SHOULD NOT be used in repository documentation or code comments.

## 4. Tool Preferences & Usage
* **Workspace Isolation & Temporary Directories**: Agents MUST NOT modify files outside the repository unless explicitly authorized. Transient operations—such as `git clone`, `curl`, `wget`, temporary downloads, and scratch scripts—MUST use a session-scoped or unique task-local temporary directory. User-local package installations MAY use their normal user-local cache. Builds MUST use session-scoped caches and temporary directories where the relevant tool supports them.
* **Tool and Library Availability**: When a REQUIRED tool or library is unavailable, agents MUST attempt to install it in a user-local, project-local, conversation-local, or task-local location. Installations MUST NOT modify system-wide state without explicit authorization. If installation fails, agents MUST prompt the user and report that the code style could not be fully applied.
* **Scripting & CLI**: Standard utilities SHOULD be preferred for routine shell work. [`yq`](https://github.com/mikefarah/yq) MAY be used for structured-data transformations. Shell pipelines SHOULD be preferred when they remain clear; Python COULD be used for stateful or complex algorithms.
* **Git**: When committing, agents MUST extract bot identity from configuration (`CFG="${SDLCBOT_CONFIG:-$HOME/.config/sdlcbot/config.toml}"`, `GIT_USER="$(yq '.github.user' "$CFG")"`, `GIT_EMAIL="$(yq '.git.email' "$CFG")"`, `GIT_KEY="$(yq '.git.signingkey' "$CFG")"`) and MUST use `git -c user.name="$GIT_USER" -c user.email="$GIT_EMAIL" -c user.signingkey="$GIT_KEY"` so commits are attributed to the configured bot account and signing key.
  * **Sign Commits**: Commits MUST be cryptographically signed with `git -c user.name="$GIT_USER" -c user.email="$GIT_EMAIL" -c user.signingkey="$GIT_KEY" commit -S`. If signing fails because the configured bot key is missing, the commit MAY omit `-S`; signing failures for other reasons MUST be reported to the user.
  * **Pushing**: Agents MUST obtain user approval before pushing unless explicit session permission has been granted.
  * **Commit Message Construction**: Each commit-message paragraph MUST be passed as a separate argument. The commit command MUST include `--trailer "Assisted-by: <agent>:<model> [tools]"`; `\n` escape sequences MUST NOT be placed inside a `-m` argument. After committing, agents MUST inspect the exact message with `git log -1 --format=%B`. See the [`git commit` documentation](https://git-scm.com/docs/git-commit).
  * **Metadata Tags**: AI-assisted commits MUST include `Assisted-by: AGENT_NAME:MODEL_VERSION [TOOL1] [TOOL2]` according to the [Linux Kernel guidelines](https://docs.kernel.org/process/coding-assistants.html#attribution). `[TOOL1]` refers to analysis tools such as `coccinelle`, `sparse`, `smatch`, and `clang-tidy`; basic development tools such as `git`, `gcc`, and `make` MUST be omitted.
* **GitHub**: GitHub CLI operations SHOULD use `GH_TOKEN="$(gh auth token --user "$GIT_USER")" gh ...` to run as the configured bot account without modifying global authentication state.
* **AWS**: AWS CLI operations SHOULD use the `aws` CLI for S3, EC2, Lambda, IAM, and CloudFormation.
* **Clipboard**: Clipboard operations SHOULD use `wl-copy` and `wl-paste` where available.
* **Web Search**: When a web search is necessary, agents SHOULD CONSIDER searching in multiple languages, including Arabic, Chinese, French, German, Japanese, Korean, and Spanish.
* **Asset Sourcing & Attribution**: When searching the web and using external data or placeholder assets (e.g., images, graphics, components), the source SHOULD be open, [Creative Commons](https://creativecommons.org/), or freely redistributable. Attribution MUST include the source location/URL, original creator, license, retrieval timestamp, and relevant citation and redistribution metadata.
  * **In-Code Attribution**: Attribution SHOULD be placed in header or inline code comments when supported by the file format.
  * **Sidecar Metadata File (`.meta.toml`)**: If attribution cannot be placed in a code comment (e.g., binary assets or image files), an adjacent `<original_file_name>.meta.toml` file MUST be used. It MUST contain a single `[meta]` [TOML](https://toml.io/) table of string key-value pairs (`key = "value"`) containing citation metadata attributes and data.

## 5. Report Generation Standards
* **Reports & Pandoc**: Complex reports MUST use `pandoc` with GitHub-flavored markdown (`-t gfm`). Markdown SHOULD be iterated on before HTML is regenerated, and HTML generation MUST be non-destructive.
* **Slide Decks & Marp**: Slide decks SHOULD use [Marp](https://marp.app/) and MAY use Mermaid diagrams where appropriate.
  * **Portability**: Report prompts, skills, scripts, filters, and templates MUST remain vendor-neutral and repository-local. Relative paths and standard command-line interfaces MUST be used. Agent-specific adapters MAY invoke the shared implementation but MUST remain OPTIONAL.
  * **CDN Assets**: Reputable CDN-hosted open-source assets SHOULD be preferred over checking equivalent assets into the repository.
  * **Code Samples**: Code samples SHOULD be wrapped in collapsible `<details><summary>` blocks containing appropriate code blocks.
  * **Build Command & Metadata**: Each report MUST document its build command. Generated reports MUST include the Git SHA and HTML rendering timestamp.
  * **Change History & Attribution**: Reports MUST include an append-only change history signed by the agent using an attribution tag similar to Git (`Assisted-by: AGENT_NAME:MODEL_VERSION [TOOLS]`).
  * **Section Links**: Markdown headings MUST NOT contain explicit IDs. HTML generation MUST use a shared, repository-local Pandoc Lua filter to make each heading a self-link through its automatically generated ID. The filter MUST leave Markdown and GFM output unchanged.
