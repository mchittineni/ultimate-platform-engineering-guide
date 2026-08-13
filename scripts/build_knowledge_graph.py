#!/usr/bin/env python3
"""Build the knowledge graph over the question vault and render it as HTML.

The graph is derived, never hand-maintained: every question file is scanned for
platform-engineering concepts (control plane, golden path, policy as code, SLO,
tenancy model, ...), and two questions are linked when they share concepts that
are rare across the vault. Rarity weighting (IDF) is what keeps "kubernetes"
from linking everything to everything.

The same graph feeds two consumers:

* this script, which renders a self-contained HTML page for GitHub Pages;
* ``inject_wikilinks.py``, which writes the top edges of each node into the
  ``## Related Questions`` block of the question file itself.

Three interchangeable renderings ("prototypes") are available:

    constellation  force-directed map of the whole vault, dark console theme
    atlas          capability atlas - groups and topics laid out, links on demand
    pathway        difficulty lanes with a generated study route

Usage:
    python3 scripts/build_knowledge_graph.py --output docs/index.html
    python3 scripts/build_knowledge_graph.py --prototype atlas --output docs/atlas.html
    python3 scripts/build_knowledge_graph.py --prototype all --output-dir docs
    python3 scripts/build_knowledge_graph.py --json docs/graph.json
    python3 scripts/build_knowledge_graph.py --stats

Exit codes: 0 = built, 1 = nothing to build (empty vault).
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from lib_content import REPO_ROOT, Question, Topic, all_questions, load_topics, topic_meta
from validate_content import strip_code_blocks

DEFAULT_BASE_URL = "https://github.com/mchittineni/ultimate-platform-engineering-guide/blob/main/"

# Concepts the vault actually argues about. The key is the label shown in the UI;
# the values are the surface forms searched for in title and body. Matching is
# word-boundary based on lowercased prose with code fences stripped, so a concept
# named only inside a YAML sample does not count as the question being about it.
CONCEPTS: dict[str, tuple[str, ...]] = {
    "control plane": ("control plane",),
    "data plane": ("data plane",),
    "reconciliation": ("reconcil", "desired state", "drift detection"),
    "custom resources": ("custom resource", "crd"),
    "operators": ("operator pattern", "kubernetes operator", "controller-runtime", "custom controller"),
    "kubernetes": ("kubernetes", "k8s", "kubelet", "kubectl"),
    "namespaces": ("namespace",),
    "multi-tenancy": ("multi-tenan", "multitenan", "tenant"),
    "blast radius": ("blast radius",),
    "golden path": ("golden path", "paved road", "paved path"),
    "self-service": ("self-service", "self service"),
    "developer portal": ("developer portal", "backstage", "internal developer platform"),
    "service catalog": ("service catalog", "service catalogue", "software catalog"),
    "cognitive load": ("cognitive load",),
    "developer experience": ("developer experience", "developer productivity"),
    "DORA metrics": ("dora", "lead time for change", "change failure rate", "deployment frequency", "mttr"),
    "platform as a product": ("as a product", "platform product", "product manager", "product thinking"),
    "gitops": ("gitops", "argo cd", "argocd", "flux"),
    "pull vs push delivery": ("pull-based", "push-based", "pull model", "push model"),
    "ci/cd": ("ci/cd", "continuous delivery", "continuous integration", "build pipeline"),
    "progressive delivery": ("progressive delivery", "canary", "blue-green", "blue/green", "traffic shift"),
    "feature flags": ("feature flag", "feature toggle", "kill switch"),
    "rollback": ("rollback", "roll back", "revert the deploy"),
    "ephemeral environments": ("ephemeral environment", "preview environment", "on-demand environment"),
    "environment parity": ("environment parity", "production-like", "staging"),
    "infrastructure as code": ("infrastructure as code", "terraform", "pulumi", "opentofu"),
    "crossplane": ("crossplane", "composition", "claim"),
    "module design": ("terraform module", "reusable module", "golden module"),
    "state management": ("terraform state", "state file", "state locking"),
    "policy as code": ("policy as code", "open policy agent", "opa", "rego", "gatekeeper", "kyverno"),
    "admission control": ("admission controller", "validating webhook", "mutating webhook", "admission"),
    "rbac": ("rbac", "role-based access", "least privilege"),
    "secrets management": ("secret management", "external secrets", "sealed secrets", "hashicorp vault", "secrets manager"),
    "workload identity": ("workload identity", "irsa", "oidc", "federated identity", "service account token"),
    "supply chain security": ("supply chain", "sbom", "sigstore", "cosign", "provenance", "slsa", "image signing"),
    "images and registries": ("container image", "registry", "base image", "image scanning"),
    "network isolation": ("network policy", "service mesh", "mtls", "east-west traffic", "istio", "cilium"),
    "zero trust": ("zero trust",),
    "observability": ("observability", "opentelemetry", "telemetry", "instrumentation"),
    "metrics": ("prometheus", "metric cardinality", "time-series", "recording rule"),
    "tracing": ("distributed trace", "distributed tracing", "trace context", "span"),
    "logging": ("structured logging", "log aggregation", "log pipeline", "loki"),
    "slo and error budget": ("slo", "sli", "error budget", "service level objective"),
    "alerting": ("alert", "on-call", "paging", "pager"),
    "incident response": ("incident", "postmortem", "post-mortem", "blameless"),
    "resilience patterns": ("circuit breaker", "graceful degradation", "backpressure", "retry storm", "bulkhead"),
    "autoscaling": ("autoscal", "hpa", "karpenter", "cluster autoscaler", "scale to zero"),
    "capacity and quotas": ("resource quota", "limit range", "requests and limits", "bin pack", "noisy neighbour", "noisy neighbor"),
    "cost attribution": ("chargeback", "showback", "cost allocation", "cost attribution", "unit cost"),
    "finops": ("finops", "cost optimi", "committed use", "reserved instance", "savings plan", "spot instance"),
    "interface versioning": ("versioning", "semver", "semantic version", "api version", "breaking change"),
    "deprecation and migration": ("deprecat", "migrate consumers", "migration path", "sunset"),
    "abstraction design": ("abstraction", "escape hatch", "escapable", "leaky"),
    "platform api design": ("developer-facing api", "api design", "interface contract", "platform contract"),
    "architecture decision records": ("architecture decision record", "adr"),
    "build vs buy": ("build or buy", "build-versus-buy", "build vs buy", "buy versus build", "vendor"),
    "managed services": ("managed service", "managed offering", "fully managed"),
    "multi-cloud": ("multi-cloud", "multicloud", "hybrid cloud", "cloud portability", "lock-in"),
    "aws": ("aws", "amazon web services", "eks", "iam role", "cloudformation"),
    "azure": ("azure", "aks", "entra id", "bicep", "management group"),
    "gcp": ("gcp", "google cloud", "gke", "cloud run"),
    "landing zones": ("landing zone", "account vending", "organizational unit", "service control policy", "subscription vending"),
    "compliance": ("compliance", "soc 2", "pci", "iso 27001", "audit trail", "regulator"),
    "team topologies": ("team topolog", "stream-aligned", "enabling team", "operating model", "conway"),
    "adoption and mandates": ("adoption", "mandate", "voluntary migration", "incentive"),
    "support model": ("support model", "office hours", "escalation path", "service level agreement"),
    "datastores": ("postgres", "datastore", "dynamodb", "etcd", "relational database"),
    "caching": ("cache", "redis", "valkey"),
    "eventing": ("event-driven", "message queue", "kafka", "pub/sub", "webhook delivery"),
    "scorecards": ("scorecard", "maturity model", "compliance score"),
    "documentation": ("documentation", "runbook", "docs as code"),
    "interview signal": ("interview", "candidate", "hiring", "interviewer"),
}

# Concepts that describe the venue rather than the idea. They still colour the
# graph, but they are damped so a shared cloud provider alone is a weak link.
BROAD_CONCEPTS = frozenset({"kubernetes", "aws", "azure", "gcp", "interview signal", "documentation"})

TITLE_BOOST = 2.0          # a concept named in the title is what the question is about
CROSS_TOPIC_BOOST = 1.25   # links that cross a topic boundary teach more than in-topic ones
CROSS_GROUP_BOOST = 1.10
BROAD_DAMPING = 0.35
MIN_EDGE_SCORE = 1.2
MAX_EDGES_PER_NODE = 4

PROTOTYPES = ("constellation", "atlas", "pathway")

DIFFICULTY_ORDER = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}

# Distinct hues per topic group, readable on both the dark and the light shells.
GROUP_COLORS = {
    "Platform Foundations": "#4c9aff",
    "Platform Architecture": "#7b6cf6",
    "Kubernetes and Control Planes": "#00b8d9",
    "Delivery and Progressive Rollout": "#36b37e",
    "Security and Governance": "#ff5c8a",
    "Cloud Platforms": "#ffab00",
    "Reliability and Observability": "#ff7452",
    "Economics and Operating Model": "#c2a3ff",
    "Interview Prep": "#8fa3b8",
}
FALLBACK_COLOR = "#8fa3b8"


@dataclass(frozen=True)
class Edge:
    source: int
    target: int
    score: float
    concepts: tuple[str, ...]


# --------------------------------------------------------------------------- #
# Graph construction
# --------------------------------------------------------------------------- #

def _alias_pattern(alias: str) -> re.Pattern[str]:
    """Word-boundary match, tolerant of the hyphen/space variants in the prose."""
    escaped = re.escape(alias).replace(r"\ ", r"[\s-]+")
    return re.compile(rf"(?<![a-z0-9])(?:{escaped})", re.IGNORECASE)


_COMPILED = {label: tuple(_alias_pattern(a) for a in aliases) for label, aliases in CONCEPTS.items()}


def concepts_in(text: str) -> set[str]:
    return {label for label, patterns in _COMPILED.items() if any(p.search(text) for p in patterns)}


def question_concepts(q: Question) -> tuple[set[str], set[str]]:
    """Concepts found anywhere in the question, and the subset found in the title."""
    prose = strip_code_blocks(q.body)
    return concepts_in(f"{q.title}\n{prose}"), concepts_in(q.title)


def _idf(document_frequency: Counter, total: int) -> dict[str, float]:
    """Rare concepts carry the signal; a concept in every file carries none."""
    return {label: math.log(total / df) if df else 0.0 for label, df in document_frequency.items()}


def _pair_score(
    a: Question,
    b: Question,
    concepts: dict[int, set[str]],
    titles: dict[int, set[str]],
    idf: dict[str, float],
    groups: dict[str, str],
) -> tuple[float, tuple[str, ...]]:
    shared = concepts[a.id] & concepts[b.id]
    if not shared:
        return 0.0, ()

    score = 0.0
    for label in shared:
        weight = idf.get(label, 0.0)
        if label in BROAD_CONCEPTS:
            weight *= BROAD_DAMPING
        if label in titles[a.id] and label in titles[b.id]:
            weight *= TITLE_BOOST
        score += weight

    # Normalise by how much each question covers. Without this the longest answers
    # - which touch a bit of everything - become hubs that crowd out the precise,
    # single-idea links that are actually worth following.
    score /= math.sqrt(len(concepts[a.id]) * len(concepts[b.id])) / 4.0

    if a.topic_dir != b.topic_dir:
        score *= CROSS_TOPIC_BOOST
        if groups.get(a.topic_dir) != groups.get(b.topic_dir):
            score *= CROSS_GROUP_BOOST

    ranked = tuple(sorted(shared, key=lambda label: (-idf.get(label, 0.0), label)))
    return score, ranked


def build_graph(topics: list[Topic] | None = None) -> dict:
    """Derive nodes and edges from the vault. Deterministic for a given vault."""
    topics = topics if topics is not None else load_topics()
    questions = [q for q in all_questions(topics) if q.id > 0]
    meta = topic_meta()
    groups = {directory: entry.get("group", "Other") for directory, entry in meta.items()}
    topic_titles = {t.directory: t.title for t in topics}

    concepts: dict[int, set[str]] = {}
    titles: dict[int, set[str]] = {}
    document_frequency: Counter = Counter()
    for q in questions:
        found, in_title = question_concepts(q)
        concepts[q.id], titles[q.id] = found, in_title
        document_frequency.update(found)
    idf = _idf(document_frequency, len(questions) or 1)

    # Score every pair once, then keep each node's strongest few. Taking the union
    # (not the intersection) of both directions keeps a niche question connected
    # even when its neighbour has richer options.
    ranked: dict[int, list[tuple[float, int, tuple[str, ...]]]] = {q.id: [] for q in questions}
    for i, a in enumerate(questions):
        for b in questions[i + 1:]:
            score, shared = _pair_score(a, b, concepts, titles, idf, groups)
            if score < MIN_EDGE_SCORE:
                continue
            ranked[a.id].append((score, b.id, shared))
            ranked[b.id].append((score, a.id, shared))

    kept: dict[tuple[int, int], Edge] = {}
    for node_id, candidates in ranked.items():
        candidates.sort(key=lambda item: (-item[0], item[1]))
        for score, other, shared in candidates[:MAX_EDGES_PER_NODE]:
            key = (min(node_id, other), max(node_id, other))
            if key not in kept:
                kept[key] = Edge(key[0], key[1], round(score, 3), shared[:4])

    edges = sorted(kept.values(), key=lambda e: (-e.score, e.source, e.target))
    degree: Counter = Counter()
    for e in edges:
        degree[e.source] += 1
        degree[e.target] += 1

    nodes = [
        {
            "id": q.id,
            "title": q.title,
            "slug": q.slug,
            "topic": q.topic_dir,
            "topicTitle": topic_titles.get(q.topic_dir, q.topic_dir),
            "group": groups.get(q.topic_dir, "Other"),
            "difficulty": q.difficulty,
            "path": f"{q.topic_dir}/{q.filename}",
            "concepts": sorted(concepts[q.id], key=lambda c: (-idf.get(c, 0.0), c))[:6],
            "degree": degree[q.id],
        }
        for q in sorted(questions, key=lambda q: q.id)
    ]

    group_order: dict[str, int] = {}
    for directory, entry in meta.items():
        group_order.setdefault(entry.get("group", "Other"), int(entry.get("order", 0)))

    return {
        "meta": {
            "questions": len(nodes),
            "topics": len([t for t in topics if t.questions]),
            "edges": len(edges),
            "concepts": len(document_frequency),
        },
        "groups": [
            {"name": name, "color": GROUP_COLORS.get(name, FALLBACK_COLOR), "order": order}
            for name, order in sorted(group_order.items(), key=lambda kv: kv[1])
        ],
        "topics": [
            {
                "directory": t.directory,
                "title": t.title,
                "group": groups.get(t.directory, "Other"),
                "order": int(meta[t.directory].get("order", 0)),
                "description": meta[t.directory].get("description", ""),
                "count": len(t.questions),
            }
            for t in topics
            if t.questions
        ],
        "nodes": nodes,
        "edges": [{"s": e.source, "t": e.target, "w": e.score, "c": list(e.concepts)} for e in edges],
    }


def related_ids(graph: dict, node_id: int, limit: int = MAX_EDGES_PER_NODE) -> list[int]:
    """Strongest neighbours of a node, cross-topic first - the wikilink order."""
    node_topic = {n["id"]: n["topic"] for n in graph["nodes"]}
    scored: list[tuple[bool, float, int]] = []
    for edge in graph["edges"]:
        if edge["s"] == node_id:
            other = edge["t"]
        elif edge["t"] == node_id:
            other = edge["s"]
        else:
            continue
        same_topic = node_topic.get(other) == node_topic.get(node_id)
        scored.append((same_topic, -edge["w"], other))
    scored.sort()
    return [other for _, _, other in scored[:limit]]


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

BASE_CSS = """
*,*::before,*::after{box-sizing:border-box}
body{margin:0;font-family:ui-sans-serif,-apple-system,"Segoe UI",Inter,system-ui,sans-serif;
 -webkit-font-smoothing:antialiased}
