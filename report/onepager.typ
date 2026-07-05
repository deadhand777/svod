#set page(paper: "a4", margin: (x: 1.6cm, top: 1.2cm, bottom: 1.6cm))
#set text(font: "Libertinus Serif", size: 8pt)
#show heading: set text(weight: "bold")
#set par(justify: true, leading: 0.55em)
#show heading: set block(above: 0.6em, below: 0.35em)
#show figure: set block(spacing: 0.5em)

#let navy = rgb("#142F4E")
#let orange = rgb("#EA993F")
#show heading: set text(weight: "bold", fill: navy)

#set page(footer: context {
  if here().page() == 1 {
    line(length: 100%, stroke: 0.5pt + gray)
    v(2pt)
    text(size: 7.5pt, fill: gray)[Method: duckdb aggregation · winsorized growth features · k-means (k=2 by silhouette) · RandomForest+SHAP interpretability check. Interactive charts and methodology: https://deadhand777.github.io/svod. Raw Dataxis data excluded from the public repository.]
  }
})

#align(center)[
  #text(size: 14pt, weight: "bold", fill: navy)[The US SVOD Market 2021–2022: The Great Deceleration]
  #v(1pt)
  #text(size: 9pt, fill: gray)[Dataxis take-home · quarterly subscriber data, 131 platforms · full reproducible pipeline: https://deadhand777.github.io/svod]
]
#v(2pt)
#line(length: 100%, stroke: 1pt + orange)

== The market in one number
#grid(
  columns: (60%, 40%),
  column-gutter: 1em,
  align(horizon)[#figure(image("assets/market.png", width: 95%))],
  [Total US SVOD subscriptions grew from 372.6M (2021Q1) to 510.3M (2022Q4), but YoY growth decelerated every single quarter of 2022 — 23.2% (Q1), 20.2% (Q2), 18.7% (Q3), 15.3% (Q4) — a monotonic slowdown, not a one-off dip. The second-order view confirms it: QoQ growth acceleration stays negative across 2022, so the slowdown itself is steady. Netflix, the market's bellwether, lost 795,171 subscribers net over the year (67.82M → 67.03M) — the most negative net-add figure in the dataset — concentrated in H1 (-607k Q1, -1.1M Q2), with only a partial H2 rebound (+94k Q3, +820k Q4).],
)

== A two-speed market — with a twist
#grid(
  columns: (60%, 40%),
  column-gutter: 1em,
  align(horizon)[#figure(image("assets/clusters.png", width: 95%))],
  [K-means segmentation (k=2 by silhouette 0.64) splits the 105 fully-observed platforms into two segments, not the three the "deceleration" framing suggests. Segment 1 — hypergrowth challengers — is 7 platforms (Paramount+, Peacock, Discovery+, Fubo, Fox Nation, Dove Channel, Vidgo) averaging 139% growth in 2021 and a still-strong 55% in 2022. Segment 0 — the broad field — is the other 98 platforms (giants plus the entire long tail) averaging a modest 17% (2021) to 23% (2022). The twist: giants aren't a monolith and don't form their own cluster — they sit in the broad field beside long-tail platforms like Mubi and Shudder. Netflix and Showtime Streaming shrank in 2022 while Amazon Prime Video, HBO Max and YouTube Premium accelerated. A SHAP surrogate confirms segments are driven by growth regime, not size.],
)

== Who moved the market
#grid(
  columns: (60%, 40%),
  column-gutter: 1em,
  align(horizon)[#figure(image("assets/waterfall.png", width: 95%))],
  [The net-add ranking over 2021Q4→2022Q4 confirms the two-speed pattern directly: Paramount+ (+14,981,000) and Peacock Premium (+11,915,408) are the market's largest gainers by a wide margin, with Amazon Prime Video (+5,245,681) a distant third. At the other end, Netflix (-795,171) and Showtime Streaming (-433,674) are the two clearest net losers, with Sling TV (-152,000) also declining. The broad field is not uniformly weak — it just lacks the challenger segment's outsized gains. The market-share shift over the same window tells the same story: the same gainers are gaining share and the same losers ceding it, not just raw subscriber counts.],
)

== Structure and concentration
#grid(
  columns: (60%, 40%),
  column-gutter: 1em,
  align(horizon)[#figure(image("assets/concentration.png", width: 95%))],
  [Market concentration fell steadily across the whole window: HHI dropped from 1220 (2021Q1) to 908 (2022Q4) and CR4 from 62.3% to 51.0%, declining every single quarter — including throughout 2021 — with no inflection at the 2021/2022 boundary. This is a continuous fragmentation trend, not a 2022-specific correction: the deconcentration already under way in 2021 is the same process that continued through 2022, alongside a decelerating overall growth rate. For 2023: expect growth to keep normalizing while the share war between challengers and giants intensifies further.],
)
