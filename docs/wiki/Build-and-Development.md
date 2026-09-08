# Build and development

## Public development loop

1. Read `AGENTS.md` and the relevant public design or build document.
2. Keep implementation and documentation aligned before adding new code.
3. Run the narrowest applicable static check for the changed layer.
4. Record unresolved runtime work as evidence gaps, not as completed support.

## Areas of ownership

- `26x86` owns the guided workflow, OpenCore integration, EFI preparation, and
  diagnostics.
- `nextcore/` owns public Nextcore contracts and experiments documented in the
  repository.
- `docs/` owns public specifications, guides, and evidence boundaries.
- `_isolated/` is private reference material and is not part of public work.

## Documentation rules

Use public names and observable contracts. Do not publish private source names,
internal implementation details, extracted assets, or isolated research
transcripts. Put unresolved cross-area decisions in the owning design document.
