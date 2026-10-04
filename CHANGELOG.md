# Changelog

## 0.2.0
- Added NES mapper-name metadata.
- Added 2×2 metatile inspection sheets.
- Added color palette preview sheets.
- Added APU access scanner and candidate sound-driver region export.
- Added PPU access scanner CSV.
- Added pointer-table detector.
- Added RLE-like/map-data heuristic detector.
- Added PRG entropy map.
- Added scored ROM region classification and `Analysis/REPORT.md`.
- Added resource-tree GUI with preview pane for reports, JSON, CSV, ASM and text.
- Added stronger output manifest.
- Fixed packaging omissions from v0.1 (`plugins/base.py`, package init files).
- Verified CLI extraction on a real 32KB PRG / 8KB CHR NROM image reconstructed from Tank 1990 resources.
