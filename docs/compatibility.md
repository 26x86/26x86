---
hide: [toc]
---
<div class="portal" data-portal-page="compatibility" markdown>
<span class="portal-eyebrow">Hardware / Model reference</span>

# Find your Mac.

Search by model name or identifier. Apple operating system support and NextCore physical boot evidence are shown separately.

<div class="portal-notice" markdown>
**A model listing is not a NextCore compatibility approval.** Physical macOS desktop output remains unverified. Generic PCs, including the current Samsung target, are outside this Apple model catalog.
</div>

<form class="portal-filters" data-model-filters role="search" hidden>
<label class="portal-search-label">Search models<input type="search" name="q" placeholder="MacPro5,1, MacBook Air, M4…" autocomplete="off"></label>
<label>Family<select name="family"><option value="">All families</option></select></label>
<label>Architecture<select name="architecture"><option value="">All architectures</option><option value="intel">Intel</option><option value="apple-silicon">Apple silicon</option><option value="powerpc">PowerPC</option><option value="m68k">Motorola 68k</option><option value="unknown">Unknown</option></select></label>
<button type="reset" class="portal-button secondary">Reset filters</button>
</form>
<p class="portal-result-status" data-model-status role="status" aria-live="polite">The catalog is loading. Reference links below remain available.</p>
<noscript><p>Interactive filters require JavaScript. The complete model dataset and reference documents below remain available.</p></noscript>
<div data-model-detail></div>
<div class="portal-model-grid" data-model-results></div>

## Reference documents

- [Complete model dataset](data/mac-models.json)
- [Supported hardware notes](wiki/Supported-Models.md)
- [macOS support overview](wiki/macOS-Support.md)
- [Pre-AVX Mac Pro](wiki/Pre-AVX-Mac-Pro.md)
- [T2 Mac notes](wiki/T2-Mac-Notes.md)
- [Known limitations](wiki/Known-Issues.md)

**Current Status:** A source-linked model reference with independent NextCore evidence. **Target State:** Model-specific compatibility backed by reproducible physical testing.
</div>
