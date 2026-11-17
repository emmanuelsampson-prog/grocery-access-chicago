"""Create readable notebooks with executed public analytical outputs."""
import nbformat as nbf
from pathlib import Path
from src.download import ROOT

def md(text):return nbf.v4.new_markdown_cell(text)
def code(text):return nbf.v4.new_code_cell(text)

SETUP="""from pathlib import Path
import sys, json
ROOT = Path.cwd()
if not (ROOT / 'data').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import geopandas as gpd
from IPython.display import display, Image, Markdown
pd.set_option('display.max_columns', 20)
DATA = ROOT / 'data/processed'
FIG = ROOT / 'outputs/figures'
"""

def write(name,cells):
    book=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}})
    nbf.write(book,ROOT/'notebooks'/name)

def main():
    write('01_historical_evidence.ipynb',[
      md('# Grocery store closures and replacement openings in Chicago\n\n**Emmanuel Amissah Sampson · Study period 2021–2025**\n\nThis notebook documents six verified business events at five premises and places them in the wider SNAP retailer record. The authorization history is not a census of physical store openings and closures.'),
      code(SETUP),
      md('## 1. Data provenance\nPublic inputs retain source URLs, retrieval times and SHA-256 checksums. The national USDA file is current through 31 December 2025. ACS estimates cover 2017–2021 and provide pre-event context.'),
      code("manifest = pd.DataFrame(json.loads((ROOT/'data/source_manifest.json').read_text()))\ndisplay(manifest[['id','description','bytes','sha256']])"),
      md('## 2. Verified business events\nClosure dates are last open days. Save A Lot occupies the same premises as the closed Whole Foods; this is a replacement opening, not a second new location.'),
      code("events = pd.read_csv(DATA/'verified_events.csv', dtype={'record_id':str})\ndisplay(events[['label','event_type','event_date','address','source_url']])\ndisplay(Image(filename=str(FIG/'02_event_timeline.png')))"),
      md('## 3. Administrative dates need review\nSNAP authorization can precede opening or outlast closure. Inspection dates likewise do not establish the exact last operating day. The focal analysis uses reviewed physical dates.'),
      code("display(events[['label','event_date','snap_start','snap_end','administrative_date_gap_days','review_note']])\ndisplay(Image(filename=str(FIG/'04_date_audit.png')))"),
      md('## 4. Five years of authorization history\nThe counts below use month-end eligibility and unique standardized address keys. They describe the SNAP program footprint, including broad retailer types, and must not be relabeled as verified store counts.'),
      code("history = pd.read_csv(DATA/'monthly_authorized_inventory.csv')\ndisplay(history.groupby('scope').agg(first=('unique_address_keys','first'), last=('unique_address_keys','last'), snapshots=('date','count')))\ndisplay(Image(filename=str(FIG/'03_inventory_history.png')))"),
      md('## 5. Tract context and coordinates\nAll distance calculations use EPSG:26916, NAD83 / UTM zone 16N, metres. Tract polygons shade neighborhood context; one interior origin summarizes each tract. Population weights do not measure affected shoppers.'),
      code("audit = json.loads((DATA/'data_audit.json').read_text())\ndisplay(pd.Series({k:audit[k] for k in ['tracts','populated_tracts','unmatched_acs_tracts','regional_authorization_records','projection']}))\ndisplay(Image(filename=str(FIG/'01_study_map.png')))"),
      md('## Interpretation\nThe executed record establishes dated closures and one replacement opening, quantifies the wider authorization footprint, and exposes date and coordinate discrepancies. It does not establish observed shopping journeys. Continue with notebook 02 for the modeled access comparisons and notebook 03 for the mobility input audit.')])
    write('02_before_after_access.ipynb',[
      md('# Before and after grocery access\n\n**Emmanuel Sampson · Chicago 2021–2025**\n\nThese are shortest-route accessibility estimates around verified events. The model selects the nearest eligible alternative at each date; it does not observe or prescribe shopping choices.'),
      code(SETUP),
      md('## 1. Specification\nFocal dates use the reviewed physical-event ledger. Other alternatives use USDA authorization intervals. The network is fixed at 1 January 2023. Walking assumes 4.8 km/h. Driving includes directed outbound and return routes. The main catchment is 1.6 km and the connector cap is 300 m. See `src/analysis.py` and the research protocol for the full calculation.'),
      code("from src.analysis import load_inputs, summarize\ntracts, retailers, events = load_inputs()\nsummary = json.loads((DATA/'analysis_summary.json').read_text())\ndisplay(pd.Series({k:summary[k] for k in ['study_period','projection','network_snapshot','walking_speed_kmh','focal_radius_m','max_connector_m']}))"),
      md('## 2. Annual geographic context\nThe citywide maps use straight-line distance to authorized larger grocery outlets, including regional alternatives. This is a separate measure from the routed event results.'),
      code("display(pd.read_csv(DATA/'annual_access_context.csv'))\ndisplay(Image(filename=str(FIG/'05_citywide_before_after.png')))"),
      md('## 3. Recalculate event summaries from the origin records'),
      code("routes = pd.read_csv(DATA/'event_access_origins.csv',dtype={'geoid':str})\nmain = routes[routes.variant.eq('main')]\nrecalculated = []\nfor (period,event), group in main.groupby(['period','event_id'],sort=False):\n    recalculated.append(dict(period=period,event_id=event,**summarize(group[group.distance_to_focal_m<=1600])))\nrecalculated = pd.DataFrame(recalculated)\ndisplay(recalculated[['event_id','included_origins','walk_before_minutes','walk_after_minutes','walk_change_minutes','drive_change_roundtrip_km']])\ndisplay(Image(filename=str(FIG/'07_paired_event_results.png')))"),
      md('## 4. Where the changes occur\nThe same color scale is used in all event panels. Gray areas are outside the included comparison; they are not zero-effect estimates.'),
      code("display(Image(filename=str(FIG/'06_event_change_maps.png')))\ndisplay(Image(filename=str(FIG/'08_before_after_scatter.png')))"),
      md('## 5. Equity and sensitivity\nThese comparisons use pre-event tract characteristics. They do not identify a causal household response. Alternative radii and connector screens are retained. Chatham also has a separate coordinate sensitivity.'),
      code("display(pd.read_csv(DATA/'equity_comparisons.csv'))\ndisplay(pd.read_csv(DATA/'access_sensitivity.csv'))\ndisplay(pd.Series(summary['alternate_chatham_coordinate']))\ndisplay(Image(filename=str(FIG/'09_equity_comparison.png')))"),
      md('## 6. Conditional emissions\nThe scenario uses 1,000 dedicated round trips and an illustrative 400 g CO₂/mile factor. Walking and driving shares are assumptions; route changes are not multiplied by the full tract population.'),
      code("from src.analysis import conditional_co2\nscenario = pd.read_csv(DATA/'emissions_scenarios.csv')\ndisplay(scenario)\nassert conditional_co2(1.609344,1,trips=1) == 0.4\ndisplay(Image(filename=str(FIG/'10_emissions_sensitivity.png')))"),
      md('## Discussion\nClosure effects on nearest-outlet access vary with the remaining grocery network. Reopening the Englewood address restores the location-based measure under these assumptions. That does not establish equivalent products, prices, customer return or emissions. Actual behavior requires the licensed panel described in notebook 03.')])
    write('03_mobility_and_causal_design.ipynb',[
      md('# Mobility data audit and causal research design\n\n**Chicago grocery study, 2021–2025**\n\nThis notebook records the status of the observed-data extension. It does not manufacture observations or regression results when the licensed input is absent.'),
      code(SETUP),
      md('## 1. Input availability\nPenn institutional access to Weekly Patterns Plus is verified. The provider terms await the account holder’s review before download. The expected file is private and excluded from public packaging.'),
      code("from src.mobility import audit_panel\nstatus = audit_panel(ROOT/'data/restricted/store_week.csv')\ndisplay(pd.Series(status))"),
      md('## 2. Events and weekly alignment\nUse the first full post-event week. Exclude the transition week from a weekly specification; test announcement timing separately. Whole Foods vacancy ends before the replacement opening, so it cannot supply a full year of post-closure vacancy observations.'),
      code("from src.mobility import first_full_post_week\nevents = pd.read_csv(DATA/'verified_events.csv')\nevents['first_full_post_week'] = events.event_date.map(first_full_post_week)\ndisplay(events[['label','event_date','first_full_post_week']])"),
      md('## 3. Estimands and spatial spillovers\nEstimate redistribution toward surviving destinations and origin-area shopping access. Closed-store visits mechanically fall; that alone is not a welfare or travel effect. Candidate comparison areas need stable pretrends and no overlapping closures or openings. Nearby survivors can receive diverted demand and should not automatically be controls. With few independent events, tract-level sample size does not solve weak treatment-level inference.\n\nUse event-specific estimates and clean comparisons. Treat the Englewood reopening as a separate intervention, rather than fitting one permanent post-closure indicator. See `docs/research_protocol.md` for identification assumptions and references.'),
      md('## 4. What remains unestimated\nObserved destination substitution; actual journey distance; walking or driving shifts; realized emissions; causal event-study effects. The completed access model is useful descriptive evidence, but it cannot supply these missing outcomes.'),
      code("display(Markdown((ROOT/'docs/mobility_data_request.md').read_text()))")])
    import runpy
    runpy.run_path(str(ROOT/'scripts/update_publication_records.py'))
    print('Created three notebooks')

if __name__=='__main__':main()
