import csv, hashlib, json, re, struct
from .base import ROMPlugin
from ..utils.images import nes_tile_image, make_pattern_table, make_labeled_pattern_table
from ..utils.disasm6502 import disassemble
from ..utils.nes_analysis import scan_entropy_regions, classify_regions, write_analysis_report
from ..utils.nes_audio import scan_apu_hits, write_audio_summary
from ..utils.nes_graphics import render_metatile_sheet, render_pattern_table_color
from ..utils.nes_metasprite import scan_metasprite_candidates

MAPPER_NAMES={0:'NROM',1:'MMC1',2:'UxROM',3:'CNROM',4:'MMC3',7:'AxROM',9:'MMC2',10:'MMC4',11:'Color Dreams',66:'GxROM',71:'Camerica'}

class NESPlugin(ROMPlugin):
    name='NES'
    def detect(self,data,path): return len(data)>=16 and data[:4]==b'NES\x1A'

    def extract(self,data,path,output):
        h=data[:16]; prg_banks=h[4]; chr_banks=h[5]; f6,f7=h[6],h[7]
        mapper=(f6>>4)|(f7&0xF0); trainer=bool(f6&4); nes2=(f7&0x0C)==0x08
        pos=16+(512 if trainer else 0)
        prg=data[pos:pos+prg_banks*16384]
        chrdata=data[pos+len(prg):pos+len(prg)+chr_banks*8192]
        for d in ['Graphics/Pattern_Tables','Graphics/Labeled_Tiles','Graphics/Individual_Tiles','Graphics/Metatile_2x2','Graphics/Palette_Previews','Audio','Text','Code','Scripts','Raw','Analysis']:
            (output/d).mkdir(parents=True,exist_ok=True)
        (output/'Raw/PRG_ROM.bin').write_bytes(prg); (output/'Raw/CHR_ROM.bin').write_bytes(chrdata)
        for i in range(prg_banks): (output/f'Raw/PRG_bank_{i:02d}.bin').write_bytes(prg[i*16384:(i+1)*16384])
        for i in range(chr_banks): (output/f'Raw/CHR_bank_{i:02d}.bin').write_bytes(chrdata[i*8192:(i+1)*8192])
        cpu_base=0x8000 if len(prg)>=32768 else 0xC000

        preview_palettes=[[0x0F,0x16,0x27,0x38],[0x0F,0x06,0x17,0x28],[0x0F,0x09,0x19,0x29],[0x0F,0x01,0x21,0x31]]
        for bank in range(chr_banks):
            b=chrdata[bank*8192:(bank+1)*8192]
            for pt in range(2):
                table=b[pt*4096:(pt+1)*4096]
                make_pattern_table(table).save(output/f'Graphics/Pattern_Tables/CHR{bank}_PT{pt}.png')
                make_labeled_pattern_table(table).save(output/f'Graphics/Labeled_Tiles/CHR{bank}_PT{pt}_labeled.png')
                render_metatile_sheet(table).save(output/f'Graphics/Metatile_2x2/CHR{bank}_PT{pt}_2x2.png')
                for pi,pal in enumerate(preview_palettes): render_pattern_table_color(table,pal,3).save(output/f'Graphics/Palette_Previews/CHR{bank}_PT{pt}_pal{pi}.png')
                idir=output/f'Graphics/Individual_Tiles/CHR{bank}_PT{pt}'; idir.mkdir(parents=True,exist_ok=True)
                for t in range(256): nes_tile_image(table[t*16:(t+1)*16],8).save(idir/f'tile_{t:02X}.png')

        strings=[]
        for m in re.finditer(rb'[\x20-\x7E]{4,}',prg):
            txt=m.group().decode('ascii','replace'); alpha=sum(c.isalpha() for c in txt); strings.append((m.start(),txt,alpha>=3 and alpha/max(1,len(txt))>=0.45))
        with open(output/'Text/ascii_strings.csv','w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['prg_offset','cpu_address_guess','likely_text','text'])
            for off,txt,likely in strings: w.writerow([f'0x{off:04X}',f'${(cpu_base+off)&0xFFFF:04X}','yes' if likely else 'no',txt])
        with open(output/'Text/likely_text.txt','w',encoding='utf-8') as f:
            for off,txt,likely in strings:
                if likely: f.write(f'${(cpu_base+off)&0xFFFF:04X}  {txt}\n')

        nmi=reset=irq=(None,None,None)
        if len(prg)>=6: nmi,reset,irq=struct.unpack('<HHH',prg[-6:])
        (output/'Code/linear_disassembly.asm').write_text('; ROMForge v0.2 automated 6502 linear disassembly.\n; Data regions may decode as instructions.\n\n'+'\n'.join(disassemble(prg,cpu_base)),encoding='utf-8')

        absops={0x8D:'STA',0x8E:'STX',0x8C:'STY',0xAD:'LDA',0xAE:'LDX',0xAC:'LDY',0x9D:'STA,X',0x99:'STA,Y',0xBD:'LDA,X',0xB9:'LDA,Y'}
        ppu_hits=[]
        for i in range(len(prg)-2):
            op=prg[i]; addr=prg[i+1]|(prg[i+2]<<8)
            if op in absops and 0x2000<=addr<=0x2007: ppu_hits.append((cpu_base+i,op,addr,absops[op]))
        with open(output/'Analysis/PPU_access_points.csv','w',encoding='utf-8') as f:
            f.write('cpu_address,opcode,ppu_address\n')
            for cpu,op,addr,mn in ppu_hits: f.write(f'${cpu:04X},{mn},${addr:04X}\n')

        apu_hits=scan_apu_hits(prg,cpu_base); audio_regions=write_audio_summary(output/'Audio',prg,cpu_base,apu_hits)
        pointers=[]
        for i in range(0,len(prg)-1,2):
            v=prg[i]|(prg[i+1]<<8)
            if cpu_base<=v<=0xFFFF: pointers.append((i,v))
        with open(output/'Scripts/pointer_candidates.csv','w',newline='',encoding='utf-8') as f:
            w=csv.writer(f); w.writerow(['prg_offset','source_guess','target'])
            for off,v in pointers: w.writerow([f'0x{off:04X}',f'${cpu_base+off:04X}',f'${v:04X}'])

        metasprites = scan_metasprite_candidates(prg)
        (output/'Graphics/metasprite_candidates.json').write_text(
            json.dumps([item.to_dict() for item in metasprites[:256]], indent=2),
            encoding='utf-8'
        )

        entropy_rows=scan_entropy_regions(prg,cpu_base)
        regions=classify_regions(prg,cpu_base,[(x[0],x[1],x[2]) for x in apu_hits],[(x[0],x[1],x[2]) for x in ppu_hits])
        (output/'Analysis/regions.json').write_text(json.dumps([r.to_dict() for r in regions],indent=2),encoding='utf-8')
        (output/'Analysis/entropy_map.json').write_text(json.dumps(entropy_rows,indent=2),encoding='utf-8')
        manifest={'romforge_version':'0.3.0-dev','file':path.name,'platform':'NES','format':'NES 2.0' if nes2 else 'iNES','mapper':mapper,'mapper_name':MAPPER_NAMES.get(mapper,'Unknown/less-common mapper'),'prg_banks_16kb':prg_banks,'chr_banks_8kb':chr_banks,'prg_bytes':len(prg),'chr_bytes':len(chrdata),'cpu_base_guess':f'${cpu_base:04X}','mirroring':'vertical' if f6&1 else 'horizontal','battery':bool(f6&2),'trainer':trainer,'vectors':{'NMI':f'${nmi:04X}' if nmi is not None else None,'RESET':f'${reset:04X}' if reset is not None else None,'IRQ_BRK':f'${irq:04X}' if irq is not None else None},'analysis':{'printable_string_runs':len(strings),'ppu_access_points':len(ppu_hits),'apu_access_points':len(apu_hits),'audio_candidate_regions':len(audio_regions),'pointer_candidates':len(pointers),'metasprite_candidates':len(metasprites),'classified_regions':len(regions)},'hashes':{'md5':hashlib.md5(data).hexdigest(),'sha1':hashlib.sha1(data).hexdigest()}}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        write_analysis_report(output/'Analysis/REPORT.md',manifest,regions,entropy_rows)
