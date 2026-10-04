import argparse
from pathlib import Path
from .core import extract_rom
def main():
    p=argparse.ArgumentParser(description="ROMForge extractor")
    p.add_argument("rom",type=Path)
    p.add_argument("-o","--output",type=Path,default=None)
    a=p.parse_args(); print(extract_rom(a.rom,a.output))
