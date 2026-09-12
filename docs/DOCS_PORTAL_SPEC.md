# Documentation Portal Specification

## Current Status

The Material documentation site contains technical references but does not give readers a coherent view of development evidence or a searchable model catalog. The delegated User Flow and Design scope covers the home, progress, compatibility and library pages, their shared presentation and client interactions.

## Target State

Development progress is the largest home section. Readers can distinguish authored firmware tests, original-input execution boundaries, physical display and graphics acceleration without inferred completion percentages. Existing technical pages and search remain available.

## Decisions

- Home prioritizes the current evidence boundary, milestones and routes to progress, compatibility and documentation.
- Progress presents evidence by layer, links to authoritative records and identifies what the next acceptance gate requires. The reviewed r8 checkpoint reaches a 16,384-instruction diagnostic budget after BFM support without an unsupported-instruction stop. Budget exhaustion does not establish forward progress or normal startup; physical macOS desktop remains unverified. Later reviewed data may replace this checkpoint explicitly.
- Compatibility searches `data/mac-models.json`, schema `nextcore.mac-model-catalog.v1`. Models have stable IDs, names, families, nullable years, identifiers, architecture, Apple support, NextCore evidence and source links. Apple OS support and NextCore validation are separate fields. Unknown values are displayed as unknown.
- Model search, family and architecture filters are reflected in the URL. A model detail can be linked with `model`. Reset, empty, loading and failure states remain usable with keyboard input.
- Device detail keeps each Apple-identified variant separate, including its identification facts and linked specification pages. Specification-page processor and capacity mentions are configuration options, not an installed configuration or a guarantee for every identifier on the page. Historical repository records are shown in a separate disclosure with their original dataset key and provenance. Missing fields remain explicit.
- Library uses the published MkDocs search index, aggregated by page, to search every indexed document. A curated static directory remains available without JavaScript or on network failure.
- Progress may consume `data/progress.json` with `updated_at`, `headline`, `boundary` (`label`, `detail`, `evidence_url`), `milestones` (`title`, `status`, `layer`, `summary`, `evidence_url`), and `latest` (`date`, `title`, `summary`, `url`). Static evidence links remain when data is unavailable.
- Dynamic text uses DOM text nodes. Links accept only HTTP(S) or same-origin relative URLs. No external library or analytics is added.
- The interface is mobile first, supports Material light and dark themes, visible focus, reduced motion, native semantic controls and polite status announcements. Instant navigation reinitializes each page independently.

## Acceptance

Strict MkDocs build and JavaScript syntax checks pass. Browser validation covers mobile layout, search, filters, model detail deep links, reset, no results and document navigation. Runtime browser and publication validation are integration-owned. A successful site build does not establish firmware or hardware compatibility.
