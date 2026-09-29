# AutoSIG Analyzer — Documentation Index

This folder is the complete specification for the AutoSIG Analyzer prototype (SIH). Read `00-overview.md` first for the problem statement and project summary; the rest of the files are ordered to be read roughly in pipeline order, from ingestion through deployment.

1. `00-overview.md` — problem statement, team, and project summary
2. `01-architecture.md` — system architecture and data flow
3. `02-dsp-pipeline.md` — ingestion, spectral analysis, parameter estimation, synchronization
4. `03-modulation-classification.md` — the ML modulation classifier
5. `04-hypothesis-engine.md` — Top-K hypothesis ranking
6. `05-recovery-chain.md` — demodulation, de-interleaving, FEC decoding
7. `06-validation-correlation.md` — bitstream correlation and validation
8. `07-data-generation.md` — synthetic dataset (GNU Radio flowgraph, run here via its labeled NumPy equivalent) and SigMF metadata
9. `model-training.md` — how the modulation classifier is trained (data provenance, recipe, metrics)
10. `08-file-formats.md` — `.IQ` and `.WAV` parsing specifics
11. `09-tech-stack.md` — technology choices and rationale
12. `10-project-structure.md` — repository folder layout
13. `11-ui-flow.md` — Streamlit screen-by-screen specification
14. `12-mvp-scope.md` — MVP scope, staged roadmap, risks and mitigations
15. `13-deployment-and-demo.md` — deployment steps and demo video checklist
16. `14-references.md` — verified research references
17. `design.md` — UI design system (colors, typography, layout, components)
