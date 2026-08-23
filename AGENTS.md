# Agent Coding Guidelines & Session Steering

Coding guidelines, standards, and steering rules for AI agents. Strictly adhere to these practices.

---

## 1. Code Style & Design Principles
* **Early Exits & Short-Circuiting**: Proactively check empty, missing, boundary, or short-circuit conditions at function start to minimize cognitive load and eliminate unnecessary allocations. Prefer exiting early over nesting when possible to greatly improve readability.
* **Detailed Error Handling**: Edge cases and unexpected calls must return detailed errors (e.g., calling custom sort with `nil` returns error stating input was `nil` or missing). Verify error messages and types in tests whenever possible.
* **Purity of Functions**: Prefer pure functions that do not mutate input arguments. When input immutability is expected, tests must verify input state remains unaltered after function calls.
* **Symbol Shadowing**: Avoid shadowing symbols across all programming languages; use distinct, descriptive names instead.
* **Lexicographical Ordering & File Structure**: Prefer idiomatic file structures, using alphabetical/lexicographical sorting to break ties. Whenever practical, sort series of attributes, constants, fields, functions, methods, types, and related symbols alphabetically within the file, without overriding language-, project-, user-, or framework-specific conventions.
* **Best Practice & Deviations**: Annotate any deviations from best practices with comments explaining the rationale.

