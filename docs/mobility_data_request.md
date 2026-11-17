# Mobility data specification

Study window: 1 January 2021 through 31 December 2025. Publication details: see publication.json.

Penn Libraries documents institutional access to Dewey at https://www.library.upenn.edu/lippincott/datapoints/data-access-dewey-2025. Institutional access to Weekly Patterns Plus was verified on 16 November 2026 (America/New_York). The catalog lists coverage from 2 January 2017 to 19 October 2026 and a 7 November 2026 refresh. The provider's additional terms still require the account holder's review and acceptance before download. No mobility export has been downloaded for this project.

Dataset citation: Advan Research (2025), Foot Traffic / Weekly Patterns Plus, Dewey Data, https://doi.org/10.82551/C103-N851. This records availability, not completed use of the licensed data. Do not redistribute the source table or private account information in the project.

## Request and geographic extent

Use a single consistent version of Advan Weekly Patterns or Weekly Patterns Plus for Chicago and a 10 km buffer. Request all grocery competitors in this extent, not only the six focal records. The verified event ledger provides matching addresses and company store numbers; a reviewer must resolve provider POI identities, geofences, relocations and changes of brand. Whole Foods and Save A Lot at 832 W 63rd Street require distinct business identities even when the physical geofence is shared.

Retain local Monday-start weeks; persistent store and location identifiers; brand; address; coordinates; NAICS; open and close metadata; visits and visitors; provider product/version; sampling/normalization fields and flags; and authorized aggregate home-origin fields when permitted. Never publish device traces or small origin cells. Public release of licensed aggregates is subject to the actual contract, not inferred from institutional access.

## Canonical local input

Save a reviewed aggregate file as `data/restricted/store_week.csv` with:

| Column | Meaning |
| --- | --- |
| store_id | Reviewed stable business identifier |
| week | Local Monday date, YYYY-MM-DD |
| visits | Provider visit count or estimate, with units documented |
| visitors | Provider unique visitor count or estimate |
| longitude, latitude | Reviewed POI coordinate, EPSG:4326 |
| provider_product, provider_version | Product and fixed release/version |
| normalization_denominator | Optional documented sampling denominator |
| suppressed | Optional provider suppression indicator |

The canonical schema intentionally does not silently map `raw_visit_counts` to `visit_counts`: different products have different meanings. Document the conversion, version and units before running the validator. Missing and suppressed rows must not be converted to zero. Retain actual provider file checksums in a private manifest.

## Interpretation checks

Advan's current documentation (https://docs.advanresearch.com/) distinguishes visitation and trade-area panels. Trade-area origin values should be treated as ratios or scaled indicators rather than absolute longitudinal visitor counts. Its distance-from-home field is a median haversine distance from a home geohash to the POI, not a measured street journey. Neither this field nor a foot-traffic count identifies walking or driving.

Audit at least a full seasonal cycle before and after each event where the event history permits it. For the Whole Foods vacancy effect, the post-closure window ends before Save A Lot opens; a full year of untreated vacancy is not available. Record announced closures and anticipation: Whole Foods announced its exit months before its last day, while Walmart announced the four closures on 11 April 2023. Examine both announcement and operating dates in sensitivity work.

## Required before estimating an effect

1. Match identities and geofences and inspect known business-date discrepancies.
2. Plot coverage, missingness, panel normalization and seasonality before fitting models.
3. Audit other grocery changes in treated and comparison catchments.
4. Define treatment, spatial spillovers and controls before inspecting treatment coefficients.
5. Review the license for permitted aggregate outputs; keep raw inputs private.
6. Report comparisons as descriptive if the data cannot support causal identification.
