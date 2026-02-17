import uuid

ISI_HTML = """\
<div data-isi="true" data-editable="false">

<h2>INDICATION</h2>
<p>FRUZAQLA is indicated for the treatment of adult patients with metastatic colorectal cancer (mCRC) who have been previously treated with fluoropyrimidine-, oxaliplatin-, and irinotecan-based chemotherapy, an anti-VEGF biological therapy, and, if RAS wild-type, an anti-EGFR therapy.</p>

<h2>WARNINGS AND PRECAUTIONS</h2>

<h3>Hypertension</h3>
<p>Hypertension occurred in 49% of 911 patients who received FRUZAQLA. Grade 3 hypertension occurred in 28% of patients. Monitor blood pressure prior to initiation and regularly during treatment. Initiate or adjust antihypertensive therapy as appropriate. Withhold, dose reduce, or permanently discontinue based on severity.</p>

<h3>Hemorrhagic Events</h3>
<p>Hemorrhagic events occurred in patients treated with FRUZAQLA including gastrointestinal hemorrhage (6%). Permanently discontinue FRUZAQLA in patients who experience Grade 3 or 4 hemorrhagic events.</p>

<h3>Infections</h3>
<p>Infections occurred in 18% of patients treated with FRUZAQLA vs 12% with placebo. Withhold FRUZAQLA for Grade 3 or 4 infection.</p>

<h3>Gastrointestinal Perforation</h3>
<p>Gastrointestinal perforation or fistula occurred in 1.3% of patients treated with FRUZAQLA. Permanently discontinue FRUZAQLA in patients who develop gastrointestinal perforation or fistula.</p>

<h3>Hepatotoxicity</h3>
<p>Hepatotoxicity occurred in patients treated with FRUZAQLA. Increased ALT/AST occurred in 48% of patients. Monitor liver function tests prior to and during treatment. Withhold, dose reduce, or permanently discontinue based on severity.</p>

<h3>Proteinuria</h3>
<p>Proteinuria occurred in 36% of patients treated with FRUZAQLA. Monitor for proteinuria prior to and during treatment. Withhold, dose reduce, or permanently discontinue for proteinuria based on severity.</p>

<h3>Palmar-Plantar Erythrodysesthesia</h3>
<p>Palmar-plantar erythrodysesthesia (PPE) occurred in 35% of patients treated with FRUZAQLA. Withhold, dose reduce, or permanently discontinue based on severity.</p>

<h3>Posterior Reversible Encephalopathy Syndrome</h3>
<p>Posterior reversible encephalopathy syndrome (PRES) can occur with FRUZAQLA. Permanently discontinue in patients who develop PRES.</p>

<h3>Impaired Wound Healing</h3>
<p>Impaired wound healing can occur in patients who receive drugs that inhibit VEGF signaling. Withhold FRUZAQLA prior to elective surgery. Do not administer for at least 2 weeks after major surgery and until adequate wound healing.</p>

<h3>Arterial Thromboembolic Events</h3>
<p>Arterial thromboembolic events occurred in 0.8% of patients treated with FRUZAQLA. Permanently discontinue in patients who develop arterial thromboembolic events.</p>

<h3>Allergic Reactions to FD&amp;C Yellow No. 5 and No. 6</h3>
<p>FRUZAQLA capsules contain FD&amp;C Yellow No. 5 (tartrazine) and FD&amp;C Yellow No. 6, which may cause allergic-type reactions in certain susceptible persons.</p>

<h3>Embryo-Fetal Toxicity</h3>
<p>Based on findings from animal studies and its mechanism of action, FRUZAQLA can cause fetal harm when administered to a pregnant woman. Advise pregnant women of the potential risk to a fetus.</p>

<h2>ADVERSE REACTIONS</h2>
<p>The most common adverse reactions (incidence &ge;20%) were hypertension, palmar-plantar erythrodysesthesia, proteinuria, dysphonia, abdominal pain, diarrhea, and asthenia.</p>

<h2>DRUG INTERACTIONS</h2>
<p>Avoid concomitant use with strong or moderate CYP3A inducers. Co-administration with strong or moderate CYP3A inducers may decrease FRUZAQLA concentrations, which may reduce FRUZAQLA efficacy.</p>

<h2>USE IN SPECIFIC POPULATIONS</h2>
<p>Lactation: Advise women not to breastfeed during treatment with FRUZAQLA and for 2 weeks after the last dose.</p>

</div>
"""

ISI_ASSET = {
    "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "asset-isi-block")),
    "name": "ISI Block",
    "asset_type": "document",
    "file_url": "/static/assets/isi-block.html",
    "metadata": {"html": ISI_HTML},
}
