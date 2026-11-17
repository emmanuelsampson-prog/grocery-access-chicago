"""Adapt the shared Chicago narrative to the Philadelphia report template."""
from publication_content import ROOT,content
import json
D=content()
OUT=ROOT/'outputs/public'
TITLE=D['title'];SUBTITLE=D['subtitle'];AUTHOR=D['author']
DATE=f"{D['publication_status']} · {D['publication_date']} · {D['version']}"
REPO=D['repository'];SITE=D['website']
REFERENCES=[(label,url) for _,label,url in D['references']]
def get_sections():
    result=[]
    for page in D['pages']:
        blocks=[]
        for b in page['blocks']:
            if 'paragraph' in b:blocks.append({'type':'p','text':b['paragraph']})
            elif 'figure' in b:blocks.append({'type':'figure','file':'../figures/'+b['figure']+'.png','caption':b['caption'],'alt':b['caption']})
            else:
                t=b['table'];widths=([.30,.11,.12,.12,.13,.22] if len(t['headers'])==6 else [.13,.27,.27,.33])
                blocks.append({'type':'table','caption':'Event access comparisons' if len(t['headers'])==6 else 'Annual authorization and access context','headers':t['headers'],'rows':t['rows'],'widths':widths})
        result.append({'id':page['id'],'title':page['title'],'blocks':blocks})
    return result

def write_records():
    (ROOT/'site/content.json').write_text(json.dumps(D,indent=2,ensure_ascii=False)+'\n')
    md=[f'# {TITLE}\n\n{SUBTITLE}\n\n{AUTHOR} · University of Pennsylvania\n\n{DATE}\n']
    for page in D['pages']:
        md.append('## '+page['title']+'\n')
        for b in page['blocks']:
            if 'paragraph' in b:md.append(b['paragraph']+'\n')
            elif 'figure' in b:md.append(f"![{b['caption']}](../outputs/figures/{b['figure']}.png)\n")
            else:
                t=b['table'];md+=['| '+' | '.join(t['headers'])+' |','| '+' | '.join(['---']*len(t['headers']))+' |']
                md+=['| '+' | '.join(row)+' |' for row in t['rows']];md.append('')
    md+=['## References\n']+[f'[{i}] {label} [Source]({url})\n' for i,label,url in D['references']]
    md+=['## Research records\n',f'[Website]({SITE}) · [Repository]({REPO}) · [Main executed notebook]({REPO}/blob/main/notebooks/02_before_after_access.ipynb) · [Release]({REPO}/releases/tag/{D["version"]})\n']
    (ROOT/'docs/report.md').write_text('\n'.join(md))
