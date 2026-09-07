# CausalFlow Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a 784-line, four-file Streamlit script into a tested `causalflow` package with a real domain model, four input formats, live filtering, no server-side state, and English + Spanish documentation.

**Architecture:** A single immutable domain object, `LagGraph`, sits between input and output. Every loader's only job is to produce a `LagGraph`; every renderer's only job is to consume one. This kills three of the four verified defects structurally rather than by patching: node registration is derived from edges so it cannot drift, the colour scale is computed from the data's own magnitude so it cannot mis-normalise, and the app holds graphs in `st.session_state` so no request touches the filesystem.

**Tech Stack:** Python 3.11+, Streamlit, gravis, NumPy, SciPy, pytest.

**Spec:** `https://claude.ai/code/artifact/db5ca26f-adce-4cd9-8c0b-d303df159599` — *Where Causal Graphs Goes Next*, the positioning review whose Gap 01/02/03 sections this plan implements. The findings it lists were reproduced against commit `759c082`; see "Findings this plan closes" below.

---

## Global Constraints

- **Python 3.11+.** Type syntax `X | None` is used throughout; do not add `from __future__ import annotations` workarounds for 3.9.
- **Node ids are 1-based integers.** `data/rename_nodes.json` and `data/brain_3d.json` are keyed `"1"`..`"360"`. Every loader must preserve 1-based ids. Never renumber.
- **`streamlit run visual.py` from `src/` must keep working.** The public deployment at `causal-graphs.streamlit.app` targets that path and the README documents it. `src/visual.py` survives as a three-line shim.
- **No module under `src/causalflow/` may open a file for writing.** Enforced by a test (Stage 7). Downloads are served from in-memory buffers.
- **All dependencies pinned with `==`.** The existing `setuptools<82` pin shows a break has already been hit once.
- **Spanish documentation is preserved, not replaced.** `README.md` becomes English, `README.es.md` keeps the Spanish. Both PDFs move to `docs/legacy/` and stay in the repo.
- **Edge marks use the PCMCI+ vocabulary verbatim:** `-->`, `o-o`, `x-x`, `<->`. Do not invent alternative spellings.
- **Commit after every task.** Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`).

## Findings this plan closes

| # | Defect | Location (commit `759c082`) | Closed by |
|---|---|---|---|
| 1 | `2^31` used as a sentinel where `2**31` was meant; Python `^` is XOR so the floor is `29` | `plot_methods.py:313` | Stage 2 |
| 2 | Lag-0 edge targets never registered as nodes | `plot_methods.py:87-100` | Stage 1 + Stage 4 |
| 3 | Server-side scratch file `src/data/graph.json` rewritten per upload (cross-user leak) | `plot_methods.py:231` | Stage 5 + Stage 6 |
| 4 | Bare `except` swallowing parse errors; `verify_node`/`verify_edge` always false | `plot_methods.py:163-186` | Stage 3 |
| 5 | `make_colorbar_graph` never called; `add_colorbar` uses unimported `realpath`; deps missing | `visual.py:112`, `plot_methods.py:354` | Stage 6 |
| 6 | `aux_graph.py` / `edges_color.py` imported by nothing; `color_edges` uses `pos_edges` unbound | `src/` | Stage 6 |
| 7 | Weights averaged across lags, destroying sign cancellation | `plot_methods.py:137-145` | Stage 1 + Stage 3 |
| 8 | `.mat` key prefixes hard-coded at the call site | `visual.py:73` | Stage 3 + Stage 5 |
| 9 | No significance or magnitude thresholding; 360 nodes render as a hairball | `visual.py` | Stage 5 |
| 10 | No caching; every widget interaction rebuilds all 360 nodes | `visual.py:73` | Stage 5 |

**Deferred to a follow-up plan (not in scope here):** custom SVG arrowheads per edge mark, the bundled atlas registry, the two-graph diff view, and extracting a pip-installable distribution. Each of those is a feature with its own spec; this plan delivers the foundation they need and stops.

## File Structure

**Created**

| Path | Responsibility |
|---|---|
| `src/causalflow/__init__.py` | Package exports: `LagGraph`, `LaggedEdge`, `EdgeMark`, `load_any` |
| `src/causalflow/model.py` | The domain object. `EdgeMark`, `LaggedEdge`, `LagGraph` + query/filter/subgraph |
| `src/causalflow/colors.py` | Symmetric diverging colour scale, CVD-safe endpoints |
| `src/causalflow/serialize.py` | Native v2 JSON read/write (the download format) |
| `src/causalflow/loaders/__init__.py` | Format dispatch: `load_any(file, **options)` |
| `src/causalflow/loaders/matlab.py` | `.mat` with configurable `linkLag`/`vallag` prefixes |
| `src/causalflow/loaders/legacy_json.py` | The old `{"graph":…, "digraph":…}` format |
| `src/causalflow/loaders/tigramite_npz.py` | Tigramite `.npz`: `graph`, `val_matrix`, `p_matrix`, `var_names` |
| `src/causalflow/loaders/edge_csv.py` | Long-form `source,target,lag,value[,pvalue][,mark]` |
| `src/causalflow/render.py` | `LagGraph` → gravis dict |
| `src/causalflow/app.py` | Streamlit UI, session state, filters |
| `tests/` | Mirrors the package, one test module per source module |
| `docs/input-formats.md` | The input contract for all five formats |
| `docs/user-manual.md`, `docs/manual-usuario.md` | Manual, EN + ES |
| `README.md`, `README.es.md`, `CHANGELOG.md` | |
| `.streamlit/config.toml`, `.github/workflows/tests.yml`, `pytest.ini`, `requirements-dev.txt` | |

**Modified**

| Path | Change |
|---|---|
| `src/visual.py` | Replaced by a shim that calls `causalflow.app.main()` |
| `requirements.txt` | Pinned; graphviz/pyvis/matplotlib dropped |
| `.gitignore` | Add `src/data/` |

**Deleted**

| Path | Reason |
|---|---|
| `src/plot_methods.py` | Superseded; behaviour distributed across `model`/`colors`/`loaders`/`render` |
| `src/aux_graph.py`, `src/edges_color.py` | Dead code, imported by nothing |
| `src/data/graph.json` (tracked!) | Server-side scratch file; `git rm` it |

---

# Stage 0 — Test harness

*Nothing can be safely refactored until there is somewhere to put a regression test. This stage adds no behaviour.*

### Task 0.1: pytest scaffolding and CI

**Files:**
- Create: `pytest.ini`, `requirements-dev.txt`, `tests/__init__.py`, `tests/conftest.py`, `.github/workflows/tests.yml`

**Interfaces:**
- Produces: pytest fixture `fixtures_dir` (a `pathlib.Path` to `tests/fixtures/`), importable by every later test module. `src/` is on `sys.path`, so tests import `from causalflow.model import LagGraph`.

- [ ] **Step 1: Create the pytest configuration**

`pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = src
addopts = -ra --strict-markers
filterwarnings =
    error::DeprecationWarning:causalflow.*
```

- [ ] **Step 2: Create the dev requirements**

`requirements-dev.txt`:

```
-r requirements.txt
pytest==9.1.1
```

- [ ] **Step 3: Create the shared fixture**

`tests/conftest.py`:

```python
from pathlib import Path

import pytest

TESTS_ROOT = Path(__file__).parent


@pytest.fixture
def fixtures_dir() -> Path:
    """Directory holding small hand-written input files used by loader tests."""
    return TESTS_ROOT / "fixtures"


@pytest.fixture
def repo_root() -> Path:
    """Repository root, for tests that read the shipped sample data."""
    return TESTS_ROOT.parent
```

Create `tests/__init__.py` as an empty file and `tests/fixtures/.gitkeep` as an empty file.

- [ ] **Step 4: Add a placeholder test so the harness is provably wired**

`tests/test_harness.py`:

```python
def test_src_is_importable():
    """pythonpath=src in pytest.ini must put the package on sys.path."""
    import causalflow  # noqa: F401


def test_fixtures_dir_exists(fixtures_dir):
    assert fixtures_dir.is_dir()
```

- [ ] **Step 5: Run it and watch the first test fail**

Run: `python3 -m pytest tests/test_harness.py -v`
Expected: `test_src_is_importable` FAILS with `ModuleNotFoundError: No module named 'causalflow'`; `test_fixtures_dir_exists` PASSES.

This is the correct state — the package does not exist yet. Task 1.1 makes it pass.

- [ ] **Step 6: Add the CI workflow**

`.github/workflows/tests.yml`:

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -r requirements-dev.txt
      - run: python -m pytest -v
```

- [ ] **Step 7: Commit**

```bash
git add pytest.ini requirements-dev.txt tests .github
git commit -m "test: add pytest harness and CI workflow"
```

---

### Task 0.2: Capture the shipped sample as a fixture

**Files:**
- Create: `tests/fixtures/legacy_graph.json`

**Interfaces:**
- Produces: a small legacy-format file that Task 3.3 asserts against. Keeping it tiny and hand-written (rather than reading `data/graph.json`, which is 131 KB) makes loader failures readable.

- [ ] **Step 1: Write the fixture**

This is the exact shape `plot_methods.get_json_data` consumed — four nodes, one contemporaneous edge, two lagged edges, one of which carries two lags in its label.

`tests/fixtures/legacy_graph.json`:

```json
{
  "graph": {
    "graph": {
      "directed": false,
      "metadata": {"node_color": "gray"},
      "nodes": {
        "1": {"metadata": {"label": "R_V1", "title": "R_V1"}},
        "2": {"metadata": {"label": "R_MST", "title": "R_MST"}}
      },
      "edges": [
        {"source": 1, "target": 2, "metadata": {"color": "#ff0000", "hover": "0.6596"}}
      ]
    }
  },
  "digraph": {
    "graph": {
      "directed": true,
      "metadata": {"node_color": "gray"},
      "nodes": {
        "1": {"metadata": {"label": "R_V1", "title": "R_V1"}},
        "3": {"metadata": {"label": "R_V6", "title": "R_V6"}},
        "4": {"metadata": {"label": "R_V2", "title": "R_V2"}}
      },
      "edges": [
        {"source": 1, "target": 3, "metadata": {"color": "#0000ff", "hover": "-0.6575", "label": "2"}},
        {"source": 3, "target": 4, "metadata": {"color": "#ff5353", "hover": "0.4210", "label": "1,3"}}
      ]
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/legacy_graph.json
git commit -m "test: add legacy graph format fixture"
```

---

# Stage 1 — Domain model

*One immutable object that every loader produces and every renderer consumes. Finding #2 (missing nodes) and finding #7 (lag averaging) are closed here by construction: nodes are derived from edges, and edges keep their own lag.*

### Task 1.1: `LagGraph`, `LaggedEdge`, `EdgeMark`

**Files:**
- Create: `src/causalflow/__init__.py`, `src/causalflow/model.py`, `tests/test_model.py`

**Interfaces:**
- Produces, relied on by every later task:
  - `EdgeMark` — str enum, members `DIRECTED="-->"`, `UNORIENTED="o-o"`, `CONFLICT="x-x"`, `BIDIRECTED="<->"`
  - `LaggedEdge(source: int, target: int, lag: int, value: float, mark: EdgeMark = EdgeMark.DIRECTED, pvalue: float | None = None)` — frozen dataclass
  - `LagGraph(labels: dict[int, str], edges: tuple[LaggedEdge, ...], positions: dict[int, tuple[float, float, float]] | None = None)` — frozen dataclass
  - `LagGraph.max_lag -> int`, `.node_ids -> tuple[int, ...]`, `.label_of(int) -> str`
  - `LagGraph.contemporaneous() -> LagGraph`, `.lagged() -> LagGraph`
  - `LagGraph.filtered(*, alpha=None, min_abs_value=None, lags=None) -> LagGraph`
  - `LagGraph.subgraph(node_ids) -> LagGraph`
  - `LagGraph.renamed(mapping) -> LagGraph`

- [ ] **Step 1: Write the failing tests**

`tests/test_model.py`:

