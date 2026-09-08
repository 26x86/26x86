# Documentation publication QA

Current: the deployed NextCore front page returns HTTP 200, but its three raw
HTML action buttons retain `.md` source paths and each returns HTTP 404. The
generated routes `wiki/`, `wiki/Getting-Started/` and `wiki/Supported-Models/`
already exist and return HTTP 200. The local site reproduces the broken buttons.
Desired: preserve the design and labels while letting MkDocs resolve source-page
links correctly; verify entry routes, required assets and NextCore branding.

DECIDED, delegated by the Build Plan owner under BP23: convert only the confirmed
button links to Markdown inside explicitly parsed HTML containers. Rebuild with
the existing MkDocs environment and `--strict`, then inspect the generated links
and serve the built pages for HTTP checks. Inspect the front page and its primary
wiki destinations for unresolved local links/assets and misleading product labels.
Any additional change must correspond to an observed problem. Scope is docs/index,
MkDocs configuration, wiki links and docs/assets; production and frozen runtime
evidence remain untouched. Root owns Git commit/push and live deployment.

Source and live evidence are saved in this directory. A local correction is not
represented as deployed until the remote revision is published and rechecked.

The four entry pages contain 51 unique local targets. Beyond the three buttons,
the only missing route is `wiki/Home/`, linked twice from the documentation hub
even though that legacy page is explicitly excluded from publication. DECIDED:
point the questions entry to the published Troubleshooting page and installer/
backup entry to Getting started, retaining the exclusion and upstream attribution.

The owner also delegated the Getting started introduction's product label: name
NextCore's companion tools while explicitly retaining the external OpenCore EFI
preparation scope. Markdown introduces a paragraph around the three buttons;
use `display: contents` on that wrapper so the existing flex spacing/wrapping,
button labels and CSS classes remain unchanged. Check desktop and narrow layouts.

Result: strict MkDocs build passes. All 47 unique internal page/asset targets
from the four primary entry pages return HTTP 200 from the built site. Chrome
shows all three buttons with their original classes and flex gaps; actual clicks
reach the expected document headings. At 1920 and 390 pixels the page has no
horizontal overflow; the narrow layout wraps the third button onto a second row.
The picker image loads, all four page titles use NextCore, and upstream OpenCore
preparation attribution remains explicit. Temporary viewport and tab were reset/
closed, and the owned local HTTP server was terminated and reaped.

The deployed pre-fix buttons and excluded Home route were directly confirmed as
404. Their intended destination routes and front-page assets return live 200.
Corrected live publication remains pending root's PR6 commit/deployment.
No MkDocs configuration or link-validation setting was changed. The four source
paths and final hashes are recorded in `result.json` and `verified-files.txt`.
