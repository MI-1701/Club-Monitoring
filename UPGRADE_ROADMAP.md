# Clubs Monitoring — Professional Upgrade Roadmap

*Cross-referenced from the original audit (`AUDIT_ET_RECOMMANDATIONS.md`) and extended analysis.  
Each task maps to a file, a clear action, and a definition of done.*

---

## Reading This Document

Tasks are grouped into three tiers:

- 🔴 **BLOCK** — Must be done before any public launch or Fiverr listing.
- 🟠 **HIGH** — Required for a professional, trustworthy product.
- 🟡 **MEDIUM** — Competitive differentiation; do after the first two tiers.

Each task includes: what the problem is, exactly what to do, which file(s) to touch, and what "done" looks like.

---

## 🔴 TIER 1 — Launch Blockers (Do First)

---

### T1-A · Complete the i18n — The App Speaks Half-English

**Problem**  
The audit identifies 9 specific locations in `app.py` where French strings are hardcoded instead of going through `t()`. If a user switches the language to English, they see a broken hybrid: some labels in English, others still in French. The entire `page_methode()` function (lines 892–956) is written as raw French prose with no English equivalent. All five Plotly chart functions have fixed French titles and tooltips.

This is the most visible quality failure in the product. Any international coach or Fiverr buyer will catch it in under 60 seconds.

**Exact locations to fix (from audit §4.1)**

| File | Line | Current (broken) | Fix |
|------|------|-------------------|-----|
| `app.py` | 466 | `st.subheader("Synthese par joueuse")` | `st.subheader(t("synthese_joueuse"))` |
| `app.py` | 484 | `tableau["Bien-etre"]` | `tableau[t("col_bien_etre")]` |
| `app.py` | 489 | `st.subheader("Disponibilite")` | `st.subheader(t("disponibilite"))` |
| `app.py` | 492 | `st.caption("Jours d'absence recadres...")` | `st.caption(t("dispo_note"))` — key exists in `i18n.py` |
| `app.py` | 498 | `st.subheader("Charge hebdomadaire de l'equipe")` | `st.subheader(t("charge_hebdo_equipe"))` — key exists |
| `app.py` | 514 | `yaxis=dict(title="Charge (unites arbitraires)")` | `yaxis=dict(title=t("charge_ua"))` — key exists |
| `app.py` | 800 | `st.selectbox("Indicateur", ...)` | `st.selectbox(t("indicateur"), ...)` |
| `app.py` | 892–956 | entire `page_methode()` in raw French | write full EN version in `i18n.py`, render via `t()` |

**Plotly functions to update** (pass `lang` as parameter, build strings from `t()`):
- `tracer_acwr()`
- `tracer_hooper()`
- `tracer_monotonie_contrainte()`
- `tracer_sauts()`
- `tracer_croissance()`

**Files to touch:** `app.py`, `i18n.py`

**Definition of done:**  
Switch the language selector to English → every visible string, every chart title, every tooltip, and the entire Methode page renders in English. No French string survives anywhere in the English view.

---

### T1-B · Add `tests/test_i18n.py` — Prevent Silent Regressions

**Problem**  
There are 69 tests across 5 files but zero tests for `i18n.py`. A developer can add a key in French and forget its English counterpart. No CI check will catch this. Users will see raw key names (e.g., `"col_bien_etre"`) appear directly in the UI.

**What to build**

Create `tests/test_i18n.py` with three test groups:

1. **Key symmetry test** — assert that every key present in the `"fr"` dict is also present in the `"en"` dict, and vice versa.
2. **No empty values** — assert that no key maps to an empty string `""` or `None` in either language.
3. **Template interpolation test** — for every value containing `{variable}` placeholders, assert that formatting with dummy values raises no `KeyError` or `IndexError`.

**Files to touch:** `tests/test_i18n.py` (create), `.github/workflows/` (no change needed — pytest already runs all tests)

**Definition of done:**  
`pytest tests/test_i18n.py` passes with ≥ 10 tests. Adding a key in one language without the other causes an immediate CI failure.

---

### T1-C · Fix the README — Remove Dead Image References

