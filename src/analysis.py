"""Descriptive authorization trends and event-specific modeled access.

No regression in this module estimates observed behavioral or causal effects.
"""
from __future__ import annotations
import json
import hashlib
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from scipy.sparse import load_npz
from scipy.sparse.csgraph import connected_components,dijkstra
from pyproj import Transformer
from src.download import ROOT
from src.prepare import active,CRS

OUT=ROOT/'data/processed'
WALK_KMH=4.8
MAIN_RADIUS=1600
MAX_CONNECTOR=300
PERIODS=[('whole_foods_closure','2022-11-13','2022-11-14',['whole_foods_englewood']),
         ('walmart_closures','2023-04-16','2023-04-17',['walmart_chatham','walmart_kenwood','walmart_lakeview','walmart_little_village']),
         ('save_a_lot_opening','2023-05-10','2023-05-11',['save_a_lot_englewood'])]

def load_inputs():
    t=gpd.read_file(OUT/'tract_context.geojson').to_crs(CRS)
    r=pd.read_csv(OUT/'regional_retailer_history.csv',dtype={'record_id':str,'zip_code':str},
       parse_dates=['authorization_start','authorization_end','reviewed_start','reviewed_end'])
    e=pd.read_csv(OUT/'verified_events.csv',dtype={'record_id':str})
    return t,r,e

def weighted(frame,column):
    f=frame[frame[column].notna() & (frame.population>0)]
    return float(np.average(f[column],weights=f.population)) if len(f) else None

def summarize(frame):
    f=frame[frame.main_included].copy()
    out=dict(eligible_origins=len(frame),included_origins=len(f),
             excluded_origins=len(frame)-len(f),tract_population_context=int(f.population.sum()))
    for c in ['walk_before_minutes','walk_after_minutes','walk_change_minutes',
              'drive_before_roundtrip_km','drive_after_roundtrip_km','drive_change_roundtrip_km']:
        out[c]=weighted(f,c)
    for mode,unit in [('walk','minutes'),('drive','roundtrip_km')]:
        delta=f[f'{mode}_change_{unit}']
        out[f'{mode}_increase_origins']=int((delta>1e-5).sum())
        out[f'{mode}_decrease_origins']=int((delta<-1e-5).sum())
        out[f'{mode}_unchanged_origins']=int((delta.abs()<=1e-5).sum())
    for phase in ['before','after']:
        out[f'walk_within_15min_{phase}_pct']=float(100*np.average(f[f'walk_{phase}_minutes']<=15,weights=f.population)) if len(f) else None
    return out

def conditional_co2(delta_km,car_share,trips=1000,additional_share=1.,g_per_mile=400.):
    """Tailpipe kg for assumed vehicle round trips; no observed emissions claim."""
    if not 0<=car_share<=1 or not 0<=additional_share<=1 or trips<0 or g_per_mile<0:
        raise ValueError('Invalid scenario assumption')
    return delta_km/1.609344*trips*car_share*additional_share*g_per_mile/1000

def route_fingerprint(origins,stores):
    digest=hashlib.sha256()
    digest.update(origins[['geoid','origin_x','origin_y']].to_csv(index=False).encode())
    digest.update(stores[['record_id','x','y']].to_csv(index=False).encode())
    for mode in ['walk','drive']:
        for name in [mode,mode+'_nodes']:
            with (OUT/f'network/{name}.npz').open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

