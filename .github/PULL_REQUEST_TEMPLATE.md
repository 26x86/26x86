## What does this PR do?

<!-- One paragraph. What changed and why. -->

## Type of change

- [ ] docs (site, wiki, mkdocs nav)
- [ ] module (Nextcore submodule pointer bump)
- [ ] code (patcher, tooling, CI)
- [ ] CI/deployment
- [ ] other: _____

## Checks

- [ ] I read the [branching and release policy](docs/wiki/Branching-and-Release.md).
- [ ] Changes follow the [developer guide](docs/wiki/Developer.md).
- [ ] No `_isolated/` path is staged (pre-commit guard enforces this).
- [ ] If I bumped a Nextcore module I staged the **gitlink** only
      (`git add nextcore/crates/<module>`), never module file contents.
- [ ] `docs-build`, `isolated-asset-guard`, and `workspace-tests` are expected to
      pass (or a justification is given in the description).

## Documentation

- [ ] User-facing behavior changed → `docs/wiki/` updated and `mkdocs build --strict` passes locally.

## Evidence

<!-- For boot-engineering changes: which layer does this PR measure, and what
     is the acceptance boundary? A passed static check is never a boot result. -->

## Related

- Closes #_____ (if any)