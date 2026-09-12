/* NextCore documentation portal: dependency-free, accessible progressive enhancement. */
(() => {
  "use strict";
  const script = document.querySelector('script[src*="assets/javascripts/portal.js"]');
  const base = new URL("../../", script ? script.src : location.href);
  const el = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  };
  const link = (label, value) => {
    const node = el("a", label);
    if (typeof value !== "string" || !value) return el("span", label);
    try {
      const url = new URL(value, base);
      if (["http:", "https:"].includes(url.protocol)) node.href = url.href;
    } catch (_) { /* Malformed source links remain plain text. */ }
    return node;
  };
  const getJSON = async (path) => {
    const response = await fetch(new URL(path, base));
    if (!response.ok) throw new Error("Catalog unavailable");
    return response.json();
  };
  const labelArchitecture = (value) => ({
    intel: "Intel", "apple-silicon": "Apple silicon", powerpc: "PowerPC", m68k: "Motorola 68k", unknown: "Unknown"
  }[value] || "Unknown");
  const searchText = (value) => String(value || "").toLocaleLowerCase().normalize("NFKD");
  const termsMatch = (haystack, query) => searchText(query).trim().split(/\s+/).every(term => haystack.includes(term));
  const badge = (text, style = "") => el("span", text, "portal-badge " + style);
  const statusLabel = value => ({"validated-in-ovmf": "Validated in OVMF", "in-progress": "In development", "not-ready": "Not ready", unverified: "Unverified"}[value] || value);
  const factList = entries => {
    const list = el("dl", undefined, "portal-facts");
    for (const [label, value] of entries) {
      const text = Array.isArray(value) ? value.join(" · ") : value;
      list.append(el("dt", label), el("dd", text === false ? "No" : text === true ? "Yes" : text || "Not documented"));
    }
    return list;
  };
  function specificationDetails(model) {
    const section = el("section", undefined, "portal-variant-section");
    section.append(el("h3", "Apple variants & technical specifications"), el("p", "A model identifier can cover different releases and configurations. Keep each variant and its source page separate.", "portal-small"));
    const specs = model.technical_specifications || [];
    const used = new Set();
    const appendSpec = (container, spec) => {
      const block = el("div", undefined, "portal-specification");
      block.append(el("h5", "Options mentioned on the specification page"));
      block.append(factList([
        ["Processor mentions", spec.processor_mentions],
        ["Memory capacity mentions", spec.memory_capacity_mentions],
        ["Storage capacity mentions", spec.storage_capacity_mentions]
      ]));
      block.append(el("p", spec.scope || "Specification-page options; not measured installed hardware.", "portal-small"));
      block.append(link("Read this Apple specification →", spec.source_url));
      container.append(block);
    };
    for (const variant of model.variants || []) {
      const card = el("article", undefined, "portal-variant");
      card.append(el("h4", variant.name), el("p", (variant.identifiers || []).join(" · ") || "Identifier not verified", "portal-model-id"));
      const factLabels = {chip: "Chip", colors: "Colors", front_ports: "Front ports", ports: "Ports"};
      const entries = Object.entries(variant.facts || {}).map(([key, value]) => [factLabels[key] || key.replaceAll("_", " "), value]);
      if (entries.length) card.append(factList(entries));
      else card.append(el("p", "Additional configuration facts are not transcribed for this variant. Consult its technical specification.", "portal-small"));
      if (variant.source_url) card.append(link("Apple identification source →", variant.source_url));
      for (const url of variant.technical_specs_urls || []) {
        const spec = specs.find(item => item.source_url === url);
        if (spec) { appendSpec(card, spec); used.add(url); }
        else { const reference = el("p"); reference.append(link("Apple technical specification →", url)); card.append(reference); }
      }
      section.append(card);
    }
    for (const spec of specs.filter(item => !used.has(item.source_url))) {
      const card = el("article", undefined, "portal-variant");
      card.append(el("h4", "Model specification reference"));
      appendSpec(card, spec); section.append(card);
    }
    if (!(model.variants || []).length && !specs.length) {
      section.append(el("p", "No separate variant records are transcribed. Consult the source-linked catalog summary and Apple technical specification."));
      if (model.apple_support?.source_url) section.append(link("Open Apple source →", model.apple_support.source_url));
    }
    const historical = model.repository_hardware || [];
    if (historical.length) {
      const disclosure = el("details", undefined, "portal-historical");
      disclosure.append(el("summary", "Historical repository hardware records (" + historical.length + ")"));
      disclosure.append(el("p", "These are recorded dataset values, not Apple-verified specifications or measurements of your Mac. Internal device names are preserved as recorded. They do not establish NextCore compatibility.", "portal-small"));
      for (const record of historical) {
        disclosure.append(el("h4", record.dataset_key || record.name || "Historical record"));
        disclosure.append(factList([
          ["CPU generation", record.cpu_generation], ["Stock GPUs", record.stock_gpus],
          ["Stock storage", record.stock_storage], ["Display size (inches)", record.screen_inches],
          ["Wireless", record.wireless], ["Bluetooth", record.bluetooth],
          ["Ethernet", record.ethernet], ["UGA graphics", record.uga_graphics]
        ]));
      }
      const source = (model.sources || []).find(item => /repository.*historical|SMBIOS/i.test(item.label));
      if (source) disclosure.append(link(source.label, source.url));
      section.append(disclosure);
    }
    return section;
  }
  const empty = (target, title, text) => {
    target.replaceChildren();
    const panel = el("div", undefined, "portal-empty");
    panel.append(el("h3", title), el("p", text));
    target.append(panel);
  };
  const writeURL = (form, extra = {}) => {
    const url = new URL(location.href);
    for (const control of form.elements) {
      if (!control.name) continue;
      if (control.value) url.searchParams.set(control.name, control.value);
      else url.searchParams.delete(control.name);
    }
    for (const [key, value] of Object.entries(extra)) {
      if (value) url.searchParams.set(key, value);
      else url.searchParams.delete(key);
    }
    history.replaceState(null, "", url);
  };
  const readURL = (form) => {
    const params = new URLSearchParams(location.search);
    for (const control of form.elements) {
      if (control.name) control.value = params.get(control.name) || "";
    }
  };
  const wireFilters = (root, form, render) => {
    form.hidden = false;
    readURL(form);
    form.addEventListener("submit", event => event.preventDefault());
    form.addEventListener("input", () => { writeURL(form, {model: ""}); render(); });
    form.addEventListener("reset", () => {
      // The reset event occurs before the browser resets native controls.
      queueMicrotask(() => { writeURL(form, {model: ""}); render(); });
    });
    const onPop = () => {
      if (!root.isConnected) { window.removeEventListener("popstate", onPop); return; }
      readURL(form); render();
    };
    window.addEventListener("popstate", onPop);
    render();
  };

  async function models(root) {
    const status = root.querySelector("[data-model-status]");
    const results = root.querySelector("[data-model-results]");
    const detail = root.querySelector("[data-model-detail]");
    const form = root.querySelector("[data-model-filters]");
    try {
      const catalog = await getJSON("data/mac-models.json");
      if (catalog.schema !== "nextcore.mac-model-catalog.v1" || !Array.isArray(catalog.models)) throw new Error("Invalid catalog");
      const rows = [...catalog.models].sort((a, b) => (b.year || 0) - (a.year || 0) || a.name.localeCompare(b.name));
      const families = [...new Set(rows.map(row => row.family).filter(Boolean))].sort();
      for (const family of families) {
        const option = el("option", family); option.value = family; form.elements.family.append(option);
      }
      const showDetail = (model, focus = false) => {
        detail.replaceChildren();
        if (!model) return;
        const panel = el("section", undefined, "portal-model-detail");
        const heading = el("h2", model.name);
        heading.tabIndex = -1;
        const close = el("button", "Close details", "portal-button secondary");
        close.type = "button";
        close.addEventListener("click", () => {
          writeURL(form, {model: ""});
          detail.replaceChildren();
          const original = [...results.querySelectorAll("button")].find(button => button.dataset.modelId === model.id);
          (original || form.elements.q).focus();
        });
        panel.append(badge("Model reference"), heading, el("p", (model.identifiers || []).join(" · ") || "Identifier not verified"), close);
        const facts = el("dl", undefined, "portal-facts");
        const addFact = (name, value) => facts.append(el("dt", name), el("dd", value || "Not documented"));
        addFact("Architecture", labelArchitecture(model.architecture));
        addFact("Family / release", model.family + (model.year ? " / " + model.year : ""));
        for (const [key, value] of Object.entries(model.details || {})) {
          addFact(key.charAt(0).toUpperCase() + key.slice(1), typeof value === "string" ? value : null);
        }
        panel.append(facts);
        const apple = el("div", undefined, "portal-evidence-block");
        const support = model.apple_support || {};
        apple.append(el("h3", "Apple operating system support"));
        apple.append(el("p", "Latest released macOS listed by the source: " + (support.latest_macos || "Not documented")));
        if (support.macos_27) {
          const state = support.macos_27.status;
          apple.append(el("p", "macOS 27 eligibility: " + (state === "eligible" ? "Listed as eligible by Apple" : state === "ineligible" ? "Not listed as eligible by Apple" : "Not verified")));
          apple.append(link("Apple macOS 27 reference →", support.macos_27.source_url));
        }
        if (support.source_url) {
          const reference = el("p"); reference.append(link("Apple model identification →", support.source_url)); apple.append(reference);
        }
        if (support.verified_at) apple.append(el("small", "Source checked " + support.verified_at));
        const nextcore = el("div", undefined, "portal-evidence-block");
        nextcore.append(el("h3", "NextCore physical boot evidence"), badge(model.nextcore?.status || "unverified", "pending"));
        nextcore.append(el("p", model.nextcore?.summary || "No model-specific physical desktop evidence."));
        if (model.nextcore?.architecture_support === "not-implemented") nextcore.append(el("p", "NextCore execution support for this architecture is not implemented."));
        if (model.nextcore?.evidence_url) nextcore.append(link("Read model evidence →", model.nextcore.evidence_url));
        panel.append(apple, nextcore);
        panel.append(specificationDetails(model));
        const sources = el("ul");
        for (const source of model.sources || []) {
          const item = el("li"); item.append(link(source.label, source.url)); sources.append(item);
        }
        panel.append(el("h3", "Sources & configuration notes"), sources);
        for (const note of model.notes || []) panel.append(el("p", note, "portal-small"));
        detail.append(panel);
        if (focus) { heading.focus({preventScroll: true}); panel.scrollIntoView({block: "start", behavior: "auto"}); }
      };
      const render = () => {
        const q = form.elements.q.value;
        const family = form.elements.family.value;
        const architecture = form.elements.architecture.value;
        const filtered = rows.filter(model =>
          (!family || model.family === family) && (!architecture || model.architecture === architecture) &&
          termsMatch(searchText([model.name, model.family, model.year, model.details?.cpu, ...(model.identifiers || []), ...(model.variants || []).map(variant => variant.name)].join(" ")), q));
        status.textContent = filtered.length + " of " + rows.length + " model records · Sources checked " + catalog.updated_at + " · NextCore evidence is separate from Apple support.";
        results.replaceChildren();
        if (!filtered.length) empty(results, "No models match these filters.", "Try a shorter identifier, another family, or reset the filters.");
        for (const model of filtered) {
          const card = el("article", undefined, "portal-model-card");
          card.append(el("span", model.family + " / " + labelArchitecture(model.architecture), "portal-eyebrow"));
          card.append(el("h3", model.name), el("p", (model.identifiers || []).join(" · ") || "Identifier not verified", "portal-model-id"));
          card.append(el("p", "Apple OS: " + (model.apple_support?.latest_macos || "See source")), badge("NextCore: " + (model.nextcore?.status || "unverified"), "pending"));
          const button = el("button", "View model & sources →", "portal-card-button");
          button.type = "button";
          button.dataset.modelId = model.id;
          button.setAttribute("aria-label", "View " + model.name + " " + (model.identifiers || []).join(", ") + " details and sources");
          button.addEventListener("click", () => { writeURL(form, {model: model.id}); showDetail(model, true); });
          card.append(button);
          results.append(card);
        }
        const selectedId = new URLSearchParams(location.search).get("model");
        showDetail(rows.find(model => model.id === selectedId));
        if (selectedId && !rows.some(model => model.id === selectedId)) {
          empty(detail, "This model link is not in the catalog.", "Search the model name or identifier below.");
        }
      };
      wireFilters(root, form, render);
    } catch (_) {
      status.textContent = "The model catalog could not be loaded. Use the complete dataset or reference documents below.";
    }
  }

  async function library(root) {
    const status = root.querySelector("[data-library-status]");
    const results = root.querySelector("[data-library-results]");
    const form = root.querySelector("[data-library-filters]");
    try {
      const index = await getJSON("search/search_index.json");
      const pages = new Map();
      for (const doc of index.docs) {
        const location = doc.location.split("#")[0];
        if (!pages.has(location)) pages.set(location, {location, title: doc.title, text: ""});
        const page = pages.get(location);
        page.text += " " + doc.title + " " + doc.text;
        if (!doc.location.includes("#")) page.title = doc.title;
      }
      const rows = [...pages.values()].map(page => ({
        ...page,
        category: /(?:Architecture|Build-and-Development|Nextcore-Modules|Developer|Branching-and-Release)/i.test(page.location) ? "engineering" : /^(wiki\/|profiles\/|SETUP|EFI-OPTIMIZE)/i.test(page.location) ? "guides" :
          /^(|index\.html|progress\/|compatibility\/|library\/)$/i.test(page.location) ? "portal" : "engineering"
      })).sort((a, b) => a.title.localeCompare(b.title));
      const categoryLabels = {guides: "Guides & hardware", engineering: "Engineering & evidence", portal: "Project overview"};
      const render = () => {
        const query = form.elements.q.value;
        const category = form.elements.category.value;
        const filtered = rows.filter(row => (!category || row.category === category) && termsMatch(searchText(row.title + " " + row.text), query));
        status.textContent = filtered.length + " of " + rows.length + " published documents";
        results.replaceChildren();
        if (!filtered.length) empty(results, "No documents found.", "Try a broader term or choose all collections.");
        for (const row of filtered) {
          const card = el("article", undefined, "portal-library-card");
          card.append(el("span", categoryLabels[row.category], "portal-eyebrow"));
          const heading = el("h3"); heading.append(link(row.title, row.location || "./"));
          card.append(heading);
          // Search content is plain text; never inject indexed HTML.
          const text = row.text.replace(/\s+/g, " ").trim();
          card.append(el("p", text.length > 170 ? text.slice(0, 167) + "…" : text));
          results.append(card);
        }
      };
      wireFilters(root, form, render);
    } catch (_) {
      status.textContent = "The search index could not be loaded. Browse the collections below or use the site navigation.";
    }
  }

  async function progress(root) {
    try {
      const data = await getJSON("data/progress.json");
      const boundary = root.querySelector("[data-progress-boundary]");
      if (boundary && data.boundary?.label && data.boundary?.detail) {
        boundary.replaceChildren(badge("Current execution boundary"), el("h2", data.boundary.label), el("p", data.boundary.detail));
        if (data.boundary.evidence_url) boundary.append(link("Inspect the evidence →", data.boundary.evidence_url));
        if (data.updated_at) boundary.append(el("p", "Reviewed " + data.updated_at, "portal-small"));
      }
      const milestones = root.querySelector("[data-progress-milestones]");
      if (milestones && Array.isArray(data.milestones) && data.milestones.length) {
        milestones.replaceChildren();
        for (const [index, item] of data.milestones.entries()) {
          const card = el("article", undefined, "portal-step");
          card.append(el("span", String(index + 1).padStart(2, "0"), "portal-step-number"), badge(statusLabel(item.status || item.layer || "Evidence"), item.status === "validated-in-ovmf" ? "verified" : ""), el("h3", item.title), el("p", item.summary));
          if (item.evidence_url) card.append(link("Read the evidence →", item.evidence_url));
          milestones.append(card);
        }
      }
      const metrics = root.querySelector("[data-progress-metrics]");
      if (metrics && Array.isArray(data.metrics)) {
        metrics.replaceChildren();
        for (const item of data.metrics) {
          const metric = el("div", undefined, "portal-metric");
          metric.append(el("strong", item.value), el("span", item.label), el("p", item.detail));
          metrics.append(metric);
        }
      }
      const latest = root.querySelector("[data-progress-latest]");
      if (latest && Array.isArray(data.latest) && data.latest.length) {
        latest.replaceChildren();
        for (const item of data.latest) {
          const card = el("article", undefined, "portal-update");
          card.append(el("span", item.date, "portal-eyebrow"), el("h3", item.title), el("p", item.summary));
          if (item.url) card.append(link("Read the update →", item.url));
          latest.append(card);
        }
      }
    } catch (_) { /* Reviewed static evidence remains available when offline. */ }
  }

  function init() {
    const root = document.querySelector("[data-portal-page]");
    if (!root || root.dataset.portalReady) return;
    root.dataset.portalReady = "true";
    if (root.dataset.portalPage === "compatibility") models(root);
    if (root.dataset.portalPage === "library") library(root);
    if (["home", "progress"].includes(root.dataset.portalPage)) progress(root);
  }
  if (typeof document$ !== "undefined") document$.subscribe(init);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
