# MedicoBuddy AI — Authentic Evidence Source Pack

Validated: 2026-07-26

This pack is a production-oriented source registry for MedicoBuddy AI. It does
not contain pirated journal papers or copied website content. It provides direct
official downloads where automated reuse is allowed, official access pages where
licensing must be checked, and live APIs for current evidence.

## Start here

1. Use the downloadable **MedlinePlus Health Topic XML** as the consumer-health seed corpus.
2. Use **PubMed E-utilities** for metadata and abstracts.
3. Retrieve full text only from the **PMC Open Access Subset**, after checking the article-level licence.
4. Add WHO, NICE, CDC, NCCIH, AAD and Government of India sources using the policy in `source_manifest.csv`.
5. Store the original source URL, publisher, publication/update date, retrieval date, licence, evidence tier and exact supporting passage with every chunk.

## Evidence Tiers

| Tier | Meaning | Permitted use |
|---|---|---|
| A | Current official guideline, government dataset or high-quality review | Primary grounding and safety |
| B | Official consumer-health or professional-organization guidance | Plain-language self-care and escalation |
| T | Government-published traditional Ayurveda source | Traditional-context lane only |
| S | Safety, fraud or interaction source | Contraindications and claim blocking |

`T` does **not** mean scientifically proven. A traditional recommendation must
be labelled “traditional use”, must not be converted into a cure claim, and must
not be presented without a contemporary safety/evidence check.

## Critical Ingestion Rules

- Do not ingest ResearchGate pages, random blogs, scraped paywalled articles or unlicensed PDFs.
- Do not bulk-download all PubMed results. PubMed is primarily bibliographic; use PMC's Open Access services for reusable full text.
- For a public/commercial deployment, prefer PMC records whose licence permits commercial reuse. Store the article-level licence with every chunk.
- Do not copy or redistribute NICE or AAD content unless their terms permit it. Use their pages as live/link-only evidence sources.
- Treat the CCRAS Ayurveda documents as traditional context. Block internal herbs, supplements, nasal instillation, dosage, disease-treatment protocols, surgery and “cure” claims from user-facing output.
- Never represent an MCP connection as evidence. Evidence exists only after a real record has been returned, normalized and attached to a citation.