a{color:inherit}
button{font:inherit;cursor:pointer}
input,select{font:inherit}
"""

# Every template below is assembled from repository content, but it is still
# untrusted-by-default text: it is escaped with esc() and materialised through
# DOMParser rather than assigned to innerHTML, so a stray angle bracket in a
# question title can never become markup.
DOM_HELPERS = """
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const nodesFrom = markup =>
  Array.from(new DOMParser().parseFromString('<body>' + markup, 'text/html').body.childNodes);
const setHTML = (el, markup) => el.replaceChildren(...nodesFrom(markup));
const addHTML = (el, markup) => el.append(...nodesFrom(markup));
const setSVG = (el, markup) => {
  const doc = new DOMParser().parseFromString(
    '<svg xmlns="http://www.w3.org/2000/svg">' + markup + '</svg>', 'image/svg+xml');
  el.replaceChildren(...Array.from(doc.documentElement.childNodes));
};
"""


def _page(title: str, description: str, css: str, body: str, script: str, graph: dict) -> str:
    payload = json.dumps(graph, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<style>{BASE_CSS}{css}</style>
</head>
<body>
{body}
<script id="graph-data" type="application/json">{payload}</script>
<script>
const GRAPH = JSON.parse(document.getElementById('graph-data').textContent);
GRAPH.byId = Object.fromEntries(GRAPH.nodes.map(n => [n.id, n]));
const BASE_URL = {json.dumps(_page.base_url)};
const urlFor = n => BASE_URL + n.path;
const colorOf = g => (GRAPH.groups.find(x => x.name === g) || {{}}).color || '{FALLBACK_COLOR}';
const neighboursOf = id => GRAPH.edges
  .filter(e => e.s === id || e.t === id)
  .sort((a, b) => b.w - a.w)
  .map(e => ({{ node: GRAPH.byId[e.s === id ? e.t : e.s], edge: e }}));
{DOM_HELPERS}
{script}
</script>
</body>
</html>
"""