```python
import pytest

from causalflow.model import EdgeMark, LaggedEdge, LagGraph


def make_graph() -> LagGraph:
    """1 --0--> 2, 1 --1--> 3, 3 --2--> 4. Only node 1 is labelled."""
    return LagGraph(
        labels={1: "R_V1"},
        edges=(
            LaggedEdge(1, 2, lag=0, value=0.6, mark=EdgeMark.UNORIENTED, pvalue=0.01),
            LaggedEdge(1, 3, lag=1, value=-0.4, pvalue=0.20),
            LaggedEdge(3, 4, lag=2, value=0.9, pvalue=0.001),
        ),
    )


def test_node_ids_include_every_edge_endpoint():
    """Regression for finding #2: edge targets were never registered as nodes."""
    graph = make_graph()
    assert graph.node_ids == (1, 2, 3, 4)


def test_label_falls_back_to_the_node_id():
    graph = make_graph()
    assert graph.label_of(1) == "R_V1"
    assert graph.label_of(4) == "4"


def test_max_lag():
    assert make_graph().max_lag == 2
    assert LagGraph(labels={}, edges=()).max_lag == 0


def test_contemporaneous_and_lagged_partition_the_edges():
    graph = make_graph()
    assert len(graph.contemporaneous().edges) == 1
    assert len(graph.lagged().edges) == 2
    assert all(e.lag == 0 for e in graph.contemporaneous().edges)
    assert all(e.lag > 0 for e in graph.lagged().edges)


def test_filtered_by_alpha_drops_insignificant_edges():
    kept = make_graph().filtered(alpha=0.05)
    assert {(e.source, e.target) for e in kept.edges} == {(1, 2), (3, 4)}


def test_filtered_by_alpha_keeps_edges_with_no_pvalue():
    """A format that carries no p-values must not vanish when alpha is set."""
    graph = LagGraph(labels={}, edges=(LaggedEdge(1, 2, lag=0, value=0.5),))
    assert len(graph.filtered(alpha=0.05).edges) == 1


def test_filtered_by_magnitude_uses_absolute_value():
    kept = make_graph().filtered(min_abs_value=0.5)
    assert {(e.source, e.target) for e in kept.edges} == {(1, 2), (3, 4)}


def test_filtered_by_lags():
    kept = make_graph().filtered(lags=[1, 2])
    assert {e.lag for e in kept.edges} == {1, 2}


def test_filtered_combines_criteria():
    kept = make_graph().filtered(alpha=0.05, min_abs_value=0.7, lags=[2])
    assert len(kept.edges) == 1
    assert kept.edges[0].target == 4


def test_subgraph_keeps_edges_with_both_endpoints_selected():
    kept = make_graph().subgraph([3, 4])
    assert {(e.source, e.target) for e in kept.edges} == {(3, 4)}


def test_renamed_accepts_string_keys_from_json():
    """rename_nodes.json has string keys; the model must not care."""
    renamed = make_graph().renamed({"1": "V1", 3: "V6"})
    assert renamed.label_of(1) == "V1"
    assert renamed.label_of(3) == "V6"


def test_graph_is_immutable():
    graph = make_graph()
    with pytest.raises(Exception):
        graph.edges = ()
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/test_model.py -v`
Expected: collection error — `ModuleNotFoundError: No module named 'causalflow'`.

- [ ] **Step 3: Write the model**

`src/causalflow/model.py`:

```python
"""The domain model for time-lagged causal graphs.

Every loader produces a ``LagGraph``; every renderer consumes one. Keeping node
identity derived from the edges means a graph can never claim an edge whose
endpoints it does not know about.
"""

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Mapping, Sequence


class EdgeMark(str, Enum):
    """Edge marks as emitted by PCMCI+ and LPCMCI.

    The distinction between these is the scientific content of a causal
    discovery run: whether an edge's direction was determined, left ambiguous
    by Markov equivalence, or actively conflicted.
    """

    DIRECTED = "-->"
    UNORIENTED = "o-o"
    CONFLICT = "x-x"
    BIDIRECTED = "<->"


@dataclass(frozen=True, slots=True)
class LaggedEdge:
    """One causal link at one time lag.

    ``lag`` 0 is contemporaneous. ``value`` is the signed test statistic
    (a correlation, a regression coefficient, a transfer entropy — the model
    does not assume a range).
    """

    source: int
    target: int
    lag: int
    value: float
    mark: EdgeMark = EdgeMark.DIRECTED
    pvalue: float | None = None


@dataclass(frozen=True)
class LagGraph:
    """A causal graph resolved over the lag axis.

    ``labels`` is a lookup table, not the node set: a node exists because an
    edge touches it. ``positions`` maps node id to (x, y, z) for the 3D view.
    """

    labels: Mapping[int, str]
    edges: tuple[LaggedEdge, ...]
    positions: Mapping[int, tuple[float, float, float]] | None = None

    @property
    def max_lag(self) -> int:
        return max((edge.lag for edge in self.edges), default=0)

    @property
    def lags(self) -> tuple[int, ...]:
        return tuple(sorted({edge.lag for edge in self.edges}))

    @property
    def node_ids(self) -> tuple[int, ...]:
        """Every node touched by an edge, ascending.

        Derived rather than stored: this is what makes it impossible to emit an
        edge whose endpoint has no node entry.
        """
        touched: set[int] = set()
        for edge in self.edges:
            touched.add(edge.source)
            touched.add(edge.target)
        return tuple(sorted(touched))

    def label_of(self, node_id: int) -> str:
        return self.labels.get(node_id, str(node_id))

    def contemporaneous(self) -> "LagGraph":
        return self.filtered(lags=[0])

    def lagged(self) -> "LagGraph":
        keep = tuple(edge for edge in self.edges if edge.lag > 0)
        return replace(self, edges=keep)

    def filtered(
        self,
        *,
        alpha: float | None = None,
        min_abs_value: float | None = None,
        lags: Sequence[int] | None = None,
    ) -> "LagGraph":
        """Return a copy keeping only edges that pass every supplied criterion.

        An edge with no p-value survives an ``alpha`` filter: formats such as
        ``.mat`` carry no significance information, and silently emptying the
        graph would be worse than showing it unfiltered.
        """
        wanted_lags = None if lags is None else set(lags)
        keep = tuple(
            edge
            for edge in self.edges
            if (alpha is None or edge.pvalue is None or edge.pvalue <= alpha)
            and (min_abs_value is None or abs(edge.value) >= min_abs_value)
            and (wanted_lags is None or edge.lag in wanted_lags)
        )
        return replace(self, edges=keep)

    def subgraph(self, node_ids: Iterable[int]) -> "LagGraph":
        """Keep only edges whose *both* endpoints are selected."""
        selected = set(node_ids)
        keep = tuple(
            edge
            for edge in self.edges
            if edge.source in selected and edge.target in selected
        )
        return replace(self, edges=keep)

    def renamed(self, mapping: Mapping) -> "LagGraph":
        """Apply a {node id: new label} mapping. Keys may be int or str."""
        merged = dict(self.labels)
        for key, label in mapping.items():
            merged[int(key)] = str(label)
        return replace(self, labels=merged)
```

`src/causalflow/__init__.py`:

```python
"""Interactive visualisation of time-lagged causal graphs."""

from causalflow.model import EdgeMark, LaggedEdge, LagGraph

__all__ = ["EdgeMark", "LaggedEdge", "LagGraph"]
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/test_model.py tests/test_harness.py -v`
Expected: all PASS, including `test_src_is_importable` from Task 0.1.

- [ ] **Step 5: Commit**

```bash
git add src/causalflow/__init__.py src/causalflow/model.py tests/test_model.py
git commit -m "feat: add LagGraph domain model with lag-aware edges"
```

---

# Stage 2 — Colour scale

*Finding #1 lives here. The fix is not to correct `2^31` to `2**31` — it is to delete the sentinel search entirely and normalise against the data's own largest magnitude, which is scale-invariant by construction.*

### Task 2.1: Symmetric diverging scale

**Files:**
- Create: `src/causalflow/colors.py`, `tests/test_colors.py`

**Interfaces:**
- Produces: `scale_max(values: Iterable[float]) -> float`, `color_for(value: float, vmax: float) -> str` (returns `#rrggbb`), `legend_stops(vmax: float, count: int = 9) -> list[tuple[float, str]]`

- [ ] **Step 1: Write the failing tests**

`tests/test_colors.py`:

```python
from causalflow.colors import color_for, legend_stops, scale_max


def test_scale_max_is_the_largest_magnitude():
    assert scale_max([0.2, -0.8, 0.5]) == 0.8
    assert scale_max([]) == 0.0


def test_scale_is_invariant_to_units():
    """Regression for finding #1.

    plot_methods.py:313 initialised its floor to ``2^31``, which is XOR and
    evaluates to 29 — so weights above ~29 normalised against the wrong
    minimum. Correlations in [-1, 1] worked by accident; regression
    coefficients and transfer entropies did not. The same data expressed in
    different units must produce the same picture.
    """
    small = [color_for(value, scale_max([0.5, 0.8])) for value in (0.5, 0.8)]
    large = [color_for(value, scale_max([50.0, 80.0])) for value in (50.0, 80.0)]
    assert small == large


def test_sign_selects_the_hue():
    vmax = 1.0
    assert color_for(1.0, vmax) == "#b2182b"
    assert color_for(-1.0, vmax) == "#2166ac"


def test_zero_is_neutral():
    assert color_for(0.0, 1.0) == "#f7f7f7"


def test_degenerate_scale_does_not_divide_by_zero():
    assert color_for(0.0, 0.0) == "#f7f7f7"


def test_values_beyond_the_scale_clamp():
    assert color_for(5.0, 1.0) == color_for(1.0, 1.0)
    assert color_for(-5.0, 1.0) == color_for(-1.0, 1.0)


def test_magnitude_is_monotonic():
    vmax = 1.0
    weak = color_for(0.2, vmax)
    strong = color_for(0.9, vmax)
    assert weak != strong
    assert int(strong[1:3], 16) > int(weak[1:3], 16) or int(strong[5:7], 16) < int(weak[5:7], 16)


def test_legend_stops_span_the_scale_symmetrically():
    stops = legend_stops(0.8, count=5)
    assert [value for value, _ in stops] == [-0.8, -0.4, 0.0, 0.4, 0.8]
    assert all(colour.startswith("#") and len(colour) == 7 for _, colour in stops)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/test_colors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.colors'`.

- [ ] **Step 3: Write the colour scale**

`src/causalflow/colors.py`:

```python
"""Signed diverging colour scale for edge weights.

Endpoints are the ColorBrewer RdBu extremes, which stay distinguishable under
the common forms of colour vision deficiency. The scale is symmetric about
zero and normalised against the largest magnitude in the data, so it behaves
identically whether the weights are correlations or transfer entropies.
"""

from typing import Iterable

RGB = tuple[int, int, int]

NEGATIVE: RGB = (33, 102, 172)   # #2166ac
NEUTRAL: RGB = (247, 247, 247)   # #f7f7f7
POSITIVE: RGB = (178, 24, 43)    # #b2182b


def scale_max(values: Iterable[float]) -> float:
    """The half-range of a symmetric scale: the largest magnitude present."""
    return max((abs(value) for value in values), default=0.0)


def color_for(value: float, vmax: float) -> str:
    """Map a signed value onto the scale, as ``#rrggbb``.

    ``vmax`` is the output of :func:`scale_max` for the whole edge set, so
    every edge in one graph is shaded against the same denominator.
    """
    if vmax <= 0:
        return _to_hex(NEUTRAL)
    fraction = max(-1.0, min(1.0, value / vmax))
    endpoint = POSITIVE if fraction >= 0 else NEGATIVE
    return _to_hex(_lerp(NEUTRAL, endpoint, abs(fraction)))


def legend_stops(vmax: float, count: int = 9) -> list[tuple[float, str]]:
    """Evenly spaced (value, colour) pairs from -vmax to +vmax, for a colourbar."""
    if count < 2:
        raise ValueError("a legend needs at least two stops")
    step = (2 * vmax) / (count - 1)
    values = [round(-vmax + step * index, 10) for index in range(count)]
    return [(value, color_for(value, vmax)) for value in values]


def _lerp(start: RGB, end: RGB, fraction: float) -> RGB:
    return tuple(  # type: ignore[return-value]
        round(a + (b - a) * fraction) for a, b in zip(start, end)
    )


def _to_hex(rgb: RGB) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/test_colors.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/causalflow/colors.py tests/test_colors.py
git commit -m "fix: replace XOR-sentinel colour scaling with a symmetric diverging scale"
```

---

# Stage 3 — Loaders

*Five formats, one output type. Each loader is independently testable and independently rejectable. Finding #4 (silent parse failures) and finding #8 (hard-coded prefixes) close here.*

### Task 3.1: Loader errors and the dispatch registry

**Files:**
- Create: `src/causalflow/loaders/__init__.py`, `tests/loaders/__init__.py`, `tests/loaders/test_registry.py`

**Interfaces:**
- Produces:
  - `class LoaderError(ValueError)` — every loader raises this, with a message written for the person who uploaded the file
  - `load_any(file, *, filename: str | None = None, link_prefix: str = "linkLag", value_prefix: str = "vallag") -> LagGraph`
  - `SUPPORTED_EXTENSIONS: tuple[str, ...]`
- Consumes (added by Tasks 3.2–3.5): `load_matlab`, `load_legacy_json`, `load_tigramite_npz`, `load_edge_csv`, `load_native_json`

- [ ] **Step 1: Write the failing tests**

`tests/loaders/test_registry.py`:

```python
import io

import pytest

from causalflow.loaders import SUPPORTED_EXTENSIONS, LoaderError, load_any


def test_unknown_extension_names_what_is_supported():
    with pytest.raises(LoaderError) as excinfo:
        load_any(io.BytesIO(b"whatever"), filename="results.xlsx")
    message = str(excinfo.value)
    assert ".xlsx" in message
    assert ".mat" in message and ".npz" in message and ".csv" in message


def test_filename_defaults_to_the_file_objects_own_name(fixtures_dir):
    """Streamlit's UploadedFile carries .name; callers should not have to pass it."""
    with open(fixtures_dir / "legacy_graph.json", "rb") as handle:
        graph = load_any(handle)
    assert graph.node_ids


def test_supported_extensions_are_advertised():
    assert set(SUPPORTED_EXTENSIONS) == {".mat", ".json", ".npz", ".csv"}
```

Create `tests/loaders/__init__.py` as an empty file.

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/loaders/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.loaders'`.

- [ ] **Step 3: Write the registry**

`src/causalflow/loaders/__init__.py`:

