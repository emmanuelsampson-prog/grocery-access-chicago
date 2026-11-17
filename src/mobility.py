"""Validate licensed aggregated store-week inputs without publishing records.

This module deliberately performs no behavioral estimation when the input is
absent. Provider versions must not be pooled without a documented crosswalk.
"""
from pathlib import Path
import pandas as pd
import numpy as np

REQUIRED={'store_id','week','visits','visitors','longitude','latitude','provider_product','provider_version'}

def audit_panel(path):
    path=Path(path)
    if not path.exists():
        return {'status':'awaiting_licensed_data','rows':0,
          'message':'No observed store-week mobility panel has been supplied. No event-study coefficient has been estimated.'}
    frame=pd.read_csv(path,dtype={'store_id':str})
    missing=REQUIRED-set(frame.columns)
    if missing:raise ValueError('Missing required fields: '+', '.join(sorted(missing)))
    frame['week']=pd.to_datetime(frame.week,errors='raise')
    if frame.duplicated(['store_id','week']).any():raise ValueError('Duplicate store-week records')
    if (frame.week.dt.dayofweek!=0).any():raise ValueError('Week must be a local Monday start')
    for c in ['visits','visitors']:
        frame[c]=pd.to_numeric(frame[c],errors='raise')
        if (frame[c].dropna()<0).any():raise ValueError(f'Negative {c}')
    products=frame[['provider_product','provider_version']].drop_duplicates()
    if len(products)!=1:raise ValueError('Mixed provider products or versions require an explicit harmonization review')
    gaps=frame.sort_values('week').groupby('store_id').week.diff().dt.days
    return {'status':'input_present_review_required','rows':len(frame),'stores':frame.store_id.nunique(),
      'first_week':frame.week.min().date().isoformat(),'last_week':frame.week.max().date().isoformat(),
      'missing_visits':int(frame.visits.isna().sum()),'gaps_over_seven_days':int((gaps>7).sum()),
      'causal_ready':False,
      'message':'Coverage alone does not establish a valid comparison group, stable sample or parallel trends.'}

def first_full_post_week(event_date):
    date=pd.Timestamp(event_date).normalize()
    return date+pd.Timedelta(days=7-date.day_of_week)

def event_time(weeks,event_date):
    """Relative weeks; omit the transition week in estimation specifications."""
    return ((pd.to_datetime(weeks)-first_full_post_week(event_date)).dt.days//7).astype(int)

def missing_is_not_zero(frame):
    """Explicitly preserve missing visits when constructing a complete index."""
    output=[]
    for key,group in frame.groupby('store_id'):
        group=group.set_index('week').sort_index()
        index=pd.date_range(group.index.min(),group.index.max(),freq='W-MON')
        aligned=group.reindex(index).rename_axis('week').reset_index()
        aligned['store_id']=key;output.append(aligned)
    return pd.concat(output,ignore_index=True)
