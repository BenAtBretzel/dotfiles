# CoderPad Go Agent Guidelines & Steering

Specialized guidelines, execution rules, and code standards for AI agents operating within a CoderPad Go environment.

---

## 1. CoderPad Go Environment Architecture & Constraints

### 1.1 Run Target Configuration (`.cpad`)
The `.cpad` file defines project run targets in JSON format. Every target requires a unique key, a human-readable `label`, and a shell `command`.

Recommended `.cpad` layout (configured to run the entire test suite):
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

* **Custom Targets**: Add or update keys in the `targets` object as needed to define additional build, execution, or test tasks. Ensure the `test` target command executes all package tests (`go test ./...`) rather than restricting execution to a single test file.
* **Label**: Used for visual UI button display.
* **Command**: Shell command executed when triggering the target.

### 1.2 Resource & Container Limits
* **Memory Limit**: 2 GB RAM maximum. Write memory-efficient code, avoid unnecessary allocations, and minimize memory overhead.
* **Network Bandwidth Limit**: 75 MB total consumed bandwidth per container lifetime. Minimize external HTTP calls during testing and restrict `go get` installations to required dependencies.
* **CPU Usage**: Unthrottled by default; keep computational tasks efficient to prevent performance degradation.

### 1.3 Collaboration & Editor Rules
* **File Modifications**: Modify code files via the editor API rather than direct shell edits to preserve visibility for all session participants.
* **Shell Usage**: Restrict shell operations to running test suites (`go test ./...`), package installation (`go get <package>`), environment inspection, or code formatting/linting tools.

---

## 2. Go Code Style & Technical Principles

* **Early Exits & Short-Circuiting**: Check empty, missing, boundary, or short-circuit conditions at function start to minimize cognitive load and avoid memory allocations under container limits.
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
* **Git Conventions**:
  * **Signed Commits**: Always cryptographically sign commits using `git commit -S`. Prompt the user if key signing fails.
  * **Commit Structure**: Pass multi-line commit messages using separate `-m` arguments (`git commit -S -m "<subject>" -m "<body>"`). Include proper trailers (`Assisted-by: AGENT_NAME:MODEL_VERSION [TOOLS]`).
  * **Remote Push**: Prompt the user before running `git push`.
