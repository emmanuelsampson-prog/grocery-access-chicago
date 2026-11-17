"""Package reviewed public source for the publication import workflow.

Usage: python scripts/create_public_archive.py /path/to/bootstrap.zip
Network files travel separately; the final GitHub Release is a complete git archive.
"""
from pathlib import Path
import sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def package(output):
    files=[]
    for name in ['README.md','LICENSE','requirements.txt','.gitignore','.nojekyll','index.html','publication.json','data/source_manifest.json','data/network_manifest.json','data/restricted/README.md']:
        p=ROOT/name
        if p.exists():files.append(p)
    for name in ['src','scripts','tests','docs','notebooks','site','outputs/figures','outputs/public']:
        files.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.log'])
    files.extend(p for p in (ROOT/'data/processed').glob('*') if p.suffix in ['.csv','.json','.geojson'])
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in sorted(set(files)):archive.write(p,p.relative_to(ROOT))
    print(f'{len(set(files))} reviewed files; {Path(output).stat().st_size/1e6:.2f} MB')
if __name__=='__main__':package(Path(sys.argv[1]))
