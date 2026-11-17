const select=document.querySelector('#event-select');
const summary=document.querySelector('#map-summary');
let events=[];
function draw(){
  const e=events.find(item=>item.id===select.value);if(!e)return;
  const img=document.querySelector('#event-map');img.src=e.png;img.alt=e.label+': before and after tract access';
  document.querySelector('#map-full').href=e.png;
  document.querySelector('#map-svg').href=e.svg;
  const direction=e.change>0?'longer':e.change<0?'shorter':'unchanged';
  summary.textContent=`${e.label}: ${e.n} tract origins. Population-weighted walking equivalent: ${e.before.toFixed(2)} minutes before → ${e.after.toFixed(2)} minutes after (${Math.abs(e.change).toFixed(2)} minutes ${direction}). Modeled access, not observed journeys.`;
  document.querySelector('#tract-values').replaceChildren(...e.tracts.map(t=>{const row=document.createElement('tr');[t.geoid,t.walk_before_minutes.toFixed(2),t.walk_after_minutes.toFixed(2)].forEach(v=>{const cell=document.createElement('td');cell.textContent=v;row.append(cell);});return row;}));
}
fetch('site/event_maps.json').then(r=>{if(!r.ok)throw Error('Map data unavailable');return r.json()}).then(data=>{
  events=data;select.replaceChildren(...events.map(e=>{const o=document.createElement('option');o.value=e.id;o.textContent=e.label+' — '+e.type;return o;}));
  select.value='walmart_kenwood';select.disabled=false;select.addEventListener('change',draw);draw();
}).catch(()=>{summary.textContent='The event selector could not load. The static maps and result tables remain available.';});
