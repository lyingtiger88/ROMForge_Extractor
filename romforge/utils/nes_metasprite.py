"""Heuristic NES metasprite table discovery.

A common NES layout stores OAM-like 4-byte records: Y, tile, attributes, X,
terminated by a Y byte of 0xFF. Games vary, so findings are candidates rather
than claims about a specific engine.
"""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class MetaSpriteCandidate:
    offset: int
    sprite_count: int
    width: int
    height: int
    records: tuple

    def to_dict(self):
        data = asdict(self)
        data["offset_hex"] = f"0x{self.offset:04X}"
        return data


def scan_metasprite_candidates(prg: bytes, min_sprites: int = 3, max_sprites: int = 64):
    candidates = []
    offset = 0
    length = len(prg)

    while offset + min_sprites * 4 + 1 <= length:
        records = []
        pos = offset
        valid = True

        while len(records) < max_sprites and pos + 4 <= length:
            y = prg[pos]
            if y == 0xFF:
                break

            tile = prg[pos + 1]
            attr = prg[pos + 2]
            x = prg[pos + 3]

            # OAM attributes normally use palette bits 0-1 plus priority/flip
            # bits 5-7; bits 2-4 should be clear.
            if y >= 240 or (attr & 0x1C):
                valid = False
                break

            records.append((y, tile, attr, x))
            pos += 4

        terminated = pos < length and prg[pos] == 0xFF
        if valid and terminated and len(records) >= min_sprites:
            xs = [record[3] for record in records]
            ys = [record[0] for record in records]
            candidates.append(
                MetaSpriteCandidate(
                    offset=offset,
                    sprite_count=len(records),
                    width=max(xs) - min(xs) + 8,
                    height=max(ys) - min(ys) + 8,
                    records=tuple(records),
                )
            )
            # Do not emit the same table again starting at every record.
            offset = pos + 1
        else:
            offset += 1

    return candidates
