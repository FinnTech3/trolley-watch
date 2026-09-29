# Design decisions

The questions I would expect to be asked about this, and the answers.

## Why rebuild the official index at all?

Because the question is about a split of the official index, so the split is
only worth anything if the whole matches. The price quotes come with no
instructions for turning them into the published numbers; the method in
`indices.py` is the one that reproduces them, found by trying the
alternatives against every item and month. Until it matched, there was
nothing to split.

## Why a tolerance of 0.02 index points?

The ONS publishes item indices to three decimal places, and 4,761 of the
7,715 item-months match to all three. The rest differ in the second or third
decimal, which I put down to prices and base prices that the file stores
rounded. The largest gap outside imputed items is 0.017, so 0.02 is a
tolerance the data meets with a little room, not one chosen to let something
through. The twins miss it by thousands of item-months.

## Why not gate the imputed items?

During 2021 the ONS could not collect some items in some places and filled
the gaps, flagging those item-months as partly or fully imputed. Their
published values are not made from the quotes in the file alone, so failing
to reproduce them would say nothing about the method. They are counted and
reported (135 of them, worst 0.36) rather than dropped silently.

## Why rank on the midpoint of two prices?

Ranking a quote on its January price and then measuring its change from
January builds in regression to the mean: anything that made the January
price unusually low makes the later change unusually high. Ranking on the
later price does the opposite. The midpoint of the two logarithms is
uncorrelated with the chance part of the change, as long as the chance part
is as big in January as in the later month. The tests show it on prices
with a known answer, and the data show it too: in 2024, when there was
little to separate the thirds, they came out within 0.2 points of each
other.

## Why within each region and shop type, not across the country?

The ONS's index is built stratum by stratum, and splitting within each
stratum keeps its structure: each region and shop type keeps its own cheap
end, and the stratum weights still apply. Splitting across the whole
country instead mixes in where the shop is. Both are reported, and they agree
within half a point.

## Why share the January change between the thirds?

Because there is nothing else to use. Each January the ONS replaces part of
its sample and publishes the new sample's prices, not the old one's January
prices, so a quote cannot be followed from December into January. I tried
matching quotes across the new year by shop and series, and the matched
changes did not reproduce the published January item indices anywhere near
as closely as the rest of the year's quotes reproduce theirs, so I did not
trust them. Giving every third its item's published January change is
conservative: any difference between the thirds in those three months is
left out.

## Why not show each item's cheap and dear prices in the app?

Because they are noise. An item has a few hundred quotes a month; a third of
them, a few dozen, split across strata, with products coming and going.
Breakfast cereal's cheap third comes out 3% down over the four years and its
middle third 51% up, which no one should act on. Across a hundred and fifty
items the noise averages out, so the thirds are reported for food as a whole,
and the app's trolley uses each item's own published index, which is
accurate.

## Why leave out items priced in two units?

An item like "strawberries per kg or punnet" has quotes in both units, so its
cheapest third is partly its punnets. Ranking those prices ranks the unit, not
the product. There are eight such items, 3.5% of the food weight in 2022.
Items sold in a range of sizes ("olive oil, 500ml to 1 litre") stay in,
because leaving them out would lose 39% of the food weight; instead the gap is
measured with and without them, and it is the same size.

## Why chain the ONS's item indices for the trolley, not rebuild them?

Because a few items, potatoes in 2021 among them, were priced centrally and
have no quotes, and a trolley without potatoes would be a strange trolley.
Where there are quotes, the check shows the rebuilt index and the published
one agree within 0.02, so the choice changes nothing else.

## How are re-coded items handled?

Nine times in these four years the ONS replaced an item with a new code for
what is, on its description, the same product: eggs in 2022, potatoes in 2022,
melon and pineapple in 2023, among others. The old item's path runs to the
January the new one starts from, and the new one carries on from there. That
is how the CPI itself joins one year's basket to the next. Items the ONS
dropped without a successor, like rotisserie chicken, are not in the trolley.

## How is a trolley's rise worked out?

As a fixed January 2021 trolley: each chosen item's share is its share of the
CPI's 2021 weights among the items chosen, which is the ONS's estimate of how
household spending divides between them. The rise is the weighted average of
the items' rises. The app's tests reproduce the pipeline's worked example to
six decimal places.

## Why stop at December 2024?

The food quotes go on to January 2026, but from February 2025 the ONS
publishes indices for consumption segments that pool several items with
weights it does not publish. In a test month I could rebuild the segments
holding a single item and not the rest, which is not a check. The analysis
ends where the checks do.

## Why no charting library?

The charts are lines and bars. Drawn as SVG directly they resize to the
screen so their text stays readable on a phone, and the page stays small.

## Why eight drawn shapes rather than 43 pictures?

Forty-three separate illustrations would be forty-three styles, and the eye
would read the drawings instead of the prices. Eight shapes, one per ONS food
group, make the shelf one family: a tin is a tin whether it holds tuna or
tomatoes. The thing that varies between items is the thing that matters, which
is the colour and the number on the tag.

## Why colour the items by rank, not by how much they rose?

Olive oil is up 157% and the next dearest is up 77%. On a scale of the actual
rises, olive oil would be the only coloured thing on the shelf and everything
else would sit in a grey huddle. Colouring by rank, cheapest rise to dearest,
spreads the shelf evenly and leaves the exact figures to the tags, where they
can be read.

## Why does the trolley start full?

Because an empty trolley has no answer in it, and the page is meant to answer
before it asks. The 43 everyday items are the trolley the write-up quotes, so
the page opens on that figure, and emptying it is one tap.