```python
"""Format dispatch.

Every loader takes a binary file object and returns a
:class:`~causalflow.model.LagGraph`, or raises :class:`LoaderError` with a
message meant for the person who uploaded the file.
"""

import json
from pathlib import Path

from causalflow.model import LagGraph


class LoaderError(ValueError):
    """A file could not be read. The message is shown directly to the user."""


from causalflow.loaders.edge_csv import load_edge_csv  # noqa: E402
from causalflow.loaders.legacy_json import load_legacy_json  # noqa: E402
from causalflow.loaders.matlab import load_matlab  # noqa: E402
from causalflow.loaders.tigramite_npz import load_tigramite_npz  # noqa: E402

SUPPORTED_EXTENSIONS = (".mat", ".json", ".npz", ".csv")


def load_any(
    file,
    *,
    filename: str | None = None,
    link_prefix: str = "linkLag",
    value_prefix: str = "vallag",
) -> LagGraph:
    """Read any supported file into a LagGraph, dispatching on extension."""
    name = filename or getattr(file, "name", "")
    extension = Path(str(name)).suffix.lower()

    if extension == ".mat":
        return load_matlab(file, link_prefix=link_prefix, value_prefix=value_prefix)
    if extension == ".npz":
        return load_tigramite_npz(file)
    if extension == ".csv":
        return load_edge_csv(file)
    if extension == ".json":
        return _load_json_dialect(file)

    supported = ", ".join(SUPPORTED_EXTENSIONS)
    raise LoaderError(
        f"Cannot read '{extension or name}'. Supported formats: {supported}."
    )


def _load_json_dialect(file) -> LagGraph:
    """Both JSON dialects share an extension, so pick by looking inside."""
    from causalflow.serialize import load_native_json

    raw = file.read()
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise LoaderError(f"Not valid JSON: {error.msg} at line {error.lineno}.") from error

    if not isinstance(payload, dict):
        raise LoaderError("Expected a JSON object at the top level.")
    if "graph" in payload and "digraph" in payload:
        return load_legacy_json(payload)
    if payload.get("format") == "causalflow/v2":
        return load_native_json(payload)
    raise LoaderError(
        "Unrecognised JSON. Expected either the legacy format (top-level "
        "'graph' and 'digraph' keys) or a CausalFlow v2 file "
        "(\"format\": \"causalflow/v2\")."
    )
```

- [ ] **Step 4: Run the tests and verify they fail on the missing loaders, not the registry**

Run: `python3 -m pytest tests/loaders/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.loaders.edge_csv'`. The registry is written; Tasks 3.2–3.5 fill it in. Do not commit a broken import — go straight to Task 3.2 and commit the registry together with the MATLAB loader.

---

### Task 3.2: MATLAB loader

**Files:**
- Create: `src/causalflow/loaders/matlab.py`, `tests/loaders/test_matlab.py`

**Interfaces:**
- Produces: `load_matlab(file, *, link_prefix: str = "linkLag", value_prefix: str = "vallag") -> LagGraph`

- [ ] **Step 1: Write the failing tests**

`tests/loaders/test_matlab.py`:

```python
import io

import numpy as np
import pytest
from scipy.io import savemat

from causalflow.loaders import LoaderError
from causalflow.loaders.matlab import load_matlab
from causalflow.model import EdgeMark


def write_mat(**arrays) -> io.BytesIO:
    buffer = io.BytesIO()
    savemat(buffer, arrays)
    buffer.seek(0)
    return buffer


def test_reads_one_edge_per_lag():
    lag0 = np.array([[0.0, 0.6, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    lag1 = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, -0.4], [0.0, 0.0, 0.0]])
    graph = load_matlab(
        write_mat(linkLag0=lag0, vallag0=lag0, linkLag1=lag1, vallag1=lag1)
    )
    assert {(e.source, e.target, e.lag, e.value) for e in graph.edges} == {
        (1, 2, 0, 0.6),
        (2, 3, 1, -0.4),
    }


def test_node_ids_are_one_based():
    """rename_nodes.json is keyed '1'..'360'; renumbering would break it."""
    lag0 = np.array([[0.0, 0.6], [0.0, 0.0]])
    graph = load_matlab(write_mat(linkLag0=lag0, vallag0=lag0))
    assert graph.node_ids == (1, 2)


def test_every_edge_endpoint_is_a_known_node():
    """Regression for finding #2, at the loader boundary."""
    lag0 = np.array([[0.0, 0.6, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    graph = load_matlab(write_mat(linkLag0=lag0, vallag0=lag0))
    known = set(graph.node_ids)
    assert all(e.source in known and e.target in known for e in graph.edges)


def test_lag_zero_is_unoriented_and_later_lags_are_directed():
    lag0 = np.array([[0.0, 0.6], [0.0, 0.0]])
    lag1 = np.array([[0.0, 0.3], [0.0, 0.0]])
    graph = load_matlab(
        write_mat(linkLag0=lag0, vallag0=lag0, linkLag1=lag1, vallag1=lag1)
    )
    marks = {edge.lag: edge.mark for edge in graph.edges}
    assert marks[0] is EdgeMark.UNORIENTED
    assert marks[1] is EdgeMark.DIRECTED


def test_prefixes_are_configurable():
    """Regression for finding #8: the prefixes were hard-coded at the call site."""
    lag0 = np.array([[0.0, 0.6], [0.0, 0.0]])
    graph = load_matlab(
        write_mat(adjacency0=lag0, weights0=lag0),
        link_prefix="adjacency",
        value_prefix="weights",
    )
    assert len(graph.edges) == 1


def test_missing_prefix_reports_what_the_file_actually_contains():
    lag0 = np.array([[0.0, 0.6], [0.0, 0.0]])
    with pytest.raises(LoaderError) as excinfo:
        load_matlab(write_mat(adjacency0=lag0, weights0=lag0))
    message = str(excinfo.value)
    assert "linkLag0" in message
    assert "adjacency0" in message


def test_non_square_matrix_is_rejected():
    with pytest.raises(LoaderError, match="square"):
        load_matlab(
            write_mat(linkLag0=np.zeros((2, 3)), vallag0=np.zeros((2, 3)))
        )


def test_self_loops_are_dropped():
    lag1 = np.array([[0.5, 0.0], [0.0, 0.0]])
    graph = load_matlab(write_mat(linkLag0=np.zeros((2, 2)), vallag0=np.zeros((2, 2)),
                                  linkLag1=lag1, vallag1=lag1))
    assert all(edge.source != edge.target for edge in graph.edges)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/loaders/test_matlab.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.loaders.matlab'`.

- [ ] **Step 3: Write the loader**

`src/causalflow/loaders/matlab.py`:

```python
"""Read the ``.mat`` layout this project started with.

A file holds one adjacency matrix and one value matrix per lag, named by a
shared prefix and a lag index: ``linkLag0``/``vallag0``, ``linkLag1``/``vallag1``,
and so on. The prefixes are arguments rather than constants because other
MATLAB pipelines name their variables differently.
"""

import numpy as np
from scipy.io import loadmat

from causalflow.model import EdgeMark, LaggedEdge, LagGraph


def load_matlab(
    file,
    *,
    link_prefix: str = "linkLag",
    value_prefix: str = "vallag",
) -> LagGraph:
    from causalflow.loaders import LoaderError

    try:
        data = loadmat(file)
    except Exception as error:  # scipy raises a wide range of types here
        raise LoaderError(f"Could not read the MATLAB file: {error}") from error

    if f"{link_prefix}0" not in data or f"{value_prefix}0" not in data:
        present = sorted(key for key in data if not key.startswith("__"))
        raise LoaderError(
            f"Expected variables named '{link_prefix}0' and '{value_prefix}0'. "
            f"This file contains: {', '.join(present) or '(nothing)'}. "
            "Set the variable prefixes in the sidebar to match your file."
        )

    edges: list[LaggedEdge] = []
    lag = 0
    while f"{link_prefix}{lag}" in data and f"{value_prefix}{lag}" in data:
        links = np.atleast_2d(data[f"{link_prefix}{lag}"])
        values = np.atleast_2d(data[f"{value_prefix}{lag}"])
        _check_shapes(links, values, lag, link_prefix, value_prefix)

        mark = EdgeMark.UNORIENTED if lag == 0 else EdgeMark.DIRECTED
        for row, column in zip(*np.nonzero(links)):
            if row == column:
                continue  # self-loops carry no information in this view
            edges.append(
                LaggedEdge(
                    source=int(row) + 1,   # 1-based: matches rename_nodes.json
                    target=int(column) + 1,
                    lag=lag,
                    value=float(values[row, column]),
                    mark=mark,
                )
            )
        lag += 1

    return LagGraph(labels={}, edges=tuple(edges))


def _check_shapes(links, values, lag: int, link_prefix: str, value_prefix: str) -> None:
    from causalflow.loaders import LoaderError

    if links.ndim != 2 or links.shape[0] != links.shape[1]:
        raise LoaderError(
            f"'{link_prefix}{lag}' must be a square matrix, got shape {links.shape}."
        )
    if values.shape != links.shape:
        raise LoaderError(
            f"'{value_prefix}{lag}' has shape {values.shape} but "
            f"'{link_prefix}{lag}' has shape {links.shape}; they must match."
        )
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/loaders/test_matlab.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/causalflow/loaders tests/loaders
git commit -m "feat: add MATLAB loader with configurable variable prefixes"
```

---

### Task 3.3: Legacy JSON loader

**Files:**
- Create: `src/causalflow/loaders/legacy_json.py`, `tests/loaders/test_legacy_json.py`

**Interfaces:**
- Produces: `load_legacy_json(payload: dict) -> LagGraph` — takes the already-parsed dict, because the registry sniffs the dialect before dispatching

- [ ] **Step 1: Write the failing tests**

`tests/loaders/test_legacy_json.py`:

```python
import json

import pytest

from causalflow.loaders import LoaderError, load_any
from causalflow.loaders.legacy_json import load_legacy_json
from causalflow.model import EdgeMark


def load_fixture(fixtures_dir):
    return json.loads((fixtures_dir / "legacy_graph.json").read_text())


def test_reads_contemporaneous_and_lagged_edges(fixtures_dir):
    graph = load_legacy_json(load_fixture(fixtures_dir))
    assert {(e.source, e.target, e.lag) for e in graph.edges} == {
        (1, 2, 0),
        (1, 3, 2),
        (3, 4, 1),
        (3, 4, 3),
    }


def test_multi_lag_label_expands_to_one_edge_per_lag(fixtures_dir):
    """The old format wrote '1,3' in a single edge's label."""
    graph = load_legacy_json(load_fixture(fixtures_dir))
    lags = sorted(e.lag for e in graph.edges if (e.source, e.target) == (3, 4))
    assert lags == [1, 3]


def test_values_come_from_the_hover_field(fixtures_dir):
    graph = load_legacy_json(load_fixture(fixtures_dir))
    contemporaneous = next(e for e in graph.edges if e.lag == 0)
    assert contemporaneous.value == pytest.approx(0.6596)


def test_labels_are_preserved(fixtures_dir):
    graph = load_legacy_json(load_fixture(fixtures_dir))
    assert graph.label_of(1) == "R_V1"
    assert graph.label_of(4) == "R_V2"


def test_lag_zero_edges_are_unoriented(fixtures_dir):
    graph = load_legacy_json(load_fixture(fixtures_dir))
    assert next(e for e in graph.edges if e.lag == 0).mark is EdgeMark.UNORIENTED


def test_malformed_edge_says_which_edge():
    """Regression for finding #4: a bare except printed to stdout and rendered blank."""
    payload = {
        "graph": {"graph": {"nodes": {}, "edges": [{"source": 1}]}},
        "digraph": {"graph": {"nodes": {}, "edges": []}},
    }
    with pytest.raises(LoaderError) as excinfo:
        load_legacy_json(payload)
    assert "target" in str(excinfo.value)


def test_registry_routes_legacy_files_by_content(fixtures_dir):
    with open(fixtures_dir / "legacy_graph.json", "rb") as handle:
        graph = load_any(handle)
    assert len(graph.edges) == 4


def test_shipped_sample_data_still_loads(repo_root):
    """The 131 KB file in data/ is what existing users have on disk."""
    with open(repo_root / "data" / "graph.json", "rb") as handle:
        graph = load_any(handle)
    assert graph.edges
    known = set(graph.node_ids)
    assert all(e.source in known and e.target in known for e in graph.edges)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/loaders/test_legacy_json.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.loaders.legacy_json'`.

- [ ] **Step 3: Write the loader**

`src/causalflow/loaders/legacy_json.py`:

