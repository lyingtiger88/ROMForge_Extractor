from __future__ import annotations
from pathlib import Path
import struct

APU_REGS = {
0x4000:'SQ1_VOL',0x4001:'SQ1_SWEEP',0x4002:'SQ1_LO',0x4003:'SQ1_HI',
0x4004:'SQ2_VOL',0x4005:'SQ2_SWEEP',0x4006:'SQ2_LO',0x4007:'SQ2_HI',
0x4008:'TRI_LINEAR',0x400A:'TRI_LO',0x400B:'TRI_HI',
0x400C:'NOISE_VOL',0x400E:'NOISE_LO',0x400F:'NOISE_HI',
0x4010:'DMC_FREQ',0x4011:'DMC_RAW',0x4012:'DMC_START',0x4013:'DMC_LEN',
0x4015:'APU_STATUS',0x4017:'FRAME_COUNTER'
}

def scan_apu_hits(prg: bytes, cpu_base: int):
    hits=[]
    absops={0x8D:'STA',0x8E:'STX',0x8C:'STY',0xAD:'LDA',0xAE:'LDX',0xAC:'LDY',0x9D:'STA,X',0x99:'STA,Y',0xBD:'LDA,X',0xB9:'LDA,Y'}
    for i in range(len(prg)-2):
        op=prg[i]
        if op not in absops: continue
        a=prg[i+1]|(prg[i+2]<<8)
        if a in APU_REGS:
            hits.append((cpu_base+i,op,a,absops[op],APU_REGS[a]))
    return hits


def candidate_audio_regions(prg: bytes, cpu_base: int, hits, radius=192):
    ranges=[]
    for h in hits:
        off=h[0]-cpu_base
        ranges.append((max(0,off-radius),min(len(prg),off+radius)))
    ranges.sort(); merged=[]
    for lo,hi in ranges:
        if merged and lo<=merged[-1][1]+32:
            merged[-1]=(merged[-1][0],max(merged[-1][1],hi))
        else: merged.append((lo,hi))
    return merged


def write_audio_summary(out: Path, prg: bytes, cpu_base: int, hits):
    out.mkdir(parents=True,exist_ok=True)
    with open(out/'APU_access_points.csv','w',encoding='utf-8') as f:
        f.write('cpu_address,opcode,apu_address,apu_name\n')
        for cpu,op,addr,mn,name in hits:
            f.write(f'${cpu:04X},{mn},${addr:04X},{name}\n')
    regions=candidate_audio_regions(prg,cpu_base,hits)
    for n,(lo,hi) in enumerate(regions):
        (out/f'candidate_audio_region_{n:02d}_${cpu_base+lo:04X}-${cpu_base+hi-1:04X}.bin').write_bytes(prg[lo:hi])
    return regions
