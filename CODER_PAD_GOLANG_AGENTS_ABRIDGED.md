# CoderPad Go Agent Guidelines & Steering

Specialized guidelines, execution rules, and code standards for AI agents operating within a CoderPad Go environment.

---

## 1. CoderPad Go Environment Architecture & Context

### 1.1 Run Target Configuration (`.cpad`)
The `.cpad` JSON file configures UI run targets:

```json
{
  "targets": {
    "run": {
      "label": "Main",
      "command": "go run src/main.go"
    },
    "test": {
      "label": "Tests",
      "command": "go test ./..."
    }
  }
}
```
* Ensure the `test` target command executes all package tests (`go test ./...`).

### 1.2 Environment Focus & Container Boundaries
* **Interview Priorities**: Prioritize clean, readable, correct, and testable code over premature runtime or memory optimizations.
* **Container Boundaries**: Container provides 2 GB RAM and a 75 MB network bandwidth limit per session. Keep package installations (`go get`) and network I/O minimal.

### 1.3 Collaboration & Editor Rules
* **File Modifications**: Modify code files via the editor API rather than direct shell edits to preserve visibility for all session participants.
* **Shell Usage**: Restrict shell operations to running test suites (`go test ./...`), package installation (`go get <package>`), environment inspection, or code formatting/linting tools.

---

## 2. Go Code Style & Technical Principles

* **Early Exits & Short-Circuiting**: Check empty, missing, boundary, or short-circuit conditions at function start to minimize cognitive load and enhance code readability.
* **Detailed Error Handling**: Edge cases and unexpected calls must return descriptive errors. Validate error types and messages in test suites.
* **Purity of Functions**: Prefer pure functions that do not mutate input data. Verify input immutability in unit tests.
* **Symbol Shadowing**: Explicitly avoid variable or package symbol shadowing; use clear, distinct naming.
* **Standard & Approved Libraries**:
  * Stdlib: Standard Go [`maps`](https://pkg.go.dev/maps), [`slices`](https://pkg.go.dev/slices), and [`cmp`](https://pkg.go.dev/cmp) packages.
  * Third-Party Utilities: [`samber/lo`](https://github.com/samber/lo) for functional helpers, [`emirpasic/gods`](https://github.com/emirpasic/gods) for data structures, and [`go-playground/validator`](https://github.com/go-playground/validator) for struct validation.
  * Unit Testing Context: Use `t.Context()` or explicit test contexts in unit tests; avoid `context.TODO()` or `context.Background()`.

---

## 3. Code Quality & Empirical Verification

* **Formatting**: Ensure all `.go` files pass standard formatting (`go fmt ./...`).
* **Linting**: Maintain zero lint issues with `golangci-lint run`.
* **Test Coverage**: Construct table-driven test suites covering boundary conditions and error paths.
* **Target Verification**: Validate changes empirically using the `.cpad` run targets (`go run`, `go test`) or shell execution before marking tasks complete.

---

## 4. Communication & Tooling Standards

* **Writing Style**: Factual, concise, and objective. Avoid conversational filler and emojis.
* **Documentation**: Document exported functions and complex algorithms. Use markdown links when referring to external specifications or documentation.