```python
"""Read the ``{"graph": …, "digraph": …}`` format this project wrote before v2.

The old format is lossy: it stored one averaged weight per node pair together
with a comma-separated list of the lags that pair appeared at, so the
per-lag values cannot be recovered. Each listed lag gets an edge carrying the
shared averaged value. New exports use the v2 format, which keeps them apart.
"""

from causalflow.model import EdgeMark, LaggedEdge, LagGraph


def load_legacy_json(payload: dict) -> LagGraph:
    from causalflow.loaders import LoaderError

    labels: dict[int, str] = {}
    edges: list[LaggedEdge] = []

    for section, default_lag, mark in (
        ("graph", 0, EdgeMark.UNORIENTED),
        ("digraph", None, EdgeMark.DIRECTED),
    ):
        block = _require(payload, section, LoaderError)
        inner = _require(block, "graph", LoaderError, context=section)

        for node_id, node in (inner.get("nodes") or {}).items():
            label = (node.get("metadata") or {}).get("label")
            if label is not None:
                labels[int(node_id)] = str(label)

        for index, edge in enumerate(inner.get("edges") or []):
            edges.extend(
                _read_edge(edge, index, section, default_lag, mark, LoaderError)
            )

    return LagGraph(labels=labels, edges=tuple(edges))


def _read_edge(edge, index, section, default_lag, mark, LoaderError):
    for field in ("source", "target"):
        if field not in edge:
            raise LoaderError(
                f"Edge {index} in '{section}' is missing '{field}'. "
                "Every edge needs a 'source' and a 'target'."
            )

    metadata = edge.get("metadata") or {}
    try:
        value = float(metadata.get("hover", 0.0))
    except (TypeError, ValueError):
        raise LoaderError(
            f"Edge {index} in '{section}' has a non-numeric 'hover' value: "
            f"{metadata.get('hover')!r}."
        ) from None

    lags = _read_lags(metadata.get("label"), default_lag, index, section, LoaderError)
    return [
        LaggedEdge(
            source=int(edge["source"]),
            target=int(edge["target"]),
            lag=lag,
            value=value,
            mark=mark,
        )
        for lag in lags
    ]


def _read_lags(label, default_lag, index, section, LoaderError):
    if label is None:
        if default_lag is None:
            raise LoaderError(
                f"Edge {index} in '{section}' has no 'label', so its lag is unknown."
            )
        return [default_lag]
    try:
        return [int(part) for part in str(label).split(",") if part.strip()]
    except ValueError:
        raise LoaderError(
            f"Edge {index} in '{section}' has a lag label that is not a list of "
            f"integers: {label!r}."
        ) from None


def _require(payload, key, LoaderError, context=None):
    if key not in payload:
        where = f" inside '{context}'" if context else ""
        raise LoaderError(f"Missing required key '{key}'{where}.")
    return payload[key]
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/loaders -v`
Expected: all PASS, including `test_registry.py` from Task 3.1 — the registry's imports now resolve except for `edge_csv` and `tigramite_npz`. If those still fail, comment nothing out; complete Tasks 3.4 and 3.5 before re-running the full loader suite.

- [ ] **Step 5: Commit**

```bash
git add src/causalflow/loaders/legacy_json.py tests/loaders/test_legacy_json.py
git commit -m "feat: add legacy JSON loader with per-edge error messages"
```

---

### Task 3.4: Tigramite `.npz` loader

**Files:**
- Create: `src/causalflow/loaders/tigramite_npz.py`, `tests/loaders/test_tigramite_npz.py`

**Interfaces:**
- Produces: `load_tigramite_npz(file) -> LagGraph`

This is the single highest-leverage task in the plan: it is what lets a climate or AIOps user try the tool without converting anything.

- [ ] **Step 1: Write the failing tests**

`tests/loaders/test_tigramite_npz.py`:

```python
import io

import numpy as np
import pytest

from causalflow.loaders import LoaderError
from causalflow.loaders.tigramite_npz import load_tigramite_npz
from causalflow.model import EdgeMark


def write_npz(**arrays) -> io.BytesIO:
    buffer = io.BytesIO()
    np.savez(buffer, **arrays)
    buffer.seek(0)
    return buffer


def empty_graph(n: int, tau: int):
    return np.full((n, n, tau + 1), "", dtype="<U3")


def test_reads_a_lagged_directed_link():
    graph_array = empty_graph(3, 2)
    graph_array[0, 1, 1] = "-->"
    values = np.zeros((3, 3, 3))
    values[0, 1, 1] = 0.42
    graph = load_tigramite_npz(write_npz(graph=graph_array, val_matrix=values))
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert (edge.source, edge.target, edge.lag) == (1, 2, 1)
    assert edge.value == pytest.approx(0.42)
    assert edge.mark is EdgeMark.DIRECTED


def test_contemporaneous_mirror_is_not_double_counted():
    """graph[i,j,0]='-->' is mirrored by graph[j,i,0]='<--'; emit one edge."""
    graph_array = empty_graph(2, 0)
    graph_array[0, 1, 0] = "-->"
    graph_array[1, 0, 0] = "<--"
    graph = load_tigramite_npz(
        write_npz(graph=graph_array, val_matrix=np.full((2, 2, 1), 0.5))
    )
    assert len(graph.edges) == 1
    assert (graph.edges[0].source, graph.edges[0].target) == (1, 2)


def test_unoriented_and_conflicting_marks_survive():
    """Regression for Gap 01: these were flattened into 'undirected'."""
    graph_array = empty_graph(3, 0)
    graph_array[0, 1, 0] = graph_array[1, 0, 0] = "o-o"
    graph_array[1, 2, 0] = graph_array[2, 1, 0] = "x-x"
    graph = load_tigramite_npz(
        write_npz(graph=graph_array, val_matrix=np.full((3, 3, 1), 0.3))
    )
    assert {edge.mark for edge in graph.edges} == {EdgeMark.UNORIENTED, EdgeMark.CONFLICT}
    assert len(graph.edges) == 2  # each symmetric pair emitted once


def test_bidirected_latent_confounder_mark_survives():
    graph_array = empty_graph(2, 0)
    graph_array[0, 1, 0] = graph_array[1, 0, 0] = "<->"
    graph = load_tigramite_npz(
        write_npz(graph=graph_array, val_matrix=np.full((2, 2, 1), 0.3))
    )
    assert graph.edges[0].mark is EdgeMark.BIDIRECTED


def test_p_matrix_is_carried_onto_the_edges():
    graph_array = empty_graph(2, 1)
    graph_array[0, 1, 1] = "-->"
    p_values = np.ones((2, 2, 2))
    p_values[0, 1, 1] = 0.003
    graph = load_tigramite_npz(
        write_npz(graph=graph_array, val_matrix=np.full((2, 2, 2), 0.5), p_matrix=p_values)
    )
    assert graph.edges[0].pvalue == pytest.approx(0.003)


def test_missing_p_matrix_leaves_pvalues_unset():
    graph_array = empty_graph(2, 1)
    graph_array[0, 1, 1] = "-->"
    graph = load_tigramite_npz(
        write_npz(graph=graph_array, val_matrix=np.full((2, 2, 2), 0.5))
    )
    assert graph.edges[0].pvalue is None


def test_var_names_become_labels():
    graph_array = empty_graph(2, 1)
    graph_array[0, 1, 1] = "-->"
    graph = load_tigramite_npz(
        write_npz(
            graph=graph_array,
            val_matrix=np.full((2, 2, 2), 0.5),
            var_names=np.array(["temperature", "pressure"]),
        )
    )
    assert graph.label_of(1) == "temperature"
    assert graph.label_of(2) == "pressure"


def test_missing_graph_array_is_reported_with_the_keys_present():
    with pytest.raises(LoaderError) as excinfo:
        load_tigramite_npz(write_npz(val_matrix=np.zeros((2, 2, 1))))
    assert "graph" in str(excinfo.value)
    assert "val_matrix" in str(excinfo.value)


def test_mismatched_shapes_are_rejected():
    with pytest.raises(LoaderError, match="shape"):
        load_tigramite_npz(
            write_npz(graph=empty_graph(3, 1), val_matrix=np.zeros((2, 2, 2)))
        )


def test_unknown_mark_is_reported_not_silently_dropped():
    graph_array = empty_graph(2, 1)
    graph_array[0, 1, 1] = "?!?"
    with pytest.raises(LoaderError, match=r"\?!\?"):
        load_tigramite_npz(
            write_npz(graph=graph_array, val_matrix=np.full((2, 2, 2), 0.5))
        )
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/loaders/test_tigramite_npz.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.loaders.tigramite_npz'`.

- [ ] **Step 3: Write the loader**

`src/causalflow/loaders/tigramite_npz.py`:

```python
"""Read Tigramite (PCMCI / PCMCI+ / LPCMCI) results saved with ``np.savez``.

Expected arrays::

    graph       (N, N, tau_max+1) of strings — "", "-->", "<--", "o-o", "x-x", "<->"
    val_matrix  (N, N, tau_max+1) of floats  — the test statistic
    p_matrix    (N, N, tau_max+1) of floats  — optional
    var_names   (N,) of strings              — optional

``graph[i, j, tau] == "-->"`` is a link from i to j at lag tau. At lag 0 the
array is symmetric: an entry and its mirror describe one edge, so symmetric
marks are emitted once, and ``"<--"`` is skipped as the mirror of ``"-->"``.
"""

import numpy as np

from causalflow.model import EdgeMark, LaggedEdge, LagGraph

_MARKS = {
    "-->": EdgeMark.DIRECTED,
    "o-o": EdgeMark.UNORIENTED,
    "x-x": EdgeMark.CONFLICT,
    "<->": EdgeMark.BIDIRECTED,
}
_MIRROR = "<--"


def load_tigramite_npz(file) -> LagGraph:
    from causalflow.loaders import LoaderError

    try:
        archive = np.load(file, allow_pickle=False)
    except Exception as error:
        raise LoaderError(f"Could not read the .npz archive: {error}") from error

    present = list(archive.files)
    for required in ("graph", "val_matrix"):
        if required not in present:
            raise LoaderError(
                f"Missing required array '{required}'. This archive contains: "
                f"{', '.join(present) or '(nothing)'}. Save one with "
                "np.savez(path, graph=graph, val_matrix=val_matrix, "
                "p_matrix=p_matrix, var_names=var_names)."
            )

    marks = archive["graph"]
    values = archive["val_matrix"]
    p_values = archive["p_matrix"] if "p_matrix" in present else None

    if marks.ndim != 3 or marks.shape[0] != marks.shape[1]:
        raise LoaderError(
            f"'graph' must have shape (N, N, tau_max+1), got {marks.shape}."
        )
    if values.shape != marks.shape:
        raise LoaderError(
            f"'val_matrix' has shape {values.shape} but 'graph' has "
            f"{marks.shape}; they must match."
        )
    if p_values is not None and p_values.shape != marks.shape:
        raise LoaderError(
            f"'p_matrix' has shape {p_values.shape} but 'graph' has "
            f"{marks.shape}; they must match."
        )

    labels = _read_labels(archive, marks.shape[0], present)
    edges = _read_edges(marks, values, p_values, LoaderError)
    return LagGraph(labels=labels, edges=tuple(edges))


def _read_labels(archive, n_nodes: int, present: list[str]) -> dict[int, str]:
    if "var_names" not in present:
        return {}
    names = archive["var_names"]
    return {index + 1: str(name) for index, name in enumerate(names[:n_nodes])}


def _read_edges(marks, values, p_values, LoaderError) -> list[LaggedEdge]:
    edges: list[LaggedEdge] = []
    n_nodes, _, n_lags = marks.shape

    for lag in range(n_lags):
        for i in range(n_nodes):
            for j in range(n_nodes):
                symbol = str(marks[i, j, lag])
                if not symbol or symbol == _MIRROR:
                    continue
                if symbol not in _MARKS:
                    raise LoaderError(
                        f"Unrecognised edge mark {symbol!r} at graph[{i}, {j}, {lag}]. "
                        f"Expected one of: {', '.join(sorted(_MARKS))}, '<--', or ''."
                    )
                if i == j:
                    continue
                # A symmetric mark describes one edge written twice; keep i < j.
                if symbol != "-->" and i > j:
                    continue

                edges.append(
                    LaggedEdge(
                        source=i + 1,
                        target=j + 1,
                        lag=lag,
                        value=float(values[i, j, lag]),
                        mark=_MARKS[symbol],
                        pvalue=None if p_values is None else float(p_values[i, j, lag]),
                    )
                )
    return edges
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/loaders/test_tigramite_npz.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/causalflow/loaders/tigramite_npz.py tests/loaders/test_tigramite_npz.py
git commit -m "feat: read Tigramite .npz results with full PCMCI+ edge marks"
```

---

### Task 3.5: Edge-list CSV loader and native v2 serialization

**Files:**
- Create: `src/causalflow/loaders/edge_csv.py`, `src/causalflow/serialize.py`, `tests/loaders/test_edge_csv.py`, `tests/test_serialize.py`

**Interfaces:**
- Produces:
  - `load_edge_csv(file) -> LagGraph`
  - `dump_native_json(graph: LagGraph) -> bytes` — the download payload
  - `load_native_json(payload: dict) -> LagGraph`

- [ ] **Step 1: Write the failing tests**

`tests/loaders/test_edge_csv.py`:

```python
import io

import pytest

from causalflow.loaders import LoaderError
from causalflow.loaders.edge_csv import load_edge_csv
from causalflow.model import EdgeMark


def csv_file(text: str) -> io.BytesIO:
    return io.BytesIO(text.encode("utf-8"))


def test_reads_the_minimal_column_set():
    graph = load_edge_csv(csv_file("source,target,lag,value\n1,2,0,0.6\n2,3,1,-0.4\n"))
    assert {(e.source, e.target, e.lag, e.value) for e in graph.edges} == {
        (1, 2, 0, 0.6),
        (2, 3, 1, -0.4),
    }


def test_optional_pvalue_and_mark_columns_are_used():
    graph = load_edge_csv(
        csv_file("source,target,lag,value,pvalue,mark\n1,2,0,0.6,0.01,o-o\n")
    )
    edge = graph.edges[0]
    assert edge.pvalue == pytest.approx(0.01)
    assert edge.mark is EdgeMark.UNORIENTED


def test_string_node_names_become_labels():
    graph = load_edge_csv(csv_file("source,target,lag,value\ntemp,pressure,1,0.5\n"))
    assert set(graph.labels.values()) == {"temp", "pressure"}
    assert len(graph.edges) == 1


def test_missing_column_names_the_column_and_what_was_found():
    with pytest.raises(LoaderError) as excinfo:
        load_edge_csv(csv_file("source,target,value\n1,2,0.6\n"))
    message = str(excinfo.value)
    assert "lag" in message and "source" in message


def test_bad_row_reports_the_line_number():
    with pytest.raises(LoaderError, match="line 3"):
        load_edge_csv(csv_file("source,target,lag,value\n1,2,0,0.6\n1,2,x,0.6\n"))


def test_unknown_mark_is_rejected():
    with pytest.raises(LoaderError, match="mark"):
        load_edge_csv(csv_file("source,target,lag,value,mark\n1,2,0,0.6,==>\n"))


def test_empty_file_is_reported():
    with pytest.raises(LoaderError, match="empty"):
        load_edge_csv(csv_file(""))
```

