"""What the six Runix Data domain pages say, in one place.

tools/build_domain_pages.py renders each entry into <slug>.html with the same
template, so the pages stay uniform and a domain is updated by editing its
entry here, not by hand-editing HTML.

The pages are written from public domain expertise: the standards, formats and
open references practitioners in each field already use, and the cleaning
rules that follow from them. They make no claim about datasets Runix holds,
volumes delivered or customers served -- that material is to be added by the
company when it exists (2026-09-30: "build the pages on public domain
expertise; I will add our own later"). Every reference is a public source and
is probed by tools/link_rot.py.

Fields:
  key, slug, name        anchor on /data (#domain-<key>), page file, display name
  title, description     <title> and meta description
  h1                     two lines
  sub                    the hero paragraph
  panel                  (label, value) rows for the reference card beside the
                         hero: what each record is checked against
  kinds                  (name, text): the data the domain covers
  rules                  (title, text, basis): a cleaning rule, and the public
                         practice or standard it follows
  refs                   (name, url, what it is)
  faq                    (question, answer); answers are plain text
  cta                    closing heading
"""

DOMAINS = [
    {
        "key": "code", "slug": "code-data", "name": "Code",
        "title": "Code Data for AI Training and Evaluation — Runix Data",
        "description": "Repository and task data for code models and coding agents: licence-checked, deduplicated, scrubbed of secrets, and verified by running the tests.",
        "h1": ("Code data,", "verified by running it"),
        "sub": "Repository and task data for code models and coding agents, the focus of Runix Data: licence-checked file by file, deduplicated across forks, scrubbed of secrets, and verified by executing the tests rather than reading them.",
        "panel": [
            ("licence", "SPDX identifier, detected per file"),
            ("provenance", "repository, commit, path"),
            ("secrets", "key and token patterns, entropy"),
            ("duplicates", "exact hash + MinHash near-dup"),
            ("tasks", "fail-to-pass, pass-to-pass"),
            ("evaluation", "split by repository, decontaminated"),
        ],
        "kinds": [
            ("Source code corpora", "Files with their repository, commit and licence, for pre-training and continued training of code models."),
            ("Repository tasks", "An issue, the patch that resolves it and the tests that prove it, for training and evaluating coding agents."),
            ("Review pairs", "A diff and the review comments it drew, for models that review code rather than write it."),
            ("Evaluation sets", "Tasks held back from training and checked against public benchmarks, so a score measures ability rather than memory."),
        ],
        "rules": [
            ("Licence first", "Every file carries a licence identifier detected by scanning the file, not trusted from a README. Files whose licence does not permit your use are left out, and the licence travels with every record that stays.",
             "The SPDX License List for identifiers; scanners such as ScanCode; public code corpora such as The Stack, built from permissively licensed repositories with an opt-out."),
            ("One copy of each file", "Forks, vendored dependencies and generated or minified files make up much of raw code. Exact hashing removes copies, and near-duplicate detection catches the files that differ by a header or a whitespace change.",
             "The MinHash near-deduplication used to build large public code corpora."),
            ("No secrets leave", "API keys, tokens, private keys and passwords are found with pattern and entropy rules and removed or replaced before anything leaves the pipeline.",
             "The rule sets of open-source scanners such as gitleaks and detect-secrets."),
            ("Run, not read", "A task counts only if, in a clean container, the reference patch makes its target tests pass, the unpatched repository makes those tests fail, and the rest of the suite still passes. A task whose target tests pass without the patch is dropped.",
             "SWE-bench's execution-based evaluation, with fail-to-pass and pass-to-pass tests."),
            ("Statements that match the tests", "A task statement describes what the tests actually check, so a model is not graded on behaviour the statement never asked for.",
             "The human review that produced SWE-bench Verified, which screened tasks for underspecified statements and unfair tests."),
            ("Evaluation kept clean", "Evaluation tasks are split from training data by repository, not by row, and checked for overlap with public benchmarks.",
             "Standard decontamination practice for code benchmarks."),
        ],
        "refs": [
            ("SPDX License List", "https://spdx.org/licenses/", "Standard short identifiers for licences used in open-source and other shared software and data."),
            ("ScanCode Toolkit", "https://github.com/aboutcode-org/scancode-toolkit", "Open-source licence and copyright detection."),
            ("The Stack (BigCode)", "https://huggingface.co/datasets/bigcode/the-stack", "A public code corpus of permissively licensed source, with an opt-out."),
            ("SWE-bench", "https://www.swebench.com/", "Execution-based evaluation of coding agents on real repository issues."),
            ("gitleaks", "https://github.com/gitleaks/gitleaks", "Open-source secret scanning for repositories."),
            ("detect-secrets", "https://github.com/Yelp/detect-secrets", "Open-source detection of secrets in code."),
        ],
        "faq": [
            ("Which licences do you accept?", "Permissive licences by default. Anything else only when you ask for it and the licence allows your use, and the licence identifier travels with every file either way."),
            ("How do you know a coding task is fair?", "It is run: in a clean container, the reference patch must make its target tests pass, the unpatched repository must make those tests fail, and the rest of the suite must still pass. The statement is then checked against what the tests actually test."),
        ],
        "cta": "Send us a sample of your code tasks",
    },
    {
        "key": "finance", "slug": "finance-data", "name": "Finance",
        "title": "Finance Data for AI Training and Evaluation — Runix Data",
        "description": "Filings, statements, market and transaction data for models that must get the numbers right: units normalised, restatements kept apart, entities resolved.",
        "h1": ("Finance data,", "read the way an analyst reads it"),
        "sub": "Filings, statements, market and transaction records for models that have to get the numbers right: units and periods normalised, restated figures kept apart, entities resolved across identifiers, and account data masked.",
        "panel": [
            ("filings", "XBRL: US GAAP and IFRS taxonomies"),
            ("entities", "LEI (ISO 17442), SEC CIK"),
            ("instruments", "ISIN (ISO 6166), FIGI"),
            ("venues", "MIC (ISO 10383)"),
            ("currency", "ISO 4217, with scale and sign"),
            ("periods", "fiscal period, as filed"),
        ],
        "kinds": [
            ("Regulatory filings", "Annual and quarterly reports and their amendments, with the tagged financial facts inside them."),
            ("Financial statements", "Income statements, balance sheets and cash-flow statements, figure by figure, with the period each belongs to."),
            ("Market and reference data", "Instruments, venues and prices, tied to the identifiers the market already uses."),
            ("Transaction records", "Ledgers and payment records, with account data masked before anything else happens."),
        ],
        "rules": [
            ("The same unit before any comparison", "Scale, currency and sign are normalised before two figures are compared: a value reported in thousands is not a value reported in units, and a cost shown as positive in one filing is negative in another.",
             "Numeric XBRL facts carry a unit and a stated rounding (the decimals attribute); ISO 4217 currency codes."),
            ("Periods as filed", "Every figure keeps the reporting period it belongs to. Many fiscal years do not end on 31 December, and a balance at a date is not a flow over a quarter.",
             "XBRL's instant and duration contexts."),
            ("Restatements kept apart", "A restated figure replaces an earlier one, either in an amended filing or as a revised comparative in a later report. Both are kept, with which supersedes which, so a corrected number is never presented as current.",
             "Amendment forms such as 10-K/A and 10-Q/A in SEC EDGAR, and revised prior-period comparatives in later filings."),
            ("One entity, many identifiers", "Tickers change, companies rename and merge. Each record is tied to a stable identifier, the LEI where one exists and the SEC's CIK for anyone that files with the SEC.",
             "The Legal Entity Identifier (ISO 17442) maintained through GLEIF; OpenFIGI for instruments."),
            ("Frameworks not mixed", "US GAAP and IFRS figures are kept apart, and are only combined through a mapping you can inspect.",
             "The separate US GAAP and IFRS XBRL taxonomies."),
            ("Account data masked", "Account and card numbers and personal data are masked before a record reaches a training set. A record that cannot be cleared is held back, not passed through.",
             "The long-standing convention of showing only the last digits of an account or card number."),
        ],
        "refs": [
            ("XBRL International", "https://www.xbrl.org/", "The not-for-profit consortium behind XBRL, the open standard for tagged business reporting."),
            ("SEC EDGAR", "https://www.sec.gov/edgar/search/", "US public company filings, including their XBRL data."),
            ("IFRS Accounting Taxonomy", "https://www.ifrs.org/issued-standards/ifrs-taxonomy/", "The XBRL taxonomy for IFRS financial statements."),
            ("GLEIF", "https://www.gleif.org/", "The foundation that runs the Global LEI System and publishes LEI data."),
            ("OpenFIGI", "https://www.openfigi.com/", "Open identifiers for financial instruments."),
            ("ISO 4217 currency codes", "https://www.six-group.com/en/products-services/financial-information/market-reference-data/data-standards.html", "The current code list, from SIX, the standard's maintenance agency."),
        ],
        "faq": [
            ("Which accounting frameworks?", "US GAAP and IFRS, kept apart. Figures are only combined across frameworks through a mapping you can inspect."),
            ("Can a model learn a number that was later restated?", "Not as the current figure. Restated figures are linked to the ones they replace, whether the correction came in an amendment or a later filing, and the delivery says which is current."),
        ],
        "cta": "Send us a sample of your financial data",
    },
    {
        "key": "cybersecurity", "slug": "cybersecurity-data", "name": "Cybersecurity",
        "title": "Cybersecurity Data for AI Training and Evaluation — Runix Data",
        "description": "Advisories, vulnerability records, logs and threat reports for security models: merged across sources, versions normalised, indicators defanged, labels traced.",
        "h1": ("Security data,", "with nothing live inside"),
        "sub": "Advisories, vulnerability records, logs and threat reports for models that triage, detect and explain: merged across sources, affected versions normalised, indicators defanged, and every label traceable to the rule that set it.",
        "panel": [
            ("vulnerabilities", "CVE ID; NVD and OSV merged"),
            ("weaknesses", "CWE weakness IDs, not categories"),
            ("severity", "CVSS vector, version kept"),
            ("behaviour", "MITRE ATT&amp;CK techniques"),
            ("intelligence", "STIX 2.1 objects"),
            ("indicators", "defanged: hxxp, example[.]com"),
        ],
        "kinds": [
            ("Vulnerability advisories", "CVE records, vendor advisories and ecosystem databases for the same flaws, merged into one record each."),
            ("Logs and alerts", "Endpoint, network and application events, with personal data and secrets masked."),
            ("Threat intelligence", "Reports and indicators, structured and defanged so nothing in them is live."),
            ("Detection content", "Rules and the events they fire on, for models that write or explain detections."),
        ],
        "rules": [
            ("One vulnerability, one record", "The same flaw appears in the NVD, vendor advisories and package ecosystems in different words. Records are merged on the CVE identifier and the aliases OSV records list, with every source kept.",
             "The CVE Program's identifiers; the NVD; the aliases field of the OSV schema."),
            ("Versions you can query", "Affected and fixed versions are normalised into ranges a program can compare, per package ecosystem.",
             "The OSV schema's affected ranges; CPE names for products."),
            ("Severity as scored", "CVSS vectors are kept with their version and never mixed: a v3.1 score and a v4.0 score are different measurements.",
             "FIRST's CVSS specifications."),
            ("Nothing live ships", "URLs, domains and IP addresses are defanged, malware is referenced by hash rather than included, and exploit code is excluded.",
             "The defanging conventions used across threat-intelligence sharing."),
            ("Techniques named the same way", "Attacker behaviour is labelled with ATT&amp;CK technique identifiers, so two reports describing the same technique say so.",
             "MITRE ATT&amp;CK; STIX 2.1 for structured intelligence."),
            ("Labels you can trace", "Every detection label records the rule or analyst decision that assigned it, so a disputed label can be checked rather than argued about.",
             "Detection rules with stable identifiers, as in the open Sigma rule format."),
        ],
        "refs": [
            ("CVE Program", "https://www.cve.org/", "Identifiers for publicly disclosed vulnerabilities."),
            ("National Vulnerability Database", "https://nvd.nist.gov/", "NIST's analysis of CVE records, with CVSS and CPE data."),
            ("OSV", "https://osv.dev/", "An open vulnerability database and schema for open-source packages."),
            ("CWE", "https://cwe.mitre.org/", "A catalogue of software and hardware weakness types."),
            ("CVSS", "https://www.first.org/cvss/", "FIRST's standard for scoring vulnerability severity."),
            ("MITRE ATT&amp;CK", "https://attack.mitre.org/", "A knowledge base of adversary tactics and techniques."),
            ("STIX and TAXII", "https://oasis-open.github.io/cti-documentation/", "OASIS standards for structured threat intelligence."),
            ("Sigma", "https://github.com/SigmaHQ/sigma", "An open, generic format for detection rules, each rule with its own identifier."),
        ],
        "faq": [
            ("Can delivered data contain live malware or exploits?", "No. Indicators are defanged, malware is referenced by hash, and exploit code is excluded."),
            ("How are conflicting advisories handled?", "They are merged on the CVE identifier and the aliases OSV lists, with every source kept, so a model sees where the sources agree and where they do not."),
        ],
        "cta": "Send us a sample of your security data",
    },
    {
        "key": "legal", "slug": "legal-data", "name": "Legal",
        "title": "Legal Data for AI Training and Evaluation — Runix Data",
        "description": "Contracts, case law and legislation for models that must cite what they rely on: clauses segmented, citations normalised, jurisdiction and dates tagged.",
        "h1": ("Legal data,", "traced to its source"),
        "sub": "Contracts, case law and legislation for models that have to cite what they rely on: clauses segmented, citations normalised, every text tagged with its jurisdiction and the date it took effect, and privileged or personal data redacted.",
        "panel": [
            ("case law", "ECLI where issued; court, date"),
            ("legislation", "ELI and CELEX for EU texts"),
            ("structure", "Akoma Ntoso sections, clauses"),
            ("citations", "one normalised form each"),
            ("dates", "in force, amended, repealed"),
            ("privacy", "privileged and personal data out"),
        ],
        "kinds": [
            ("Contracts", "Agreements and templates, segmented into clauses with their headings and cross-references."),
            ("Judgments", "Decisions with their court, date and citations, linked to the authorities they rely on."),
            ("Legislation and regulation", "Statutes and rules as in force on a given date, with their amendments."),
            ("Drafting and review tasks", "A clause, the issue with it and the revision, for models that draft and review."),
        ],
        "rules": [
            ("Clauses, not pages", "Contracts are segmented into clauses, keeping headings, numbering and cross-references, so each clause can be retrieved, compared and labelled on its own.",
             "Akoma Ntoso, the OASIS standard for legislative and judicial documents; public contract-clause taxonomies such as CUAD."),
            ("The same case is the same case", "Citations are normalised to one form per authority, and parallel citations are linked, so a model does not treat two references to one judgment as two cases.",
             "The European Case Law Identifier (ECLI) and national neutral citations."),
            ("Law has a date", "Every text carries its jurisdiction and the date it took effect. Amended and repealed versions are kept apart, so a model can answer as of a date.",
             "Point-in-time consolidation, as in EUR-Lex (whose consolidated texts are for reference; the Official Journal is authoritative) and the European Legislation Identifier (ELI)."),
            ("Privilege and personal data out", "Privileged material and personal data are redacted before processing continues, and names in judgments follow the anonymisation the court applied.",
             "The anonymisation courts apply to the judgments they publish."),
            ("The text's own licence", "Much legislation and many judgments can be reused freely; commercial databases and commentary usually cannot, and stay out unless they are licensed for your use.",
             "The reuse terms published by each source."),
        ],
        "refs": [
            ("EUR-Lex", "https://eur-lex.europa.eu/", "EU law, with consolidated versions and CELEX numbers."),
            ("European Legislation Identifier", "https://eur-lex.europa.eu/eli-register/about.html", "Stable identifiers for legislation."),
            ("Akoma Ntoso", "https://www.oasis-open.org/standard/akn-v1-0/", "The OASIS standard, from the LegalDocML committee, for legislative and judicial documents."),
            ("CUAD", "https://www.atticusprojectai.org/cuad", "The Atticus Project's open dataset of commercial contracts with expert-labelled clauses."),
            ("CourtListener", "https://www.courtlistener.com/", "Free Law Project's open archive of US court opinions."),
            ("Caselaw Access Project", "https://case.law/", "Harvard Law School's open archive of US case law."),
        ],
        "faq": [
            ("Which jurisdictions do you cover?", "Those agreed in your specification. Every document carries its jurisdiction, so combining them is a decision, not an accident."),
            ("Can a model be asked what the law was on a date?", "Yes, if the data is built for it: amended and repealed versions are kept apart with the dates they were in force."),
        ],
        "cta": "Send us a sample of your legal data",
    },
    {
        "key": "embodied-ai", "slug": "embodied-ai-data", "name": "Embodied AI",
        "title": "Embodied AI Data: Robot Demonstrations — Runix Data",
        "description": "Robot trajectories, teleoperation and multi-sensor recordings for policies that learn from demonstration: streams aligned, calibration kept, episodes segmented.",
        "h1": ("Robot data,", "aligned to one clock"),
        "sub": "Trajectories, teleoperation sessions and multi-sensor recordings for policies that learn from demonstration: streams aligned in time, calibration kept with every episode, recordings segmented into episodes, and action spaces normalised across robots.",
        "panel": [
            ("containers", "ROS 2 bags and MCAP, read losslessly"),
            ("robot", "URDF kept with the episode"),
            ("time", "one clock; drift and drops reported"),
            ("episodes", "start, end, outcome, instruction"),
            ("actions", "units, frames and rates normalised"),
            ("delivery", "RLDS or LeRobot format"),
        ],
        "kinds": [
            ("Teleoperation demonstrations", "Episodes recorded by an operator driving the robot, with the instruction that was given."),
            ("Autonomous rollouts", "Episodes the policy ran itself, successes and failures both, labelled as such."),
            ("Multi-sensor recordings", "Cameras, depth, joint states and force-torque readings from the same run."),
            ("Language-annotated episodes", "Episodes paired with the task description, for policies that take instructions."),
        ],
        "rules": [
            ("One clock", "Cameras, joint states and force readings are timestamped by different devices. Streams are aligned to one clock, and drift and dropped frames are reported rather than silently interpolated over.",
             "Timestamped message containers such as ROS 2 bags and MCAP."),
            ("Calibration travels with the data", "Camera intrinsics and extrinsics and the robot's description are stored with each episode, not in a separate file that gets lost.",
             "URDF robot descriptions; the per-episode metadata in open robot datasets."),
            ("Episodes, not hours of tape", "Long recordings are split into episodes with a start, an end, the outcome and the instruction that was given.",
             "The episode structure of RLDS and LeRobot datasets."),
            ("Failures labelled, unsafe removed", "Failed attempts are kept and labelled, because a policy learns from them too. Unsafe or corrupted episodes are removed, with the reason recorded.",
             "Open datasets that release labelled failures, such as DROID's episodes marked not successful."),
            ("Actions comparable across robots", "Units, coordinate frames and control rates are normalised, so data from different robots and controllers can be trained on together.",
             "The gap Open X-Embodiment documented: its cross-robot data shares a 7-DoF end-effector action normalised per dataset, but leaves coordinate frames unaligned."),
        ],
        "refs": [
            ("MCAP", "https://mcap.dev/", "An open container format for timestamped robotics data."),
            ("rosbag2", "https://github.com/ros2/rosbag2", "The ROS 2 recording tool; its default storage format has been MCAP since ROS 2 Iron."),
            ("URDF", "https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html", "The XML format that describes a robot's links and joints."),
            ("RLDS", "https://github.com/google-research/rlds", "Google Research's episode-based format for robot and reinforcement-learning data."),
            ("Open X-Embodiment", "https://robotics-transformer-x.github.io/", "A collaboration pooling robot data across many embodiments."),
            ("LeRobot", "https://github.com/huggingface/lerobot", "Hugging Face's open library and dataset format for robot learning."),
        ],
        "faq": [
            ("Which robots and formats do you work with?", "We read ROS 2 bags and MCAP directly; other logging formats are assessed on a sample. Delivery is in the format your training code expects, such as RLDS or LeRobot."),
            ("Why keep failed episodes?", "A policy learns from them too, as long as they are labelled. Unsafe or corrupted episodes are the ones removed, with the reason recorded."),
        ],
        "cta": "Send us a sample of your robot data",
    },
    {
        "key": "ai-for-science", "slug": "ai-for-science-data", "name": "AI for Science",
        "title": "AI for Science Data: Antibody and Protein Records — Runix Data",
        "description": "Antibody and protein sequence and structure data for scientific models: formats validated, one numbering scheme, accessions reconciled, measurements kept apart.",
        "h1": ("Antibody and protein data,", "where a bad merge changes the answer"),
        "sub": "Sequence and structure records for models in antibody and protein work: formats validated, one numbering scheme applied across sources, accessions reconciled, and measured values kept apart from computed ones. Our scope here is biological data.",
        "panel": [
            ("sequences", "FASTA; alphabet and length checked"),
            ("numbering", "one scheme: IMGT, Kabat, Chothia"),
            ("structures", "PDB mmCIF, chains mapped"),
            ("identity", "UniProt accessions reconciled"),
            ("antibodies", "SAbDab and OAS conventions"),
            ("repertoires", "AIRR Community standards"),
        ],
        "kinds": [
            ("Antibody sequences", "Heavy and light chains, paired where the source pairs them, numbered under one scheme."),
            ("Protein sequences", "Sequences with their accession, organism and the evidence behind them."),
            ("Structures", "Experimental structures with their chains mapped to the sequences they contain."),
            ("Assay measurements", "Binding and activity values with their units and method, never mixed with predictions."),
        ],
        "rules": [
            ("Formats validated, not just parsed", "Sequences are checked for their alphabet, length and truncation, not only read. A file that parses is not necessarily a sequence that makes sense.",
             "The FASTA format and the validation built into public sequence databases."),
            ("One numbering scheme", "IMGT, Kabat and Chothia number antibody residues differently and draw the loops in different places. One scheme is applied across every source, so a position means the same thing everywhere.",
             "IMGT numbering and tools such as ANARCI that number antibody sequences."),
            ("Accessions reconciled", "The same protein appears under different identifiers in sequence databases, structure archives and papers. They are mapped to one entity, and conflicts are reported rather than settled silently.",
             "UniProt accessions; cross-references between UniProt and the PDB."),
            ("Measured, not asserted", "Measured values keep their units and method, and computed properties are labelled as computed. A binding site that was predicted is not recorded as one that was observed.",
             "Structural antibody databases such as SAbDab, which record each structure's experimental method and resolution and, where available, a curated binding affinity."),
            ("Scope stated", "Our work in this domain is limited to biological data: antibody and protein records. Materials, climate and chemistry data are outside it.",
             "A stated scope, so what is outside it is clear."),
        ],
        "refs": [
            ("UniProt", "https://www.uniprot.org/", "The reference database of protein sequences and function."),
            ("RCSB Protein Data Bank", "https://www.rcsb.org/", "The US data centre of the PDB archive of experimentally determined structures; computed models on the site are labelled as such."),
            ("IMGT", "https://www.imgt.org/", "The international ImMunoGeneTics information system and its numbering."),
            ("ANARCI", "https://github.com/oxpig/ANARCI", "Antibody numbering and receptor classification."),
            ("SAbDab", "https://sabdab.opig.stats.ox.ac.uk/", "The Structural Antibody Database (now SAbDab2), from Oxford's OPIG."),
            ("Observed Antibody Space", "https://opig.stats.ox.ac.uk/webapps/oas/", "A database of antibody repertoire sequences."),
            ("AIRR Community", "https://www.antibodysociety.org/the-airr-community/", "Standards for adaptive immune receptor repertoire data."),
        ],
        "faq": [
            ("Do you work on materials or chemistry data?", "No. Our scope here is biological data: antibody and protein records."),
            ("Where can we see how you approach this data?", "We teach it in a free course, released under CC BY-SA 4.0 and taught in Chinese, with <a href=\"https://ai4s.runixcloud.io/en/\" target=\"_blank\" rel=\"noopener\">an English overview</a> on ai4s.runixcloud.io."),
        ],
        "cta": "Send us a sample of your antibody or protein data",
    },
]