_page.base_url = DEFAULT_BASE_URL  # type: ignore[attr-defined]


# ---- prototype 1: constellation -------------------------------------------- #

CONSTELLATION_CSS = """
:root{--bg:#0b1017;--panel:#121a24;--line:#1e2a38;--text:#e6edf5;--muted:#8195ad;--accent:#4c9aff}
body{background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{display:flex;align-items:center;gap:20px;padding:14px 22px;border-bottom:1px solid var(--line);
 background:linear-gradient(180deg,#101823,#0b1017)}
h1{margin:0;font-size:16px;letter-spacing:.02em;font-weight:650}
h1 span{color:var(--muted);font-weight:400}
.stats{display:flex;gap:16px;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.stats b{color:var(--text);font-weight:600}
.spacer{flex:1}
#search{background:#0d141d;border:1px solid var(--line);color:var(--text);border-radius:7px;
 padding:7px 11px;width:260px;outline:none}
#search:focus{border-color:var(--accent)}
select{background:#0d141d;border:1px solid var(--line);color:var(--text);border-radius:7px;padding:7px 9px}
main{flex:1;display:flex;min-height:0}
#stage{flex:1;position:relative}
canvas{display:block;width:100%;height:100%;cursor:grab}
#legend{position:absolute;left:16px;bottom:16px;display:flex;flex-direction:column;gap:5px;
 background:rgba(11,16,23,.82);border:1px solid var(--line);border-radius:10px;padding:11px 13px;
 backdrop-filter:blur(6px)}
.leg{display:flex;align-items:center;gap:8px;font-size:11.5px;color:var(--muted);
 background:none;border:0;padding:2px 0;text-align:left}
.leg.off{opacity:.32}
.dot{width:9px;height:9px;border-radius:50%;flex:none}
#tip{position:absolute;pointer-events:none;background:#0d141d;border:1px solid var(--line);border-radius:8px;
 padding:8px 10px;font-size:12.5px;max-width:300px;opacity:0;transition:opacity .12s;
 box-shadow:0 8px 26px rgba(0,0,0,.5)}
aside{width:352px;border-left:1px solid var(--line);background:var(--panel);padding:20px;overflow-y:auto}
aside .hint{color:var(--muted);font-size:13px;line-height:1.65}
.badge{display:inline-block;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;
 border:1px solid var(--line);border-radius:20px;padding:3px 9px;color:var(--muted);margin-right:6px}
aside h2{font-size:16.5px;line-height:1.4;margin:12px 0 10px}
a.open{display:inline-block;margin-top:4px;font-size:12.5px;color:var(--accent);text-decoration:none}
h3{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:22px 0 9px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11.5px;background:#0d141d;border:1px solid var(--line);border-radius:6px;padding:3px 8px;color:#b6c6d8}
.rel{display:block;width:100%;text-align:left;background:#0d141d;border:1px solid var(--line);
 border-radius:9px;padding:10px 12px;margin-bottom:7px;color:var(--text);font-size:13px;line-height:1.45}
.rel:hover{border-color:var(--accent)}
.rel small{display:block;color:var(--muted);font-size:11px;margin-top:4px}
"""