def main():
    tracts,retailers,events=load_inputs()
    tracts=tracts[tracts.population>0].reset_index(drop=True)
    retailers=retailers[retailers.is_larger_grocery].reset_index(drop=True)
    transform=Transformer.from_crs(4326,CRS,always_xy=True)
    ex,ey=transform.transform(events.longitude.values,events.latitude.values)
    events['x']=ex;events['y']=ey
    # Citywide annual context uses uncorrected authorization dates, explicitly.
    annual=[]
    for year in range(2021,2026):
        date=f'{year}-12-31'
        avail=active(retailers,date)
        dist,which=cKDTree(avail[['x','y']]).query(tracts[['origin_x','origin_y']])
        tracts[f'authorization_nearest_{year}_km']=dist/1000
        annual.append(dict(year=year,city_authorized_larger_addresses=avail.loc[avail.inside_chicago,'site_key'].nunique(),
          weighted_straight_distance_km=float(np.average(dist/1000,weights=tracts.population)),
          population_weighted_origins_within_800m_pct=float(100*np.average(dist<=800,weights=tracts.population))))
    tracts.to_file(OUT/'tract_annual_access.geojson',driver='GeoJSON')
    pd.DataFrame(annual).to_csv(OUT/'annual_access_context.csv',index=False)

    # Fixed catchments at 2.4 km allow 0.8/1.6/2.4 km sensitivity.
    origin_distance=cdist(tracts[['origin_x','origin_y']],events[['x','y']])
    potential=tracts[origin_distance.min(axis=1)<=2400].copy().reset_index(drop=True)
    stores=retailers.copy()
    # An alternative Chatham coordinate is audited without silently resolving it.
    alt=stores[stores.record_id.eq('1037375')].copy()
    alt['record_id']='1037375_city_coordinate'
    insp=pd.read_csv(OUT/'event_inspection_corroboration.csv')
    ch=insp[insp.event_id.eq('walmart_chatham')][['longitude','latitude']].median()
    alt['longitude']=ch.longitude;alt['latitude']=ch.latitude
    alt['x'],alt['y']=transform.transform(ch.longitude,ch.latitude)
    stores=pd.concat([stores,alt],ignore_index=True)
    distance_by_mode={};snaps={}
    cache=OUT/'route_matrix.npz'
    fingerprint=route_fingerprint(potential,stores)
    use_cache=False
    if cache.exists():
        z=np.load(cache,allow_pickle=False)
        use_cache=('input_sha256' in z.files and str(z['input_sha256'])==fingerprint)
    if use_cache:
        for mode in ['walk','drive']:
            distance_by_mode[mode]=(z[mode+'_outbound'],z[mode+'_return'])
            snaps[mode]=(z[mode+'_origin_snap'],z[mode+'_destination_snap'])
    else:
        arrays={'input_sha256':np.array(fingerprint),'geoids':potential.geoid.to_numpy(dtype=str),'record_ids':stores.record_id.to_numpy(dtype=str)}
        for mode in ['walk','drive']:
            graph=load_npz(OUT/f'network/{mode}.npz')
            xy=np.load(OUT/f'network/{mode}_nodes.npz')['xy']
            _,comp=connected_components(graph,directed=True,connection='weak')
            chosen=np.flatnonzero(comp==np.bincount(comp).argmax())
            tree=cKDTree(xy[chosen])
            os,oi=tree.query(potential[['origin_x','origin_y']]);ds,di=tree.query(stores[['x','y']])
            oi=chosen[oi];di=chosen[di]
            out=np.empty((len(potential),len(stores)));back=np.empty_like(out)
            reverse=graph.T.tocsr()
            for start in range(0,len(potential),8):
                stop=min(start+8,len(potential))
                out[start:stop]=dijkstra(graph,directed=True,indices=oi[start:stop])[:,di]
                back[start:stop]=dijkstra(reverse,directed=True,indices=oi[start:stop])[:,di]
            connector=os[:,None]+ds[None,:]
            out+=connector;back+=connector
            distance_by_mode[mode]=(out,back);snaps[mode]=(os,ds)
            arrays.update({mode+'_outbound':out,mode+'_return':back,
                           mode+'_origin_snap':os,mode+'_destination_snap':ds})
            print('Routed',mode,len(potential),'origins',len(stores),'destination records',flush=True)
        np.savez_compressed(cache,**arrays)

    records=[]
    for period,before,after,event_ids in PERIODS:
        e=events[events.event_id.isin(event_ids)].reset_index(drop=True)
        proximity=cdist(potential[['origin_x','origin_y']],e[['x','y']])
        assignment=proximity.argmin(axis=1);distance=proximity.min(axis=1)
        for variant in ['main','alternate_chatham_coordinate'] if period=='walmart_closures' else ['main']:
            f=potential.drop(columns='geometry').copy()
            f['period']=period;f['variant']=variant;f['before_date']=before;f['after_date']=after
            f['event_id']=e.event_id.to_numpy()[assignment]
            f['distance_to_focal_m']=distance
            f['population_context_only']=True
            for mode in ['walk','drive']:
                outbound,inbound=distance_by_mode[mode]
                total=outbound if mode=='walk' else outbound+inbound
                os,ds=snaps[mode]
                f[mode+'_origin_snap_m']=os
                for phase,date in [('before',before),('after',after)]:
                    eligible=active(stores,date,corrected=True).index
                    allowed=np.zeros(len(stores),dtype=bool);allowed[eligible]=True
                    allowed &= (ds<=MAX_CONNECTOR)
                    allowed &= stores.record_id.ne('1037375_city_coordinate').to_numpy() if variant=='main' else stores.record_id.ne('1037375').to_numpy()
                    m=total.copy();m[:,~allowed]=np.inf
                    winner=m.argmin(axis=1);best=m[np.arange(len(f)),winner]
                    f[f'{mode}_{phase}_record_id']=stores.record_id.to_numpy()[winner]
                    f[f'{mode}_{phase}_destination']=stores.store_name.to_numpy()[winner]
                    f[f'{mode}_{phase}_destination_snap_m']=ds[winner]
                    f[f'{mode}_{phase}_'+('minutes' if mode=='walk' else 'roundtrip_km')]=best/1000/(WALK_KMH/60) if mode=='walk' else best/1000
                unit='minutes' if mode=='walk' else 'roundtrip_km'
                f[f'{mode}_change_{unit}']=f[f'{mode}_after_{unit}']-f[f'{mode}_before_{unit}']
            routecols=['walk_before_minutes','walk_after_minutes','drive_before_roundtrip_km','drive_after_roundtrip_km']
            f['all_routes_reachable']=np.isfinite(f[routecols]).all(axis=1)
            f['max_origin_snap_m']=f[['walk_origin_snap_m','drive_origin_snap_m']].max(axis=1)
            f['main_included']=(f.distance_to_focal_m<=MAIN_RADIUS)&(f.max_origin_snap_m<=MAX_CONNECTOR)&f.all_routes_reachable
            records.append(f[f.distance_to_focal_m<=2400])
    results=pd.concat(records,ignore_index=True)
    results.replace([np.inf,-np.inf],np.nan).to_csv(OUT/'event_access_origins.csv',index=False)
    main=results[results.variant.eq('main')]
    summary=[]
    for (period,key),f in main.groupby(['period','event_id'],sort=False):
        eligible=f[f.distance_to_focal_m<=MAIN_RADIUS]
        summary.append(dict(period=period,event_id=key,**summarize(eligible)))
    pd.DataFrame(summary).to_csv(OUT/'event_access_summary.csv',index=False)
    equity=[];sensitivity=[];emissions=[]
    for period,f in main.groupby('period',sort=False):
        for column,threshold,label in [('poverty_share',.2,'Poverty'),('no_vehicle_share',.3,'No vehicle')]:
            for high in [False,True]:
                g=f[f[column].notna() & ((f[column]>=threshold)==high) & (f.distance_to_focal_m<=MAIN_RADIUS)]
                equity.append(dict(period=period,group=f'{label} '+('at least ' if high else 'below ')+f'{threshold:.0%}',**summarize(g)))
        for radius in [800,1600,2400]:
            for max_snap in [100,200,300]:
                g=f[f.distance_to_focal_m<=radius].copy()
                snapcols=[c for c in g if c.endswith('_snap_m')]
                g['main_included']=g.all_routes_reachable & (g[snapcols].max(axis=1)<=max_snap)
                sensitivity.append(dict(period=period,radius_m=radius,max_snap_m=max_snap,**summarize(g)))
        s=summarize(f[f.distance_to_focal_m<=MAIN_RADIUS])
        for car in [0,.25,.5,.75,1.]:
            emissions.append(dict(period=period,assumed_car_share=car,assumed_round_trips=1000,
              additional_travel_share=1.,tailpipe_co2_change_kg=conditional_co2(s['drive_change_roundtrip_km'],car)))
    pd.DataFrame(equity).to_csv(OUT/'equity_comparisons.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(OUT/'access_sensitivity.csv',index=False)
    pd.DataFrame(emissions).to_csv(OUT/'emissions_scenarios.csv',index=False)
    alt=results[results.variant.eq('alternate_chatham_coordinate') & results.event_id.eq('walmart_chatham')]
    alt=summarize(alt[alt.distance_to_focal_m<=MAIN_RADIUS])
    report={'study_period':'2021–2025','analysis_type':'Descriptive historical record and modeled accessibility, not observed behavior or causal effects',
       'projection':'EPSG:26916; NAD83 / UTM zone 16N; metres','network_snapshot':'2023-01-01',
       'walking_speed_kmh':WALK_KMH,'focal_radius_m':MAIN_RADIUS,'max_connector_m':MAX_CONNECTOR,
       'annual_authorization_context':annual,'events':summary,'alternate_chatham_coordinate':alt,
       'mobility_status':'Institutional access verified; provider terms pending user review; not downloaded',
       'important_limitations':['Candidate alternatives are larger SNAP-authorized outlets; physical operating histories for other retailers are not independently verified.',
         'All event comparisons hold the street network fixed. Route lengths describe modeled access.',
         'Origin weights are tract population context, not affected customer counts.',
         'Small number of focal sites; nearby survivors may receive spillovers and are not automatically valid controls.',
         'Nearest-store routing does not measure shopping choices, mode shifts, purchases, trip chaining or realized emissions.']}
    (OUT/'analysis_summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(pd.DataFrame(summary).to_string(index=False))

if __name__=='__main__':main()
