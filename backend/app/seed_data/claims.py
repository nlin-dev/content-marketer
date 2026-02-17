import uuid

CLAIMS = [
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-1")),
        "text": "In FRESCO-2, FRUZAQLA + BSC significantly improved overall survival vs placebo + BSC (7.4 vs 4.8 months, a 2.6-month difference); HR=0.66 (95% CI: 0.55-0.80); P<0.001",
        "category": "efficacy_os",
        "sources": ["visual-aid.pdf#FRESCO-2-OS", "medication-prescription.pdf#table-7"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-2")),
        "text": "In FRESCO, FRUZAQLA + BSC significantly improved overall survival vs placebo + BSC (9.3 vs 6.6 months, a 2.7-month difference); HR=0.65 (95% CI: 0.51-0.83); P<0.001",
        "category": "efficacy_os",
        "sources": ["visual-aid.pdf#FRESCO-OS", "medication-prescription.pdf#table-7"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-3")),
        "text": "FRUZAQLA more than doubled median progression-free survival in FRESCO-2 (3.7 vs 1.8 months); HR=0.32 (95% CI: 0.27-0.39); P<0.001, a 68% reduction in risk of disease progression or death",
        "category": "efficacy_pfs",
        "sources": ["visual-aid.pdf#FRESCO-2-PFS", "medication-prescription.pdf#table-7"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-4")),
        "text": "FRUZAQLA more than doubled median progression-free survival in FRESCO (3.7 vs 1.8 months); HR=0.26 (95% CI: 0.21-0.34), a 74% reduction in risk of disease progression or death",
        "category": "efficacy_pfs",
        "sources": ["visual-aid.pdf#FRESCO-PFS", "medication-prescription.pdf#table-7"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-5")),
        "text": "In FRESCO-2, the majority of adverse reactions were manageable and predictable. The most common adverse reactions (incidence >=20%) were hypertension, palmar-plantar erythrodysesthesia, proteinuria, dysphonia, abdominal pain, diarrhea, and asthenia.",
        "category": "safety",
        "sources": ["medication-prescription.pdf#section-6.1", "visual-aid.pdf#FRESCO-2-safety"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-6")),
        "text": "Adverse reactions leading to treatment discontinuation occurred in 20% of patients treated with FRUZAQLA + BSC vs 21% for placebo + BSC in FRESCO-2",
        "category": "safety",
        "sources": ["medication-prescription.pdf#section-6.1", "visual-aid.pdf#FRESCO-2-safety"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-7")),
        "text": "FRUZAQLA is a novel, selective inhibitor of all 3 VEGF receptors (VEGFR-1, VEGFR-2, and VEGFR-3) that minimizes off-target kinase activity and maximizes drug exposure",
        "category": "moa",
        "sources": ["visual-aid.pdf#MOA", "medication-prescription.pdf#section-12.1"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-8")),
        "text": "FRUZAQLA is a non-chemotherapy that limits off-target kinase activity, allowing for high drug exposure and sustained target inhibition",
        "category": "moa",
        "sources": ["visual-aid.pdf#MOA"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-9")),
        "text": "The recommended dose of FRUZAQLA is 5 mg orally once daily for the first 21 days of each 28-day cycle until disease progression or unacceptable toxicity",
        "category": "dosing",
        "sources": ["medication-prescription.pdf#section-2.1", "visual-aid.pdf#dosing"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-10")),
        "text": "FRUZAQLA can be taken with or without food at approximately the same time each day",
        "category": "dosing",
        "sources": ["medication-prescription.pdf#section-2.1"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-11")),
        "text": "In FRESCO-2, patients treated with FRUZAQLA experienced delayed or maintained time to deterioration vs placebo across QoL measures including emotional functioning (4.1 vs 2.8 months), social functioning (3.2 vs 2.3 months), and GHS QLQ-C30 (2.1 vs 1.8 months)",
        "category": "qol",
        "sources": ["visual-aid.pdf#QoL"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-12")),
        "text": "In FRESCO-2, OS benefit was consistent across most prespecified subgroups regardless of duration of metastatic disease, RAS status, prior types of therapy, and presence of liver metastases",
        "category": "subgroups",
        "sources": ["visual-aid.pdf#FRESCO-2-OS-subgroups"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-13")),
        "text": "In FRESCO-2, PFS benefit was consistent across most prespecified subgroups with HR=0.32 (95% CI: 0.27-0.39) for the ITT population",
        "category": "subgroups",
        "sources": ["visual-aid.pdf#FRESCO-2-PFS-subgroups"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-14")),
        "text": "Disease control rate was stable for more than half of patients treated with FRUZAQLA + BSC: 56% with FRUZAQLA + BSC vs 16% with placebo + BSC in FRESCO-2",
        "category": "dcr",
        "sources": ["visual-aid.pdf#FRESCO-2-DCR"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-15")),
        "text": "Disease control rate was stable for more than half of patients treated with FRUZAQLA + BSC: 62% with FRUZAQLA + BSC vs 12% with placebo + BSC in FRESCO",
        "category": "dcr",
        "sources": ["visual-aid.pdf#FRESCO-DCR"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-16")),
        "text": "New treatments that extend survival while preserving QoL are needed to reduce mortality rates in mCRC. CRC can be deadly, with low survival rates for patients with metastatic disease: ~15% 5-year relative survival rate for patients with distant mCRC",
        "category": "unmet_need",
        "sources": ["visual-aid.pdf#unmet-need"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-17")),
        "text": "FRUZAQLA is the first and only novel targeted therapy approved for mCRC, regardless of mutation status, in more than a decade",
        "category": "positioning",
        "sources": ["visual-aid.pdf#cover"],
    },
    {
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "claim-18")),
        "text": "Fruquintinib (FRUZAQLA) is a National Comprehensive Cancer Network (NCCN) Category 2A potential treatment option for patients with previously treated mCRC, regardless of mutation status",
        "category": "positioning",
        "sources": ["visual-aid.pdf#cover"],
    },
]