CONSTELLATION_BODY = """
<header>
  <h1>Platform Engineering <span>· knowledge constellation</span></h1>
  <div class="stats" id="stats"></div>
  <div class="spacer"></div>
  <input id="search" type="search" placeholder="Search questions and concepts…" aria-label="Search">
  <select id="difficulty" aria-label="Difficulty">
    <option value="">All difficulty</option><option>Beginner</option>
    <option>Intermediate</option><option>Advanced</option>
  </select>
</header>
<main>
  <div id="stage"><canvas id="canvas"></canvas><div id="legend"></div><div id="tip"></div></div>
  <aside id="panel"><p class="hint">Each dot is one interview question; each line is a concept two
    questions genuinely share. Drag a dot to rearrange, scroll to zoom, click to read its neighbourhood.</p></aside>
</main>
"""

CONSTELLATION_JS = """
const cv = document.getElementById('canvas'), ctx = cv.getContext('2d');
const stage = document.getElementById('stage'), tip = document.getElementById('tip');
const panel = document.getElementById('panel');
let W = 0, H = 0;
const dpr = Math.min(devicePixelRatio || 1, 2);

setHTML(document.getElementById('stats'),
  `<span><b>${GRAPH.meta.questions}</b> questions</span><span><b>${GRAPH.meta.topics}</b> topics</span>` +
  `<span><b>${GRAPH.meta.edges}</b> links</span>`);

// Phyllotaxis seed positions: deterministic, so every reload settles the same way.
const nodes = GRAPH.nodes.map((n, i) => {
  const a = i * 2.399963, r = 26 * Math.sqrt(i + 1);
  return { ...n, x: Math.cos(a) * r, y: Math.sin(a) * r, vx: 0, vy: 0 };
});
const index = Object.fromEntries(nodes.map(n => [n.id, n]));
const links = GRAPH.edges.map(e => ({ a: index[e.s], b: index[e.t], w: e.w, c: e.c }));
const radius = n => 4 + Math.min(5, (n.degree || 0) * 0.7);
const groupCentres = {};
GRAPH.groups.forEach((g, i) => {
  const a = (i / GRAPH.groups.length) * Math.PI * 2 - Math.PI / 2;
  groupCentres[g.name] = { x: Math.cos(a) * 340, y: Math.sin(a) * 250 };
});

const view = { x: 0, y: 0, k: 1 };
const hiddenGroups = new Set(), highlighted = new Set();
let alpha = 1, selected = null, hovered = null, dragging = null, query = '', difficulty = '';
let userMoved = false;   // auto-fit stops the moment the reader takes the wheel

const visible = n => !hiddenGroups.has(n.group) && (!difficulty || n.difficulty === difficulty);
const matches = n =>
  !query || (n.title + ' ' + n.topicTitle + ' ' + n.concepts.join(' ')).toLowerCase().includes(query);

function simulate() {
  alpha *= 0.992;
  for (const n of nodes) {
    for (const m of nodes) {
      if (m === n) continue;
      const dx = n.x - m.x, dy = n.y - m.y, d2 = dx * dx + dy * dy || 0.01;
      if (d2 > 40000) continue;
      const f = 520 / d2;
      n.vx += dx * f; n.vy += dy * f;
    }
  }
  for (const l of links) {
    const dx = l.b.x - l.a.x, dy = l.b.y - l.a.y;
    const d = Math.hypot(dx, dy) || 0.01, target = 90 - Math.min(35, l.w * 4);
    // Cross-group links pull weakly: they should bend the clusters towards each
    // other, not dissolve them into one cloud.
    const stiffness = l.a.group === l.b.group ? 0.02 : 0.005;
    const f = (d - target) * stiffness, ux = dx / d * f, uy = dy / d * f;
    l.a.vx += ux; l.a.vy += uy; l.b.vx -= ux; l.b.vy -= uy;
  }
  for (const n of nodes) {
    const c = groupCentres[n.group] || { x: 0, y: 0 };
    n.vx += (c.x - n.x) * 0.028 - n.x * 0.0008;
    n.vy += (c.y - n.y) * 0.028 - n.y * 0.0008;
    n.vx *= 0.86; n.vy *= 0.86;
    if (n !== dragging) { n.x += n.vx; n.y += n.vy; }
  }
}

function draw() {
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(W / 2 + view.x, H / 2 + view.y);
  ctx.scale(view.k, view.k);

  for (const l of links) {
    if (!visible(l.a) || !visible(l.b)) continue;
    const lit = highlighted.size && highlighted.has(l.a.id) && highlighted.has(l.b.id);
    ctx.strokeStyle = lit ? 'rgba(76,154,255,.6)' : 'rgba(125,158,196,.17)';
    ctx.lineWidth = lit ? 1.4 : 0.7;
    ctx.beginPath(); ctx.moveTo(l.a.x, l.a.y); ctx.lineTo(l.b.x, l.b.y); ctx.stroke();
  }
  ctx.font = '10px ui-sans-serif,system-ui';
  for (const n of nodes) {
    if (!visible(n)) continue;
    const dim = (highlighted.size && !highlighted.has(n.id)) || !matches(n);
    ctx.globalAlpha = dim ? 0.16 : 1;
    ctx.beginPath(); ctx.arc(n.x, n.y, radius(n), 0, 6.284);
    ctx.fillStyle = colorOf(n.group); ctx.fill();
    if (n === selected) { ctx.lineWidth = 2; ctx.strokeStyle = '#e6edf5'; ctx.stroke(); }
    if (!dim && (view.k > 1.5 || n === selected || n === hovered)) {
      ctx.globalAlpha = Math.min(1, view.k - 0.6);
      ctx.fillStyle = '#c4d3e4';
      ctx.fillText(n.title.length > 46 ? n.title.slice(0, 44) + '…' : n.title, n.x + radius(n) + 5, n.y + 3.5);
    }
    ctx.globalAlpha = 1;
  }
  ctx.restore();
}

// Keep the whole vault in frame while it settles, easing rather than snapping,
// and hand control over permanently as soon as the reader pans, drags or zooms.
function autofit() {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of nodes) {
    if (!visible(n)) continue;
    minX = Math.min(minX, n.x); maxX = Math.max(maxX, n.x);
    minY = Math.min(minY, n.y); maxY = Math.max(maxY, n.y);
  }
  if (!isFinite(minX)) return;
  const pad = 70;
  const k = Math.min(1.8, Math.max(0.3,
    Math.min((W - pad * 2) / (maxX - minX || 1), (H - pad * 2) / (maxY - minY || 1))));
  const cx = -(minX + maxX) / 2 * k, cy = -(minY + maxY) / 2 * k;
  view.k += (k - view.k) * 0.08;
  view.x += (cx - view.x) * 0.08;
  view.y += (cy - view.y) * 0.08;
}

function frame() {
  if (alpha > 0.005) simulate();
  if (!userMoved) autofit();
  draw();
  requestAnimationFrame(frame);
}

const toWorld = (px, py) => ({ x: (px - W / 2 - view.x) / view.k, y: (py - H / 2 - view.y) / view.k });

function pick(px, py) {
  const p = toWorld(px, py);
  let best = null, bestD = 14 / view.k;
  for (const n of nodes) {
    if (!visible(n)) continue;
    const d = Math.hypot(n.x - p.x, n.y - p.y);
    if (d < Math.max(bestD, radius(n) + 4)) { best = n; bestD = d; }
  }
  return best;
}

cv.addEventListener('pointermove', ev => {
  const r = cv.getBoundingClientRect(), px = ev.clientX - r.left, py = ev.clientY - r.top;
  if (dragging) {
    const p = toWorld(px, py);
    dragging.x = p.x; dragging.y = p.y;
    alpha = Math.max(alpha, 0.25);
    return;
  }
  if (ev.buttons === 1) {
    userMoved = true;
    view.x += ev.movementX; view.y += ev.movementY;
    return;
  }
  hovered = pick(px, py);
  cv.style.cursor = hovered ? 'pointer' : 'grab';
  if (!hovered) { tip.style.opacity = 0; return; }
  tip.style.opacity = 1;
  tip.style.left = Math.min(px + 14, r.width - 310) + 'px';
  tip.style.top = (py + 16) + 'px';
  setHTML(tip, `<b>${esc(hovered.title)}</b><br>` +
    `<span style="color:#8195ad">${esc(hovered.topicTitle)} · ${esc(hovered.difficulty)}</span>`);
});
cv.addEventListener('pointerdown', ev => {
  const r = cv.getBoundingClientRect();
  const hit = pick(ev.clientX - r.left, ev.clientY - r.top);
  if (hit) { dragging = hit; cv.setPointerCapture(ev.pointerId); }
});
cv.addEventListener('pointerup', () => {
  if (dragging) { select(dragging); dragging = null; }
});
cv.addEventListener('wheel', ev => {
  ev.preventDefault();
  userMoved = true;
  view.k = Math.min(4, Math.max(0.35, view.k * (ev.deltaY < 0 ? 1.12 : 0.89)));
}, { passive: false });

function select(n) {
  selected = n;
  highlighted.clear();
  highlighted.add(n.id);
  const near = neighboursOf(n.id);
  near.forEach(x => highlighted.add(x.node.id));
  setHTML(panel, `
    <span class="badge" style="border-color:${colorOf(n.group)};color:${colorOf(n.group)}">${esc(n.topicTitle)}</span>
    <span class="badge">${esc(n.difficulty)}</span>
    <h2>${esc(n.title)}</h2>
    <a class="open" href="${esc(urlFor(n))}" target="_blank" rel="noopener">Read the answer →</a>
    <h3>Concepts</h3>
    <div class="chips">${n.concepts.map(c => `<span class="chip">${esc(c)}</span>`).join('')}</div>
    <h3>Connected questions</h3>
    ${near.map(({ node, edge }) => `<button class="rel" data-id="${node.id}">${esc(node.title)}
      <small>${esc(node.topicTitle)} · shares ${esc(edge.c.join(', '))}</small></button>`).join('')
      || '<p class="hint">No strong links yet.</p>'}`);
  panel.querySelectorAll('.rel').forEach(b => b.onclick = () => {
    const t = index[+b.dataset.id];
    userMoved = true;
    view.k = Math.max(view.k, 1.6);
    view.x = -t.x * view.k; view.y = -t.y * view.k;
    select(t);
  });
}

const legend = document.getElementById('legend');
setHTML(legend, GRAPH.groups.map(g =>
  `<button class="leg" data-g="${esc(g.name)}"><span class="dot" style="background:${g.color}"></span>${esc(g.name)}</button>`
).join(''));
legend.querySelectorAll('.leg').forEach(b => b.onclick = () => {
  const g = b.dataset.g;
  hiddenGroups.has(g) ? hiddenGroups.delete(g) : hiddenGroups.add(g);
  b.classList.toggle('off');
});
document.getElementById('search').oninput = e => { query = e.target.value.trim().toLowerCase(); };
document.getElementById('difficulty').onchange = e => { difficulty = e.target.value; };

function resize() {
  const r = stage.getBoundingClientRect();
  W = r.width; H = r.height;
  cv.width = W * dpr; cv.height = H * dpr;
}
addEventListener('resize', resize);
resize();
frame();
"""


