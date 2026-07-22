# Agent Coding Guidelines & Session Steering

Coding guidelines, standards, and steering rules for AI agents. Strictly adhere to these practices.

---

## 1. Code Style & Design Principles
* **Short-Circuit & Edge Cases**: Proactively check empty, missing, boundary, or short-circuit conditions at function start to minimize cognitive load and eliminate unnecessary allocations.
* **Detailed Error Handling**: Edge cases and unexpected calls must return detailed errors (e.g., calling custom sort with `nil` returns error stating input was `nil` or missing). Verify error messages and types in tests whenever possible.
* **Purity of Functions**: Prefer pure functions that do not mutate input arguments. When input immutability is expected, tests must verify input state remains unaltered after function calls.
* **Best Practice & Deviations**: Annotate any deviations from best practices with comments explaining the rationale.

### Language-Specific Standards
| Language | Standards & Best Practice Tooling |
| :--- | :--- |
| **Go** | Stdlib [`maps`](https://pkg.go.dev/maps), [`slices`](https://pkg.go.dev/slices), [`cmp`](https://pkg.go.dev/cmp). Prefer [`samber/lo`](https://github.com/samber/lo) (helpers), [`emirpasic/gods`](https://github.com/emirpasic/gods) (data structures), [`go-playground/validator`](https://github.com/go-playground/validator) (validation). |
| **JavaScript** | [TypeScript](https://www.typescriptlang.org/). |
| **Python** | [Beartype](https://github.com/beartype/beartype) (new code). |
| **Ruby** | [Sorbet](https://sorbet.org/). |

## 2. Code Quality & Linting Standards
* **Formatting**: All Go files must conform to standard `gofmt` (`go fmt ./...` before finalizing changes).
* **Linter**: Code must pass `golangci-lint run` with **0 issues**.
* **Coverage**: Achieve high statement coverage using table-driven test suites covering edge cases, boundary values, and input variations.

## 3. Writing & Communication Style
* **Factual & Objective**: Comments, documentation, and explanations must be strictly factual and objective.
* **Terse & Concise**: Maintain a professional tone bordering on terse. Avoid conversational filler.
* **Citations & Links**: Provide markdown links to original sources or authoritative docs when referencing external definitions/tools (prefer permalinks or include "retrieved at" date).
* **Code Documentation & Comments**: Place documentation on functions; use inline comments only when needed to explain complexity, constants, or magic numbers.
* **Emojis**: Avoid emojis.

## 4. Tool Preferences & Usage
* **Scripting & CLI**: Prefer standard utilities (`jq`, `curl`, `sed`, `find`, `xargs`, `ncat`, etc.) over Python. Only drop to Python as a last resort.
* **Git**:
  * **Sign Commits**: Always sign commits and prompt user on failure.
  * **Pushing**: Prompt user before pushing, unless explicit session permission is granted.
  * **Metadata Tags**: Tag AI commits with `Assisted-by: AGENT_NAME:MODEL_VERSION [TOOL1] [TOOL2]` per [Linux Kernel guidelines](https://docs.kernel.org/process/coding-assistants.html#attribution). `[TOOL1]` = analysis tools (`coccinelle`, `sparse`, `smatch`, `clang-tidy`); omit basic dev tools (`git`, `gcc`, `make`). Ex: `Assisted-by: Claude:claude-3-opus coccinelle sparse`.
* **GitHub**: Use `gh` CLI (PRs, issues, repos, releases, gists).
* **AWS**: Use `aws` CLI (S3, EC2, Lambda, IAM, CloudFormation).
* **Clipboard**: Use `wl-copy` and `wl-paste` class of tools.