`tests/test_serialize.py`:

```python
import json

from causalflow.loaders import load_any
from causalflow.model import EdgeMark, LaggedEdge, LagGraph
from causalflow.serialize import dump_native_json, load_native_json


def sample() -> LagGraph:
    return LagGraph(
        labels={1: "R_V1", 2: "R_MST"},
        edges=(
            LaggedEdge(1, 2, lag=0, value=0.6, mark=EdgeMark.UNORIENTED, pvalue=0.01),
            LaggedEdge(2, 1, lag=2, value=-0.4, mark=EdgeMark.DIRECTED),
        ),
        positions={1: (1.0, 2.0, 3.0)},
    )


def test_round_trip_preserves_everything():
    original = sample()
    restored = load_native_json(json.loads(dump_native_json(original)))
    assert restored.edges == original.edges
    assert dict(restored.labels) == dict(original.labels)
    assert dict(restored.positions) == dict(original.positions)


def test_payload_declares_its_format():
    payload = json.loads(dump_native_json(sample()))
    assert payload["format"] == "causalflow/v2"


def test_per_lag_values_are_not_averaged():
    """Regression for finding #7: the old format collapsed lags into one weight."""
    graph = LagGraph(
        labels={},
        edges=(
            LaggedEdge(1, 2, lag=1, value=0.7),
            LaggedEdge(1, 2, lag=3, value=-0.6),
        ),
    )
    restored = load_native_json(json.loads(dump_native_json(graph)))
    assert sorted(edge.value for edge in restored.edges) == [-0.6, 0.7]


def test_registry_routes_v2_files_by_their_format_key(tmp_path):
    path = tmp_path / "export.json"
    path.write_bytes(dump_native_json(sample()))
    with open(path, "rb") as handle:
        assert len(load_any(handle).edges) == 2
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/loaders/test_edge_csv.py tests/test_serialize.py -v`
Expected: FAIL with `ModuleNotFoundError` for `causalflow.loaders.edge_csv` and `causalflow.serialize`.

- [ ] **Step 3: Write the CSV loader**

`src/causalflow/loaders/edge_csv.py`:

```python
"""Read a long-form edge list.

Required columns: ``source``, ``target``, ``lag``, ``value``.
Optional columns: ``pvalue``, ``mark``.

Node columns may hold integers or names; names are assigned stable ids in
first-seen order and kept as labels. This is the fallback format for any
pipeline the dedicated loaders do not cover.
"""

import csv
import io

from causalflow.model import EdgeMark, LaggedEdge, LagGraph

REQUIRED_COLUMNS = ("source", "target", "lag", "value")


def load_edge_csv(file) -> LagGraph:
    from causalflow.loaders import LoaderError

    raw = file.read()
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    if not text.strip():
        raise LoaderError("The CSV file is empty.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise LoaderError("The CSV file has no header row.")

    columns = [name.strip() for name in reader.fieldnames]
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise LoaderError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Found: {', '.join(columns)}. Expected a header row with at least "
            f"{', '.join(REQUIRED_COLUMNS)}."
        )

    ids: dict[str, int] = {}
    labels: dict[int, str] = {}
    edges: list[LaggedEdge] = []

    for line_number, row in enumerate(reader, start=2):
        edges.append(_read_row(row, line_number, ids, labels, LoaderError))

    return LagGraph(labels=labels, edges=tuple(edges))


def _read_row(row, line_number, ids, labels, LoaderError) -> LaggedEdge:
    try:
        lag = int(str(row["lag"]).strip())
        value = float(str(row["value"]).strip())
    except (TypeError, ValueError) as error:
        raise LoaderError(f"Could not read line {line_number}: {error}.") from error

    mark = EdgeMark.UNORIENTED if lag == 0 else EdgeMark.DIRECTED
    raw_mark = (row.get("mark") or "").strip()
    if raw_mark:
        try:
            mark = EdgeMark(raw_mark)
        except ValueError:
            allowed = ", ".join(member.value for member in EdgeMark)
            raise LoaderError(
                f"Unknown mark {raw_mark!r} on line {line_number}. "
                f"Expected one of: {allowed}."
            ) from None

    pvalue = None
    raw_pvalue = (row.get("pvalue") or "").strip()
    if raw_pvalue:
        try:
            pvalue = float(raw_pvalue)
        except ValueError:
            raise LoaderError(
                f"Could not read 'pvalue' on line {line_number}: {raw_pvalue!r}."
            ) from None

    return LaggedEdge(
        source=_node_id(row["source"], ids, labels),
        target=_node_id(row["target"], ids, labels),
        lag=lag,
        value=value,
        mark=mark,
        pvalue=pvalue,
    )


def _node_id(raw, ids: dict[str, int], labels: dict[int, str]) -> int:
    key = str(raw).strip()
    if key not in ids:
        if key.isdigit():
            ids[key] = int(key)
        else:
            ids[key] = max(ids.values(), default=0) + 1
            labels[ids[key]] = key
    return ids[key]
```

- [ ] **Step 4: Write the v2 serializer**

`src/causalflow/serialize.py`:

```python
"""The CausalFlow v2 JSON format — what the Download button produces.

Unlike the legacy format it keeps one record per (source, target, lag), so
values at different lags are never averaged together, and it carries p-values
and edge marks.
"""

import json

from causalflow.model import EdgeMark, LaggedEdge, LagGraph

FORMAT = "causalflow/v2"


def dump_native_json(graph: LagGraph) -> bytes:
    payload = {
        "format": FORMAT,
        "labels": {str(node_id): label for node_id, label in graph.labels.items()},
        "positions": {
            str(node_id): list(position)
            for node_id, position in (graph.positions or {}).items()
        },
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "lag": edge.lag,
                "value": edge.value,
                "mark": edge.mark.value,
                "pvalue": edge.pvalue,
            }
            for edge in graph.edges
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def load_native_json(payload: dict) -> LagGraph:
    from causalflow.loaders import LoaderError

    edges = []
    for index, edge in enumerate(payload.get("edges") or []):
        try:
            edges.append(
                LaggedEdge(
                    source=int(edge["source"]),
                    target=int(edge["target"]),
                    lag=int(edge["lag"]),
                    value=float(edge["value"]),
                    mark=EdgeMark(edge.get("mark", EdgeMark.DIRECTED.value)),
                    pvalue=None if edge.get("pvalue") is None else float(edge["pvalue"]),
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise LoaderError(f"Edge {index} is malformed: {error}.") from error

    labels = {int(k): str(v) for k, v in (payload.get("labels") or {}).items()}
    positions = {
        int(k): tuple(float(component) for component in v)
        for k, v in (payload.get("positions") or {}).items()
    }
    return LagGraph(labels=labels, edges=tuple(edges), positions=positions or None)
```

- [ ] **Step 5: Run the whole loader suite and verify it passes**

Run: `python3 -m pytest tests/loaders tests/test_serialize.py -v`
Expected: all PASS, including `tests/loaders/test_registry.py` — every import in the registry now resolves.

- [ ] **Step 6: Commit**

```bash
git add src/causalflow/loaders/edge_csv.py src/causalflow/serialize.py tests/loaders/test_edge_csv.py tests/test_serialize.py
git commit -m "feat: add edge-list CSV loader and lossless v2 export format"
```

---

# Stage 4 — Rendering

*One function converts a `LagGraph` into the dict gravis expects. Because it reads `graph.node_ids`, finding #2 cannot recur here.*

### Task 4.1: `LagGraph` → gravis

**Files:**
- Create: `src/causalflow/render.py`, `tests/test_render.py`

**Interfaces:**
- Produces: `to_gravis(graph: LagGraph, *, directed: bool, use_positions: bool = False) -> dict`

- [ ] **Step 1: Write the failing tests**

`tests/test_render.py`:

```python
import pytest

from causalflow.model import EdgeMark, LaggedEdge, LagGraph
from causalflow.render import to_gravis


def sample() -> LagGraph:
    return LagGraph(
        labels={1: "R_V1"},
        edges=(
            LaggedEdge(1, 2, lag=0, value=0.6, mark=EdgeMark.UNORIENTED, pvalue=0.01),
            LaggedEdge(2, 3, lag=2, value=-0.9, mark=EdgeMark.DIRECTED),
        ),
        positions={1: (1.0, 2.0, 3.0), 2: (4.0, 5.0, 6.0), 3: (7.0, 8.0, 9.0)},
    )


def test_every_edge_endpoint_has_a_node_entry():
    """Regression for finding #2, at the render boundary — the bug's actual home."""
    rendered = to_gravis(sample(), directed=True)
    nodes = set(rendered["graph"]["nodes"])
    for edge in rendered["graph"]["edges"]:
        assert edge["source"] in nodes
        assert edge["target"] in nodes


def test_directed_flag_is_carried_through():
    assert to_gravis(sample(), directed=True)["graph"]["directed"] is True
    assert to_gravis(sample(), directed=False)["graph"]["directed"] is False


def test_unlabelled_nodes_fall_back_to_their_id():
    rendered = to_gravis(sample(), directed=True)
    labels = {
        node_id: node["metadata"]["label"]
        for node_id, node in rendered["graph"]["nodes"].items()
    }
    assert labels[1] == "R_V1"
    assert labels[3] == "3"


def test_edges_are_coloured_against_the_shared_scale():
    rendered = to_gravis(sample(), directed=True)
    colours = [edge["metadata"]["color"] for edge in rendered["graph"]["edges"]]
    assert all(colour.startswith("#") and len(colour) == 7 for colour in colours)
    # -0.9 is the largest magnitude, so it reaches the negative endpoint.
    assert "#2166ac" in colours


def test_hover_reports_value_lag_and_significance():
    rendered = to_gravis(sample(), directed=True)
    hover = rendered["graph"]["edges"][0]["metadata"]["hover"]
    assert "0.6" in hover
    assert "lag 0" in hover
    assert "0.01" in hover


def test_lag_is_the_visible_edge_label():
    rendered = to_gravis(sample(), directed=True)
    assert rendered["graph"]["edges"][1]["metadata"]["label"] == "2"


def test_ambiguous_marks_are_drawn_dashed():
    """Gap 01: o-o and x-x must be visually distinct from a determined arrow."""
    rendered = to_gravis(sample(), directed=True)
    by_mark = {
        edge["metadata"]["hover"].split()[0]: edge["metadata"].get("edge_style")
        for edge in rendered["graph"]["edges"]
    }
    styles = [edge["metadata"].get("edge_style") for edge in rendered["graph"]["edges"]]
    assert "dashed" in styles   # the o-o edge
    assert "solid" in styles    # the --> edge


def test_positions_are_attached_only_when_requested():
    without = to_gravis(sample(), directed=True, use_positions=False)
    assert "x" not in without["graph"]["nodes"][1]["metadata"]

    with_positions = to_gravis(sample(), directed=True, use_positions=True)
    metadata = with_positions["graph"]["nodes"][1]["metadata"]
    assert (metadata["x"], metadata["y"], metadata["z"]) == (1.0, 2.0, 3.0)


def test_requesting_positions_without_any_is_an_error():
    graph = LagGraph(labels={}, edges=(LaggedEdge(1, 2, lag=0, value=0.5),))
    with pytest.raises(ValueError, match="position"):
        to_gravis(graph, directed=False, use_positions=True)


def test_empty_graph_renders_without_crashing():
    rendered = to_gravis(LagGraph(labels={}, edges=()), directed=True)
    assert rendered["graph"]["nodes"] == {}
    assert rendered["graph"]["edges"] == []
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/test_render.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.render'`.

- [ ] **Step 3: Write the renderer**

`src/causalflow/render.py`:

```python
"""Convert a LagGraph into the nested dict gravis consumes.

Nodes come from ``graph.node_ids``, which is derived from the edges, so a
rendered graph cannot contain an edge whose endpoint has no node entry.
"""

from causalflow.colors import color_for, scale_max
from causalflow.model import EdgeMark, LagGraph

_GRAPH_DEFAULTS = {
    "node_color": "gray",
    "node_opacity": 0.7,
    "node_border_size": 2,
    "node_border_color": "black",
}

# A determined direction is drawn solid; anything the algorithm left open is dashed.
_STYLES = {
    EdgeMark.DIRECTED: "solid",
    EdgeMark.BIDIRECTED: "solid",
    EdgeMark.UNORIENTED: "dashed",
    EdgeMark.CONFLICT: "dashed",
}


def to_gravis(graph: LagGraph, *, directed: bool, use_positions: bool = False) -> dict:
    if use_positions and not graph.positions:
        raise ValueError(
            "This graph has no node positions. Upload a 3D positions file first."
        )

    vmax = scale_max(edge.value for edge in graph.edges)

    nodes = {}
    for node_id in graph.node_ids:
        metadata = {"label": graph.label_of(node_id), "title": graph.label_of(node_id)}
        if use_positions:
            position = (graph.positions or {}).get(node_id)
            if position is not None:
                metadata["x"], metadata["y"], metadata["z"] = (
                    float(position[0]),
                    float(position[1]),
                    float(position[2]),
                )
        nodes[node_id] = {"metadata": metadata}

    edges = [
        {
            "source": edge.source,
            "target": edge.target,
            "metadata": {
                "color": color_for(edge.value, vmax),
                "label": str(edge.lag),
                "hover": _hover(edge),
                "edge_style": _STYLES[edge.mark],
            },
        }
        for edge in graph.edges
    ]

    return {
        "graph": {
            "directed": directed,
            "metadata": dict(_GRAPH_DEFAULTS),
            "nodes": nodes,
            "edges": edges,
        }
    }


def _hover(edge) -> str:
    parts = [f"{edge.mark.value} {edge.value:.4f} at lag {edge.lag}"]
    if edge.pvalue is not None:
        parts.append(f"p = {edge.pvalue:.4g}")
    return " · ".join(parts)
```

