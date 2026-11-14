# Code and third-party data

The source code is distributed under the MIT license in `LICENSE`, retaining
the upstream copyright notice for bstaple1 and unrealities. This Chinese-display
fork does not claim authorship of the upstream application.

Card names, card images, game identities, sets and other game content belong
to their respective rights holders, including Wizards of the Coast. The code
license does not grant rights to that third-party content. This is an unofficial
fan tool, not a Wizards of the Coast or 17Lands product.

`resources/localization/cards.json` is a names-only projection of the pinned
`1996Neil/mtga-card-names` release. It includes client/registry and community
translations; not every translation is official. Its manifest records provenance.

The historical statistics in `resources/datasets/` and localization test inputs
derive from 17Lands data. They contain names, identities and numeric statistics,
not an assertion that the underlying third-party data is MIT-licensed. See the
source publisher's terms and attribution requirements for your use.

The separate `gh-pages` warehouse is an upstream-style 17Lands/Scryfall data
output. Some card records there include third-party rules text used by existing
card analysis. It is not the full client localization table, is not original
code, and is not relicensed as MIT. This cleanup does not change the scoring
inputs or silently remove those runtime fields.

Public fixtures omit game rules/flavor text. Synthetic fixture rules are marked
by synthetic card names. The three upstream screenshots retain upstream
provenance; this fork does not claim ownership of depicted game assets.

The repository and public build do not include a full Arena localization table.
English compatibility indexes are generated locally from an unmodified database
the user already has. Do not commit those indexes, game databases, account logs,
personal paths or internal verification artifacts.
