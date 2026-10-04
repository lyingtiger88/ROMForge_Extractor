from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
from .nes_analysis import NES_MASTER_PALETTE


def decode_tile_indices(tile: bytes):
    out=[[0]*8 for _ in range(8)]
    for y in range(8):
        lo,hi=tile[y],tile[y+8]
        for x in range(8):
            bit=7-x
            out[y][x]=((lo>>bit)&1)|(((hi>>bit)&1)<<1)
    return out


def render_tile_color(tile: bytes, palette, scale=1):
    idx=decode_tile_indices(tile)
    im=Image.new('RGB',(8,8))
    px=im.load()
    for y in range(8):
        for x in range(8):
            px[x,y]=NES_MASTER_PALETTE[palette[idx[y][x]] & 0x3F]
    if scale!=1: im=im.resize((8*scale,8*scale),Image.Resampling.NEAREST)
    return im


def render_pattern_table_color(table: bytes, palette, scale=4):
    out=Image.new('RGB',(16*8*scale,16*8*scale))
    for t in range(256):
        out.paste(render_tile_color(table[t*16:(t+1)*16],palette,scale),((t%16)*8*scale,(t//16)*8*scale))
    return out


def render_metatile_sheet(table: bytes, scale=4):
    cell=16*scale+28
    out=Image.new('L',(8*cell,8*cell),255)
    d=ImageDraw.Draw(out)
    from .images import nes_tile_image
    for gy in range(8):
        for gx in range(8):
            n=gy*8+gx
            x=(n%8)*cell; y=(n//8)*cell
            g=Image.new('L',(16,16),255)
            ids=[]
            for yy in range(2):
                for xx in range(2):
                    tid=(gy*2+yy)*16+(gx*2+xx)
                    ids.append(tid)
                    g.paste(nes_tile_image(table[tid*16:(tid+1)*16]),(xx*8,yy*8))
            out.paste(g.resize((16*scale,16*scale),Image.Resampling.NEAREST),(x,y))
            d.text((x+2,y+16*scale+2),'/'.join(f'{i:02X}' for i in ids),fill=0)
    return out