- [ ] **Step 4: Run the tests and verify they pass**

Run: `python3 -m pytest tests/test_render.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/causalflow/render.py tests/test_render.py
git commit -m "feat: render LagGraph to gravis with mark-aware edge styling"
```

---

# Stage 5 — Streamlit application

*The UI is rewritten against the new package. Findings #3, #9 and #10 close here.*

### Task 5.1: App state with no disk writes

**Files:**
- Create: `src/causalflow/app.py`, `tests/test_app.py`
- Modify: `src/visual.py` (replaced wholesale)

**Interfaces:**
- Produces:
  - `build_graph(file_bytes: bytes, filename: str, *, link_prefix: str, value_prefix: str) -> LagGraph` — the cacheable pure function
  - `apply_sidebar_files(graph, rename_bytes, positions_bytes) -> LagGraph`
  - `main() -> None` — the Streamlit entry point

- [ ] **Step 1: Write the failing tests**

These test the pure functions, not the Streamlit widgets. Everything that needs a browser is left to the manual smoke test in Task 9.1.

`tests/test_app.py`:

```python
import json

import pytest

from causalflow.app import apply_sidebar_files, build_graph
from causalflow.serialize import dump_native_json


def test_build_graph_accepts_bytes_and_a_filename(fixtures_dir):
    """Caching keys on bytes, so the entry point must not need a file object."""
    payload = (fixtures_dir / "legacy_graph.json").read_bytes()
    graph = build_graph(payload, "legacy_graph.json", link_prefix="linkLag", value_prefix="vallag")
    assert len(graph.edges) == 4


def test_rename_file_relabels_nodes(fixtures_dir):
    payload = (fixtures_dir / "legacy_graph.json").read_bytes()
    graph = build_graph(payload, "legacy_graph.json", link_prefix="linkLag", value_prefix="vallag")
    renamed = apply_sidebar_files(
        graph, rename_bytes=json.dumps({"1": "Primary visual"}).encode(), positions_bytes=None
    )
    assert renamed.label_of(1) == "Primary visual"


def test_positions_file_attaches_coordinates(fixtures_dir):
    payload = (fixtures_dir / "legacy_graph.json").read_bytes()
    graph = build_graph(payload, "legacy_graph.json", link_prefix="linkLag", value_prefix="vallag")
    positions = {"1": {"x": "10.9", "y": "-80.2", "z": "2.9"}}
    updated = apply_sidebar_files(
        graph, rename_bytes=None, positions_bytes=json.dumps(positions).encode()
    )
    assert updated.positions[1] == (10.9, -80.2, 2.9)


def test_download_payload_round_trips(fixtures_dir):
    payload = (fixtures_dir / "legacy_graph.json").read_bytes()
    graph = build_graph(payload, "legacy_graph.json", link_prefix="linkLag", value_prefix="vallag")
    assert json.loads(dump_native_json(graph))["format"] == "causalflow/v2"


def test_unreadable_upload_raises_a_message_for_the_user():
    from causalflow.loaders import LoaderError

    with pytest.raises(LoaderError):
        build_graph(b"not json at all", "broken.json", link_prefix="linkLag", value_prefix="vallag")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `python3 -m pytest tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'causalflow.app'`.

- [ ] **Step 3: Write the app**

`src/causalflow/app.py`:

```python
"""Streamlit interface.

Uploads are held in ``st.session_state`` and downloads are served from memory.
Nothing here writes to disk: the app runs as a shared multi-user deployment,
where a server-side scratch file lets one visitor's upload reach another.
"""

import io
import json

import gravis as gv
import streamlit as st
import streamlit.components.v1 as components

from causalflow.loaders import SUPPORTED_EXTENSIONS, LoaderError, load_any
from causalflow.model import LagGraph
from causalflow.render import to_gravis
from causalflow.serialize import dump_native_json

LAYOUTS = ("2D force (d3)", "2D physics (vis)", "3D (three)")


@st.cache_data(show_spinner="Reading graph…")
def build_graph(
    file_bytes: bytes,
    filename: str,
    *,
    link_prefix: str,
    value_prefix: str,
) -> LagGraph:
    """Parse an upload. Cached on the file's bytes, so widget changes are free."""
    return load_any(
        io.BytesIO(file_bytes),
        filename=filename,
        link_prefix=link_prefix,
        value_prefix=value_prefix,
    )


def apply_sidebar_files(
    graph: LagGraph,
    rename_bytes: bytes | None,
    positions_bytes: bytes | None,
) -> LagGraph:
    """Layer the optional rename and 3D-position files onto a graph."""
    if rename_bytes:
        graph = graph.renamed(json.loads(rename_bytes.decode("utf-8")))
    if positions_bytes:
        raw = json.loads(positions_bytes.decode("utf-8"))
        positions = {
            int(node_id): (float(p["x"]), float(p["y"]), float(p["z"]))
            for node_id, p in raw.items()
        }
        graph = LagGraph(labels=graph.labels, edges=graph.edges, positions=positions)
    return graph


def main() -> None:
    st.set_page_config(page_title="CausalFlow", initial_sidebar_state="expanded")
    st.title("Time-lagged causal graphs")

    upload, rename, positions, prefixes = _sidebar_inputs()
    if upload is None:
        st.info(
            "Upload a result file to begin. Supported formats: "
            f"{', '.join(SUPPORTED_EXTENSIONS)} — see docs/input-formats.md."
        )
        return

    try:
        graph = build_graph(
            upload.getvalue(),
            upload.name,
            link_prefix=prefixes[0],
            value_prefix=prefixes[1],
        )
    except LoaderError as error:
        st.error(str(error))
        return

    graph = apply_sidebar_files(
        graph,
        rename.getvalue() if rename else None,
        positions.getvalue() if positions else None,
    )
    _render(graph, has_positions=positions is not None)


def _sidebar_inputs():
    st.sidebar.title("Input")
    upload = st.sidebar.file_uploader(
        "Result file", type=[ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS]
    )
    rename = st.sidebar.file_uploader("Node names (.json, optional)", type=["json"])
    positions = st.sidebar.file_uploader("3D positions (.json, optional)", type=["json"])

    with st.sidebar.expander("MATLAB variable names"):
        link_prefix = st.text_input("Adjacency prefix", value="linkLag")
        value_prefix = st.text_input("Value prefix", value="vallag")

    return upload, rename, positions, (link_prefix, value_prefix)


def _render(graph: LagGraph, *, has_positions: bool) -> None:
    filtered = _filter_controls(graph)

    st.download_button(
        "Download graph (.json)",
        data=dump_native_json(filtered),
        file_name="causalflow-graph.json",
        mime="application/json",
    )

    st.caption(
        f"{len(filtered.node_ids)} nodes · {len(filtered.edges)} edges · "
        f"lags 0–{filtered.max_lag}"
    )
    if not filtered.edges:
        st.warning("No edges pass the current filters. Loosen them in the sidebar.")
        return

    layout = st.sidebar.selectbox("Layout", LAYOUTS)
    contemporaneous = filtered.contemporaneous()
    lagged = filtered.lagged()

    if layout == "3D (three)":
        if not has_positions:
            st.error("The 3D layout needs a positions file. Upload one in the sidebar.")
            return
        _plot_three(filtered)
        return

    if contemporaneous.edges:
        st.markdown("### Contemporaneous links (lag 0)")
        _plot_2d(contemporaneous, layout, directed=False)
    if lagged.edges:
        st.markdown("### Lagged links (lag ≥ 1)")
        _plot_2d(lagged, layout, directed=True)


def _filter_controls(graph: LagGraph) -> LagGraph:
    st.sidebar.title("Filters")
    has_pvalues = any(edge.pvalue is not None for edge in graph.edges)

    alpha = None
    if has_pvalues:
        alpha = st.sidebar.slider("Significance α", 0.0, 1.0, 0.05, 0.01)
    else:
        st.sidebar.caption("This format carries no p-values.")

    magnitudes = [abs(edge.value) for edge in graph.edges] or [0.0]
    min_abs_value = st.sidebar.slider(
        "Minimum |value|", 0.0, float(max(magnitudes)), 0.0, float(max(magnitudes)) / 100 or 0.01
    )
    lags = st.sidebar.multiselect("Lags", graph.lags, default=list(graph.lags))

    selected = graph.filtered(alpha=alpha, min_abs_value=min_abs_value, lags=lags)

    nodes = st.sidebar.multiselect(
        "Restrict to nodes", [selected.label_of(n) for n in selected.node_ids]
    )
    if nodes:
        wanted = {n for n in selected.node_ids if selected.label_of(n) in nodes}
        selected = selected.subgraph(wanted)
    return selected


def _plot_2d(graph: LagGraph, layout: str, *, directed: bool) -> None:
    data = to_gravis(graph, directed=directed)
    if layout == "2D physics (vis)":
        figure = gv.vis(
            data,
            edge_size_factor=4,
            edge_label_data_source="label",
            node_label_data_source="label",
            layout_algorithm="forceAtlas2Based",
            show_edge_label=True,
            avoid_overlap=1,
        )
    else:
        figure = gv.d3(
            data,
            edge_size_factor=2,
            edge_label_data_source="label",
            node_label_data_source="label",
            show_edge_label=True,
            many_body_force_strength=-100,
            edge_curvature=0.4 if directed else 0.0,
        )
    components.html(figure.to_html(), height=520)


def _plot_three(graph: LagGraph) -> None:
    data = to_gravis(graph, directed=True, use_positions=True)
    figure = gv.three(
        data,
        edge_size_factor=2,
        edge_label_data_source="label",
        node_label_data_source="label",
        layout_algorithm_active=False,
    )
    components.html(figure.to_html(), height=520)
```

- [ ] **Step 4: Replace `visual.py` with a shim**

The deployment targets this path; keeping it preserves the public URL and the README's run instructions.

`src/visual.py`:

```python
"""Streamlit entry point: ``streamlit run visual.py`` from the src/ directory."""

from causalflow.app import main

main()
```

- [ ] **Step 5: Run the tests and verify they pass**

Run: `python3 -m pytest tests/test_app.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/causalflow/app.py src/visual.py tests/test_app.py
git commit -m "feat: rewrite the app on session state with filters and caching"
```

---

# Stage 6 — Removing the old code

*Only now, with the replacement tested, is it safe to delete. Findings #3, #5 and #6 close here.*

### Task 6.1: Delete dead modules, untrack the scratch file, prune dependencies

**Files:**
- Delete: `src/plot_methods.py`, `src/aux_graph.py`, `src/edges_color.py`, `src/data/graph.json`, `src/__pycache__/`
- Modify: `requirements.txt`, `.gitignore`
- Create: `.streamlit/config.toml`

- [ ] **Step 1: Confirm nothing still imports the old modules**

Run: `grep -rn "plot_methods\|aux_graph\|edges_color" --include=*.py src tests`
Expected: no output. If anything matches, fix it before deleting.

- [ ] **Step 2: Delete the modules and the tracked scratch file**

`src/data/graph.json` is committed to the repository *and* rewritten at runtime — it is the mechanism of finding #3, so it has to leave the index, not just the working tree.

```bash
git rm src/plot_methods.py src/aux_graph.py src/edges_color.py
git rm -r --cached src/data
rm -rf src/data src/__pycache__
```

- [ ] **Step 3: Update `.gitignore`**

Append:

```
# runtime scratch space — the app must never write here
src/data/
.streamlit/secrets.toml
```

- [ ] **Step 4: Pin the runtime dependencies**

`requirements.txt` — graphviz, pyvis and matplotlib were only used by the deleted `aux_graph.py`:

```
setuptools==81.0.0
streamlit==1.41.1
gravis==0.1.0
networkx==3.4.2
numpy==2.2.1
scipy==1.15.1
```

Before committing, confirm each pin resolves: `pip install -r requirements.txt --dry-run`. If a version is unavailable for the CI Python, pin the nearest available release and note it in the commit message.

- [ ] **Step 5: Add the Streamlit configuration**

`.streamlit/config.toml` — the 131 KB sample is small, but a 360-node `.npz` with a `p_matrix` is not:

```toml
[server]
maxUploadSize = 50

[browser]
gatherUsageStats = false
```

- [ ] **Step 6: Verify the suite still passes and the app still starts**

Run: `python3 -m pytest -v`
Expected: all PASS.

Run: `cd src && timeout 25 streamlit run visual.py --server.headless true`
Expected: startup logs show a local URL and no traceback. Ctrl-C or let the timeout end it.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: remove dead modules, untrack runtime scratch file, pin deps"
```

