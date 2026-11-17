"""Fixed January 2023 OSM street graph for modeled access comparisons.

Nodes and length measurements are projected to NAD83 / UTM 16N (metres).
Drive graphs respect way-level one-way tags, but not relation turn restrictions.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import osmium
from pyproj import Transformer
from scipy.sparse import coo_matrix,save_npz
from src.download import ROOT

BBOX=(-87.92,41.62,-87.50,42.04)
COMMON={'abandoned','construction','no','planned','platform','proposed','raceway','razed'}
WALK=COMMON|{'motorway','motorway_link','bus_guideway','cycleway','rest_area','services'}
DRIVE=COMMON|{'bridleway','bus_guideway','cycleway','elevator','escalator','footway','path','pedestrian','steps','track','corridor'}

def usable(tags,mode):
    if 'highway' not in tags or tags.get('area')=='yes':return False
    explicit=tags.get('foot') if mode=='walk' else tags.get('motorcar',tags.get('motor_vehicle'))
    if explicit in {'no','private'}:return False
    if tags.get('access') in {'no','private'} and explicit not in {'yes','designated','permissive','destination'}:return False
    return tags['highway'] not in (WALK if mode=='walk' else DRIVE)

class Roads(osmium.SimpleHandler):
    def __init__(self):
        super().__init__();self.nodes={};self.edges={'walk':{},'drive':{}}
    def node(self,n):
        if n.location.valid():
            x,y=n.location.lon,n.location.lat
            if BBOX[0]<=x<=BBOX[2] and BBOX[1]<=y<=BBOX[3]:self.nodes[n.id]=(x,y)
    def way(self,w):
        tags=dict(w.tags)
        modes=[m for m in self.edges if usable(tags,m)]
        if not modes:return
        refs=[n.ref for n in w.nodes]
        one=tags.get('oneway')
        if one is None and (tags.get('junction')=='roundabout' or tags.get('highway') in {'motorway','motorway_link'}):one='yes'
        for u,v in zip(refs,refs[1:]):
            if u not in self.nodes or v not in self.nodes or u==v:continue
            for mode in modes:
                direction=one if mode=='drive' else tags.get('oneway:foot','no')
                if direction!='-1':self.edges[mode][u,v]=None
                if direction not in {'yes','1','true'}:self.edges[mode][v,u]=None

def main():
    output=ROOT/'data/processed/network';output.mkdir(exist_ok=True,parents=True)
    pbf=ROOT/'data/raw/illinois-230101.osm.pbf'
    reader=osmium.io.Reader(str(pbf));snapshot=reader.header().get('osmosis_replication_timestamp');reader.close()
    if not snapshot.startswith('2023-01-01'):raise ValueError(snapshot)
    h=Roads();h.apply_file(str(pbf));print('Parsed street nodes',len(h.nodes),flush=True)
    transform=Transformer.from_crs(4326,26916,always_xy=True)
    manifest={'snapshot_utc':snapshot,'crs':'EPSG:26916','bbox_west_south_east_north':BBOX,
      'source_url':'https://download.geofabrik.de/north-america/us/illinois-230101.osm.pbf',
      'license':'© OpenStreetMap contributors, ODbL 1.0; Geofabrik distribution',
      'limitations':'Fixed network for all dates. No traffic, turn restrictions, conditional permissions, comprehensive node barriers, mode choice or observed trajectories. Short straight connectors attach address and origin points to graph nodes.',
      'files':[]}
    for mode in ['walk','drive']:
        edges=np.array(list(h.edges[mode]),dtype=np.int64)
        ids=np.unique(edges);idx={n:i for i,n in enumerate(ids)}
        lonlat=np.array([h.nodes[n] for n in ids]);x,y=transform.transform(lonlat[:,0],lonlat[:,1]);xy=np.c_[x,y]
        u=np.array([idx[n] for n in edges[:,0]],dtype=np.int32);v=np.array([idx[n] for n in edges[:,1]],dtype=np.int32)
        length=np.linalg.norm(xy[u]-xy[v],axis=1)
        graph=coo_matrix((length,(u,v)),shape=(len(ids),len(ids))).tocsr()
        save_npz(output/f'{mode}.npz',graph)
        np.savez_compressed(output/f'{mode}_nodes.npz',ids=ids,xy=xy)
        manifest['files'].append({'mode':mode,'nodes':len(ids),'edges':len(edges),
            'graph_sha256':hashlib.sha256((output/f'{mode}.npz').read_bytes()).hexdigest(),
            'node_sha256':hashlib.sha256((output/f'{mode}_nodes.npz').read_bytes()).hexdigest()})
        print(mode,len(ids),len(edges),flush=True)
    (ROOT/'data/network_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
