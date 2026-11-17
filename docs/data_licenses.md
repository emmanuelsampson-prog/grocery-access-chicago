# Data attribution and redistribution

The MIT license covers original project code. It does not replace the terms of third-party data.

| Included material | Source and applicable terms | Project modifications |
| --- | --- | --- |
| Retailer-history subset and authorization summaries | [USDA historical SNAP retailer data](https://www.fns.usda.gov/snap/retailer-locator/data), a public federal data release | Regional filtering, standardized address keys, classes and date-specific eligibility. Verified focal business dates are recorded separately. |
| Tract estimates and margins of error | [U.S. Census Bureau ACS](https://www.census.gov/programs-surveys/acs), public federal statistics | Cook County extraction, Chicago tract joins and calculated percentages. |
| Tracts, community areas and inspection corroboration | [City of Chicago Data Portal](https://data.cityofchicago.org), [Data Terms of Use](https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html) | Selected fields, coordinate projection, joins and inspection subsets. Original acquisition dates and checksums remain in the source manifest. |
| Street graphs, node coordinates and route-derived databases | © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/), via [Geofabrik](https://download.geofabrik.de/north-america/us/illinois.html) | January 2023 extract clipped to the documented extent; mode-specific graphs, projected nodes and calculated routes. These adapted databases are distributed under ODbL 1.0. |
| Event facts and source references | Company announcements and contemporaneous reporting, linked in the event ledger | Factual dates, addresses and short original summaries. News articles, photographs and source-page copies are not redistributed. |

The four graph files are in `data/processed/network/` in the repository and full release package. Identical copies are attached individually to the release. `data/network_manifest.json` records their hashes and the original network snapshot. `data/source_manifest.json` preserves acquisition timestamps and source-file hashes; `SHA256SUMS.txt` on the release verifies the downloadable assets.

No licensed mobility source or derived mobility results are included. Provider-term acceptance, input validation and redistribution review are still required before that extension can be published.

## City of Chicago data notice

This site provides applications using data that has been modified for use from its original source, www.cityofchicago.org, the official website of the City of Chicago. The City of Chicago makes no claims as to the content, accuracy, timeliness, or completeness of any of the data provided at this site. The data provided at this site is subject to change at any time. It is understood that the data provided at this site is being used at one's own risk.