**Problem**  
`README.md` references `Pictures/vue_equipe_1.png` and similar paths. This folder does not exist. Any developer, recruiter, or Fiverr buyer who visits the GitHub repository sees broken image placeholders at the top of the README — the first thing anyone reads. This communicates "unfinished" more loudly than any code issue.

**What to do**

Step 1 — Take real screenshots of the app with demo data loaded, in both FR and EN, at full resolution (≥ 1280px wide). Minimum captures needed:

- Vue d'équipe (team overview with KPIs and alert center visible)
- Fiche joueuse (player profile, 360° banner)
- Saisie rapide (data entry grid filled)
- Rapport PDF (download button visible)

Step 2 — Create `Pictures/` folder in the repo root and commit the screenshots.

Step 3 — Update `README.md` to reference real paths and add captions in both FR and EN.

**Files to touch:** `README.md`, `Pictures/` (create folder)

**Definition of done:**  
Opening the GitHub repository URL shows all images loading correctly. The README communicates the product's purpose, features, and quality in one scroll.

---

## 🟠 TIER 2 — Professional Quality

---

### T2-A · Homogenize the Repository Layer Across All Pages

**Problem**  
`depot.py` defines `DepotDonnees` and `DepotSession` as an abstraction layer, explicitly designed so that switching to a SQL backend (`DepotPostgres`) requires zero changes to the UI pages. But only `page_saisie_rapide` actually uses the `depot` instance. Every other page receives the raw `donnees` dict directly, which means the architecture claim is not backed by the code. Any future client asking for persistent storage would require a full page-by-page rewrite.

**What to do**

Pass the `depot` instance as a parameter (or access it from `st.session_state`) in all 7 page functions:

- `page_equipe(depot, ...)`
- `page_joueuse(depot, ...)`
- `page_saisie_rapide(depot, ...)` ← already done
- `page_bienetre(depot, ...)`
- `page_comparaison(depot, ...)`
- `page_rapports(depot, ...)`
- `page_methode(depot, ...)` ← no data needed, but keep signature consistent

Replace all direct `donnees["seances"]`, `donnees["bien_etre"]`, etc. accesses inside those pages with `depot.seances()`, `depot.bien_etre()`, etc.

**Files to touch:** `app.py`, `depot.py` (verify all accessor methods exist)

**Definition of done:**  
No page function accesses `donnees` dict directly. Searching `app.py` for `donnees["` returns zero results outside of `depot.py` itself.

---

### T2-B · Make CSV Validation Errors Actionable

**Problem**  
When `securite.py` or `donnees.py` rejects a file, the user currently receives a generic error message. A coach who made a typo in row 14 of their RPE column has no way of knowing what went wrong or how to fix it. The validation logic is already precise and correct — only the output is insufficient.

**What to do**

Update every validation error path to include three pieces of information:
1. The exact column name where the error occurred.
2. The row number (1-indexed from the CSV, not the DataFrame index).
3. The expected valid range or format.

Example format:
```
Row 14 — Column "RPE": value '11' is outside the valid range [1–10].
Row 3 — Column "duree_min": value '-5' must be greater than 0.
```

This applies to: RPE out of range, duration ≤ 0, negative jumps, missing required columns, encoding rejection.

Add these structured messages to `i18n.py` as parameterized templates so they translate correctly.

**Files to touch:** `donnees.py`, `securite.py`, `i18n.py`

**Definition of done:**  
Uploading a CSV with a known bad value produces a message that tells the coach exactly which row and column to fix, in the active language.

---

### T2-C · Add Onboarding / Empty State

**Problem**  
A new user opening the app without uploading any CSV sees an empty, silent interface. There is no guidance, no sample data, no "start here" signal. This is a high abandonment point for any first-time evaluator — including Fiverr buyers testing the demo link.

**What to do**

Detect the empty-state condition at app load (no session data present). Display a welcome panel that contains:

