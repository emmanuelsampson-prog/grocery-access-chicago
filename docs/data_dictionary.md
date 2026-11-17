# Data dictionary

Identifiers such as `geoid` and `record_id` must be read as strings. Dates are calendar dates unless a field explicitly states UTC. EPSG:4326 coordinates are longitude and latitude in degrees; `x`, `y`, `origin_x` and `origin_y` use EPSG:26916 metres.

| File | Grain | Key fields and interpretation |
| --- | --- | --- |
| verified_events.csv | One reviewed business event | `event_id`, `event_type`, `event_date` (last open day for closure, first open day for opening), `effective_date`, address, coordinate source, source/corroboration URLs, administrative date gap |
| regional_retailer_history.csv | One historical USDA authorization record | `record_id`, store type, authorization intervals, reviewed intervals, regional coordinates, `inside_chicago`, `is_larger_grocery`, `site_key` standardized address |
| event_inspection_corroboration.csv | One relevant City inspection | Inspection identifiers, observed inspection date, address and coordinates; not a business-date estimate |
| tract_context.csv / .geojson | One Census 2020 tract | ACS 2017–2021 estimates and MOEs; vehicle and poverty shares; projected geographic origin and its method |
| monthly_authorized_inventory.csv | Month × retailer scope | `unique_address_keys` is the authorization footprint, not independently verified operating stores |
| annual_access_context.csv | One December 31 snapshot | City larger-grocery address count; population-weighted straight-line distance and 800 m threshold summary |
| tract_annual_access.geojson | One populated tract | `authorization_nearest_YEAR_km` is straight-line distance, not a route |
| event_access_origins.csv | Origin × event period × coordinate variant | Before/after nearest destinations, walk minutes, directed driving round-trip km, connector lengths, catchment distance, reachability and `main_included` |
| event_access_summary.csv | One focal event | Included/excluded origins and population-context weighted means; increases/decreases/unchanged counts; modeled 15-minute threshold shares |
| equity_comparisons.csv | Event period × context group | Descriptive summaries. Poverty and vehicle groups overlap across classifications. No individual or causal effects |
| access_sensitivity.csv | Event period × radius × connector screen | Same modeled routes under alternative origin-inclusion screens; stricter screens do not reroute to other candidates |
| emissions_scenarios.csv | Event period × assumed car share | Conditional tailpipe kg CO₂ for assumed dedicated trips, not observed emissions |
| analysis_summary.json | One run summary | Specification, result summaries, Chatham coordinate comparison and limitations |
| network/*.npz | Mode-specific sparse graph or nodes | Directed edge lengths in metres; `*_nodes.npz` stores projected node coordinates; source and hashes in network_manifest.json |

`tract_population_context` is the sum of population estimates attached to included origins. Do not treat it as a customer count or multiply it by the route change to estimate total travel. Englewood appears in both closure and replacement comparisons.

USDA larger-grocery classes combine Supermarket, Super Store and Large Grocery Store. They are not an equivalence test for products, service or price. ACS MOEs are retained but not propagated through descriptive subgroup estimates. Missing or suppressed mobility observations must remain missing, never automatically zero.
