# ROMForge Extractor v0.2

A modular ROM resource extraction and reverse-engineering toolkit.

## v0.2 focus: NES/Famicom

### Graphics
- PRG/CHR bank extraction
- Standard NES 16×16 pattern-table PNGs
- Labeled tile sheets
- Individual 8×8 tiles
- 2×2 metatile inspection sheets
- Multiple color palette preview sheets

### Audio analysis
- NES APU register-reference detection
- Candidate sound-driver region extraction
- Addressed APU access list
- Architecture ready for game-specific NSF/WAV renderer modules

### Text / scripts
- Printable-text scan
- Likely-text filtering
- ROM pointer candidates
- Pointer-table detection
- RLE-like data detection for likely maps/tables

### Code
- 6502 linear disassembly
- NMI / RESET / IRQ vector extraction
- PPU access-point detection
- APU access-point detection
- Mapper metadata

### Automated analysis
`Analysis/REPORT.md` ranks candidate regions for pointer tables, palettes, RLE/map-like data, audio code, and PPU/graphics code. It also creates a PRG entropy map.

## GUI
`python romforge_gui.py`

The v0.2 GUI includes a resource tree and text/code/report preview pane.

## CLI
`python romforge.py game.nes`

## Requirements
`pip install -r requirements.txt`

## Reality of ROM extraction
A ROM normally does not contain the game's original source project. ROMForge can recover machine code/disassembly, graphics data, tables, strings, sound-driver data and other resources. Exact complete sprites, levels, scripts and WAV/NSF tracks may require a game-specific decoder because commercial games use custom formats and compression.

## Roadmap
- v0.3: game-specific NES audio sandbox + NSF/WAV rendering framework, deeper metasprite/nametable analysis
- v0.4: Game Boy / Game Boy Color plugin
- v0.5: SNES plugin
- later: Mega Drive / Genesis and additional systems
