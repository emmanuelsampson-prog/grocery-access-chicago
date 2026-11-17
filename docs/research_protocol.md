# Research protocol

## Research question and contribution

How do documented grocery closures and a replacement opening alter nearby residents' access to larger grocery outlets, and how are shopping visits redistributed across remaining destinations? The Chicago study covers 2021–2025, with focal business events in November 2022, April 2023 and May 2023. It separates historical evidence, modeled accessibility and the prospective analysis of observed behavior.

The public-data analysis is complete only for the outputs actually executed in the notebooks. It is not a causal mobility study. Its contribution is a reproducible event ledger, a five-year authorization inventory, explicit date and coordinate audits, fixed-network access comparisons and an empirical foundation for the mobility extension.

## Historical evidence and eligibility

Six events affect five premises: the Englewood Whole Foods closure; the four Walmart closures in Chatham, Kenwood, Lakeview and Little Village; and the Save A Lot opening at the former Whole Foods site. A closure date is the last public operating day. An opening date is the first reported public opening day. Closed locations leave the event inventory on the following day. Publication details are recorded in publication.json; publication is separate from the study and acquisition dates.

USDA SNAP authorizations are a dated public registry of program eligibility. Their start and end dates are not general physical business opening and closure dates. For focal events, the verified physical dates replace the relevant authorization boundary. All other candidate destinations retain their administrative eligibility intervals. The primary eligible classes are USDA Supermarket, Super Store and Large Grocery Store. These classes do not guarantee equivalent prices, product ranges, hours, membership conditions or accessibility for disabled shoppers. The registry omits nonparticipating businesses.

## Geography and access

Chicago's 789 Census 2020 tracts are joined to 2017–2021 ACS estimates and margins of error. This is pre-event context; overlapping ACS five-year estimates are not used as annual outcomes. Analysis coordinates are EPSG:26916, NAD83 / UTM zone 16N, in metres. The projected polygon centroid is the origin when it lies inside its tract; otherwise an interior representative point is used. Neither is a household address or population-weighted residential center.

The regional destination pool includes outlets within 10 km of the Chicago tract union, including out-of-city Illinois and Indiana alternatives. Annual citywide context uses straight-line proximity to authorized larger grocery outlets. It is labeled separately from the routed event analysis.

The event analysis holds a 1 January 2023 OpenStreetMap network fixed. It selects nearest eligible destinations separately for walking distance and driving round-trip distance. A driving return is computed on directed roads and is not assumed equal to the outbound distance. The primary catchment is a 1.6 km straight-line radius from a focal site, with 0.8 and 2.4 km alternatives. The four Walmart closures are applied together; other Walmart locations are retained. The algorithm selects a nearest eligible destination rather than forcing customers to a designated replacement.

Origins and destinations are attached to the largest weakly connected mode-specific network by short straight connectors. The main connector limit is 300 m. The analysis preserves connector lengths and tests stricter screens. The graph does not fully encode turn restrictions, conditional permissions, node barriers, traffic delay, crossing safety or accessibility needs. These are modeled access lengths, not observed routes. Tract population weights summarize neighborhood context and do not estimate affected customers.

The Chatham City inspection record lists 8331 S Stewart Avenue, whereas Walmart and USDA list 8431 S Stewart Avenue. Main results use the USDA point; a separate sensitivity uses the City point while holding the origins fixed. Englewood's two brands use the same City address geocode. All original source coordinates are recoverable from the input files.

## Observed behavior and spatial difference in differences

The licensed mobility extension will first audit data coverage. The primary candidate outcomes are visits to surviving grocery destinations and changes in the distribution of observed shopping destinations. Counts at the closed store mechanically collapse; that alone is not evidence of increased travel or lost grocery consumption.

An event-specific design will distinguish directly exposed neighborhoods, nearby destinations receiving diverted visits, and more distant candidate comparison areas. Spatial exposure must be measured against all documented nearby events. Candidate controls require similar pre-event trends, adequate sample coverage and no overlapping treatment. Nearby surviving outlets are potential spillover recipients, not automatically controls. Distance rings will be tested against pre-event catchments rather than treated as exogenous boundaries.

For multiple closure cohorts, consider group-time treatment effects with clean comparisons, following Callaway and Sant'Anna (2021). Reopening is a treatment reversal: the Englewood vacancy and replacement opening need separate event-specific estimands and windows rather than a single absorbing treatment. Report event-specific dynamics, lead coefficients, pretrend diagnostics, comparison-area balance, anticipation sensitivity and alternative spillover radii. Few independent closure sites limit inference; many tract observations do not create many independent interventions. A placebo or permutation exercise is a diagnostic, not a guarantee of identification. Spatial dependence and cluster uncertainty require explicit treatment.

Business exits respond to demand and profitability. The design must address sorting and declining pretrends; a corporate announcement does not by itself make assignment exogenous. Spatial RDD is not justified by an arbitrary neighborhood or municipal boundary. Spatial IV requires a credible instrument and exclusion restriction; neither is currently identified. They remain possible future designs only if a defensible assignment mechanism is found.

## Emissions

Conditional tailpipe change is extra vehicle round-trip km / 1.609344 × assumed trips × assumed car share × additional-travel share × grams CO2 per mile / 1000. The default illustration uses 1,000 dedicated trips and 400 g CO2 per mile, with car share varied from zero to one. Route distances are already round trips. The illustration excludes upstream emissions, electric-vehicle mix, occupancy, delivery, transit, trip chaining and suppressed travel. It does not establish that closures cause driving or that openings reduce realized emissions.

## References

Callaway, B., and Sant'Anna, P. H. C. (2021). Difference-in-Differences with multiple time periods. Journal of Econometrics, 225(2), 200–230. https://doi.org/10.1016/j.jeconom.2020.12.001

Butts, K. Difference-in-Differences with Spatial Spillovers. Author working paper. https://www.kylebutts.com/papers/spatial-spillovers/

Advan Research. Data dictionaries, Weekly Patterns Plus. https://docs.advanresearch.com/

U.S. Environmental Protection Agency. Greenhouse Gas Emissions from a Typical Passenger Vehicle. https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle
