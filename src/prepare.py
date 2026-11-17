"""Create the reviewed event ledger, regional retailer inventory and tract context."""
from __future__ import annotations
import json
import zipfile
import re
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import shape
from src.download import ROOT

CRS = 26916  # NAD83 / UTM zone 16N, metres
OUT = ROOT / 'data/processed'
LARGE_TYPES = ['Supermarket', 'Super Store', 'Large Grocery Store']
WALMART = 'https://corporate.walmart.com/news/2023/04/11/walmart-announces-closure-of-four-chicago-stores'
WBEZ = 'https://www.wbez.org/chicago/2023/04/17/walmart-closes-four-stores-in-chicago'
WHOLE = 'https://www.wbez.org/culture-the-arts/2022/11/13/englewood-whole-foods-closes-november-13-2022'
SAVE = 'https://chicago.suntimes.com/2023/5/11/23720073/englewood-save-a-lot-opens-at-former-whole-foods-site-without-fanfare'

def spatial_json(filename):
    records=json.loads((ROOT/'data/raw'/filename).read_text())
    if not records or 'the_geom' not in records[0]:
        raise ValueError(f'No geometry: {filename}')
    return gpd.GeoDataFrame([{k:v for k,v in r.items() if k!='the_geom'} for r in records],
                            geometry=[shape(r['the_geom']) for r in records], crs=4326).to_crs(CRS)

