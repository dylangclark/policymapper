B.C. adaptation network explorer
===============================

Research-funding tab (2 November 2026)
------------------------------------
index.html is the GitHub Pages entry point. It now includes tab 3, Research
funding, built from research_projects.csv (the supplied
all_identified_projects_matched_with_grant_dollars(2).csv, unchanged).

Rebuild the complete GitHub page with this command on one line:
  python build_network.py "bc_adaptation_network_input 1.0.xlsx" --screening "bc_adaptation_outcome_screen 2.0.xlsx" --policies "bc_policy_failures_and_enablers.xlsx" --research research_projects.csv -o index.html

Keep research_funding.py, research_institutions.json and research_treemap.js beside
the generator and network_template.html. rebuild_network.cmd runs this command.
The finished index.html embeds all data and scripts; it works offline on its own.
Commit the regenerated index.html to the GitHub Pages publishing branch to update
the hosted page. The generator never uploads files or edits source data.

Tab 3 controls:
- Geography: British Columbia, All Canada, or All source records (including foreign
  and missing institutions). Default All Canada. BC is the source IS BC flag at
  award, not project location or current PI affiliation.
- Lead institutions: Universities only (default) or All lead institutions.
  Explicit country/type classifications are in research_institutions.json. Missing
  institutions and four foreign records are excluded from Canadian views. New
  institution labels stop the build until a lookup is added; they are not silently
  assumed Canadian. Original institution labels remain in the evidence panel.
- Group by: Theme -> objective, Objective, University / lead institution, or dollar
  bands (<$100k; $100k-<$500k; $500k-<$1m; >=$1m).
- Order groups and projects by dollar value descending/ascending or name A-Z.
  Change theme or search project title, PI, institution or grant ID.
- Click group headers or use Focus group to enlarge a subset; All groups resets.
  Project tiles support hover, keyboard focus/Enter, click and tap. Details retain
  all CSV fields, grant basis, mapping rationale and verification notes, plus safe
  evidence links. The project list provides larger targets for tiny rectangles.

Accounting and interpretation:
- Objective means the CSV's Primary outcome statement. One record goes to one
  primary objective/theme. Additional linked outcomes do not duplicate dollars.
  Research objectives are preserved verbatim; they are not forced into network
  outcome IDs or silently rematched to a different outcome workbook.
- Award totals, fiscal 2024 payments, one-time supplements, annual supplements and
  unconfirmed periods are separate selectable bases. Awards are the default.
  All reported values is explicitly mixed and is not a comparable spending total.
  Values are not annualized or multiplied by award term. Individual/trainee awards,
  provisional relevance and other source categories remain and are visible in
  details. They should not all be described as faculty project grants.
- Missing is not zero: unvalued records are counted and listed in each basis view;
  no rectangle area is invented. Zero values are listed without area. Integer
  cents are used for accounting. Duplicate funder/grant IDs stop generation.
- The source has 186 records, 185 values and one missing value. Its mixed-basis
  total reconciles to $47,398,097.99. Canadian universities: 165 records; BC
  universities: 47 records. Default award subset: 69 valued records / $23,569,592
  across Canada, and 23 / $8,399,643 in BC, plus the unvalued record in each view.
- This is a screened inventory with mixed award years and provisional objective
  matches, not a funding census or evidence of research gaps, effects or impact.
- Treemap outer group areas follow funding; nested headers/padding take some
  display space. Project areas within a group are proportional to selected values.
  Sorting repacks rectangles; geometric reading order is not a ranked list.
- Network/count theme controls apply only to tabs 1 and 2. Research has independent
  filters and includes all research themes present in the CSV.

Checks:
  python -m unittest discover -s . -p "test_*.py"
  node test_research_ui.cjs
The Python suite covers accounting, scope, unknown institutions, duplicate IDs,
invalid money, no secondary-outcome duplication and no annualization. The Node
suite runs the embedded scripts for all groupings, orderings, scopes and bases,
checks value-proportional nonoverlapping packing, tooltips/details, empty states,
and preservation of the 903 network edges and 856 policy associations.
Real Chrome checks also covered tab navigation, Canada/BC totals, grouping,
funding bases, project evidence, focus tooltips, group drill-down and empty search.

Previous network documentation follows. Commands without --research omit tab 3.

The generated adaptation_network.html is self-contained. Open it in a current
Chrome, Edge, Firefox or Safari browser. It works offline with no automatic
external requests. Policy-source links open only when clicked.

To rebuild the complete explorer after editing a workbook:

1. Install Python 3.9 or later.
2. In a terminal, install the dependency:
      python -m pip install openpyxl
3. Keep build_network.py, network_template.html and your workbook in the same folder.
4. Run (use py instead of python on Windows if needed):
      python build_network.py "bc_adaptation_network_input 1.0.xlsx" --screening "bc_adaptation_outcome_screen 2.0.xlsx" --policies "bc_policy_failures_and_enablers.xlsx" -o adaptation_network.html

Put the workbook in this folder, or supply its full path. The script reads it
without modifying it. Re-run after workbook edits; an existing HTML does not
update automatically. The generated HTML can be shared on its own.

Workbook contract
-----------------
- One connection sheet has headers Outcome, Failure, Enabler (Row is optional).
- Outcomes sheet: Theme, Outcome.
- Policy problems sheet: Number, Category, Failure, Statement.
- Enablers sheet: Number, Category, Enabler, Enabling condition.
- Codes may be separated by commas, semicolons, pipes or whitespace.
- Blank connection cells are permitted. Repeated codes and duplicate links count
  once. All dictionary codes appear in charts, including codes with zero links.
- Invalid/unknown codes and unknown outcome labels stop generation with an error.
- Whitespace differences are normalized. Three explicit shortened outcome labels
  found in workbook 1.0 are mapped to their canonical Outcomes labels and reported
  under "How to read this explorer". See OUTCOME_ALIASES in the script.
- Outcome IDs O001 onward follow connection-sheet first occurrence, and may change
  if that sheet is reordered. Failure/enabler IDs come directly from the workbook.
- The workbook data are authoritative. No connections from prior discussions are
  automatically added or removed by the script.

Use
---
- Counts: vertical bar charts show DISTINCT outcomes per failure/enabler. Sort by
  count or code. Hover for the label; click a bar or its key to open the network.
- Theme selection filters BOTH tabs. Count-chart codes with zero links remain.
- Network: click a node to emphasize it, direct neighbours, and incident edges.
  Everything else fades. Full statements and clickable connections appear at right.
- "Include connections through outcomes" adds all the codes attached to the same
  outcomes as a selected failure/enabler. These are shared associations, not direct
  failure-enabler edges and not a causal inference.
- Search by code or phrase; press Enter or Find. This and the connection list
  provide keyboard alternatives to clicking canvas nodes.
- Scroll to zoom; drag the background to pan; drag nodes to rearrange. Fit all,
  Fit selection, + and - control the view. Click background or Escape to clear the
  node selection; Clear selection also resets the policy filter. Node positions
  reset when the theme changes.

Interpretation
--------------
Connections reflect hypotheses coded in the workbook. Counts are not measures of
importance, prevalence, effectiveness, reducibility or policy priority. Ranked
outcome positions and colours reflect only the selected screening dimension.
There are only outcome-failure and outcome-enabler edges, never an inferred pairing
between failures and enablers. Each outcome counts once in the connection charts.

Technical notes
---------------
The HTML uses native SVG charts and a Canvas network; there are no CDN scripts,
web fonts or external assets. Workbook strings are inserted as text, and embedded
JSON is escaped to prevent workbook text from breaking the HTML script element.
Only Python's standard library and openpyxl are required to generate the file.

Screening scores and outcome ordering (version 2.0 screening update)
-------------------------------------------------------------
The package now also includes network_template.html (keep beside the script)
and bc_adaptation_outcome_screen 2.0.xlsx. This screening copy contains the user's
updated scores and notes from bc_adaptation_outcome_screen 2.0.xlsx, without rescoring.
The connection workbook is the latest bc_adaptation_network_input 1.0(1).xlsx,
packaged under the original filename for compatibility with the command below.
Neither source workbook is edited by the generator.

Rebuild with both workbooks:
  python build_network.py "bc_adaptation_network_input 1.0.xlsx" --screening "bc_adaptation_outcome_screen 2.0.xlsx" -o adaptation_network.html

Tab 2 now includes Order by: Economic risk, Governance risk, Salience, Urgency,
Combined score (sum of all four), and Theme / original order. Economic risk is selected initially when screening
is supplied. Ranked views place scores 3, 2, 1 from top to bottom across themes;
equal scores retain original network outcome order. Theme filters still apply.

Outcome boxes use pale red for 3, amber for 2, pale yellow for 1 and neutral grey
for Unknown / blank / N/A / unmatched. Each box includes its selected score in
text. The legend explains the colours; selecting an outcome shows all four
ratings and expandable screening notes. Related outcomes in the sidebar follow
the same order. Changing the order preserves the current node selection and
fits the full network. Theme / original order restores the unranked layout.
Failure/enabler nodes and chart counts retain their original meaning.

Screening rows are matched by outcome text, never by row number. The script
recognizes the actual title/header rows and economic header in the supplied
workbook. Exact matches and explicit wording aliases only: no fuzzy matching.
The one extra screening alias links "Communities experience less damaging
flooding during heavy rainfall" to the existing network's "Communities
experience less damaging surface-water flooding during heavy rainfall".
This difference is reported in workbook notes; network scope is retained.
Unknown labels, duplicate outcomes, duplicate headers and invalid scores stop
generation. Missing screening rows are neutral and generate visible warnings.