---

# Stage 7 — Test suite completion

*Stages 1–6 test each unit. This stage adds the cross-cutting guarantees no single unit owns, and the explicit regression matrix for the reproduced defects.*

### Task 7.1: Structural guarantees

**Files:**
- Create: `tests/test_no_disk_writes.py`, `tests/test_invariants.py`

**Interfaces:**
- Consumes: the whole `causalflow` package

- [ ] **Step 1: Write the disk-write guard**

This is the standing enforcement of the Global Constraint, and of finding #3. `tests/test_no_disk_writes.py`:

```python
import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).parent.parent / "src" / "causalflow"
WRITE_MODES = {"w", "wb", "a", "ab", "x", "xb", "w+", "r+"}


def python_files():
    return sorted(PACKAGE.rglob("*.py"))


def test_the_package_was_found():
    assert python_files(), f"no modules under {PACKAGE}"


@pytest.mark.parametrize("path", python_files(), ids=lambda p: p.name)
def test_no_module_opens_a_file_for_writing(path):
    """Regression for finding #3.

    plot_methods.py:231 wrote src/data/graph.json on every upload. On the
    shared deployment two visitors overwrite each other and the download
    button can serve someone else's graph. Downloads come from memory now.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name != "open":
            continue
        mode = _literal_mode(node)
        assert mode not in WRITE_MODES, (
            f"{path.name}:{node.lineno} opens a file with mode {mode!r}. "
            "Modules must not write to disk; serve downloads from a buffer."
        )


def _literal_mode(node: ast.Call) -> str:
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        return str(node.args[1].value)
    for keyword in node.keywords:
        if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
            return str(keyword.value.value)
    return "r"


@pytest.mark.parametrize("path", python_files(), ids=lambda p: p.name)
def test_no_module_calls_json_dump_to_a_file(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "dump":
            value = getattr(node.func, "value", None)
            assert getattr(value, "id", None) != "json", (
                f"{path.name}:{node.lineno} calls json.dump to a file handle. "
                "Use json.dumps and hand the bytes to st.download_button."
            )
```

- [ ] **Step 2: Write the cross-loader invariants**

Whatever the format, the same three things must hold. `tests/test_invariants.py`:

```python
import io
import json

import numpy as np
import pytest
from scipy.io import savemat

from causalflow.loaders import load_any
from causalflow.render import to_gravis


def matlab_file():
    lag0 = np.array([[0.0, 0.6, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    lag1 = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, -0.4], [0.0, 0.0, 0.0]])
    buffer = io.BytesIO()
    savemat(buffer, {"linkLag0": lag0, "vallag0": lag0, "linkLag1": lag1, "vallag1": lag1})
    buffer.seek(0)
    buffer.name = "results.mat"
    return buffer


def npz_file():
    marks = np.full((3, 3, 2), "", dtype="<U3")
    marks[0, 1, 0] = marks[1, 0, 0] = "o-o"
    marks[1, 2, 1] = "-->"
    values = np.full((3, 3, 2), 0.5)
    buffer = io.BytesIO()
    np.savez(buffer, graph=marks, val_matrix=values)
    buffer.seek(0)
    buffer.name = "results.npz"
    return buffer


def csv_file():
    buffer = io.BytesIO(b"source,target,lag,value\n1,2,0,0.6\n2,3,1,-0.4\n")
    buffer.name = "results.csv"
    return buffer


def legacy_file(fixtures_dir):
    buffer = io.BytesIO((fixtures_dir / "legacy_graph.json").read_bytes())
    buffer.name = "legacy.json"
    return buffer


ALL_FORMATS = ("matlab", "npz", "csv", "legacy")


def open_format(name, fixtures_dir):
    return {
        "matlab": matlab_file,
        "npz": npz_file,
        "csv": csv_file,
        "legacy": lambda: legacy_file(fixtures_dir),
    }[name]()


@pytest.mark.parametrize("name", ALL_FORMATS)
def test_every_format_yields_edges(name, fixtures_dir):
    assert load_any(open_format(name, fixtures_dir)).edges


@pytest.mark.parametrize("name", ALL_FORMATS)
def test_every_edge_endpoint_is_a_node_in_every_format(name, fixtures_dir):
    """Regression for finding #2, across the whole input surface."""
    graph = load_any(open_format(name, fixtures_dir))
    known = set(graph.node_ids)
    assert all(e.source in known and e.target in known for e in graph.edges)


@pytest.mark.parametrize("name", ALL_FORMATS)
def test_every_format_renders(name, fixtures_dir):
    graph = load_any(open_format(name, fixtures_dir))
    rendered = to_gravis(graph, directed=True)
    nodes = set(rendered["graph"]["nodes"])
    assert all(e["source"] in nodes and e["target"] in nodes for e in rendered["graph"]["edges"])


@pytest.mark.parametrize("name", ALL_FORMATS)
def test_node_ids_are_one_based_in_every_format(name, fixtures_dir):
    graph = load_any(open_format(name, fixtures_dir))
    assert min(graph.node_ids) >= 1


def test_the_shipped_atlas_files_line_up(repo_root):
    """rename_nodes.json and brain_3d.json must describe the same 360 parcels."""
    names = json.loads((repo_root / "data" / "rename_nodes.json").read_text())
    coordinates = json.loads((repo_root / "data" / "brain_3d.json").read_text())
    assert set(names) == set(coordinates)
    assert len(names) == 360
```

- [ ] **Step 3: Run the tests and verify they pass**

Run: `python3 -m pytest tests/test_no_disk_writes.py tests/test_invariants.py -v`
Expected: all PASS. If `test_no_module_opens_a_file_for_writing` fails, the offending module must be changed — never the test.

- [ ] **Step 4: Run the whole suite and record the count**

Run: `python3 -m pytest -q`
Expected: all PASS. Note the total in the commit message.

- [ ] **Step 5: Commit**

```bash
git add tests/test_no_disk_writes.py tests/test_invariants.py
git commit -m "test: guard against disk writes and assert cross-format invariants"
```

---

### Task 7.2: Regression tests named after the original defects

**Files:**
- Create: `tests/test_regressions.py`

Every earlier stage tests its own unit. This module exists so that a future reader can see, in one place, that each defect found in the review has a test that fails if it returns.

- [ ] **Step 1: Write the regression module**

`tests/test_regressions.py`:

```python
"""One test per defect from the 2026-09-07 review.

Each test fails if the original bug returns. The docstrings carry the
pre-refactor location so the history stays traceable.
"""

import io

import numpy as np
import pytest
from scipy.io import savemat

from causalflow.colors import color_for, scale_max
from causalflow.loaders import LoaderError, load_any
from causalflow.model import LaggedEdge, LagGraph
from causalflow.render import to_gravis
from causalflow.serialize import dump_native_json, load_native_json


def test_finding_1_colour_scale_is_unit_invariant():
    """plot_methods.py:313 — `2^31` is XOR (29), not `2**31`.

    Weights above ~29 normalised against a floor of 29. Correlations worked by
    accident; regression coefficients and transfer entropies did not.
    """
    correlations = [color_for(v, scale_max([0.5, 0.8])) for v in (0.5, 0.8)]
    coefficients = [color_for(v, scale_max([50.0, 80.0])) for v in (50.0, 80.0)]
    assert correlations == coefficients


def test_finding_2_lag_zero_targets_are_registered_as_nodes():
    """plot_methods.py:87-100 — only edge *sources* were added to the node dict.

    A 1 -> 2 link at lag 0 produced nodes [1] and edges [(1, 2)].
    """
    lag0 = np.array([[0.0, 0.6, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    buffer = io.BytesIO()
    savemat(buffer, {"linkLag0": lag0, "vallag0": lag0})
    buffer.seek(0)
    buffer.name = "results.mat"

    graph = load_any(buffer)
    assert graph.node_ids == (1, 2)
    rendered = to_gravis(graph, directed=False)
    assert set(rendered["graph"]["nodes"]) == {1, 2}


def test_finding_4_malformed_input_raises_instead_of_rendering_blank():
    """plot_methods.py:163-186 — a bare `except` printed to stdout and returned {}."""
    broken = io.BytesIO(b'{"graph": {}, "digraph": {}}')
    broken.name = "broken.json"
    with pytest.raises(LoaderError):
        load_any(broken)


def test_finding_7_lags_are_not_averaged_together():
    """plot_methods.py:137-145 — weights were averaged across lags.

    +0.7 at lag 1 and -0.6 at lag 3 collapsed to +0.05, a near-invisible edge.
    """
    graph = LagGraph(
        labels={},
        edges=(LaggedEdge(1, 2, lag=1, value=0.7), LaggedEdge(1, 2, lag=3, value=-0.6)),
    )
    restored = load_native_json(__import__("json").loads(dump_native_json(graph)))
    assert sorted(e.value for e in restored.edges) == [-0.6, 0.7]


def test_finding_8_matlab_prefixes_are_not_hard_coded():
    """visual.py:73 — 'linkLag'/'vallag' were literals at the call site."""
    lag0 = np.array([[0.0, 0.6], [0.0, 0.0]])
    buffer = io.BytesIO()
    savemat(buffer, {"adj0": lag0, "w0": lag0})
    buffer.seek(0)
    buffer.name = "results.mat"

    graph = load_any(buffer, link_prefix="adj", value_prefix="w")
    assert len(graph.edges) == 1


def test_finding_9_filters_reduce_the_edge_set():
    """visual.py — no thresholding existed; 360 nodes rendered as a hairball."""
    graph = LagGraph(
        labels={},
        edges=(
            LaggedEdge(1, 2, lag=0, value=0.9, pvalue=0.001),
            LaggedEdge(2, 3, lag=1, value=0.1, pvalue=0.400),
        ),
    )
    assert len(graph.filtered(alpha=0.05).edges) == 1
    assert len(graph.filtered(min_abs_value=0.5).edges) == 1
```

- [ ] **Step 2: Run the tests and verify they pass**

Run: `python3 -m pytest tests/test_regressions.py -v`
Expected: all PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_regressions.py
git commit -m "test: add named regression tests for every reviewed defect"
```

---

# Stage 8 — Documentation

*The Spanish PDFs are the project's biggest untapped asset and its biggest discovery barrier. This stage adds English documentation without discarding them.*

### Task 8.1: The input-format contract

**Files:**
- Create: `docs/input-formats.md`

This is the document the README will point every new user at, and the one that makes the `.npz` loader findable.

- [ ] **Step 1: Write it**

`docs/input-formats.md`:

````markdown
# Input formats

CausalFlow reads five formats. All of them become the same internal object: a
set of edges, each carrying a source, a target, a **lag**, a signed value, an
edge mark, and optionally a p-value.

Node ids are **1-based integers** in every format, so `data/rename_nodes.json`
and `data/brain_3d.json` work with all of them.

## 1. Tigramite `.npz` — recommended

Save a PCMCI / PCMCI+ / LPCMCI result directly:

```python
import numpy as np

