"""Assemble only redistributable web files; no hosting identity or private inputs."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
def assemble():
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    for name in ['index.html','.nojekyll']:
        shutil.copy2(ROOT/name,out/name)
    for name in ['site','outputs/figures','outputs/public']:
        shutil.copytree(ROOT/name,out/name,dirs_exist_ok=True)
if __name__=='__main__':assemble()
