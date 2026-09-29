# Opportunity selection — 2026-09-29

Scores are engineering judgments (1–5), not measured market forecasts. Columns:
usefulness / novelty / demand / shareability / demo / feasible MVP / technical depth /
installation ease / one-sentence clarity / expansion. Equal weighting, maximum 50.

| Idea | Scores | Total | Decision |
|---|---|---:|---|
| Skill collection dependency impact + isolated-install comparison | 5/4/5/4/5/5/4/5/5/5 | 47 | Selected: concrete issue evidence, modest reliable scope |
| MCP contract drift report | 5/1/5/4/4/4/4/4/5/5 | 41 | Existing mcp-contracts, mcpdiff, Cisco tools cover it |
| Parallel worktree conflict radar | 5/1/5/4/5/4/4/5/5/5 | 43 | Grove and Clash already cover core workflow |
| Local voice-model hardware readiness explainer | 4/3/4/4/4/3/4/3/4/4 | 37 | Too much hardware validation for trustworthy MVP |
| RAG import loss ledger for tables and diagrams | 5/4/4/4/5/3/5/3/4/5 | 42 | Valuable, but document-format fidelity is large scope |
| Agent memory deletion propagation simulator | 4/4/4/4/4/3/5/4/3/5 | 40 | Needs concrete backend adapters to become useful |
| Cross-provider agent quota replay simulator | 4/4/4/4/4/4/4/5/4/5 | 42 | Demand visible, quota semantics change rapidly |
| Skill installer collision preview | 4/3/4/4/4/5/3/5/5/4 | 41 | Useful narrow companion; less expansion than graph |
| Chat-template boundary fixture harness | 5/3/4/4/4/3/5/3/3/5 | 39 | Real reasoning leakage issues; model runtimes costly |
| Screenshot coordinate calibration checker | 4/4/3/4/5/3/5/3/4/4 | 39 | Good computer-use niche, OS matrix too large |
| Offline CLI capability catalog differ | 4/3/4/3/3/4/4/5/4/4 | 38 | Extraction reliability needs heterogeneous tools |
| Agent audit finding evidence packager | 4/3/4/4/4/4/3/5/4/5 | 40 | Adjacent to Cloudflare, needs review workflow research |

## Primary problem evidence
- [Shared reference links broken even in full installation](https://github.com/addyosmani/agent-skills/issues/468): wrong path bases across multiple skills. Closed issue; evidence of a failure class, not a claim the upstream remains broken.
- [Per-skill install omits shared references](https://github.com/addyosmani/agent-skills/issues/361): distinct packaging failure. Closed.
- [Shared versus colocated reference discussion](https://github.com/addyosmani/agent-skills/issues/329): explains the topology/design tradeoff. Closed.
- [Installer overwrites collisions](https://github.com/rohitg00/ai-engineering-from-scratch/issues/506), [CRLF manifest mismatch](https://github.com/rohitg00/ai-engineering-from-scratch/issues/504): related portability problems, not all addressed by this MVP.

## Competitive boundary
[skill-validator](https://github.com/agent-ecosystem/skill-validator) already checks
links, orphans, structure and metadata. [SkillLint](https://github.com/Meet-Miyani/agent-skill-validator)
already offers a local browser audit with graph and repair features.
[SkillPort](https://github.com/gotalab/skillport) validates and distributes skills.
Skillspine's chosen workflow is collection-level reverse impact, explanatory chains,
and explicit comparison of repository availability with per-folder installation.
The graph implementation is original; no source from these projects was copied.
This is a focused adjacent utility, not a claim of category invention.

## Name check
GitHub repository search `skillspine in:name` returned 0 results on 2026-09-29.
The account-specific endpoint returned 404 before creation. Exact web-name search
surfaced no dominant software project. This is an availability check, not trademark clearance.
