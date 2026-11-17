"""Chicago website: editorial layout, shared research text, Matplotlib figures."""
from html import escape as esc
from string import Template
from struct import unpack
from publication_content import ROOT, content

EXPLORER='''<div class="explorer" aria-labelledby="explorer-title"><p class="eyebrow">Explore the evidence · 6 comparisons</p><h3 id="explorer-title">One event. The same neighborhoods.</h3><p>Compare modeled one-way walking minutes to the nearest eligible larger grocery outlet. Both panels use the same origins, street network and scale.</p><label for="event-select">Choose a business event</label><select id="event-select" disabled><option>Loading events…</option></select><dl class="explorer-stats" aria-label="Selected event summary" aria-live="polite"><div><dt>Before</dt><dd id="event-before">11.48 <small>min</small></dd></div><div><dt>After</dt><dd id="event-after">16.10 <small>min</small></dd></div><div><dt>Change</dt><dd id="event-change">+4.62 <small>min</small></dd></div></dl><figure><a id="map-full" href="outputs/figures/explorer/walmart_kenwood.png" aria-label="Open the selected map at full size"><img id="event-map" src="outputs/figures/explorer/walmart_kenwood.png" alt="Kenwood before and after tract access maps" width="1940" height="1057" loading="lazy"></a><figcaption id="map-summary" aria-live="polite">Kenwood: 22 tract origins. Population-weighted modeled walking time increases from 11.48 to 16.10 minutes.</figcaption></figure><p class="mini"><a id="map-svg" href="outputs/figures/explorer/walmart_kenwood.svg" download>Download this Matplotlib figure as SVG ↓</a></p><details><summary>View tract values</summary><div class="table-scroll"><table><thead><tr><th scope="col">Tract GEOID</th><th scope="col">Before minutes</th><th scope="col">After minutes</th></tr></thead><tbody id="tract-values"></tbody></table></div></details><noscript><p>The selector requires JavaScript. Kenwood is shown above; all six events appear in the figures and downloadable data.</p></noscript></div>'''

def block(b):
    if 'paragraph' in b:return '<p>'+esc(b['paragraph'])+'</p>'
    if 'figure' in b:
        name=b['figure']
        width,height=unpack('>II',(ROOT/f'outputs/figures/{name}.png').read_bytes()[16:24])
        return f'<figure class="research-figure"><a href="outputs/figures/{name}.png" title="Open full-size figure"><img src="outputs/figures/{name}.png" alt="{esc(b["caption"])}" width="{width}" height="{height}" loading="lazy"></a><figcaption>{esc(b["caption"])} <a class="figure-download" href="outputs/figures/{name}.svg" download>Download SVG ↓</a></figcaption></figure>'
    t=b['table'];head=''.join('<th scope="col">'+esc(x)+'</th>' for x in t['headers'])
    rows=''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+esc(str(x))+('</th>' if i==0 else '</td>') for i,x in enumerate(row))+'</tr>' for row in t['rows'])
    return f'<div class="table-scroll" tabindex="0" role="region" aria-label="Research results table"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'

def main():
    d=content();repo=d['repository'];sections=[];toc=[]
    for i,s in enumerate(d['pages'],1):
        key=s['id'];title=esc(s['title']);body=''.join(block(b) for b in s['blocks'])
        if key=='results':body+=EXPLORER
        sections.append(f'<section id="{key}" class="research-section" aria-labelledby="heading-{key}"><header class="section-heading"><span class="section-number">{i:02d}</span><h2 id="heading-{key}">{title}</h2></header><div class="report-section">{body}</div></section>')
        toc.append(f'<li><a href="#{key}"><span>{i:02d}</span>{title}</a></li>')
    refs=''.join(f'<li>{esc(label)} <a href="{esc(url)}">Read source →</a></li>' for _,label,url in d['references'])
    groups=[('Notebooks', [('Before and after access','notebooks/02_before_after_access.ipynb'),('Historical evidence and date audit','notebooks/01_historical_evidence.ipynb'),('Mobility audit and causal design','notebooks/03_mobility_and_causal_design.ipynb')]),('Methods and data',[('Research protocol','docs/research_protocol.md'),('Data dictionary','docs/data_dictionary.md'),('Verified business-event ledger','data/processed/verified_events.csv'),('Tract-origin access comparisons','data/processed/event_access_origins.csv')]),('Provenance',[('Source records and checksums','data/source_manifest.json'),('Street network provenance','data/network_manifest.json'),('Data attribution and redistribution','docs/data_licenses.md')])]
    records=''.join('<div class="record-group"><h3>'+heading+'</h3><ul>'+''.join(f'<li><a href="{repo}/blob/main/{path}">{label}<span aria-hidden="true">→</span></a></li>' for label,path in items)+'</ul></div>' for heading,items in groups)
    values={**{k:esc(str(v)) for k,v in d.items() if not isinstance(v,(list,dict))},'sections':''.join(sections),'toc':''.join(toc),'references':refs,'records':records}
    (ROOT/'index.html').write_text(Template((ROOT/'site/template.html').read_text()).substitute(values))
    (ROOT/'.nojekyll').touch()
    from assemble_site import assemble
    assemble();print('Built Chicago editorial website')
if __name__=='__main__':main()