def active(records, date, corrected=False):
    """Authorization end dates are inclusive; physical closure is last open day."""
    prefix='reviewed_' if corrected else 'authorization_'
    date=pd.Timestamp(date)
    return records[(records[prefix+'start']<=date) &
                   (records[prefix+'end'].isna() | (records[prefix+'end']>=date))].copy()

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    tracts=spatial_json('chicago_tracts_2020.json')
    tracts['geoid']=tracts.tract_full.astype(str).str.replace('1400000US','',regex=False)
    if not tracts.geoid.str.fullmatch(r'17031\d{6}').all():
        raise ValueError('Unexpected tract identifier')
    for table in ['B01003','B08201','B17001','B19013']:
        t=pd.read_csv(ROOT/f'data/raw/acs2021_{table.lower()}_cook.dat',sep='|',dtype=str)
        t=t.loc[:,~t.columns.str.startswith('Unnamed')]
        t['geoid']=t.GEO_ID.str.replace('1400000US','',regex=False)
        t=t.drop(columns='GEO_ID')
        for c in t.columns.drop('geoid'):
            t[c]=pd.to_numeric(t[c],errors='coerce').where(lambda s:s>=0)
        tracts=tracts.merge(t,on='geoid',how='left',validate='one_to_one')
    rename={'B01003_E001':'population','B01003_M001':'population_moe',
            'B08201_E001':'households','B08201_M001':'households_moe',
            'B08201_E002':'no_vehicle_households','B08201_M002':'no_vehicle_households_moe',
            'B17001_E001':'poverty_universe','B17001_E002':'below_poverty',
            'B17001_M001':'poverty_universe_moe','B17001_M002':'below_poverty_moe',
            'B19013_E001':'median_income','B19013_M001':'median_income_moe'}
    tracts=tracts.rename(columns=rename)
    tracts=tracts[['geoid','community_area',*rename.values(),'geometry']]
    tracts['no_vehicle_share']=tracts.no_vehicle_households/tracts.households.replace(0,np.nan)
    tracts['poverty_share']=tracts.below_poverty/tracts.poverty_universe.replace(0,np.nan)
    centroid=tracts.geometry.centroid
    origins=centroid.where(tracts.geometry.covers(centroid),tracts.geometry.representative_point())
    tracts['origin_x']=origins.x;tracts['origin_y']=origins.y
    tracts['origin_method']=np.where(tracts.geometry.covers(centroid),'projected centroid','interior representative point')
    tracts.to_file(OUT/'tract_context.geojson',driver='GeoJSON')
    tracts.drop(columns='geometry').to_csv(OUT/'tract_context.csv',index=False)
    spatial_json('community_areas_table.json').to_file(OUT/'community_areas.geojson',driver='GeoJSON')
    boundary=tracts.geometry.union_all()
    with zipfile.ZipFile(ROOT/'data/raw/snap_2005_2025.zip') as archive:
        all_records=pd.read_csv(archive.open(archive.namelist()[0]),dtype=str).fillna('')
    all_records.columns=[c.lower().replace(' ','_') for c in all_records.columns]
    for c in ['latitude','longitude']:
        all_records[c]=pd.to_numeric(all_records[c],errors='coerce')
    # Include Illinois and Indiana alternatives, not just Chicago mailing addresses.
    a=all_records[all_records.latitude.between(41.50,42.20) & all_records.longitude.between(-88.15,-87.30)].copy()
    a['authorization_start']=pd.to_datetime(a.authorization_date,format='%m/%d/%Y',errors='coerce')
    a['authorization_end']=pd.to_datetime(a.end_date,format='%m/%d/%Y',errors='coerce')
    a=a[(a.authorization_start<=pd.Timestamp('2025-12-31')) &
        (a.authorization_end.isna() | (a.authorization_end>=pd.Timestamp('2021-01-01')))].copy()
    points=gpd.GeoDataFrame(a,geometry=gpd.points_from_xy(a.longitude,a.latitude),crs=4326).to_crs(CRS)
    points=points[points.geometry.distance(boundary)<=10000].copy()
    points['inside_chicago']=points.geometry.within(boundary)
    points['is_larger_grocery']=points.store_type.isin(LARGE_TYPES)
    points['address']=(points.street_number+' '+points.street_name).str.strip()
    points['reviewed_start']=points.authorization_start
    points['reviewed_end']=points.authorization_end
    points['coordinate_source']='USDA SNAP retailer file'
    points['date_basis']='SNAP authorization interval'
    specs=[
        ('whole_foods_englewood','Whole Foods, Englewood','1261186','closure','2022-11-13',WHOLE, '2022-11-14',WHOLE),
        ('walmart_chatham','Walmart, Chatham','1037375','closure','2023-04-16',WALMART,'2023-04-17',WBEZ),
        ('walmart_kenwood','Walmart, Kenwood','1166496','closure','2023-04-16',WALMART,'2023-04-17',WBEZ),
        ('walmart_lakeview','Walmart, Lakeview','1087171','closure','2023-04-16',WALMART,'2023-04-17',WBEZ),
        ('walmart_little_village','Walmart, Little Village','1087366','closure','2023-04-16',WALMART,'2023-04-17',WBEZ),
        ('save_a_lot_englewood','Save A Lot, Englewood','1531685','opening','2023-05-11',SAVE,'2023-05-11',SAVE),
    ]
    inspection=pd.read_json(ROOT/'data/raw/food_inspections_2021_2025.json')
    inspections_to_keep=[];events=[]
    for key,label,rid,kind,date,source,effective,corroboration in specs:
        idx=points.index[points.record_id==rid]
        if len(idx)!=1:raise ValueError(f'Expected one reviewed retailer record: {rid}')
        i=idx[0]; row=points.loc[i]
        date=pd.Timestamp(date)
        points.loc[i,'reviewed_end' if kind=='closure' else 'reviewed_start']=date
        points.loc[i,'date_basis']='Verified physical event replaces focal authorization boundary'
        if 'englewood' in key:
            match=inspection[inspection.address.str.contains('832 W 63RD',case=False,na=False)].copy()
            # Both brands occupied the same premises. Use the common City address geocode.
            coord=match[['longitude','latitude']].dropna().median()
            points.loc[i,'longitude']=coord.longitude;points.loc[i,'latitude']=coord.latitude
            points.loc[i,'coordinate_source']='Chicago food-inspection address geocode, 832 W 63rd St'
        else:
            store={'walmart_chatham':'5781','walmart_kenwood':'3166','walmart_lakeview':'5645','walmart_little_village':'5646'}[key]
            match=inspection[inspection.dba_name.str.contains(store,case=False,na=False)].copy()
        match['event_id']=key;inspections_to_keep.append(match)
        lag=(row.authorization_end-date).days if kind=='closure' else (date-row.authorization_start).days
        events.append(dict(event_id=key,label=label,record_id=rid,event_type=kind,event_date=date.date().isoformat(),
            effective_date=effective,address='832 W 63rd St' if 'englewood' in key else row.address,
            longitude=points.loc[i,'longitude'],latitude=points.loc[i,'latitude'],
            coordinate_source=points.loc[i,'coordinate_source'],source_url=source,corroboration_url=corroboration,
            snap_start=row.authorization_start.date().isoformat(),
            snap_end='' if pd.isna(row.authorization_end) else row.authorization_end.date().isoformat(),
            administrative_date_gap_days=int(lag),
            review_note='City lists 8331 S Stewart Ave; retailer and USDA list 8431. Main coordinate uses USDA; alternate coordinate tested separately.' if key=='walmart_chatham' else
            'Common City geocode used for both brands; original USDA Whole Foods point was displaced from the shared address.' if 'englewood' in key else 'Company/store identifier and address corroborated with City inspections'))
    points.geometry=gpd.GeoSeries(gpd.points_from_xy(points.longitude,points.latitude),index=points.index,crs=4326).to_crs(CRS)
    points['x']=points.geometry.x;points['y']=points.geometry.y
    # Address key prevents counting simultaneous administrative records at one premises twice.
    points['site_key']=(points.address.str.upper().str.replace(r'[^A-Z0-9]','',regex=True)+'|'+points.zip_code.str[:5])
    points.loc[points.record_id.isin(['1261186','1531685']),'site_key']='832W63RDST|60621'
    points.drop(columns='geometry').to_csv(OUT/'regional_retailer_history.csv',index=False)
    pd.DataFrame(events).to_csv(OUT/'verified_events.csv',index=False)
    pd.concat(inspections_to_keep).to_csv(OUT/'event_inspection_corroboration.csv',index=False)
    months=[]
    for date in pd.date_range('2021-01-31','2025-12-31',freq='ME'):
        for scope,types in [('larger_grocery',LARGE_TYPES),('all_snap',None)]:
            data=active(points,date)
            if types:data=data[data.store_type.isin(types)]
            data=data[data.inside_chicago]
            months.append(dict(date=date.date().isoformat(),scope=scope,authorized_records=len(data),
                               unique_address_keys=data.site_key.nunique()))
    pd.DataFrame(months).to_csv(OUT/'monthly_authorized_inventory.csv',index=False)
    audit=dict(study_period='2021–2025',publication=json.loads((ROOT/'publication.json').read_text()),
       tracts=len(tracts),populated_tracts=int((tracts.population>0).sum()),
       unmatched_acs_tracts=tracts.loc[tracts.population.isna(),'geoid'].tolist(),
       tract_population_context=float(tracts.population.sum()),regional_authorization_records=len(points),
       regional_larger_grocery_records=int(points.is_larger_grocery.sum()),focal_events=len(events),physical_sites=5,
       projection='EPSG:26916 — NAD83 / UTM zone 16N, metres',
       retailer_extent='Chicago tract union plus 10 km; includes out-of-city alternatives in Illinois and Indiana',
       missing_mobility='Institutional access verified; provider terms pending user review; no observed visit panel downloaded',
       completed='Verified event dates; authorization history; inspection corroboration; Census context',
       limitations=['Authorization dates for other retailers are not verified physical business dates.',
         'Larger grocery class combines USDA Supermarket, Super Store and Large Grocery Store; it is not a product, price or service-quality audit.',
         'One tract origin represents a spatial summary, not every residence or household.',
         'ACS 2017–2021 estimates describe pre-event context, not annual outcomes.'])
    (OUT/'data_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
