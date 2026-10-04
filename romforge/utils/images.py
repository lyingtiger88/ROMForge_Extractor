from PIL import Image, ImageDraw, ImageFont

NES_SHADES=[255,170,85,0]

def nes_tile_image(tile: bytes, scale: int=1):
    if len(tile)!=16: raise ValueError('NES tile must be 16 bytes')
    im=Image.new('L',(8,8),255); px=im.load()
    for y in range(8):
        lo,hi=tile[y],tile[y+8]
        for x in range(8):
            b=7-x; v=((lo>>b)&1)|(((hi>>b)&1)<<1); px[x,y]=NES_SHADES[v]
    return im.resize((8*scale,8*scale),Image.Resampling.NEAREST) if scale!=1 else im

def make_pattern_table(tb: bytes, scale: int=5):
    out=Image.new('L',(16*8*scale,16*8*scale),255)
    for t in range(256):
        out.paste(nes_tile_image(tb[t*16:(t+1)*16],scale),((t%16)*8*scale,(t//16)*8*scale))
    return out

def make_labeled_pattern_table(tb: bytes):
    fw,fh=46,52; out=Image.new('L',(16*fw,16*fh),255); d=ImageDraw.Draw(out); font=ImageFont.load_default()
    for t in range(256):
        x=(t%16)*fw; y=(t//16)*fh
        out.paste(nes_tile_image(tb[t*16:(t+1)*16],4),(x+7,y+2))
        d.rectangle((x,y,x+fw-1,y+fh-1),outline=210)
        d.text((x+5,y+37),f'{t:02X}',fill=0,font=font)
    return out

# Backward aliases
tile=nes_tile_image
pattern_table=make_pattern_table
labeled=make_labeled_pattern_table
