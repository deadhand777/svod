# US SVOD Market 2021–2022: The Great Deceleration

*Analysis of Dataxis quarterly subscriber data — 131 US platforms, 2021Q1–2022Q4.*
*[Download the one-page PDF](https://github.com/deadhand777/svod/blob/main/report/svod-analysis-2021-2022.pdf).*

## The market in one number

Total US SVOD subscriptions grew from 372.6M in 2021Q1 to 510.3M in 2022Q4. But the growth rate did not hold: year-over-year growth decelerated every single quarter of 2022, from 23.2% (Q1) to 20.2% (Q2) to 18.7% (Q3) to 15.3% (Q4) — a monotonic slowdown, not a one-off dip. The second-order view confirms this: quarter-over-quarter growth acceleration stays negative across 2022, so the slowdown itself is steady rather than driven by a single sharp quarter.

Netflix, the market's bellwether, lost 795,171 subscribers net over the year (67.82M → 67.03M), the single most negative net-add figure of any platform in the dataset. The loss was concentrated in H1 2022 (-607k in Q1, -1.1M in Q2), with only a partial rebound in H2 (+94k Q3, +820k Q4) that was not enough to offset the first-half decline.

<iframe src="charts/market.html" width="100%" height="520" frameborder="0"></iframe>

## A two-speed market — with a twist

Data-driven segmentation (k-means, k=2 chosen by silhouette score = 0.64) splits the 105 fully-observed platforms into two segments, not the three ("giants / challengers / tail") that the "deceleration" framing might suggest. **Segment 1 — hypergrowth challengers** — is a tight group of 7 platforms: Paramount+, Peacock, Discovery+, Fubo, Fox Nation, Dove Channel and Vidgo, averaging 139% growth in 2021 and a still-strong 55% in 2022. **Segment 0 — the broad field** — contains the other 98 platforms, mixing giants and the entire long tail, averaging a much more modest 17% (2021) to 23% (2022) growth.

The twist: giants are not a monolith, and they don't even form their own cluster — they sit inside the broad field alongside long-tail platforms like Mubi and Shudder. Within that field, Netflix and Showtime Streaming actually *shrank* in 2022, while Amazon Prime Video, HBO Max and YouTube Premium *accelerated*. Paramount+ (+15.0M) and Peacock (+11.9M) are the two biggest net-add movers in the entire market — hypergrowth challengers, decelerating but still the market's growth engine.

<iframe src="charts/clusters.html" width="100%" height="520" frameborder="0"></iframe>

## Who moved the market

The net-add ranking over 2021Q4→2022Q4 confirms the two-speed pattern directly: Paramount+ (+14,981,000) and Peacock Premium (+11,915,408) are the market's largest gainers by a wide margin, with Amazon Prime Video (+5,245,681) a distant third. At the other end, Netflix (-795,171) and Showtime Streaming (-433,674) are the two clearest net losers, with Sling TV (-152,000) also declining. The broad field is not uniformly weak — it just lacks the challenger segment's outsized gains. The market-share shift over the same window tells the same story: it is the same gainers that are gaining share and the same losers that are ceding it, not just raw subscriber counts.

<iframe src="charts/waterfall.html" width="100%" height="520" frameborder="0"></iframe>

## Structure and concentration

Market concentration fell steadily throughout the entire two-year window: HHI dropped from 1220 (2021Q1) to 908 (2022Q4), and CR4 fell from 62.3% to 51.0%. Both metrics decline every single quarter — including throughout 2021 — with no visible inflection at the 2021/2022 boundary. This is a continuous fragmentation trend, not a 2022-specific correction: the deconcentration already under way in 2021 is the same process that continued through 2022, just alongside a decelerating overall growth rate.

For 2023, the implication is that overall market growth should keep normalizing while the share war between challengers and giants intensifies further.

<iframe src="charts/concentration.html" width="100%" height="520" frameborder="0"></iframe>

The treemap below breaks that deconcentration down by actor: tile size is ending share, tile color is the share-point change over the window, so the orange (share-gaining) and red (share-losing) tiles side by side are what the falling HHI and CR4 actually consist of.

<iframe src="charts/treemap.html" width="100%" height="520" frameborder="0"></iframe>

*Methodology, quality checks and reproducibility: see [Methodology](methodology.md).*
