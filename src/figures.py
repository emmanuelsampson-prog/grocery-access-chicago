"""Consistent Matplotlib figures for notebooks, web and academic report."""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import Normalize,TwoSlopeNorm
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from src.download import ROOT
from src.prepare import CRS

DATA=ROOT/'data/processed';FIG=ROOT/'outputs/figures'
BLUE='#1f77b4';ORANGE='#ff7f0e';GRAY='#7f7f7f'
PERIOD_LABELS={'whole_foods_closure':'Whole Foods closure','walmart_closures':'Four Walmart closures','save_a_lot_opening':'Save A Lot opening'}

def style():
    plt.rcdefaults()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
      'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,
      'figure.titlesize':13,'axes.spines.top':False,'axes.spines.right':False,
      'axes.axisbelow':True,'savefig.dpi':200,'figure.facecolor':'white','savefig.facecolor':'white',
      'svg.fonttype':'none','pdf.fonttype':42})

def finish(fig,name,note,rect=(0,.085,1,.94)):
    fig.text(.015,.015,note,ha='left',va='bottom',fontsize=8,color='#444444',wrap=True)
    fig.tight_layout(rect=rect)
    for ext in ['png','svg']:
        fig.savefig(FIG/f'{name}.{ext}',bbox_inches='tight')
    plt.close(fig)

def furniture(ax,bounds,scale=5000,padding=1000):
    x0,y0,x1,y1=bounds
    ax.set_xlim(x0-padding,x1+padding);ax.set_ylim(y0-padding,y1+padding)
    ax.set_aspect('equal');ax.set_axis_off()
    sx=x0+(x1-x0)*.06;sy=y0+(y1-y0)*.04
    ax.plot([sx,sx+scale],[sy,sy],color='#333333',lw=2)
    ax.text(sx+scale/2,sy+(y1-y0)*.025,f'{scale/1000:g} km',ha='center',fontsize=8)
    ax.annotate('N',xy=(.94,.94),xytext=(.94,.85),xycoords='axes fraction',ha='center',fontsize=9,
                arrowprops={'arrowstyle':'-|>','color':'#333333'})

def base(ax,tracts):
    tracts.plot(ax=ax,color='#f0f0f0',edgecolor='#c8c8c8',linewidth=.15)
    tracts.dissolve().boundary.plot(ax=ax,color='#666666',linewidth=.6)

def main():
    FIG.mkdir(exist_ok=True,parents=True);style()
    tracts=gpd.read_file(DATA/'tract_context.geojson').to_crs(CRS)
    events=pd.read_csv(DATA/'verified_events.csv',dtype={'record_id':str})
    ep=gpd.GeoDataFrame(events,geometry=gpd.points_from_xy(events.longitude,events.latitude),crs=4326).to_crs(CRS)
    sites=ep[ep.event_type.eq('closure')].reset_index(drop=True)
    bounds=tracts.total_bounds
    fig=plt.figure(figsize=(9.5,7.0))
    ax=fig.add_axes([.33,.13,.49,.76])
    tracts.plot(column='no_vehicle_share',ax=ax,cmap='viridis',vmin=0,vmax=.65,edgecolor='white',linewidth=.18,
       missing_kwds={'color':'#eeeeee'})
    sites.plot(ax=ax,color='white',edgecolor='black',linewidth=1.2,markersize=95,zorder=3)
    for i,r in sites.iterrows():ax.annotate(str(i+1),(r.geometry.x,r.geometry.y),ha='center',va='center',fontsize=8,zorder=4)
    furniture(ax,bounds);fig.suptitle('Chicago grocery events and household vehicle access',y=.96)
    cb=fig.colorbar(ScalarMappable(norm=Normalize(0,.65),cmap='viridis'),cax=fig.add_axes([.85,.26,.02,.42]),extend='max')
    cb.set_label('Households without a vehicle (%)');cb.set_ticks([0,.15,.3,.45,.6]);cb.set_ticklabels(['0','15','30','45','60'])
    labels='\n'.join(f'{i+1}. {r.label}' for i,r in sites.iterrows())
    fig.text(.025,.80,labels,va='top',fontsize=10,linespacing=1.9)
    fig.text(.025,.45,'Five physical sites\nSix verified events\nStudy period: 2021–2025',va='top',fontsize=10,linespacing=1.8)
    fig.text(.025,.035,'Sources: Chicago Census 2020 tracts; ACS 2017–2021; verified retailer events. EPSG:26916, metres.\nEnglewood Whole Foods and Save A Lot share one location. Tract percentages are neighborhood context.',fontsize=8,color='#444444')
    for ext in ['png','svg']:fig.savefig(FIG/f'01_study_map.{ext}',bbox_inches='tight')
    plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,4.6))
    order=events.copy();order['event_date']=pd.to_datetime(order.event_date)
    for i,r in order.iterrows():
        ax.plot([pd.Timestamp('2022-10-01'),r.event_date],[i,i],color='#d5d5d5',lw=1)
        ax.scatter(r.event_date,i,color=BLUE if r.event_type=='closure' else ORANGE,s=58,zorder=3)
        ax.annotate(r.event_date.strftime('%d %b %Y'),(r.event_date,i),xytext=(9,0),textcoords='offset points',va='center',fontsize=9)
    ax.set_yticks(range(len(order)),order.label);ax.invert_yaxis()
    ax.set_ylim(len(order)+.15,-.5)
    ax.set_xlim(pd.Timestamp('2022-10-01'),pd.Timestamp('2023-07-30'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(axis='x',alpha=.2);ax.set_title('Six verified events at five grocery locations');ax.set_xlabel('Last day open for closures; first public opening day for Save A Lot')
    ax.legend(handles=[Line2D([],[],color=BLUE,marker='o',ls='',label='Closure'),Line2D([],[],color=ORANGE,marker='o',ls='',label='Opening')],loc='lower left',ncol=2)
    finish(fig,'02_event_timeline','Sources: Walmart announcement and WBEZ reporting; WBEZ and Chicago Sun-Times for Englewood.\nThe wider study window is 2021–2025; the focal events occur in 2022–2023.')

    inventory=pd.read_csv(DATA/'monthly_authorized_inventory.csv',parse_dates=['date'])
    fig,axs=plt.subplots(1,2,figsize=(10,4.2))
    for ax,scope,title in zip(axs,['larger_grocery','all_snap'],['Larger grocery outlets','All SNAP retailer types']):
        d=inventory[inventory.scope.eq(scope)]
        ax.plot(d.date,d.unique_address_keys,color=BLUE,lw=1.8)
        ax.set_title(title);ax.set_ylabel('Authorized address keys');ax.grid(alpha=.2)
        ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        pad=10 if scope=='larger_grocery' else 30
        ax.set_ylim(d.unique_address_keys.min()-pad,d.unique_address_keys.max()+pad)
        ax.set_xlim(pd.Timestamp('2021-01-01'),pd.Timestamp('2025-12-31'));ax.set_xlabel('Month-end snapshot')
    fig.suptitle('The wider retail setting, 2021–2025')
    finish(fig,'03_inventory_history','Source: USDA historical SNAP retailer file, as of 31 December 2025. Unique standardized addresses within Chicago.\nThese are program authorizations, not counts of verified physical openings and closures.')

    fig,ax=plt.subplots(figsize=(10,4.6))
    for i,r in events.iterrows():
        physical=pd.Timestamp(r.event_date);administrative=pd.Timestamp(r.snap_end if r.event_type=='closure' else r.snap_start)
        ax.plot([physical,administrative],[i,i],color=GRAY,lw=1.5)
        ax.scatter(physical,i,color=BLUE,s=45,zorder=3);ax.scatter(administrative,i,color=ORANGE,marker='s',s=35,zorder=3)
        ax.annotate(f'{r.administrative_date_gap_days} days',(max(physical,administrative),i),xytext=(9,0),textcoords='offset points',va='center',fontsize=9)
    ax.set_yticks(range(len(events)),events.label);ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
    ax.set_ylim(len(events)+.15,-.5)
    ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlim(pd.Timestamp('2022-10-20'),pd.Timestamp('2023-07-01'));ax.set_title('Business events and administrative dates differ')
    ax.legend(handles=[Line2D([],[],color=BLUE,marker='o',ls='',label='Verified business date'),Line2D([],[],color=ORANGE,marker='s',ls='',label='SNAP authorization boundary')],ncol=2,loc='lower left')
    finish(fig,'04_date_audit','Sources: verified event ledger and USDA authorization dates. Gap is an absolute calendar-day difference.\nThe physical event dates, rather than the authorization boundaries, define the focal comparisons.')

    if not (DATA/'analysis_summary.json').exists():return
    annual=gpd.read_file(DATA/'tract_annual_access.geojson').to_crs(CRS)
    fig,axs=plt.subplots(1,2,figsize=(10,7))
    for ax,year in zip(axs,[2021,2025]):
        base(ax,tracts);annual.plot(column=f'authorization_nearest_{year}_km',ax=ax,cmap='viridis',vmin=0,vmax=2.5,edgecolor='white',linewidth=.12)
        furniture(ax,bounds);ax.set_title(f'31 December {year}')
    cb=fig.colorbar(ScalarMappable(norm=Normalize(0,2.5),cmap='viridis'),cax=fig.add_axes([.90,.28,.018,.43]),extend='max')
    cb.set_label('Straight-line distance to nearest eligible outlet (km)')
    fig.suptitle('Citywide access to larger SNAP-authorized grocery outlets')
    fig.subplots_adjust(left=.01,right=.86,bottom=.12,top=.91,wspace=.02)
    fig.text(.015,.025,'Sources: USDA authorization history; Chicago tracts. Same scale and origins in both panels.\nStraight-line distances are not walking routes. Gray tracts have no population estimate above zero.',fontsize=8,color='#444444')
    for ext in ['png','svg']:fig.savefig(FIG/f'05_citywide_before_after.{ext}',bbox_inches='tight')
    plt.close(fig)

    routes=pd.read_csv(DATA/'event_access_origins.csv',dtype={'geoid':str})
    routes=routes[routes.variant.eq('main') & routes.main_included]
    joined=tracts.merge(routes,on='geoid',how='inner',suffixes=('','_r'))
    fig,axs=plt.subplots(2,3,figsize=(11.5,8.4))
    lim=max(5,float(np.ceil(routes.walk_change_minutes.abs().max()/5)*5))
    for ax,(_,event) in zip(axs.flat,ep.iterrows()):
        g=joined[joined.event_id.eq(event.event_id)]
        x,y=event.geometry.x,event.geometry.y
        local_bounds=(x-2500,y-2500,x+2500,y+2500)
        local=tracts.cx[local_bounds[0]:local_bounds[2],local_bounds[1]:local_bounds[3]]
        base(ax,local)
        g.plot(column='walk_change_minutes',ax=ax,cmap='RdBu_r',vmin=-lim,vmax=lim,edgecolor='#777777',linewidth=.3)
        ax.scatter(x,y,color='black',s=15,zorder=5)
        furniture(ax,local_bounds,scale=1000,padding=0);ax.set_title(event.label,fontsize=11)
    cb=fig.colorbar(ScalarMappable(norm=Normalize(-lim,lim),cmap='RdBu_r'),cax=fig.add_axes([.91,.26,.016,.48]))
    cb.set_label('After minus before: modeled walking minutes')
    fig.suptitle('Where modeled walking access changes around the focal events')
    fig.subplots_adjust(left=.025,right=.88,bottom=.12,top=.90,wspace=.10,hspace=.20)
    fig.text(.015,.025,'Same map extent (5 × 5 km) and color scale in every panel. Gray: outside the included comparison.\nFixed January 2023 OSM network; 4.8 km/h. Each shade represents a tract origin, not every household.',fontsize=8,color='#444444')
    for ext in ['png','svg']:fig.savefig(FIG/f'06_event_change_maps.{ext}',bbox_inches='tight')
    plt.close(fig)

    summary=pd.read_csv(DATA/'event_access_summary.csv').merge(events[['event_id','label']],on='event_id')
    fig,axs=plt.subplots(1,2,figsize=(11,4.8),sharey=True)
    for ax,mode,unit,title in [(axs[0],'walk','minutes','Walking minutes, one way'),(axs[1],'drive','roundtrip_km','Driving kilometres, round trip')]:
        for i,r in summary.iterrows():
            b=r[f'{mode}_before_{unit}'];a=r[f'{mode}_after_{unit}']
            ax.plot([b,a],[i,i],color=GRAY,lw=1.5);ax.scatter(b,i,color=BLUE,s=45,zorder=3);ax.scatter(a,i,color=ORANGE,s=45,zorder=3)
        ax.set_title(title);ax.grid(axis='x',alpha=.2);ax.set_xlim(left=0);ax.set_xlabel('Population-weighted tract-origin mean')
    axs[0].set_yticks(range(len(summary)),[f'{r.label} (n={r.included_origins})' for r in summary.itertuples()]);axs[0].invert_yaxis()
    axs[1].legend(handles=[Line2D([],[],color=BLUE,marker='o',ls='',label='Before'),Line2D([],[],color=ORANGE,marker='o',ls='',label='After')],loc='upper left')
    fig.suptitle('Before and after access from the same neighborhood origins')
    finish(fig,'07_paired_event_results','Nearest eligible destination is selected separately for walking and driving. n = included tract origins.\nThese are modeled access comparisons. Population weights do not count affected shoppers.')

    fig,axs=plt.subplots(1,2,figsize=(9,4.8))
    colors=[BLUE,ORANGE,'#2ca02c']
    for ax,b,a,title in [(axs[0],'walk_before_minutes','walk_after_minutes','Walking minutes, one way'),(axs[1],'drive_before_roundtrip_km','drive_after_roundtrip_km','Driving kilometres, round trip')]:
        hi=float(routes[[b,a]].max().max())*1.08
        ax.plot([0,hi],[0,hi],'--',lw=1,color=GRAY,label='No change')
        for color,(period,label) in zip(colors,PERIOD_LABELS.items()):
            d=routes[routes.period.eq(period)];ax.scatter(d[b],d[a],color=color,s=24,alpha=.7,label=label)
        ax.set(xlim=(0,hi),ylim=(0,hi),xlabel='Before',ylabel='After');ax.set_title(title);ax.set_aspect('equal');ax.grid(alpha=.2)
    axs[1].legend(loc='upper left',fontsize=8)
    finish(fig,'08_before_after_scatter','Each point is a tract origin within one event comparison. Above the diagonal means longer modeled access after the event.\nEnglewood origins appear in separate closure and replacement-opening comparisons.')

    equity=pd.read_csv(DATA/'equity_comparisons.csv')
    d=equity[equity.period.eq('walmart_closures')]
    fig,ax=plt.subplots(figsize=(9,4.2))
    ax.barh(d.group,d.walk_change_minutes,color=BLUE,height=.55)
    for i,r in enumerate(d.itertuples()):ax.text(r.walk_change_minutes+.025,i,f'{r.walk_change_minutes:.2f} min; n={r.included_origins}',va='center',fontsize=9)
    ax.set_xlabel('Population-weighted change in walking minutes');ax.set_title('Walmart closures: comparisons by neighborhood characteristics')
    ax.set_xlim(0,max(.5,d.walk_change_minutes.max()*1.55));ax.grid(axis='x',alpha=.2);ax.invert_yaxis()
    finish(fig,'09_equity_comparison','ACS 2017–2021 context. Poverty and vehicle availability are separate classifications, not mutually exclusive groups.\nDescriptive comparison of included origins; no causal subgroup effect or household behavior is estimated.')

    emissions=pd.read_csv(DATA/'emissions_scenarios.csv')
    fig,ax=plt.subplots(figsize=(9,4.5))
    for color,(period,label) in zip(colors,PERIOD_LABELS.items()):
        d=emissions[emissions.period.eq(period)];ax.plot(d.assumed_car_share*100,d.tailpipe_co2_change_kg,marker='o',color=color,label=label)
    ax.axhline(0,color=GRAY,lw=1);ax.set(xlabel='Assumed share of trips made by car (%)',ylabel='Change in tailpipe CO₂ (kg per 1,000 trips)')
    ax.set_title('Emissions implications depend on travel assumptions');ax.grid(alpha=.2);ax.legend()
    finish(fig,'10_emissions_sensitivity','Scenario: 1,000 dedicated round trips; one vehicle per car trip; all extra route distance is additional travel.\nEPA illustrative factor: 400 g CO₂/mile. This is not a measurement of realized emissions or mode shifts.')
    print('Saved ten figures in PNG and SVG')

if __name__=='__main__':main()
