## What does this PR do?

<!-- One paragraph. What changed and why. -->

## Type of change

- [ ] docs (site, wiki, mkdocs nav)
- [ ] module (NextCore workspace crate or independent module export)
- [ ] code (patcher, tooling, CI)
- [ ] CI/deployment
- [ ] other: _____

## Checks

- [ ] I read the [branching and release policy](docs/wiki/Branching-and-Release.md).
- [ ] Changes follow the [developer guide](docs/wiki/Developer.md).
- [ ] No `_isolated/` path is staged (pre-commit guard enforces this).
- [ ] Module changes identify the tracked workspace source commit and, when
      published separately, the independent release tag and verification.
- [ ] `docs-build`, `isolated-asset-guard`, and `workspace-tests` are expected to
      pass (or a justification is given in the description).

## Documentation

- [ ] User-facing behavior changed → `docs/wiki/` updated and `mkdocs build --strict` passes locally.

## Evidence

<!-- For boot-engineering changes: which layer does this PR measure, and what
     is the acceptance boundary? A passed static check is never a boot result. -->

## Related

- Closes #_____ (if any)