# ---- prototype 2: atlas ----------------------------------------------------- #

ATLAS_CSS = """
:root{--bg:#f6f8fb;--card:#fff;--line:#e2e8f0;--text:#101a26;--muted:#5c7086;--accent:#1f6feb}
body{background:var(--bg);color:var(--text)}
header{position:sticky;top:0;z-index:5;background:rgba(246,248,251,.93);backdrop-filter:blur(8px);
 border-bottom:1px solid var(--line);padding:16px 28px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}
h1{margin:0;font-size:17px;font-weight:680;letter-spacing:-.01em}
h1 span{color:var(--muted);font-weight:400}
.stats{font-size:12.5px;color:var(--muted)}
.spacer{flex:1}
input,select{border:1px solid var(--line);border-radius:8px;padding:8px 11px;background:#fff;color:var(--text);outline:none}
input:focus,select:focus{border-color:var(--accent)}
#search{width:280px}
.toggle{border:1px solid var(--line);background:#fff;border-radius:8px;padding:8px 12px;font-size:13px;color:var(--muted)}
.toggle.on{background:var(--accent);border-color:var(--accent);color:#fff}
#wrap{position:relative;padding:26px 28px 90px;max-width:1500px;margin:0 auto}
#wires{position:absolute;inset:0;pointer-events:none;z-index:1;overflow:visible}
.group{margin-bottom:34px;position:relative;z-index:2}
.group>h2{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
 margin:0 0 12px;display:flex;align-items:center;gap:9px}
.bar{width:26px;height:3px;border-radius:2px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
.topic{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:15px 16px;
 box-shadow:0 1px 2px rgba(16,26,38,.04)}
.topic h3{margin:0 0 3px;font-size:14.5px;font-weight:640}
.topic p{margin:0 0 11px;font-size:12px;color:var(--muted);line-height:1.5}
.q{display:block;width:100%;text-align:left;background:#fbfcfe;border:1px solid var(--line);border-left:3px solid;
 border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:12.8px;line-height:1.4;color:var(--text);
 transition:transform .12s,box-shadow .12s,opacity .12s}
.q:hover{transform:translateX(2px);box-shadow:0 3px 12px rgba(16,26,38,.08)}
.q.dim{opacity:.22}
.q.sel{background:#eef4ff;border-color:var(--accent);box-shadow:0 0 0 3px rgba(31,111,235,.13)}
.q.rel{background:#f4f9ff}
#drawer{position:fixed;right:0;bottom:0;top:0;width:390px;background:#fff;border-left:1px solid var(--line);
 padding:24px;overflow-y:auto;transform:translateX(100%);transition:transform .22s ease;z-index:10;
 box-shadow:-14px 0 40px rgba(16,26,38,.09)}
#drawer.open{transform:none}
#drawer h2{font-size:17px;line-height:1.4;margin:12px 0 8px}
.badge{display:inline-block;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--line);
 border-radius:20px;padding:3px 9px;color:var(--muted);margin-right:6px}
.close{position:absolute;top:16px;right:18px;border:0;background:none;font-size:19px;color:var(--muted)}
h4{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:20px 0 8px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11.5px;background:#f2f5f9;border-radius:6px;padding:3px 8px;color:#3d5266}
.rel-item{display:block;width:100%;text-align:left;background:#fbfcfe;border:1px solid var(--line);border-radius:9px;
 padding:10px 12px;margin-bottom:7px;font-size:13px;line-height:1.45;color:var(--text)}
.rel-item:hover{border-color:var(--accent)}
.rel-item small{display:block;color:var(--muted);font-size:11px;margin-top:4px}
.open{display:inline-block;margin-top:6px;color:var(--accent);text-decoration:none;font-size:13px}
"""