1. A one-click **"Load Demo Data"** button — calls the existing demo data loader from `donnees.py`.
2. A 3-step visual guide in plain language: Upload your CSVs → Explore your team → Export reports.
3. A CSV template download button for each of the 4 supported files (`seances.csv`, `bien_etre.csv`, `anthropometrie.csv`, `blessures.csv`).

The panel disappears once any data is loaded. It renders in the active language.

**Files to touch:** `app.py`, `i18n.py` (add onboarding strings)

**Definition of done:**  
A user who has never used the app opens it and reaches useful, loaded data within 2 clicks. No blank screen on first load.

---

### T2-D · Restructure `page_methode()` as a Real Reference Document

**Problem**  
`page_methode()` (lines 892–956) is written as a wall of plain French text. For a tool making decisions about injury risk and overtraining for minors, coaches and club directors need to see the scientific basis clearly. The Impellizzeri 2020 critique is integrated into `calculs.py` but invisible to users. The thresholds (Z > 1.5, ACWR > 1.5, growth > 7 cm/yr) have no visible source attribution.

**What to do**

Restructure the page into clearly labeled sections — one per metric. Each section contains:

- **What it measures** — one sentence.
- **Formula** — rendered with `st.latex()` or inline code.
- **Thresholds used** — exact values with their meaning (vigilance vs alert).
- **Scientific source** — author, year, citation.
- **Known limitation** — honest one-line caveat (e.g., ACWR critiqued by Impellizzeri et al. 2020 for regression-to-mean artifacts).

Write the complete English version of every section in `i18n.py`.

**Files to touch:** `app.py` (page_methode function), `i18n.py`

**Definition of done:**  
The Methode page reads like a methodology section from a sports science paper. A federation medical officer could evaluate the tool's scientific basis from this page alone, in either language.

---

### T2-E · Brand the PDF Reports

**Problem**  
PDF reports are the one output that leaves the app and gets seen by outsiders — parents, federation officials, medical staff. Currently they are generated with ReportLab defaults: no logo, no club branding, no professional header/footer, no consistent color identity matching the app.

**What to do**

Add to the **Rapports PDF** page (`page_rapports()`):
- An optional **club logo upload** field (PNG/JPG, stored in `st.session_state["logo"]` for the session).
- A **club name** text input, stored in session.

In `rapport_pdf.py`:
- Add a header section to both individual and team reports: club logo (if provided) on the left, report title and date on the right, a thin rule below.
- Add a footer on every page: club name, generation date, app URL, page number.
- Apply one consistent accent color (matching the app's Streamlit theme) to chart borders, table header backgrounds, and section titles.
- Increase DPI from 150 to 200 for charts in the PDF.

**Files to touch:** `rapport_pdf.py`, `app.py` (page_rapports section), `i18n.py` (header/footer strings)

**Definition of done:**  
A generated PDF printed on A4 looks like a document a professional sports organization would distribute. It contains the club's name and logo, page numbers, and is visually coherent with the web interface.

---

## 🟡 TIER 3 — Competitive Differentiation

---

### T3-A · Add Session-Level Alert Acknowledgment

**Problem**  
The alert center detects real anomalies (Z-score spikes, ACWR danger zones, Hooper deterioration). But there is no way to mark an alert as "seen" or "handled." Every session restart re-presents the same alerts with no memory. For a monitoring tool, this is a UX gap — the coach cannot tell which alerts are new vs already addressed.

**What to do (minimal viable, stays within session model)**

Add a `st.session_state["alertes_vues"]` dict. Next to each alert card in the alert center, add a checkbox or button: **"Mark as handled"** with an optional free-text note field. Store `{alerte_id: {"timestamp": ..., "note": ...}}` in session.

Acknowledged alerts render differently (grey, collapsed) rather than red/orange.

Include acknowledged alerts with their notes in the team PDF report under a section "Alert History — This Session."

**Files to touch:** `app.py` (alert center component), `rapport_pdf.py`, `i18n.py`

**Definition of done:**  
A coach can process alerts one by one, marking each handled. The team PDF report shows which alerts were raised and which were acknowledged this session.

---

### T3-B · Add Coverage Badge and Improve CI Output

**Problem**  
The CI pipeline runs `ruff + compileall + pytest` — solid. But there is no coverage report and no badge visible in the README. A technical evaluator (Fiverr buyer who is a developer, or a potential collaborator) has no quick signal of test quality.

**What to do**

In `.github/workflows/`, add `pytest --cov=. --cov-report=xml` to the test step. Configure `codecov` or `coveralls` integration (both have free tiers for public repos). Add the resulting badge to `README.md`.

Also add: a `CHANGELOG.md` with versioned history (v1.0, v2.0 sprint entries from `PROJET_ETAT.md`), and a `CONTRIBUTING.md` with setup instructions for new contributors.

**Files to touch:** `.github/workflows/` (CI config), `README.md`, add `CHANGELOG.md`, add `CONTRIBUTING.md`

**Definition of done:**  
The README shows a green coverage badge (target: ≥ 80%). The repository has a `CHANGELOG.md` and `CONTRIBUTING.md`. Running the CI locally produces a coverage summary.

---

### T3-C · Fiverr Demo — Auto-Load on Open

**Problem**  
`FICHE_FIVERR.md` is ready, but the live demo link (`club-monitoring.streamlit.app`) requires a buyer to upload a CSV before seeing any value. Most buyers will not do this. The product needs to show its value within 10 seconds of landing.

**What to do**

Add a URL query parameter check on app load: `?demo=true`. When detected, automatically load the demo dataset (already in `donnees.py`) and jump directly to the team overview page.

The Fiverr gig link becomes: `https://club-monitoring.streamlit.app?demo=true`

Also: add a visible **"Try Demo"** button on the empty state panel (T2-C) that does the same thing without requiring a URL parameter.

**Files to touch:** `app.py` (startup logic), `donnees.py` (verify demo data is complete and realistic)

**Definition of done:**  
Clicking the Fiverr demo link opens the app directly in the team overview view, fully populated, with no upload required. A buyer sees KPIs, alerts, and charts within 5 seconds.

---

## Summary — Task Checklist

### 🔴 Tier 1 — Launch Blockers

- [ ] **T1-A** · Fix all 9 hardcoded French strings in `app.py` + translate `page_methode()` + translate all Plotly charts
- [ ] **T1-B** · Create `tests/test_i18n.py` (key symmetry, empty values, template interpolation)
- [ ] **T1-C** · Take real screenshots → create `Pictures/` folder → fix `README.md` images

### 🟠 Tier 2 — Professional Quality

- [ ] **T2-A** · Pass `depot` instance to all 7 page functions; remove all direct `donnees[...]` accesses from pages
- [ ] **T2-B** · Add row/column/range detail to all CSV validation error messages, in both languages
- [ ] **T2-C** · Build empty-state onboarding panel (demo loader + 3-step guide + CSV template downloads)
- [ ] **T2-D** · Restructure `page_methode()` into per-metric sections with formula, thresholds, source, limitation
- [ ] **T2-E** · Add club logo + name to PDF reports; add professional header/footer/page numbers

### 🟡 Tier 3 — Differentiation

- [ ] **T3-A** · Add session-level alert acknowledgment with notes; include in team PDF report
- [ ] **T3-B** · Add coverage badge to CI + `CHANGELOG.md` + `CONTRIBUTING.md`
- [ ] **T3-C** · Implement `?demo=true` URL parameter for Fiverr demo link auto-load

---

## Recommended Execution Order

```
Week 1  →  T1-A + T1-B + T1-C   (launch blockers, mostly in app.py and i18n.py)
Week 2  →  T2-C + T2-B + T2-D   (UX and validation polish, high visible impact)
Week 3  →  T2-A + T2-E           (architecture and PDF — more effort, high trust signal)
Week 4  →  T3-C + T3-A + T3-B   (differentiation, CI, Fiverr launch)
```

> After Week 1 is complete, the product is launchable.  
> After Week 3, it is competitive.  
> After Week 4, it is portfolio-ready and Fiverr-listed.

---

*Roadmap generated from audit cross-analysis. Each task references the original `AUDIT_ET_RECOMMANDATIONS.md` section in its problem statement.*
