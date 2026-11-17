"""Keep notebook front matter and README synchronized without changing execution times."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'publication.json').read_text())
repo=p['repository'];site=p['website']
for path in (ROOT/'notebooks').glob('*.ipynb'):
    nb=json.loads(path.read_text());cell=nb['cells'][0];s=''.join(cell['source'])
    s=re.sub(r'\s*· Planned publication 17 November 2026','',s)
    s=s.split('\n\nPublication record:')[0]
    s+=f"\n\nPublication record: {p['status']} · {p['date_label']} · {p['version']}. [Website]({site}) · [Repository]({repo}). All maps and charts are generated with Matplotlib."
    cell['source']=s.splitlines(keepends=True);nb['metadata']['publication']={k:p[k] for k in ['status','publication_date','version','website','repository']}
    path.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n')
r=ROOT/'README.md';s=r.read_text();s=re.sub(r'^Emmanuel (?:Amissah )?Sampson · .*$',f"Emmanuel Amissah Sampson · **{p['status']}: {p['date_label']} · {p['version']}**",s,flags=re.M)
s=s.replace('The private web preview is separate from the planned GitHub Pages release.','The public release contains only redistributable inputs and analytical outputs.')
s=s.replace('The compact website ZIP excludes the network; its four graph files are offered separately.','The GitHub Release package includes the processed inputs and all four derived street-graph files. The same graph files are also available individually in the release.')
if 'python scripts/build_explorer.py' not in s:
    s=s.replace('python scripts/build_site.py','python scripts/build_explorer.py\npython scripts/build_site.py')
marker='## Read the research\n';s=s.replace(marker,marker+f'\n[Public website]({site}) · [GitHub release and full project package]({repo}/releases/tag/{p["version"]})\n' if '[Public website]' not in s else marker)
if 'All ten main figures and six explorer map pairs' not in s:
    s=s.replace('Website assets are built into `dist/`.','Website assets are built into `dist/`. All ten main figures and six explorer map pairs are generated with Matplotlib. The website and reports share one narrative in `scripts/publication_content.py`. Publication status and version come from `publication.json`.')
r.write_text(s)

# Publication metadata is separate from acquisition and execution timestamps.
audit_path=ROOT/'data/processed/data_audit.json'
audit=json.loads(audit_path.read_text());audit.pop('planned_publication_date',None)
audit['publication']={k:p[k] for k in ['status','publication_date','version','website','repository']}
audit_path.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n')
for name in ['research_protocol.md','mobility_data_request.md']:
    path=ROOT/'docs'/name;s=path.read_text()
    s=re.sub(r"The report's planned publication date is [^.;]+; it is not a data date\.","Publication details are recorded in publication.json; publication is separate from the study and acquisition dates.",s)
    s=re.sub(r' Planned public release: [^\n]+',' Publication details: see publication.json.',s)
    path.write_text(s)
