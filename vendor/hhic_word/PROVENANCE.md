# HHIC Word engine provenance

Vendored from the local canonical `00_공통/skills/hhic-skills/skills/hhic-word`
on 2026-11-13 for self-contained dashboard deployment.

Local opt-in pagination extension, 2026-11-14: blocks.py accepts paragraph
keep_together, table keep_together/keep_with_next/compact and figure
keep_with_next. Defaults retain upstream behavior. Compact tables reduce only
vertical cell/paragraph padding, preserving fonts and horizontal geometry.
This lets application JSON prevent detached table explanations without editing
generated Word XML. The template and all other engine files remain unchanged.

The donor is `Word Template_Empty_No Project Data.docx` from the same canonical
skill in OneDrive. SHA256:
`4ec89b04f8c3a88b78aa6585a0c4164afa41dcba8a7133b13fa31c6afa4277b0`.
The builder verifies templates/template_pin.json before each generation.

Pretendard Regular/Bold are copied from hhic-skills/shared/fonts with their
SIL Open Font License (fonts/OFL.txt). The Docker image registers these fonts.

Application-specific JSON composition and LibreOffice UNO rendering belong to
utils/market_report.py and scripts/render_market_uno.py. Update this vendor copy
from the canonical skill deliberately, preserving its pin and rerunning tests.
