# Paper

Preprint of the Kredo mechanism, formatted for arXiv / journal submission.

**Kredo: A Contribution-Based Mutual-Credit Economy with Soulbound Reputation and Compensatory Emission**
— Fedor Chishchin.

## Build

With [Tectonic](https://tectonic-typesetting.github.io/) (self-contained, downloads packages on demand):

```bash
tectonic main.tex        # produces main.pdf
```

Or with a full TeX distribution:

```bash
pdflatex main.tex && pdflatex main.tex
```

Or open `main.tex` on [Overleaf](https://overleaf.com) and compile there.

## Contents

- `main.tex` — the paper (self-contained: `article` class, `amsmath`/`amsthm`,
  theorems with proofs, tables, and an embedded bibliography — no BibTeX pass needed).

## Notes for submission

- The mechanism, derivations, simulator, protocols, and raw results referenced by
  the paper are the rest of this repository.
- Suggested arXiv categories: `econ.TH` (Theoretical Economics), cross-list
  `cs.GT` (Computer Science and Game Theory).
