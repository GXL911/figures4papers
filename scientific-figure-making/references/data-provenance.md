# Data provenance and manifests

When source files exist, supply them to finalize_figure with an explicit
FigureContract. Output files PNG/PDF/SVG are validated and a manifest.json
is emitted alongside them. Manifest metadata includes source and output
SHA256 hashes, timestamp, versions, random seed, transformation notes,
figure_id, source description and declared statistical semantics.

A file hash guarantees that bytes are identical, **not** that the numbers
were measured correctly. Human-readable transformation notes are not
an executable lineage proof. For stronger provenance, archive:
1. immutable source data,
2. executable preprocessing and plotting code,
3. intermediate plot data,
4. numerical verification results, and
5. final rendered figures.

Manifests may expose local source paths; review before public release.
Avoid changing data to make plots prettier or to silence failing tests.
