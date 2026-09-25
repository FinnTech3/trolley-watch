# Sources

Every file was downloaded from the Office for National Statistics on 25
September 2026. All are published under the Open Government Licence v3.0.

## The originals

The ONS publishes the CPI's price quotes and item indices month by month on
one page:

https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes

`data/sources/originals.csv` lists every original file used: 48 months of
price quotes and 48 of item indices (January 2021 to December 2024), four
annual classification frameworks and one time series, each with its address
on that page, its size and its SHA-256. The price quote files are about 13 MB
a month and are not committed; `python -m trolley.fetch` downloads them into
`data/raw`, checks each against its SHA-256, and cuts the committed extracts
from them.

## Committed

| File | What it is | SHA-256 |
|---|---|---|
| `quotes_food_2021.csv.xz` to `quotes_food_2024.csv.xz` | Extracts of the monthly price quote files: the rows for items numbered 21xxxx (food and non-alcoholic beverages), and the columns QUOTE_DATE, ITEM_ID, SHOP_CODE, REGION, SHOP_TYPE, STRATUM_TYPE, STRATUM_CELL, STRATUM_WEIGHT, SHOP_WEIGHT, PRICE, BASE_PRICE, VALIDITY, BASE_VALIDITY, INDICATOR_BOX, START_DATE, END_DATE, as published. 2,205,134 quotes. | 2021 `f8597ceb481b5975b9d7c06d40aa45b9e88571014ca407140f6404f6b84a7516`, 2022 `59766f90f917dfd8005f0822929fe2410f61ae81d4572b727c28dba5d7682c2e`, 2023 `29203b70c02a32af1da013887ef09bdbc06a51f2089da5d80b644350b9e2048d`, 2024 `b27ddcb92bad13959a2aca4fd2f244bee6f1afd8effcef33d13955144ae9eaec` |
| `item_indices_food.csv` | The food rows of each month's item index file: INDEX_DATE, ITEM_ID, ITEM_DESC, ALL_GM_INDEX (the CPI item index), COICOP_WEIGHT, and the pandemic imputation flag where the file has one | `c73d49b07a70e81e4c51fd575bc4fa32e2a487e1dc47441b927da7cf39616dc4` |
| `ons_d7bu.csv` | CPI INDEX 01: FOOD AND NON-ALCOHOLIC BEVERAGES 2015=100 (D7BU), from the MM23 dataset, as downloaded: https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7bu/mm23 | `6b356370d5e60f7c4a37a2b5cd8f639b6018a84edb4ecd9a1f9ea839935e10a5` |
| `cpi_classification_2021.xlsx` to `cpi_classification_2024.csv` | The CPI classification frameworks for 2021 to 2024, as downloaded: which COICOP class each item belongs to | 2021 `3deb813349e5005645f3144b8659aa4bb6d13ac23e029e356ff82ee7b950e75c`, 2022 `b2273dc181e611c53737a876a31f68cd05943ad11b30029607fa7fd75be9386c`, 2023 `b1895c92040cfc13666a43a660146d846a8d6b700d8887b6770b5f77c178e304`, 2024 `abde58128d1c59f1548f190760cbe8459be02f0a61c2206b7480bc1e521825c4` |
| `originals.csv` | The manifest above | `a4742dfc54bfead4d99c2e19c9607b2204147cffbdbe32e481bc5ee39ccef5bf` |

The column meanings are the ONS's glossary for the dataset, `glossaryrevised.xls`
on the same page: VALIDITY and BASE_VALIDITY 3 and 4 are validated quotes;
INDICATOR_BOX marks sales (S), recoveries (R), comparable (C) and
non-comparable (N) replacements, and items temporarily out of stock (T);
BASE_PRICE is the product's price in January of the same year.

## Traps, and what was done about them

- **February 2022 is Excel.** The item indices for that month are an .xlsx,
  not a CSV, and store numbers as floating point (99.846000000000004). The
  fetch reads it with a standard-library reader and writes the numbers as the
  CSV months do.
- **The 2021 classification "CSV" is Excel.** Its address ends .csv; the file
  is .xlsx, and is committed under its true extension. The 2022 file has no
  header row.
- **January is different.** A January item index is relative to the previous
  December, not to January, and January's item index file still carries the
  previous year's weights. The food index links each January with the new
  year's weights, from the February file.
- **January prices of the old sample are not published.** The January quote
  file holds the new year's sample only, so quotes cannot be followed across
  the new year. See DESIGN-DECISIONS.
- **Imputed items in 2021.** 135 food item-months carry the ONS's PARTIAL or
  FULL imputation flag. They are reported, not used to judge the method.
- **Items priced centrally.** A few items, potatoes in 2021 among them, have a
  published index but no quotes.
- **Item codes change.** Nine items were re-coded during the period; the
  pairs are listed in `study.SPLICES`.
- **From 2025 the structure changes.** From February 2025 the quote files add
  consumption segments and the item index files are replaced by segment
  indices; from February 2026 the food quotes stop, replaced by supermarket
  scanner data.

## Also read, not used as data

- ONS, *Tracking the lowest cost grocery items, UK, experimental analysis:
  April 2021 to September 2022*:
  https://www.ons.gov.uk/economy/inflationandpriceindices/articles/trackingthelowestcostgroceryitemsukexperimentalanalysis/april2021toseptember2022
  Quoted in the README: the lowest prices of 30 items rising around 17% in the
  twelve months to September 2022, against 15% for food and drink.