ATLAS_BODY = """
<header>
  <h1>Platform Capability Atlas <span>· every topic on one map</span></h1>
  <div class="stats" id="stats"></div>
  <div class="spacer"></div>
  <input id="search" type="search" placeholder="Filter by question or concept…" aria-label="Filter">
  <select id="difficulty" aria-label="Difficulty">
    <option value="">All difficulty</option><option>Beginner</option>
    <option>Intermediate</option><option>Advanced</option>
  </select>
  <button class="toggle" id="wires-toggle">Show all links</button>
</header>
<div id="wrap"><svg id="wires"></svg><div id="atlas"></div></div>
<aside id="drawer"><button class="close" id="close" aria-label="Close">×</button><div id="drawer-body"></div></aside>
"""

ATLAS_JS = """
const atlas = document.getElementById('atlas'), wires = document.getElementById('wires');
const wrap = document.getElementById('wrap');
const drawer = document.getElementById('drawer'), drawerBody = document.getElementById('drawer-body');
document.getElementById('stats').textContent =
  `${GRAPH.meta.questions} questions · ${GRAPH.meta.edges} concept links · ${GRAPH.meta.concepts} concepts tracked`;

const DIFF_TINT = { Beginner: .35, Intermediate: .65, Advanced: 1 };
let selected = null, showAll = false;

setHTML(atlas, GRAPH.groups.map(g => {
  const topics = GRAPH.topics.filter(t => t.group === g.name).sort((a, b) => a.order - b.order);
  if (!topics.length) return '';
  return `<section class="group">
    <h2><span class="bar" style="background:${g.color}"></span>${esc(g.name)}</h2>
    <div class="grid">${topics.map(t => `
      <article class="topic">
        <h3>${esc(t.title)}</h3><p>${esc(t.description)}</p>
        ${GRAPH.nodes.filter(n => n.topic === t.directory).map(n => `
          <button class="q" id="q${n.id}" data-id="${n.id}"
            style="border-left-color:${g.color};opacity:${0.55 + 0.45 * (DIFF_TINT[n.difficulty] || .6)}">
            ${esc(n.title)}</button>`).join('')}
      </article>`).join('')}</div>
  </section>`;
}).join(''));

const buttons = Array.from(atlas.querySelectorAll('.q'));
buttons.forEach(b => b.onclick = () => select(+b.dataset.id));

function centre(id) {
  const el = document.getElementById('q' + id);
  if (!el || el.style.display === 'none') return null;
  const r = el.getBoundingClientRect(), w = wrap.getBoundingClientRect();
  return { x: r.left - w.left + r.width / 2, y: r.top - w.top + r.height / 2 };
}

function curve(a, b, color, opacity, width) {
  const mx = (a.x + b.x) / 2, lift = Math.min(190, Math.abs(a.y - b.y) * 0.35 + 60);
  return `<path d="M${a.x},${a.y} C${mx},${a.y - lift} ${mx},${b.y + lift} ${b.x},${b.y}"
    fill="none" stroke="${color}" stroke-opacity="${opacity}" stroke-width="${width}" stroke-linecap="round"/>`;
}

function drawWires() {
  const box = wrap.getBoundingClientRect();
  wires.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
  wires.style.width = box.width + 'px';
  wires.style.height = box.height + 'px';
  let out = '';
  if (showAll) {
    for (const e of GRAPH.edges) {
      const a = centre(e.s), b = centre(e.t);
      if (a && b) out += curve(a, b, colorOf(GRAPH.byId[e.s].group), .13, 1);
    }
  }
  if (selected) {
    const a = centre(selected);
    for (const { node } of neighboursOf(selected)) {
      const b = centre(node.id);
      if (a && b) out += curve(a, b, colorOf(GRAPH.byId[selected].group), .8, 1.9);
    }
  }
  setSVG(wires, out);
}

function select(id) {
  selected = id;
  const n = GRAPH.byId[id], near = neighboursOf(id), relIds = new Set(near.map(x => x.node.id));
  buttons.forEach(b => {
    const bid = +b.dataset.id;
    b.classList.toggle('sel', bid === id);
    b.classList.toggle('rel', relIds.has(bid));
    b.classList.toggle('dim', bid !== id && !relIds.has(bid));
  });
  setHTML(drawerBody, `
    <span class="badge" style="border-color:${colorOf(n.group)};color:${colorOf(n.group)}">${esc(n.topicTitle)}</span>
    <span class="badge">${esc(n.difficulty)}</span>
    <h2>${esc(n.title)}</h2>
    <a class="open" href="${esc(urlFor(n))}" target="_blank" rel="noopener">Read the answer →</a>
    <h4>Concepts in this answer</h4>
    <div class="chips">${n.concepts.map(c => `<span class="chip">${esc(c)}</span>`).join('')}</div>
    <h4>Follow the thread</h4>
    ${near.map(({ node, edge }) => `<button class="rel-item" data-id="${node.id}">${esc(node.title)}
      <small>${esc(node.topicTitle)} · shares ${esc(edge.c.join(', '))}</small></button>`).join('')
      || '<p class="chip">No strong links yet.</p>'}`);
  drawerBody.querySelectorAll('.rel-item').forEach(b => b.onclick = () => {
    document.getElementById('q' + b.dataset.id).scrollIntoView({ behavior: 'smooth', block: 'center' });
    select(+b.dataset.id);
  });
  drawer.classList.add('open');
  drawWires();
}

document.getElementById('close').onclick = () => {
  selected = null;
  buttons.forEach(b => b.classList.remove('sel', 'rel', 'dim'));
  drawer.classList.remove('open');
  drawWires();
};

function applyFilter() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const d = document.getElementById('difficulty').value;
  buttons.forEach(b => {
    const n = GRAPH.byId[+b.dataset.id];
    const hit = (!q || (n.title + ' ' + n.concepts.join(' ')).toLowerCase().includes(q))
      && (!d || n.difficulty === d);
    b.style.display = hit ? '' : 'none';
  });
  drawWires();
}
document.getElementById('search').oninput = applyFilter;
document.getElementById('difficulty').onchange = applyFilter;
document.getElementById('wires-toggle').onclick = ev => {
  showAll = !showAll;
  ev.currentTarget.classList.toggle('on', showAll);
  drawWires();
};
addEventListener('resize', drawWires);
addEventListener('scroll', () => { if (selected || showAll) drawWires(); }, { passive: true });
drawWires();
"""


# ---- prototype 3: pathway --------------------------------------------------- #

