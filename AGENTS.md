# Agent Coding Guidelines & Session Steering

This document contains coding guidelines, standards, and steering rules derived from development sessions. Future AI agents working on this codebase should strictly adhere to these practices.

---

## 1. Code Style & Design Principles
* **Short-Circuit & Edge Cases**: Proactively check for empty, missing, boundary, or short-circuit conditions at the start of functions to minimize cognitive load and eliminate unnecessary allocations.
* **Detailed Error Handling**: Edge cases and unexpected calls must return detailed errors. For example, calling a custom sort function with `nil` should return an error stating the input was `nil` or missing. Error messages and types should be verified in tests whenever possible.
* **Purity of Functions**: Prefer pure functions that do not mutate input arguments. When input immutability is expected, tests should verify that the input state remains unaltered after the function call.
* **Best Practice & Deviations**: This code style is best practice for automated tasks, and any deviations should be annotated with comments explaining the rationale.

## 2. Code Quality & Linting Standards
* **Formatting**: All Go files must conform to standard `gofmt`. Run `go fmt ./...` before finalizing changes.
* **Linter**: Code must pass `golangci-lint run` with **0 issues**.
* **Coverage**: Achieve high statement coverage using table-driven test suites covering edge cases, boundary values, and standard input variations.

## 3. Writing & Communication Style
* **Factual & Objective**: All comments, documentation, and agent explanations must be strictly factual and objective.
* **Terse & Concise**: Maintain a professional tone bordering on terse. Avoid conversational filler.
* **Citations & Links**: Provide markdown links to original sources or authoritative documentation when referencing external definitions or tools. Citations should prefer permalinks when possible, or else include a "retrieved at" date.
* **Code Documentation & Comments**: Code documentation should be on functions, and only be placed within functions when strictly necessary to explain complexity or constants/magic numbers.

