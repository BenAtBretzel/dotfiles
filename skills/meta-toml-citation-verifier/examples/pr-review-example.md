# Pull Request Citation Verification Review Comment

The following snippet illustrates the formatted comment emitted when reviewing a GitHub Pull Request with the Meta Citation Verifier skill.

```markdown
> [!IMPORTANT]
> **Disclaimer**: This review reflects automated citation verification analysis performed by the Meta Citation Verifier skill. This is the skill's opinion and may not reflect those of the skill's authors or repository maintainers.

### Citation Verification Summary for PR #42

| Total Citations | Verified | Unsupported | Unreachable | Exempt/Internal | Pass Rate |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 4 | 4 | 0 | 0 | 0 | **100%** |

#### Itemized Review Findings

| File | Claim / Adaptation | Source URL | Verified Status |
| :--- | :--- | :--- | :---: |
| `personas/ext/go-mcp-engineer.meta.toml` | Adapted Go MCP engineering prompt | [go-mcp-expert.agent.md](https://github.com/github/awesome-copilot/blob/main/agents/go-mcp-expert.agent.md) | `VERIFIED` |
| `personas/ext/accessibility.meta.toml` | Accessibility persona adaptation | [accessibility.agent.md](https://github.com/github/awesome-copilot/blob/main/agents/accessibility.agent.md) | `VERIFIED` |
| `personas/ext/security-auditor.meta.toml` | Security auditor adaptation | [security-auditor.md](https://github.com/wshobson/agents/blob/main/plugins/comprehensive-review/agents/security-auditor.md) | `VERIFIED` |
| `personas/ext/task-breakdown.meta.toml` | Task breakdown adaptation | [task-planner.agent.md](https://github.com/github/awesome-copilot/blob/main/agents/task-planner.agent.md) | `VERIFIED` |

<details>
<summary>Substantiation Verification Details</summary>

- All 4 external upstream URLs were reachable via HTTP 200.
- License files (`LICENSES/mit-github-awesome-copilot.txt`, `LICENSES/mit-wshobson-agents.txt`) match upstream licenses (MIT).
- Copyright notices match upstream author attributions.

</details>
```
