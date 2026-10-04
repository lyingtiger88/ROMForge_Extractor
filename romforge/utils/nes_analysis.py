from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter
import math, json

NES_MASTER_PALETTE = [
(84,84,84),(0,30,116),(8,16,144),(48,0,136),(68,0,100),(92,0,48),(84,4,0),(60,24,0),
(32,42,0),(8,58,0),(0,64,0),(0,60,0),(0,50,60),(0,0,0),(0,0,0),(0,0,0),
(152,150,152),(8,76,196),(48,50,236),(92,30,228),(136,20,176),(160,20,100),(152,34,32),(120,60,0),
(84,90,0),(40,114,0),(8,124,0),(0,118,40),(0,102,120),(0,0,0),(0,0,0),(0,0,0),
(236,238,236),(76,154,236),(120,124,236),(176,98,236),(228,84,236),(236,88,180),(236,106,100),(212,136,32),
(160,170,0),(116,196,0),(76,208,32),(56,204,108),(56,180,204),(60,60,60),(0,0,0),(0,0,0),
(236,238,236),(168,204,236),(188,188,236),(212,178,236),(236,174,236),(236,174,212),(236,180,176),(228,196,144),
(204,210,120),(180,222,120),(168,226,144),(152,226,180),(160,214,228),(160,162,160),(0,0,0),(0,0,0)
]

@dataclass
class Region:
    kind: str
    start: int
    end: int
    score: float
    note: str
    def to_dict(self): return asdict(self)

def entropy(buf: bytes) -> float:
    if not buf: return 0.0
    c = Counter(buf); n = len(buf)
    return -sum((v/n)*math.log2(v/n) for v in c.values())

def scan_entropy_regions(data: bytes, base_addr: int, block=256):
    rows=[]
    for off in range(0,len(data),block):
        chunk=data[off:off+block]
        rows.append({'start':base_addr+off,'end':base_addr+off+len(chunk)-1,'entropy':round(entropy(chunk),4)})
    return rows

def find_pointer_tables(prg: bytes, cpu_base: int, min_entries=4, max_gap=0):
    out=[]; i=0
    while i+2*min_entries <= len(prg):
        vals=[]; j=i
        while j+1 < len(prg):
            v=prg[j] | (prg[j+1]<<8)
            if not (cpu_base <= v <= 0xFFFF): break
            vals.append(v); j+=2
            if len(vals)>=64: break
        if len(vals)>=min_entries:
            distinct=len(set(vals)); score=min(1.0,0.35+len(vals)/32+distinct/64)
            out.append(Region('pointer_table',cpu_base+i,cpu_base+j-1,round(score,3),f'{len(vals)} words; {distinct} distinct targets')); i=j
        else: i+=1
    keep=[]
    for r in out:
        if keep and r.start <= keep[-1].end:
            if (r.end-r.start) > (keep[-1].end-keep[-1].start): keep[-1]=r
        else: keep.append(r)
    return keep

def find_palette_candidates(prg: bytes, cpu_base: int):
    out=[]
    for size in (16,32):
        for i in range(0,len(prg)-size+1):
            b=prg[i:i+size]
            if not all(x <= 0x3F for x in b): continue
            universal=sum(1 for x in b[::4] if x in (0x0F,0x00,0x10,0x20,0x30))
            repeated=len(set(b[::4])) <= max(2,size//16+1)
            if universal >= max(2,size//16) and repeated:
                score=min(0.99,0.55+universal*0.08)
                out.append(Region('palette_candidate',cpu_base+i,cpu_base+i+size-1,round(score,3),f'{size}-byte NES-color candidate'))
    keep=[]
    for r in out:
        if keep and r.start < keep[-1].start+8: continue
        keep.append(r)
        if len(keep)>=128: break
    return keep

def find_rle_like_regions(prg: bytes, cpu_base: int, min_len=32):
    out=[]; block=128
    for i in range(0,len(prg)-block+1,32):
        b=prg[i:i+block]; runs=0; repeated=0; p=0
        while p<len(b):
            q=p+1
            while q<len(b) and b[q]==b[p]: q+=1
            if q-p>=3: runs+=1; repeated += q-p
            p=q
        ratio=repeated/len(b)
        if runs>=3 and ratio>=0.2:
            out.append(Region('rle_like_data',cpu_base+i,cpu_base+i+block-1,round(min(0.95,0.4+ratio),3),f'{runs} runs; repeated ratio {ratio:.2f}'))
    return out[:128]

def classify_regions(prg: bytes, cpu_base: int, apu_hits, ppu_hits):
    regs=[]
    regs.extend(find_pointer_tables(prg,cpu_base)); regs.extend(find_palette_candidates(prg,cpu_base)); regs.extend(find_rle_like_regions(prg,cpu_base))
    for hit in apu_hits:
        cpu=hit[0]; regs.append(Region('audio_code',max(cpu_base,cpu-96),min(0xFFFF,cpu+192),0.85,'near direct NES APU access'))
    for hit in ppu_hits:
        cpu=hit[0]; regs.append(Region('ppu_code',max(cpu_base,cpu-96),min(0xFFFF,cpu+192),0.8,'near direct NES PPU access'))
    regs.sort(key=lambda r:(r.start,r.end,r.kind)); return regs

def write_analysis_report(path: Path, manifest: dict, regions, entropy_rows):
    lines=['# ROMForge NES Analysis Report','',f"- File: `{manifest['file']}`",f"- Mapper: **{manifest['mapper']}**",f"- PRG: {manifest['prg_bytes']} bytes",f"- CHR: {manifest['chr_bytes']} bytes",f"- RESET: {manifest['vectors']['RESET']}",'','## Candidate regions','','| Type | Start | End | Score | Notes |','|---|---:|---:|---:|---|']
    for r in sorted(regions,key=lambda x:-x.score)[:180]: lines.append(f'| {r.kind} | `${r.start:04X}` | `${r.end:04X}` | {r.score:.2f} | {r.note} |')
    lines += ['','## Entropy map','','Lower-entropy blocks often contain tables/maps/text; higher entropy may be code or compressed data.','','| Start | End | Entropy |','|---:|---:|---:|']
    for e in entropy_rows: lines.append(f"| `${e['start']:04X}` | `${e['end']:04X}` | {e['entropy']:.3f} |")
    path.write_text('\n'.join(lines),encoding='utf-8')