Omitting --screening retains the original unranked behavior and disables ranking
choices. Rebuild the HTML after either workbook changes. The HTML remains a
single offline file that can be opened or shared without the Python files.
The four ratings remain available separately. Combined score is their optional
unweighted sum, ranging from 4 to 12; scores sort from highest to lowest and
boxes use a yellow-to-red colour scale for the total. The actual total is shown
on each box and in the details pane. All four component ratings must be numeric
1–3 values: any blank, Unknown, N/A or unmatched rating leaves the total unscored
(neutral grey, placed last). No partial sums or zero substitutions are used.
Equal totals retain original outcome order. This optional explorer total does
not alter the source workbook or its protected definitions tab.
Wellbeing and natural environment remain shelved in this phase.

Windows shortcut
----------------
After installing Python and openpyxl, double-click rebuild_network.cmd to rebuild
using all three bundled workbooks. Open adaptation_network.html after it completes.

Validation
----------
The supplied data match all 73 outcomes; 903 connections are preserved.
Parser tests: python -m unittest discover -s . -p "test_*.py"
All four sorts, canvas colour choices, selection persistence, theme filtering,
unknown handling and unranked compatibility were checked by executing the UI
scripts in a simulated DOM/canvas. A browser visual check was unavailable.


Policy-name edge bubbles (30 October 2026 update)
-----------------------------------------------
Rebuild the full explorer using the network, screening and consolidated policy
workbooks (one command, on one line):
  python build_network.py "bc_adaptation_network_input 1.0.xlsx" --screening "bc_adaptation_outcome_screen 2.0.xlsx" --policies "bc_policy_failures_and_enablers.xlsx" -o adaptation_network.html

The consolidated workbook must contain:
- Policies: Entry, Policy, Reviewed source, Failures addressed (codes), How failures
  are addressed / scope, Failures potentially worsened (codes), Potential worsening
  / evidence needed, Enablers supported (codes), Enabling mechanism and scope,
  Conditions potentially constrained (codes), Potential constraint / evidence needed.
- Policy-outcome links: Policy entry, Policy, Outcome ID, Outcome statement,
  Relationship, Mechanism and limits.

The detailed Policy-outcome links table is authoritative for outcome membership.
The generator does not rely on the summary ID-list cells or cached count formulas.
Entry IDs P001–P099 distinguish repeated policy titles. Outcome IDs and statements
must match the current network dictionary; unknown or inconsistent IDs/titles,
unknown codes and duplicate pairs stop generation. If the network workbook's
connection order changes its outcome IDs, update the policy reference IDs too;
the generator will reject mismatches rather than silently attach the wrong label.

A policy-name bubble is attached only when ALL of the following are present:
1. An explicit proposed policy-to-outcome match in the consolidated workbook.
2. A policy-to-failure/enabler code assignment in that workbook.
3. The existing outcome-to-code edge in the network workbook.

No additional outcome/code edge is created. This is a candidate association from
two assessments, not independent verification that the specific policy provision
addresses that failure/enabler for that outcome or that it is effective.
The original 903 edges and connection counts remain unchanged.

The supplied release has 99 policy entries and 249 policy-outcome matches,
placing 856 policy/code associations on 354 existing edges. Seven policy-outcome
pairs have no overlapping existing edge and therefore produce no bubble:
P018/O030, P018/O031, P026/O056, P037/O018, P043/O028, P053/O022, P080/O014.
They remain in the source workbook and are reported under Workbook notes.

Use in tab 2:
- Policy bubbles is checked by default. Names use readable, screen-sized labels
  anchored to the edge curves as nodes move or the view pans/zooms/reorders.
- Select a node to show names on its emphasized connections, or select a policy
  to focus its candidate associations. The policy dropdown count is across all
  themes; a theme may have fewer or no matching associations.
- Labels avoid nodes and each other by default. The status reports shown/eligible
  bubbles. Zoom, select a node, filter a policy or allow overlapping labels to see
  more names. Full lists are available in the sidebar's Policy associations list,
  including associations whose bubbles do not fit on screen.
- Long titles wrap to three lines and may be abbreviated with an ellipsis. Hover
  for the complete policy name; click for the full title, both mapping rationales,
  relationship, roles and reviewed source. The sidebar list provides keyboard access.
- Solid borders indicate an addresses/supports role. Dashed borders indicate at
  least one potential worsening/constraint role. The same policy can have both.
  Turning off Include potential constraints removes adverse roles; mixed bubbles
  remain if they also have supportive roles. Potential effects remain hypotheses.
- An edge with multiple policies receives separate bubbles. A policy linked to
  multiple edges appears on each relevant edge; these are not independent effects.
- Clear selection resets node/policy selection. Theme selection, two-hop emphasis,
  individual/combined outcome scores, canvas pan/zoom and node dragging remain.
- Omitting --policies retains the prior explorer behavior with the policy controls
  hidden. The source workbooks are read without modification. Rebuild after edits.

Policy validation covers unchanged edges, direct/enabling bubble placement,
combined positive/adverse roles, duplicate titles and invalid mapping references.
The UI scripts were exercised with a native Canvas implementation and simulated
DOM for bubble anchors, clicking, filtering, decluttering, constraints, pan/zoom,
node movement and all five scoring options. Native Canvas views were inspected;
a full browser layout check was unavailable in the execution environment.
