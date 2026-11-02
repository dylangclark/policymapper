POLICYMAPPER — IMPORTANCE × ATTENTION SCATTER
============================================

This package adds a new interactive scatter panel immediately beneath the
research-funding treemap on tab 3 (Research funding) in:
  https://github.com/dylangclark/policymapper

Files
-----
  add_attention_scatter.py       Applies/reapplies the addition to the repository
  outcome_scatter_fragment.html.in  Self-contained HTML/CSS/JavaScript component
  Export outcome to expenditures_strong.csv  The supplied scores/counts (73 outcomes)
  attention_scatter_preview.html Standalone browser preview, no internet needed

How to integrate
----------------
1. Download/extract this package into the root of a local checkout of
   dylangclark/policymapper. Place the .py, .html.in and .csv in the same folder
   as the repository's network_template.html and index.html.
2. From that folder, run:

   python add_attention_scatter.py --repo . --data "Export outcome to expenditures_strong.csv"

3. Open index.html. Select tab 3, Research funding, then scroll below the
   treemap to "Outcome importance and attention".
4. Commit the changed index.html and network_template.html, plus this patch
   script and its .html.in template if you want to be able to update scores.

The script is safe to rerun. It replaces only the content between its unique
scatter markers, leaving the rest of the existing page untouched.

The component is embedded in network_template.html; subsequent runs of the
repository's rebuild_network.cmd or build_network.py therefore retain it.
After editing the source CSV, rerun the patch script on BOTH files. If you
later regenerate index.html from the template, it will contain the latest
embedded scatter data from when the patch was last run.

Controls and interpretation
---------------------------
- X: Importance score (as provided, from 5 to 12).
- Y: Attention score (as provided, from 0 to about 376).
- Hover or keyboard focus: outcome statement, theme, number of contracts,
  number of B.C. grants. Score values are intentionally omitted from the hover.
- Click or Enter: pin an outcome's description and counts under the plot.
- Theme dropdown, searchable outcome statements, legend theme shortcuts,
  and clear filters.
- Display-only offsets separate exact coincident markers so all outcomes
  remain selectable. The scored numbers are never modified.
- The data source reports 73 outcome statements, 14 themes, and 40 outcomes
  with attention = 0. Zero is not interpreted as no research or policy work.
- The grant counts refer to B.C. grants, not necessarily all research grants
  in the research treemap. Filters above the treemap do not change this chart.
- Counts are outcome associations. If a grant/contract maps to multiple
  outcomes, adding counts across outcomes could double-count source records.

This package does not push a commit to GitHub. It produces local edits to files
in your checkout. HTML is self-contained: no CDN, network request, or JS
package dependency required.