PATHWAY_CSS = """
:root{--bg:#f7f9fc;--card:#fff;--line:#e3e9f0;--text:#0f1a26;--muted:#5d7288;--accent:#0d7d6b;--ink:#0f2231}
body{background:var(--bg);color:var(--text)}
header{background:var(--ink);color:#eaf2f8;padding:20px 28px;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
h1{margin:0;font-size:17px;font-weight:650}
h1 span{opacity:.6;font-weight:400}
header .stats{font-size:12.5px;opacity:.65}
.spacer{flex:1}
header select,header input{border:1px solid #2a4055;background:#16293a;color:#eaf2f8;border-radius:8px;
 padding:8px 11px;outline:none}
header input{width:250px}
main{display:flex;align-items:flex-start;gap:22px;padding:24px 28px 80px;max-width:1600px;margin:0 auto}
#lanes{flex:1;position:relative;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
#trace{position:absolute;inset:0;pointer-events:none;overflow:visible;z-index:0}
.lane{position:relative;z-index:1}
.lane>h2{position:sticky;top:0;background:var(--bg);margin:0 0 10px;padding:6px 0;font-size:12px;
 letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);z-index:2}
.lane>h2 b{color:var(--text);font-weight:600}
.card{display:block;width:100%;text-align:left;background:var(--card);border:1px solid var(--line);
 border-radius:11px;padding:11px 13px;margin-bottom:9px;font-size:13px;line-height:1.45;color:var(--text);
 border-left:4px solid;transition:box-shadow .12s,opacity .12s,transform .12s}
.card small{display:block;color:var(--muted);font-size:11px;margin-top:5px}
.card:hover{box-shadow:0 4px 16px rgba(15,26,38,.09);transform:translateY(-1px)}
.card.dim{opacity:.2}
.card.on{border-color:var(--accent);box-shadow:0 0 0 3px rgba(13,125,107,.15)}
.step{display:inline-flex;align-items:center;justify-content:center;width:19px;height:19px;border-radius:50%;
 background:var(--accent);color:#fff;font-size:11px;font-weight:650;margin-right:7px}
#route{width:370px;position:sticky;top:24px;background:var(--card);border:1px solid var(--line);border-radius:14px;
 padding:20px;max-height:calc(100vh - 60px);overflow-y:auto}
#route h2{margin:0 0 6px;font-size:15.5px;line-height:1.4}
#route p.hint{color:var(--muted);font-size:12.8px;line-height:1.6;margin:0}
.progress{height:5px;background:#eef2f7;border-radius:4px;margin:14px 0 16px;overflow:hidden}
.progress i{display:block;height:100%;background:var(--accent);width:0;transition:width .25s}
.step-row{display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--line)}
.step-row:last-of-type{border-bottom:0}
.step-row input{margin-top:3px;accent-color:var(--accent)}
.step-row label{font-size:13px;line-height:1.45;cursor:pointer}
.step-row.done label{text-decoration:line-through;color:var(--muted)}
.step-row small{display:block;color:var(--muted);font-size:11px;margin-top:3px}
.step-row a{color:var(--accent);text-decoration:none;font-size:11px}
.pill{display:inline-block;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);
 border:1px solid var(--line);border-radius:20px;padding:2px 8px;margin:0 5px 5px 0}
.sub{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:18px 0 4px}
#copy{margin-top:14px;border:1px solid var(--line);background:#fff;border-radius:8px;padding:8px 12px;
 font-size:12.5px;color:var(--muted);width:100%}
#copy:hover{border-color:var(--accent);color:var(--accent)}
"""

PATHWAY_BODY = """
<header>
  <h1>Study Pathways <span>· pick a destination, get a route</span></h1>
  <div class="stats" id="stats"></div>
  <div class="spacer"></div>
  <input id="search" type="search" placeholder="Find a question…" aria-label="Search">
  <select id="topic" aria-label="Topic"><option value="">All topics</option></select>
</header>
<main>
  <div id="lanes"><svg id="trace"></svg></div>
  <section id="route">
    <h2>No route yet</h2>
    <p class="hint">Pick any question as your destination. The route walks backwards through the
      concepts it leans on — easiest first — so you arrive at the hard question already holding the
      vocabulary it assumes.</p>
  </section>
</main>
"""

