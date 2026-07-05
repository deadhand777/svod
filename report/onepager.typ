#set page(paper: "a4", margin: (x: 1.6cm, y: 1.4cm))
#set text(font: "Libertinus Serif", size: 9.5pt)
#show heading: set text(weight: "bold")
#set par(justify: true)
#show figure: set block(spacing: 0.7em)

#align(center)[
  #text(size: 15pt, weight: "bold")[The US SVOD Market 2021–2022: The Great Deceleration]
  #v(2pt)
  #text(size: 9pt, fill: gray)[Dataxis take-home · quarterly subscriber data, 131 platforms · full reproducible pipeline: https://deadhand777.github.io/svod]
]
#v(4pt)

== The market in one number
Total US SVOD subscriptions grew from 372.6M (2021Q1) to 510.3M (2022Q4), but YoY growth decelerated every quarter of 2022, from 23.2% to 15.3%. Netflix — the market's bellwether — lost 795k subscribers net over the year (H1-driven: -607k in Q1, -1.1M in Q2, with only a partial H2 rebound), the largest decline of any platform in the dataset.

#figure(image("assets/market.png", width: 80%))

== A two-speed market — with a twist
K-means segmentation (k=2, silhouette 0.64) of the 105 fully-observed platforms isolates 7 hypergrowth challengers — Paramount+, Peacock, Discovery+, Fubo, Fox Nation, Dove Channel, Vidgo — averaging 139% growth in 2021 and a still-strong 55% in 2022, out of a 98-platform broad field. Paramount+ (+15.0M) and Peacock (+11.9M) are the two biggest net-add movers in the whole market: challengers, decelerating but still the growth engine. The twist: "giants" are not a monolith — Netflix and Showtime shrank in 2022 while Amazon Prime Video, HBO Max, and YouTube Premium accelerated. A SHAP surrogate check confirms segments are driven by growth regime, not size.

#figure(image("assets/waterfall.png", width: 80%))

== Structure: steady deconcentration, not a 2022 shock
HHI fell from 1220 to 908 and CR4 from 62.3% to 51.0% over the 8 quarters — declining every single quarter, including throughout 2021. The market has been steadily fragmenting since at least early 2021; 2022's growth deceleration happened on top of an already-ongoing redistribution toward challengers, not a new shock. For 2023: expect growth to normalize further while the share war among challengers and giants keeps intensifying.

#v(2pt)
#text(size: 8pt, fill: gray)[
  Method: duckdb aggregation · winsorized growth features · k-means (k=2 by silhouette) · RandomForest+SHAP interpretability check.
  Interactive charts and methodology: https://deadhand777.github.io/svod. Raw Dataxis data excluded from the public repository.
]
