# Paper

Preprint of the Kredo mechanism, formatted for arXiv / journal submission.

**Kredo: A Contribution-Based Mutual-Credit Economy with Soulbound Reputation and Compensatory Emission**
— Fedor Chishchin.

Two language versions, identical content:

- `main.tex` — English (`main.pdf`).
- `main-ru.tex` — Russian (`main-ru.pdf`), a precise translation.

## Build

The **English** version compiles with any engine:

```bash
tectonic main.tex          # produces main.pdf
# or: pdflatex main.tex && pdflatex main.tex
# or open on Overleaf
```

The **Russian** version uses `fontspec` for Cyrillic, so it needs a Unicode
engine — **XeLaTeX** (via Tectonic) or LuaLaTeX, **not** pdfLaTeX:

```bash
tectonic main-ru.tex       # produces main-ru.pdf  (recommended)
# or: xelatex main-ru.tex
# on Overleaf: set the compiler to XeLaTeX
```

It sets the main font to CMU Serif (`cmunrm.otf`, Computer Modern Unicode with
full Cyrillic) so the Russian text matches the Computer Modern look of the
English version.

## Contents

- `main.tex` / `main-ru.tex` — the paper (self-contained: theorems with proofs,
  tables, embedded bibliography — no BibTeX pass needed).

## Notes for submission

- The mechanism, derivations, simulator, protocols, and raw results referenced by
  the paper are the rest of this repository.
- Suggested arXiv categories: `econ.TH` (Theoretical Economics), cross-list
  `cs.GT` (Computer Science and Game Theory).