### Language-Specific Standards
| Language | Standards & Best Practice Tooling |
| :--- | :--- |
| **Go** | Stdlib [`maps`](https://pkg.go.dev/maps), [`slices`](https://pkg.go.dev/slices), [`cmp`](https://pkg.go.dev/cmp). Prefer [`samber/lo`](https://github.com/samber/lo) (helpers), [`emirpasic/gods`](https://github.com/emirpasic/gods) (data structures), [`go-playground/validator`](https://github.com/go-playground/validator) (validation). In unit tests, always use `t.Context()` or other test context over `context.TODO()` or `context.Background()`. Avoid using deprecated components whenever possible; check associated comments or source code. Prefer `errors.Is` and `errors.As` for error comparisons. |
| **Bash/Shell** | [`shellcheck`](https://www.shellcheck.net/) for static analysis, linting, and security. |
| **JavaScript** | [TypeScript](https://www.typescriptlang.org/). |
| **React** | Be wary of prop drilling; prefer [`Zustand`](https://github.com/pmndrs/zustand) over Redux for state management. |
| **Python** | [Beartype](https://github.com/beartype/beartype) (new code). |
| **Ruby** | [Sorbet](https://sorbet.org/). |
| **GitHub Actions / CI** | [`zizmor`](https://github.com/zizmorcore/zizmor) for static analysis and security linting of GitHub Actions, Dependabot configurations, and pre-commit scripts. |

## 2. Code Quality & Verification Standards
* **Formatting**: All Go files must conform to standard `gofmt` (`go fmt ./...` before finalizing changes).
* **Linter**: Go code must pass `golangci-lint run` with **0 issues**. Configure and use `gocognit` to enforce cognitive complexity limits (aiming for a threshold of 15-20) to ensure code remains human-readable; prefer it over `gocyclo` which penalizes flat switch statements. Bash/Shell scripts must pass `shellcheck` to enforce linting and static security analysis. CI/CD scripts (GitHub Actions, Dependabot, pre-commit) must be analyzed using `zizmor`. Project-specific linters must pass before finalizing.
* **Coverage**: Achieve high statement coverage using table-driven test suites covering edge cases, boundary values, and input variations.
* **Verification**: Never mark a task complete without running relevant build and test commands to verify runtime correctness empirically.

## 3. Writing & Communication Style
* **Factual & Objective**: Comments, documentation, and explanations must be strictly factual and objective.
* **Terse & Concise**: Maintain a professional tone bordering on terse. Avoid conversational filler.
* **Citations & Links**: Provide markdown links to original sources or authoritative docs when referencing external definitions/tools (prefer permalinks or include "retrieved at" date).
* **Code Documentation & Comments**: Place documentation on functions; use inline comments only when needed to explain complexity, constants, or magic numbers.
* **Emojis**: Avoid emojis.

## 4. Tool Preferences & Usage
* **Build Environment & Temporary Directories**: All builds must use temporary directories scoped to the current conversation session or another unique temporary location. Set environment variables such as `GOCACHE`, `GOTMPDIR`, `GOMODCACHE` (Go), `PYTHON_EGG_CACHE`, `PYTHON_PIP_CACHE` (Python), `GEM_HOME`, `BUNDLE_PATH` (Ruby), and similar build-related caching directories to session-specific paths (e.g., under the conversation's scratchpad directory or a uniquely generated temp location). This ensures complete isolation between concurrent sessions and prevents cache contamination.
* **Scripting & CLI**: Prefer standard utilities (`jq`, `curl`, `sed`, `find`, `xargs`, `ncat`, etc.). Prefer [`yq`](https://github.com/mikefarah/yq) for `jq`-like querying and transformations across structured formats (`csv`, `hcl`, `ini`, `json`, `kyaml`, `lua`, `props`, `toml`, `tsv`, `uri`, `xml`, `yaml`) using `--input-format=<format>` (e.g., `--input-format=csv`) and `--output-format=<format>` (e.g., `--output-format=toml`). Maximize CLI tools and pipeline composition for data extraction and transformations; use Python only when state management or complex algorithms make shell pipelines impractical.
* **Git**:
  * **Sign Commits**: Always cryptographically sign commits with `git commit -S`. A successful commit is sufficient; do not run `git verify-commit`. Prompt the user if signing fails.
  * **Pushing**: Prompt user before pushing, unless explicit session permission is granted.
  * **Commit Message Construction**: Pass each commit-message paragraph as a separate argument. Use `git commit -S -m "<subject>" [-m "<body>"] --trailer "Assisted-by: <agent>:<model> [tools]"`; never place `\n` escape sequences inside a `-m` argument because Git records them literally. After committing, inspect the exact message with `git log -1 --format=%B`. See the [`git commit` documentation](https://git-scm.com/docs/git-commit).
  * **Metadata Tags**: Tag AI commits with `Assisted-by: AGENT_NAME:MODEL_VERSION [TOOL1] [TOOL2]` per [Linux Kernel guidelines](https://docs.kernel.org/process/coding-assistants.html#attribution). `[TOOL1]` = analysis tools (`coccinelle`, `sparse`, `smatch`, `clang-tidy`); omit basic dev tools (`git`, `gcc`, `make`). Ex: `Assisted-by: Claude:claude-3-opus coccinelle sparse`.
* **GitHub**: Use `gh` CLI (PRs, issues, repos, releases, gists). Prior to any usage of the `gh` CLI, you MUST run `gh auth switch --user BretzelLabsBot`. If this command fails or the user cannot be resolved, prompt the user to resolve the issue before proceeding.
* **AWS**: Use `aws` CLI (S3, EC2, Lambda, IAM, CloudFormation).
* **Clipboard**: Use `wl-copy` and `wl-paste` class of tools.
* **Web Search**: When searching the web, consider also searching in Arabic, Chinese, French, German, Japanese, Korean, and Spanish to avoid constraining searches to the English-speaking world.
* **Asset Sourcing & Attribution**: When searching the web and using external data or placeholder assets (e.g., images, graphics, components), prefer open source, [Creative Commons](https://creativecommons.org/), and free sources. Always attribute the source location/URL, original creator, license, retrieval timestamp, and relevant citation and redistribution metadata.
  * **In-Code Attribution**: Place attribution in header or inline code comments when supported by the file format.
  * **Sidecar Metadata File (`.meta.toml`)**: If attribution cannot be placed in a code comment (e.g., binary assets, image formats, media files), use an adjacent `<original_file_name>.meta.toml` file containing a single `[meta]` [TOML](https://toml.io/) table of string key-value pairs (`key = "value"`) containing citation metadata attributes and data.

## 5. Report Generation Standards
* **Reports & Pandoc**: Use `pandoc` with GitHub-flavored markdown (`-t gfm`) when creating complex reports. Iterate on markdown files first, regenerating HTML non-destructively.
* **Slide Decks & Marp**: Use [Marp](https://marp.app/) for slide decks with mermaid diagrams if needed.
  * **Portability**: Keep all report prompts, skills, scripts, filters, and templates vendor-neutral and repository-local. Use relative paths and standard command-line interfaces; do not depend on agent-specific home directories, APIs, tools, or metadata. Keep agent-specific adapters optional and limited to invoking the shared implementation.
  * **CDN Assets**: Prefer reputable CDN-hosted open source CSS/JS/web assets rather than checking them in.
  * **Code Samples**: Wrap code samples in collapsible `<details><summary>` blocks containing appropriate code blocks.
  * **Build Command & Metadata**: Document the build command line within each markdown file. Include the Git SHA and HTML rendering timestamp in the generated report.
  * **Change History & Attribution**: Include an append-only list of changes at the end of all reports, signed by the agent using an attribution tag similar to Git (`Assisted-by: AGENT_NAME:MODEL_VERSION [TOOLS]`).
  * **Section Links**: Keep Markdown headings free of explicit IDs. During HTML generation, use a shared, repository-local Pandoc Lua filter to make each heading a self-link through its automatically generated ID (e.g., `<h2 id="section-title"><a href="#section-title">Section Title</a></h2>`). The filter must leave Markdown and GFM output unchanged.
