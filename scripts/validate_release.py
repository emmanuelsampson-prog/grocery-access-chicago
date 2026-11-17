"""Verify public artifacts using the Python standard library."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,zipfile
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
def main():
    books=list((ROOT/'notebooks').glob('*.ipynb'));assert len(books)==3
    for path in books:
        n=json.loads(path.read_text());codes=[c for c in n['cells'] if c['cell_type']=='code'];assert all(c['execution_count'] for c in codes),path
        assert not any(o['output_type']=='error' for c in codes for o in c['outputs']),path
    figures=list((ROOT/'outputs/figures').glob('*.svg'))+list((ROOT/'outputs/figures/explorer').glob('*.svg'))
    assert len(figures)==16,len(figures)
    assert all('Matplotlib' in f.read_text() for f in figures)
    for suffix in ['docx','pdf']:
        assert (ROOT/f'outputs/public/Chicago_Grocery_Access_Report.{suffix}').stat().st_size>100000
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k in ['src','href'] and v and not v.startswith(('http:','https:','#','data:')):
                    assert (ROOT/v.split('#')[0]).exists(),v
    Links().feed((ROOT/'index.html').read_text())
    metadata=json.loads((ROOT/'publication.json').read_text());assert metadata['study_period']=='2021–2025'
    if metadata['status']=='Published':
        for path in [ROOT/'README.md',ROOT/'index.html',ROOT/'docs/report.md',ROOT/'site/content.json',*books]:
            text=path.read_text();assert 'Planned publication' not in text and '30 November 2026' not in text,path
    print('Verified three executed notebooks, sixteen Matplotlib figures, report files, local website links and publication records')
if __name__=='__main__':main()
