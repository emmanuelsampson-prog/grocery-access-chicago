"""Download public sources with byte-level provenance; no credentials required."""
from __future__ import annotations
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"

def download(key, url, filename, description, expected=None):
    path = RAW / filename
    sidecar = path.with_suffix(path.suffix + ".provenance.json")
    if path.exists() and sidecar.exists():
        item = json.loads(sidecar.read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f"Input checksum changed: {filename}")
        return item
    response = requests.get(url, timeout=(20, 180))
    response.raise_for_status()
    content = response.content
    if expected == "zip" and not content.startswith(b"PK"):
        raise ValueError("Expected ZIP response")
    if expected == "json":
        json.loads(content)
    path.write_bytes(content)
    item = dict(id=key, url=url, file=str(path.relative_to(ROOT)), description=description,
                retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
    sidecar.write_text(json.dumps(item, indent=2) + "\n")
    return item

def acs_table(table):
    """Retain exact Cook County tract lines from the Census national bulk file.

    The national response is streamed and hashed, not retained. Estimate and
    margin-of-error columns remain intact in the county extraction.
    """
    path = RAW / f"acs2021_{table.lower()}_cook.dat"
    sidecar = path.with_suffix(".provenance.json")
    if path.exists() and sidecar.exists():
        item = json.loads(sidecar.read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f"Input checksum changed: {path.name}")
        return item
    url = ("https://www2.census.gov/programs-surveys/acs/summary_file/2021/"
           f"table-based-SF/data/5YRData/acsdt5y2021-{table.lower()}.dat")
    digest = hashlib.sha256()
    total = 0
    selected = []
    remainder = b""
    with requests.get(url, stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        for chunk in response.iter_content(1024 * 1024):
            total += len(chunk)
            digest.update(chunk)
            lines = (remainder + chunk).split(b"\n")
            remainder = lines.pop()
            for line in lines:
                if not selected:
                    if not line.startswith(b"GEO_ID|"):
                        raise ValueError("Unexpected Census schema")
                    selected.append(line)
                elif line.startswith(b"1400000US17031"):
                    selected.append(line)
        if remainder.startswith(b"1400000US17031"):
            selected.append(remainder)
    if len(selected) < 1000:
        raise ValueError("Incomplete Cook County extraction")
    content = b"\n".join(selected) + b"\n"
    path.write_bytes(content)
    item = dict(id=f"acs2021_{table}", url=url, file=str(path.relative_to(ROOT)),
                description="2017–2021 ACS five-year estimates and margins of error; Cook County tracts",
                extraction="GEO_ID starts with 1400000US17031", rows=len(selected)-1,
                retrieved_at_utc=datetime.now(timezone.utc).isoformat(), bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(), national_source_bytes=total,
                national_source_sha256=digest.hexdigest())
    sidecar.write_text(json.dumps(item, indent=2) + "\n")
    return item

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    inspections = urlencode({
        "$select":"inspection_id,dba_name,aka_name,license_,facility_type,risk,address,city,state,zip,inspection_date,inspection_type,results,latitude,longitude",
        "$where":"inspection_date >= '2021-01-01T00:00:00' AND inspection_date < '2026-01-01T00:00:00' AND (upper(facility_type) like '%GROCERY%' OR upper(dba_name) like '%WAL%MART%' OR upper(dba_name) like '%WHOLE FOODS%' OR upper(dba_name) like '%SAVE%A%LOT%')",
        "$order":"inspection_id", "$limit":50000})
    jobs = [
        ("snap_history", "https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip", "snap_2005_2025.zip", "USDA historical SNAP authorizations as of 31 December 2025; dates are program authorizations, not physical business events", "zip"),
        ("tracts_2020", "https://data.cityofchicago.org/resource/7qjk-677h.json?$limit=5000", "chicago_tracts_2020.json", "City of Chicago Census 2020 tract polygons; Census Bureau boundaries", "json"),
        ("community_areas_table", "https://data.cityofchicago.org/resource/igwz-8jzy.json?$limit=100", "community_areas_table.json", "City of Chicago community area boundaries (underlying spatial table)", "json"),
        ("food_inspections", "https://data.cityofchicago.org/resource/4ijn-s7e5.json?" + inspections, "food_inspections_2021_2025.json", "Chicago food inspections 2021–2025: grocery facilities and named chains. Inspection dates are evidence of visits, not store opening/closure dates", "json"),
        ("osm_2023", "https://download.geofabrik.de/north-america/us/illinois-230101.osm.pbf", "illinois-230101.osm.pbf", "OpenStreetMap Illinois extract dated 1 January 2023, via Geofabrik; fixed street network for all event comparisons; ODbL 1.0", None),
    ]
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[(args[0],pool.submit(download,*args)) for args in jobs]
        futures += [(table,pool.submit(acs_table,table)) for table in ['B01003','B08201','B17001','B19013']]
        for key, future in futures:
            item = future.result()
            records.append(item)
            print(key, item.get('rows', ''), item['bytes'], flush=True)
    (ROOT / "data/source_manifest.json").write_text(json.dumps(records, indent=2) + "\n")

if __name__ == '__main__':
    main()
