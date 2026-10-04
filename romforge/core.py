from pathlib import Path
from .plugins.nes import NESPlugin
PLUGINS=[NESPlugin()]
def extract_rom(path,output=None):
    path=Path(path); data=path.read_bytes()
    for p in PLUGINS:
        if p.detect(data,path):
            out=Path(output) if output else path.with_name(path.stem+"_extracted")
            out.mkdir(parents=True,exist_ok=True); p.extract(data,path,out); return out
    raise ValueError("Unsupported ROM format. Current build supports NES/iNES.")
