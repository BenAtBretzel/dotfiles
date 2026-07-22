# Agent Coding Guidelines & Session Steering

This document contains coding guidelines, standards, and steering rules derived from development sessions. Future AI agents working on this codebase should strictly adhere to these practices.

---

## 1. Code Style & Design Principles
* **Short-Circuit & Edge Cases**: Proactively check for empty, missing, boundary, or short-circuit conditions at the start of functions to minimize cognitive load and eliminate unnecessary allocations.
* **Detailed Error Handling**: Edge cases and unexpected calls must return detailed errors. For example, calling a custom sort function with `nil` should return an error stating the input was `nil` or missing. Error messages and types should be verified in tests whenever possible.
* **Purity of Functions**: Prefer pure functions that do not mutate input arguments. When input immutability is expected, tests should verify that the input state remains unaltered after the function call.
* **Best Practice & Deviations**: This code style is best practice for automated tasks, and any deviations should be annotated with comments explaining the rationale.

### Language-Specific Standards
| Language | Requirements & Tooling |
| :--- | :--- |
| **Go** | Use standard packages like [`maps`](https://pkg.go.dev/maps), [`slices`](https://pkg.go.dev/slices), and [`cmp`](https://pkg.go.dev/cmp). Prefer [`samber/lo`](https://github.com/samber/lo) (Lodash-style helpers), [`emirpasic/gods`](https://github.com/emirpasic/gods) (classical data structures), and [`go-playground/validator`](https://github.com/go-playground/validator) (struct tag validation) when helpful. |
| **JavaScript** | Use [TypeScript](https://www.typescriptlang.org/) when possible. |
| **Python** | New code must use [Beartype](https://github.com/beartype/beartype). |
| **Ruby** | Requires [Sorbet](https://sorbet.org/). |

## 2. Code Quality & Linting Standards
* **Formatting**: All Go files must conform to standard `gofmt`. Run `go fmt ./...` before finalizing changes.
* **Linter**: Code must pass `golangci-lint run` with **0 issues**.
* **Coverage**: Achieve high statement coverage using table-driven test suites covering edge cases, boundary values, and standard input variations.

## 3. Writing & Communication Style
* **Factual & Objective**: All comments, documentation, and agent explanations must be strictly factual and objective.
* **Terse & Concise**: Maintain a professional tone bordering on terse. Avoid conversational filler.
* **Citations & Links**: Provide markdown links to original sources or authoritative documentation when referencing external definitions or tools. Citations should prefer permalinks when possible, or else include a "retrieved at" date.
* **Code Documentation & Comments**: Code documentation should be on functions, and only be placed within functions when strictly necessary to explain complexity or constants/magic numbers.
* **Emojis**: Avoid emojis.

## 4. Tool Preferences & Usage
* **Scripting & Command Line Utilities**: Only drop to Python as a last resort. Prefer higher-level scripting and standard utilities like `jq`, `curl`, `sed`, `find`, `xargs`, `ncat`, etc.

### Git
* **Sign Commits**: Always sign commits and prompt the user if signing fails.
* **Pushing**: Prompt the user before pushing commits, unless explicit permission to push has been granted for the current session.
* **Metadata Tags**: All commits created, rebased, merged, etc. by agentic tools or LLMs should include an appropriate git metadata tag `Assisted-by` unless otherwise specified, following the [Linux Kernel AI Coding Assistants guidelines](https://docs.kernel.org/process/coding-assistants.html#attribution):
    
    Format:
    `Assisted-by: AGENT_NAME:MODEL_VERSION [TOOL1] [TOOL2]`
    
    * `AGENT_NAME`: The name of the AI tool or framework
    * `MODEL_VERSION`: The specific version of the model used
    * `[TOOL1] [TOOL2]`: Optional specialized analysis tools used alongside the AI (e.g., `coccinelle`, `sparse`, `smatch`, `clang-tidy`). Basic development tools (`git`, `gcc`, `make`, editors) should not be listed.
    
    Example:
    `Assisted-by: Claude:claude-3-opus coccinelle sparse`

### GitHub
* **GitHub CLI**: Use `gh` for interacting with github.com (e.g., PRs, issues, repos, releases, gists).

### AWS
* **AWS CLI**: Use `aws` for interacting with Amazon Web Services (e.g., S3, EC2, Lambda, IAM, CloudFormation).

### Clipboard
* **Clipboard Interactions**: Clipboard interactions should use the `wl-copy` and `wl-paste` class of tools.

