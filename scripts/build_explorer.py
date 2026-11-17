"""Generate every explorer map with the same Matplotlib style as report figures."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from src.figures import style,furniture,ROOT

def main():
    style();data=ROOT/'data/processed';out=ROOT/'outputs/figures/explorer';out.mkdir(parents=True,exist_ok=True)
    tracts=gpd.read_file(data/'tract_context.geojson').to_crs(26916)
    events=pd.read_csv(data/'verified_events.csv')
    events=gpd.GeoDataFrame(events,geometry=gpd.points_from_xy(events.longitude,events.latitude),crs=4326).to_crs(26916)
    routes=pd.read_csv(data/'event_access_origins.csv',dtype={'geoid':str});routes=routes[routes.variant.eq('main')&routes.main_included]
    summaries={r['event_id']:r for r in json.loads((data/'analysis_summary.json').read_text())['events']};records=[]
    for row in events.itertuples():
        r=routes[routes.event_id.eq(row.event_id)];local=tracts.merge(r[['geoid','walk_before_minutes','walk_after_minutes']],on='geoid',how='left')
        x,y=row.geometry.x,row.geometry.y;bounds=(x-2500,y-2500,x+2500,y+2500)
        local=local.cx[bounds[0]:bounds[2],bounds[1]:bounds[3]]
        fig,axes=plt.subplots(1,2,figsize=(10,5.6));fig.subplots_adjust(left=.02,right=.88,bottom=.14,top=.83,wspace=.06)
        for ax,when in zip(axes,['before','after']):
            local.plot(ax=ax,color='#e8ecef',edgecolor='white',linewidth=.4)
            local.dropna(subset=[f'walk_{when}_minutes']).plot(ax=ax,column=f'walk_{when}_minutes',cmap='viridis',vmin=0,vmax=35,edgecolor='white',linewidth=.5)
            ax.scatter([x],[y],c='black',edgecolors='white',s=35,zorder=4)
            furniture(ax,bounds,scale=1000,padding=0)
            ax.set_title(f"{when.title()} · {r[when+'_date'].iloc[0]}")
        cb=fig.colorbar(ScalarMappable(norm=Normalize(0,35),cmap='viridis'),cax=fig.add_axes([.91,.25,.02,.48]),extend='max');cb.set_label('Modeled walking minutes, one way')
        fig.suptitle(row.label+' — before and after',y=.94)
        fig.text(.025,.035,'Same tract origins, street network and color scale. Gray: outside comparison. Point: focal premises.\n4.8 km/h; EPSG:26916, metres. Street data © OpenStreetMap contributors. Modeled access, not observed journeys.',fontsize=8,color='#444')
        for ext in ['png','svg']:fig.savefig(out/f'{row.event_id}.{ext}',bbox_inches='tight')
        plt.close(fig)
        s=summaries[row.event_id];records.append({'id':row.event_id,'label':row.label,'type':row.event_type,'n':s['included_origins'],'before':s['walk_before_minutes'],'after':s['walk_after_minutes'],'change':s['walk_change_minutes'],'png':f'outputs/figures/explorer/{row.event_id}.png','svg':f'outputs/figures/explorer/{row.event_id}.svg','tracts':r[['geoid','walk_before_minutes','walk_after_minutes']].round(3).to_dict('records')})
    (ROOT/'site/event_maps.json').write_text(json.dumps(records,indent=2)+'\n');print('Built six Matplotlib before-and-after map pairs')
if __name__=='__main__':main()
