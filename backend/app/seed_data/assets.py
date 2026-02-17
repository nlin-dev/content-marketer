import uuid

_ASSET_DEFS = [
    ("km-curve-os-fresco2", "KM Curve OS FRESCO-2", "image", "visual-aid.pdf", "p7"),
    ("km-curve-os-fresco", "KM Curve OS FRESCO", "image", "visual-aid.pdf", "p14"),
    ("km-curve-pfs-fresco2", "KM Curve PFS FRESCO-2", "image", "visual-aid.pdf", "p9"),
    ("km-curve-pfs-fresco", "KM Curve PFS FRESCO", "image", "visual-aid.pdf", "p16"),
    ("forest-plot-os-fresco2", "Forest Plot OS FRESCO-2", "image", "visual-aid.pdf", "p8"),
    ("forest-plot-pfs-fresco2", "Forest Plot PFS FRESCO-2", "image", "visual-aid.pdf", "p10"),
    ("forest-plot-os-fresco", "Forest Plot OS FRESCO", "image", "visual-aid.pdf", "p15"),
    ("forest-plot-pfs-fresco", "Forest Plot PFS FRESCO", "image", "visual-aid.pdf", "p17"),
    ("study-design-fresco2", "Study Design FRESCO-2", "infographic", "visual-aid.pdf", "p4"),
    ("study-design-fresco", "Study Design FRESCO", "infographic", "visual-aid.pdf", "p12"),
    ("moa-kinome-selectivity", "MOA Kinome Selectivity", "infographic", "visual-aid.pdf", "p3"),
    ("ar-table-fresco2", "AR Table FRESCO-2", "image", "visual-aid.pdf", "p11"),
    ("lab-abnormalities-fresco2", "Lab Abnormalities FRESCO-2", "image", "visual-aid.pdf", "p11"),
    ("qol-ttd-summary", "QoL TTD Summary", "infographic", "visual-aid.pdf", "p19"),
    ("brand-logo", "Brand Logo", "image", "visual-aid.pdf", "p1"),
    ("dosing-icon", "Dosing Icon", "image", None, None),
]

ASSETS = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"asset-{slug}")),
        "name": name,
        "asset_type": atype,
        "file_url": f"/static/assets/{slug}.svg",
        "metadata": {
            "description": name,
            **({"source_pdf": pdf, "source_page": page} if pdf else {}),
        },
    }
    for slug, name, atype, pdf, page in _ASSET_DEFS
]