PATHWAY_JS = """
const lanes = document.getElementById('lanes'), trace = document.getElementById('trace');
const routeEl = document.getElementById('route');
const LEVELS = ['Beginner', 'Intermediate', 'Advanced'];
const rank = d => Math.max(0, LEVELS.indexOf(d));
document.getElementById('stats').textContent =
  `${GRAPH.meta.questions} questions · routes built from ${GRAPH.meta.edges} concept links`;

addHTML(lanes, LEVELS.map(level => {
  const inLane = GRAPH.nodes.filter(n => n.difficulty === level)
    .sort((a, b) => a.group.localeCompare(b.group) || a.id - b.id);
  return `<div class="lane"><h2><b>${level}</b> · ${inLane.length} questions</h2>
    ${inLane.map(n => `<button class="card" id="c${n.id}" data-id="${n.id}"
      style="border-left-color:${colorOf(n.group)}"><span class="label">${esc(n.title)}</span>
      <small>${esc(n.topicTitle)}</small></button>`).join('')}</div>`;
}).join(''));

const cards = Array.from(lanes.querySelectorAll('.card'));
cards.forEach(c => c.onclick = () => buildRoute(+c.dataset.id));

const topicSelect = document.getElementById('topic');
addHTML(topicSelect, GRAPH.topics.map(t =>
  `<option value="${esc(t.directory)}">${esc(t.title)}</option>`).join(''));

const adjacency = {};
for (const e of GRAPH.edges) {
  (adjacency[e.s] ||= []).push({ id: e.t, w: e.w, c: e.c });
  (adjacency[e.t] ||= []).push({ id: e.s, w: e.w, c: e.c });
}

// A route walks down from the destination through its strongest links, never
// stepping up in difficulty, then is read back in the order you should study it.
function buildRoute(targetId) {
  const target = GRAPH.byId[targetId];
  const path = [{ node: target, why: null }];
  const seen = new Set([targetId]);
  let cursor = target;
  while (path.length < 6) {
    const next = (adjacency[cursor.id] || [])
      .map(x => ({ ...x, node: GRAPH.byId[x.id] }))
      .filter(x => x.node && !seen.has(x.id) && rank(x.node.difficulty) <= rank(cursor.difficulty))
      .sort((a, b) => (rank(a.node.difficulty) - rank(b.node.difficulty)) || (b.w - a.w))[0];
    if (!next) break;
    seen.add(next.id);
    path.unshift({ node: next.node, why: next.c });
    cursor = next.node;
  }
  const extras = (adjacency[targetId] || [])
    .map(x => GRAPH.byId[x.id]).filter(n => n && !seen.has(n.id)).slice(0, 3);
  render(path, extras, target);
  paint(path.map(p => p.node.id));
}

function render(path, extras, target) {
  setHTML(routeEl, `
    <h2>Route to: ${esc(target.title)}</h2>
    <span class="pill">${path.length} stops</span><span class="pill">${esc(target.topicTitle)}</span>
    <span class="pill">${esc(target.difficulty)}</span>
    <div class="progress"><i id="bar"></i></div>
    ${path.map((p, i) => `
      <div class="step-row">
        <input type="checkbox" id="s${i}">
        <label for="s${i}">${i + 1}. ${esc(p.node.title)}
          <small>${esc(p.node.topicTitle)} · ${esc(p.node.difficulty)}${
            p.why ? ' · leads on via ' + esc(p.why.slice(0, 2).join(', ')) : ''}</small>
          <a href="${esc(urlFor(p.node))}" target="_blank" rel="noopener">open answer →</a>
        </label>
      </div>`).join('')}
    ${extras.length ? `<p class="sub">Round it out</p>` + extras.map(n =>
      `<div class="step-row"><label data-jump="${n.id}">${esc(n.title)}
        <small>${esc(n.topicTitle)} · ${esc(n.difficulty)}</small></label></div>`).join('') : ''}
    <button id="copy">Copy route as a checklist</button>`);

  const boxes = Array.from(routeEl.querySelectorAll('input[type=checkbox]'));
  const bar = document.getElementById('bar');
  boxes.forEach(b => b.onchange = () => {
    b.closest('.step-row').classList.toggle('done', b.checked);
    bar.style.width = (100 * boxes.filter(x => x.checked).length / boxes.length) + '%';
  });
  routeEl.querySelectorAll('[data-jump]').forEach(el => el.onclick = () => buildRoute(+el.dataset.jump));
  document.getElementById('copy').onclick = ev => {
    const text = path.map((p, i) =>
      `${i + 1}. [ ] ${p.node.title} (${p.node.difficulty}) - ${urlFor(p.node)}`).join('\\n');
    navigator.clipboard?.writeText(text);
    ev.currentTarget.textContent = 'Copied ✓';
  };
}

function paint(ids) {
  const set = new Set(ids);
  cards.forEach(c => {
    const id = +c.dataset.id, on = set.has(id);
    c.classList.toggle('on', on);
    c.classList.toggle('dim', !on);
    setHTML(c.querySelector('.label'),
      (on ? `<span class="step">${ids.indexOf(id) + 1}</span>` : '') + esc(GRAPH.byId[id].title));
  });
  drawTrace(ids);
}

function drawTrace(ids) {
  const box = lanes.getBoundingClientRect();
  trace.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
  trace.style.width = box.width + 'px';
  trace.style.height = box.height + 'px';
  const at = id => {
    const el = document.getElementById('c' + id);
    if (!el || el.style.display === 'none') return null;
    const r = el.getBoundingClientRect();
    return { x: r.left - box.left + r.width / 2, y: r.top - box.top + r.height / 2 };
  };
  let out = '';
  for (let i = 0; i < ids.length - 1; i++) {
    const a = at(ids[i]), b = at(ids[i + 1]);
    if (!a || !b) continue;
    const mx = (a.x + b.x) / 2;
    out += `<path d="M${a.x},${a.y} C${mx},${a.y} ${mx},${b.y} ${b.x},${b.y}" fill="none"
      stroke="#0d7d6b" stroke-opacity=".55" stroke-width="2.2" stroke-dasharray="6 5"/>`;
  }
  setSVG(trace, out);
}

const routeIds = () => cards.filter(c => c.classList.contains('on')).map(c => +c.dataset.id);

function applyFilter() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const t = topicSelect.value;
  cards.forEach(c => {
    const n = GRAPH.byId[+c.dataset.id];
    const hit = (!q || (n.title + ' ' + n.concepts.join(' ')).toLowerCase().includes(q))
      && (!t || n.topic === t);
    c.style.display = hit ? '' : 'none';
  });
  drawTrace(routeIds());
}
document.getElementById('search').oninput = applyFilter;
topicSelect.onchange = applyFilter;
addEventListener('resize', () => drawTrace(routeIds()));
addEventListener('scroll', () => drawTrace(routeIds()), { passive: true });
"""


RENDERERS = {
    "constellation": (
        "Platform Engineering Knowledge Constellation",
        "A force-directed map of every platform engineering interview question and the concepts that connect them.",
        CONSTELLATION_CSS,
        CONSTELLATION_BODY,
        CONSTELLATION_JS,
    ),
    "atlas": (
        "Platform Capability Atlas",
        "Every topic in the platform engineering guide laid out as a capability map, with concept links on demand.",
        ATLAS_CSS,
        ATLAS_BODY,
        ATLAS_JS,
    ),
    "pathway": (
        "Platform Engineering Study Pathways",
        "Pick a destination question and get a difficulty-ordered study route through the questions it leans on.",
        PATHWAY_CSS,
        PATHWAY_BODY,
        PATHWAY_JS,
    ),
}


def render(graph: dict, prototype: str) -> str:
    title, description, css, body, script = RENDERERS[prototype]
    return _page(title, description, css, body, script, graph)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def print_stats(graph: dict) -> None:
    meta = graph["meta"]
    print(f"Questions: {meta['questions']}")
    print(f"Topics:    {meta['topics']}")
    print(f"Concepts:  {meta['concepts']}")
    print(f"Edges:     {meta['edges']}")
    isolated = [n["title"] for n in graph["nodes"] if n["degree"] == 0]
    print(f"Isolated:  {len(isolated)}")
    for title in isolated:
        print(f"  - {title}")
    print("Most connected:")
    for n in sorted(graph["nodes"], key=lambda n: (-n["degree"], n["id"]))[:5]:
        print(f"  {n['degree']:>2}  {n['title']}")


def _relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--output", "-o", type=Path, help="write one HTML file here")
    parser.add_argument("--output-dir", type=Path, help="directory to write into (with --prototype all)")
    parser.add_argument(
        "--prototype", "-p", default="constellation", choices=(*PROTOTYPES, "all"),
        help="which rendering to build (default: constellation)",
    )
    parser.add_argument("--json", type=Path, help="also dump the raw graph as JSON")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="prefix for links to question files")
    parser.add_argument("--stats", action="store_true", help="print graph statistics and exit")
    args = parser.parse_args()

    _page.base_url = args.base_url.rstrip("/") + "/"  # type: ignore[attr-defined]

    graph = build_graph()
    if not graph["nodes"]:
        print("no questions found - nothing to build", file=sys.stderr)
        return 1

    if args.stats:
        print_stats(graph)
        return 0

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {_relative(args.json)}")

    targets: list[tuple[str, Path]] = []
    if args.prototype == "all":
        out_dir = args.output_dir or (args.output.parent if args.output else REPO_ROOT / "docs")
        targets = [(p, out_dir / f"{p}.html") for p in PROTOTYPES]
    elif args.output:
        targets = [(args.prototype, args.output)]
    elif args.output_dir:
        targets = [(args.prototype, args.output_dir / f"{args.prototype}.html")]
    elif not args.json:
        parser.error("give --output, --output-dir, --json, or --stats")

    for prototype, path in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(graph, prototype), encoding="utf-8")
        print(
            f"built {prototype:<14} -> {_relative(path)}  "
            f"({graph['meta']['questions']} nodes, {graph['meta']['edges']} edges)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