results = pcmci.run_pcmciplus(tau_min=0, tau_max=5, pc_alpha=0.01)
np.savez(
    "results.npz",
    graph=results["graph"],            # (N, N, tau_max+1) strings — required
    val_matrix=results["val_matrix"],  # (N, N, tau_max+1) floats  — required
    p_matrix=results["p_matrix"],      # (N, N, tau_max+1) floats  — optional
    var_names=np.array(var_names),     # (N,) strings              — optional
)
```

`graph[i, j, tau]` holds one of:

| Symbol | Meaning | Drawn as |
|---|---|---|
| `""` | no link | — |
| `-->` | directed cause from i to j | solid, arrowhead |
| `<--` | mirror of `-->` at lag 0 | skipped (one edge per pair) |
| `o-o` | adjacent, direction Markov-equivalent | dashed |
| `x-x` | conflicting orientation | dashed |
| `<->` | latent common cause | solid, both ends |

With `p_matrix` present the sidebar gains a significance slider.

## 2. Edge-list `.csv` — the universal fallback

```csv
source,target,lag,value,pvalue,mark
R_V1,R_MST,0,0.6596,0.004,o-o
R_V1,R_V3B,2,-0.6575,0.011,-->
```

`source`, `target`, `lag`, `value` are required; `pvalue` and `mark` are
optional. Node columns may be integers or names — names are assigned ids in
first-seen order and kept as labels.

## 3. MATLAB `.mat`

One adjacency matrix and one value matrix per lag, sharing a prefix:

```
linkLag0, vallag0    % lag 0 — contemporaneous, N x N
linkLag1, vallag1    % lag 1
...
```

A non-zero entry in `linkLag{k}[i][j]` creates an edge from node `i+1` to node
`j+1` at lag `k`, valued `vallag{k}[i][j]`. If your variables use different
names, set the prefixes under **MATLAB variable names** in the sidebar. This
format carries no p-values and no edge marks.

## 4. CausalFlow `.json` (v2) — what Download produces

```json
{
  "format": "causalflow/v2",
  "labels": {"1": "R_V1"},
  "positions": {"1": [10.91, -80.27, 2.92]},
  "edges": [
    {"source": 1, "target": 2, "lag": 0, "value": 0.6596, "mark": "o-o", "pvalue": 0.004}
  ]
}
```

Round-trips without loss. Use it to save a filtered view and reopen it later.

## 5. Legacy `.json` — still readable

The `{"graph": …, "digraph": …}` shape written by versions before the refactor.
It is **lossy**: it stored one averaged weight per node pair plus a
comma-separated list of the lags that pair appeared at, so per-lag values
cannot be recovered. Each listed lag gets an edge carrying the shared value.
Re-export as v2 to stop losing information.

## Companion files

**Node names** — `{"1": "R_V1", "2": "R_MST"}`. See `data/rename_nodes.json`
(the 360 parcels of the HCP-MMP1 / Glasser atlas).

**3D positions** — `{"1": {"x": 10.91, "y": -80.27, "z": 2.92}}`. See
`data/brain_3d.json` (MNI centroids for the same 360 parcels). Required for
the 3D layout.
````

- [ ] **Step 2: Verify every claim against the code**

Run: `python3 -m pytest tests/loaders -v`

Check by hand that the column names in the CSV section match `REQUIRED_COLUMNS`
in `src/causalflow/loaders/edge_csv.py`, that the mark table matches `_MARKS`
in `src/causalflow/loaders/tigramite_npz.py`, and that the v2 example matches
the keys `dump_native_json` emits. Documentation that drifts from the parser is
worse than none.

- [ ] **Step 3: Commit**

```bash
git add docs/input-formats.md
git commit -m "docs: document all five input formats"
```

---

### Task 8.2: README, in English and Spanish

**Files:**
- Modify: `README.md`
- Create: `README.es.md`, `CHANGELOG.md`
- Move: `documentation(es).pdf`, `user_manual(es).pdf` → `docs/legacy/`

- [ ] **Step 1: Move the PDFs, keeping them in the repository**

```bash
mkdir -p docs/legacy
git mv "documentation(es).pdf" "docs/legacy/documentation(es).pdf"
git mv "user_manual(es).pdf" "docs/legacy/user_manual(es).pdf"
```

- [ ] **Step 2: Write the English README**

The first line is what search engines and GitHub's preview show. "Causal Graphs"
is not findable; the method names are.

`README.md`:

````markdown
# CausalFlow

Interactive viewer for **time-lagged causal graphs** — the output of causal
discovery on multivariate time series (PCMCI, PCMCI+, LPCMCI, Granger, and
anything else that produces one adjacency matrix per lag).

Upload a result, threshold it by significance or magnitude, isolate a node's
neighbourhood, and read every link's lag and test statistic on hover. Ships
with a 360-region HCP-MMP1 (Glasser) brain atlas for 3D anatomical layout.

**Live app:** https://causal-graphs.streamlit.app

## Quick start

```bash
pip install -r requirements.txt
cd src
streamlit run visual.py
```

The interface opens in your default browser.

## Input

| Format | Carries lags | Carries p-values | Carries edge marks |
|---|---|---|---|
| Tigramite `.npz` | yes | yes | yes |
| Edge-list `.csv` | yes | yes | yes |
| MATLAB `.mat` | yes | no | no |
| CausalFlow `.json` (v2) | yes | yes | yes |
| Legacy `.json` | partially | no | no |

Full contract, including the exact `np.savez` call for a Tigramite result:
**[docs/input-formats.md](docs/input-formats.md)**.

## What it shows

- **Contemporaneous links (lag 0)** and **lagged links (lag ≥ 1)** as separate graphs.
- **Edge colour** — signed value on a symmetric diverging scale; red positive, blue negative, shade by magnitude.
- **Edge label** — the lag.
- **Edge style** — solid where the direction was determined (`-->`, `<->`), dashed where the algorithm left it open (`o-o`, `x-x`).
- **Layouts** — 2D force (d3), 2D physics (vis), and 3D from supplied coordinates.

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Source lives in `src/causalflow/`: `model.py` (the `LagGraph` object every
part of the system passes around), `loaders/` (one module per format),
`colors.py`, `render.py`, `app.py`.

## Documentation

- [Input formats](docs/input-formats.md)
- [User manual](docs/user-manual.md) · [Manual de usuario](docs/manual-usuario.md)
- [Changelog](CHANGELOG.md)
- Original Spanish write-up and manual: [`docs/legacy/`](docs/legacy/)

## Authors

Dennis Fiallo Muñoz · Lauren Guerra Hernández

Licensed under Apache 2.0 — see [LICENSE](LICENSE).
````

- [ ] **Step 3: Write the Spanish README**

`README.es.md` — a faithful translation of the above, opening:

````markdown
# CausalFlow

Visor interactivo de **grafos causales con retardo temporal** — la salida de
algoritmos de descubrimiento causal sobre series temporales multivariadas
(PCMCI, PCMCI+, LPCMCI, Granger, y cualquier otro que produzca una matriz de
adyacencia por cada retardo).

Sube un resultado, fíltralo por significación o magnitud, aísla la vecindad de
un nodo, y lee el retardo y el estadístico de cada enlace al pasar el cursor.
Incluye el atlas cerebral HCP-MMP1 (Glasser) de 360 regiones para la
distribución anatómica en 3D.

**Aplicación en línea:** https://causal-graphs.streamlit.app

## Inicio rápido

```bash
pip install -r requirements.txt
cd src
streamlit run visual.py
```
````

Translate every remaining section of `README.md` in the same order, and add at
the top of `README.md`: `*Léeme en [español](README.es.md).*` — with the mirror
line `*Read this in [English](README.md).*` at the top of `README.es.md`.

- [ ] **Step 4: Write the changelog**

`CHANGELOG.md`:

```markdown
# Changelog

## [2.0.0] — unreleased

### Added
- Tigramite `.npz` loader reading `graph`, `val_matrix`, `p_matrix`, `var_names`.
- Edge-list `.csv` loader.
- CausalFlow v2 JSON export, lossless across lags, p-values and edge marks.
- Significance (α), magnitude and lag filters; node-subset selection.
- Configurable MATLAB variable prefixes.
- Test suite and CI.
- English documentation: README, input formats, user manual.

### Changed
- Rewritten as the `causalflow` package. `streamlit run visual.py` still works.
- Edge colours now use a symmetric, CVD-safe diverging scale.
- Ambiguous edge marks (`o-o`, `x-x`) are drawn dashed instead of being flattened.
- Uploads are held in session state; downloads are served from memory.

### Fixed
- Colour scale mis-normalised any weight above ~29 (`2^31` is XOR, not `2**31`).
- Lag-0 edge targets were never registered as nodes.
- Uploads overwrote a shared server-side file, so one visitor could receive another's graph.
- Malformed uploads rendered a blank page instead of reporting the problem.

### Removed
- `aux_graph.py` and `edges_color.py` (imported by nothing).
- The non-functional colour-bar tab, and the graphviz/pyvis/matplotlib dependencies.
```

- [ ] **Step 5: Check every link resolves**

Run:

```bash
grep -o '](\(docs\|README\|LICENSE\|CHANGELOG\)[^)]*)' README.md README.es.md \
  | sed 's/.*](//; s/)$//' | sort -u | while read -r target; do
      [ -e "$target" ] || echo "BROKEN: $target"
    done
```

Expected: no `BROKEN:` lines. `docs/user-manual.md` and `docs/manual-usuario.md`
will still be missing at this point — Task 8.3 creates them; re-run this check
at the end of that task.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "docs: English README, Spanish translation, changelog; archive PDFs"
```

---

### Task 8.3: The user manual, both languages

**Files:**
- Create: `docs/user-manual.md`, `docs/manual-usuario.md`

The Spanish PDF manual documents an interface that Stage 5 changed. Rather than
regenerate a PDF, the manual becomes Markdown that lives beside the code and can
be updated in the same commit as a UI change.

- [ ] **Step 1: Read the manual being replaced**

Run: `pdftotext "docs/legacy/user_manual(es).pdf" - | less`

Carry forward everything still true — the graph-type descriptions, the companion
file formats, the meaning of each sidebar control. Drop what Stage 5 removed
(the colour-bar tab) and add what it introduced (filters, layouts, prefixes).

- [ ] **Step 2: Write the English manual**

`docs/user-manual.md`, covering in order:

1. **Opening a result** — the five formats, with a pointer to `docs/input-formats.md`; what the error messages mean and what to do about each.
2. **Naming the nodes** — the rename file; that ids are 1-based; that `data/rename_nodes.json` is the 360-parcel Glasser atlas.
3. **Filters** — α (hidden when the format carries no p-values, and why), minimum |value|, lag selection, node subset. State plainly that filters compose and that the Download button exports the *filtered* graph.
4. **Reading the picture** — the colour scale (red positive, blue negative, shade by magnitude, symmetric about zero); the lag as the edge label; solid vs dashed for determined vs open direction, with the four marks named.
5. **Layouts** — d3 (stable, best for export), vis (force-directed, interactive), three (3D, requires a positions file).
6. **Exporting** — v2 JSON, what it preserves, how to reopen it.
7. **Limits** — upload cap of 50 MB; graphs beyond a few thousand edges are slow in the browser, so threshold first.

- [ ] **Step 3: Write the Spanish manual**

`docs/manual-usuario.md` — the same seven sections, translated. This is the file
that replaces `user_manual(es).pdf` as the current manual; the PDF stays in
`docs/legacy/` as the historical record.

- [ ] **Step 4: Verify the manual against the running app**

Run: `cd src && streamlit run visual.py`

Upload `data/graph.json`. Walk through each of the seven sections and confirm
every control named in the manual exists with that label, and every claim about
its behaviour holds. Fix the manual — or the app — where they disagree.

- [ ] **Step 5: Re-run the link check from Task 8.2 Step 5**

Expected: no `BROKEN:` lines.

- [ ] **Step 6: Commit**

```bash
git add docs/user-manual.md docs/manual-usuario.md
git commit -m "docs: replace the PDF manual with maintained Markdown, EN and ES"
```

---

# Stage 9 — Release

### Task 9.1: Full verification and deployment check

**Files:**
- Modify: none unless a check fails

- [ ] **Step 1: Run the full suite from a clean checkout**

```bash
git status --short          # expect no output
python3 -m pytest -v
```

Expected: every test passes. Record the count.

- [ ] **Step 2: Verify the dependency list is complete and sufficient**

```bash
python3 -m venv /tmp/causalflow-check
/tmp/causalflow-check/bin/pip install -r requirements.txt
/tmp/causalflow-check/bin/python -c "import causalflow.app" 2>&1 | tail -5
```

Run from `src/` so the package resolves. Expected: no `ModuleNotFoundError`.
A failure here means `requirements.txt` is missing a runtime dependency —
exactly the class of defect that made the colour-bar feature uninstallable.

- [ ] **Step 3: Smoke-test each format in the browser**

```bash
cd src && streamlit run visual.py
```

For each of the four checks, confirm the graph draws and the edge count in the
caption is non-zero:

- `data/graph.json` (legacy) with `data/rename_nodes.json` — node labels read `R_V1`, not `1`.
- The same, plus `data/brain_3d.json` and the **3D (three)** layout — parcels sit in anatomical positions.
- A `.npz` written by the snippet in `docs/input-formats.md` — the α slider appears.
- A two-line `.csv` — dashed edges at lag 0, solid at lag 1.

Then confirm the two failure paths report rather than blank: upload a `.txt`
(expect the unsupported-format message naming the four extensions), and a
truncated `.json` (expect a parse error naming the line).

- [ ] **Step 4: Confirm the scratch file is gone for good**

```bash
git ls-files src/data          # expect no output
ls src/data 2>/dev/null        # expect no such directory, after a full session
```

Run this *after* Step 3, so the app has processed several uploads. Any
reappearance means a write path survived Stage 6.

- [ ] **Step 5: Confirm CI is green**

```bash
git push origin HEAD
gh run watch
```

Expected: the `tests` workflow passes on the pushed branch.

- [ ] **Step 6: Redeploy and verify the public app**

The Streamlit Cloud app targets `src/visual.py`, which still exists — the deploy
should pick the new commit up automatically. Open
https://causal-graphs.streamlit.app, upload `data/graph.json`, and confirm the
graph renders. If the deploy fails, the logs will name the missing pin; fix
`requirements.txt` and push again.

- [ ] **Step 7: Tag the release**

```bash
git tag -a v2.0.0 -m "Package refactor: five input formats, filters, tests, English docs"
git push origin v2.0.0
```

---

## Self-review

**Spec coverage.** Every finding in the review's Gap 02 table has a closing stage
and a named test in Task 7.2. Gap 01 (edge vocabulary) is covered for loading
(Task 3.4), the model (Task 1.1), and rendering as solid-vs-dashed (Task 4.1);
per-mark SVG arrowheads are explicitly deferred and listed as out of scope. Gap
03 (interop) is covered by Tasks 3.2–3.5. The user's three explicit asks —
refactor, test stages, documentation and README — are Stages 1–6, Stage 7, and
Stage 8 respectively.

**Placeholder scan.** No step says "add error handling" or "write tests for the
above" without the code. Task 8.3 specifies its seven sections by content rather
than pasting a full manual, which is the one deliberate exception: the source
material is a PDF the implementer must read in Step 1, and pre-writing a
translation of a document nobody has re-read would be worse than useless.

**Type consistency.** `LagGraph`, `LaggedEdge` and `EdgeMark` keep the same
signatures from Task 1.1 through Task 9.1. `load_any` takes
`(file, *, filename, link_prefix, value_prefix)` everywhere. `to_gravis` takes
`(graph, *, directed, use_positions)` everywhere. `dump_native_json` returns
`bytes` and `load_native_json` takes an already-parsed `dict` — matching how the
registry sniffs the JSON dialect before dispatch. `LoaderError` is defined in
`loaders/__init__.py` and imported inside functions by the loader modules, which
is what keeps the circular import between the registry and its loaders from
biting at module load.
