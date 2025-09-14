TEMPLATES = {
    "HL": {
        "title": "SRS – High Level (HL)",
        "content": """# SRS – High Level (HL)
ID: Y10K-<PROJ>-<AREA>-HL-<NNN>   Version: vX.Y.Z   Ägare: <namn>   Datum: <YYYY-MM-DD>

## Sammanfattning & mål
<sammanfattning>

## Scope & icke-scope
<scope>

## Aktörer & användningsfall (kort)
<aktörer och use-cases>

## Icke-funktionella krav (NFR)
Prestanda: <...>  Säkerhet: <...>  Tillgänglighet: <...>  Compliance: <...>

## Antaganden & beroenden
<listor>

## Risker & mitigering
<lista>

## Arkitektur (C4 Context/Container, 1 sida)
<kort översikt, vad som integreras och hur>

## Komponentkarta (tentativ)
<lista av planerade komponenter med framtida CMP-ID>
"""
    },
    "LL": {
        "title": "SRS – Low Level (LL)",
        "content": """# SRS – Low Level (LL)
ID: Y10K-<PROJ>-<AREA>-LL-<NNN>   Version: vX.Y.Z   Länkar: HL=<ID>, ADR=<ID>

## API-spec
Endpoints, kontrakt (OpenAPI/JSON), felkoder.

## Data
Tabeller, index, constraints, retention.

## Flöden/diagram
Sekvens-/tillståndsdiagram vid behov.

## NFR-budget
Latency (p95): <...>  Throughput: <...>  Kostnad: <...>  Observability: <krav>

## Testkrav
Enhet, integration, E2E, prestanda, säkerhet.

## Risker/kompromisser
Kända skuldområden och trade-offs.
"""
    },
    "CMP": {
        "title": "Komponentspec (CMP)",
        "content": """# Komponentspec (CMP)
ID: Y10K-<PROJ>-<AREA>-CMP-<NNN>   Version: vX.Y.Z   Ägare: <namn>

## Syfte & scope
<beskrivning>

## Gränssnitt
In/Out, kontrakt, beroenden.

## Data
Läs/skriv, schema/nycklar (Postgres/Redis).

## Fel & återhämtning
Idempotens, retries, rate-limits.

## Observability
Loggnycklar, metrics, tracing-punkter.

## Acceptanskriterier (AC)
<lista>

## DoD (checklista)
<lista>
"""
    },
    "ADR": {
        "title": "ADR (Architecture Decision Record)",
        "content": """# ADR: <beslutstitel>
SRS-ID: <kopplingar>

## Kontext
Varför behövs beslutet?

## Alternativ
A/B/C med trade-offs.

## Beslut
Detta väljs och varför.

## Konsekvenser
Tekniska/operativa följder + hur utfallet mäts.

## Länkar
SRS-ID, PR, mätningar.
"""
    },
    "TICKET": {
        "title": "Ticket-mall",
        "content": """# Ticket
Titel: [Y10K-<PROJ>-<AREA>-<TYPE>-<NNN>] Kort beskrivning

## Beskrivning
Syfte, scope.

## Länkar
HL/LL/ADR/PR.

## AC
- [ ] <kriterium>

## DoR/DoD
- [ ] DoR uppfyllt
- [ ] DoD uppfyllt

## Testnoter
Vad verifieras i PR/QA.
"""
    }
}


BASE_TEMPLATE_ENGLISH = {
    "HL": {
        "title": "SRS — High Level (HL)",
        "content": """# SRS — High Level (HL)
ID: Y10K-<PROJ>-<AREA>-HL-<NNN>   Version: vX.Y.Z   Owner: <name>   Date: <YYYY-MM-DD>

## Summary & Goals
<summary>

## Scope & Out of Scope
<scope>

## Actors & Use Cases (brief)
<actors and use-cases>

## Non-Functional Requirements (NFRs)
Performance: <...>  Security: <...>  Availability: <...>  Compliance: <...>

## Assumptions & Dependencies
<lists>

## Risks & Mitigations
<list>

## Architecture (C4 Context/Container, 1 page)
<short overview of integrations and approach>

## Component Map (tentative)
<list of planned components with future CMP-IDs>
"""
    },
    "LL": {
        "title": "SRS — Low Level (LL)",
        "content": """# SRS — Low Level (LL)
ID: Y10K-<PROJ>-<AREA>-LL-<NNN>   Version: vX.Y.Z   Links: HL=<ID>, ADR=<ID>

## API Spec
Endpoints, contracts (OpenAPI/JSON), error codes.

## Data
Tables, indexes, constraints, retention.

## Flows/Diagrams
Sequence/state diagrams where needed.

## NFR Budget
Latency (p95): <...>  Throughput: <...>  Cost: <...>  Observability: <requirements>

## Test Requirements
Unit, integration, E2E, performance, security.

## Risks/Trade-offs
Known debt areas and trade-offs.
"""
    },
    "CMP": {
        "title": "Component Spec (CMP)",
        "content": """# Component Spec (CMP)
ID: Y10K-<PROJ>-<AREA>-CMP-<NNN>   Version: vX.Y.Z   Owner: <name>

## Purpose & Scope
<description>

## Interfaces
Inputs/Outputs, contracts, dependencies.

## Data
Read/write, schema/keys (Postgres/Redis).

## Errors & Recovery
Idempotency, retries, rate limits.

## Observability
Log keys, metrics, tracing points.

## Acceptance Criteria (AC)
<list>

## DoD (Checklist)
<list>
"""
    },
    "ADR": {
        "title": "ADR (Architecture Decision Record)",
        "content": """# ADR: <decision title>
SRS-IDs: <links>

## Context
Why is this decision needed?

## Alternatives
A/B/C with trade-offs.

## Decision
What is chosen and why.

## Consequences
Technical/operational effects + how to measure outcomes.

## Links
SRS-ID, PRs, metrics.
"""
    },
    "TICKET": {
        "title": "Ticket Template",
        "content": """# Ticket
Title: [Y10K-<PROJ>-<AREA>-<TYPE>-<NNN>] Short description

## Description
Purpose, scope.

## Links
HL/LL/ADR/PR.

## AC
- [ ] <criterion>

## DoR/DoD
- [ ] DoR met
- [ ] DoD met

## Test Notes
What to verify in PR/QA.
"""
    }
}

# Swedish (sv): localized content mirroring TEMPLATES
TEMPLATE_SWEDISH = {
    "HL": {
        "title": "SRS — High Level (HL)",
        "content": """# SRS — High Level (HL)
ID: Y10K-<PROJ>-<AREA>-HL-<NNN>   Version: vX.Y.Z   Ägare: <namn>   Datum: <YYYY-MM-DD>

## Sammanfattning & Mål
<sammanfattning>

## Scope & icke-scope
<scope>

## Aktörer & användningsfall (kort)
<aktörer och use-cases>

## Icke-funktionella krav (NFR)
Prestanda: <...>  Säkerhet: <...>  Tillgänglighet: <...>  Compliance: <...>

## Antaganden & beroenden
<listor>

## Risker & mitigering
<lista>

## Arkitektur (C4 Context/Container, 1 sida)
<kort översikt, vad som integreras och hur>

## Komponentkarta (tentativ)
<lista av planerade komponenter med framtida CMP-ID>
"""
    },
    "LL": {
        "title": "SRS — Low Level (LL)",
        "content": """# SRS — Low Level (LL)
ID: Y10K-<PROJ>-<AREA>-LL-<NNN>   Version: vX.Y.Z   Länkar: HL=<ID>, ADR=<ID>

## API-spec
Endpoints, kontrakt (OpenAPI/JSON), felkoder.

## Data
Tabeller, index, constraints, retention.

## Flöden/diagram
Sekvens-/tillståndsdiagram vid behov.

## NFR-budget
Latency (p95): <...>  Throughput: <...>  Kostnad: <...>  Observability: <krav>

## Testkrav
Enhet, integration, E2E, prestanda, säkerhet.

## Risker/kompromisser
Kända skuldområden och trade-offs.
"""
    },
    "CMP": {
        "title": "Komponentspec (CMP)",
        "content": """# Komponentspec (CMP)
ID: Y10K-<PROJ>-<AREA>-CMP-<NNN>   Version: vX.Y.Z   Ägare: <namn>

## Syfte & scope
<beskrivning>

## Gränssnitt
In/Out, kontrakt, beroenden.

## Data
Läs/skriv, schema/nycklar (Postgres/Redis).

## Fel & återhämtning
Idempotens, retries, rate-limits.

## Observability
Loggnycklar, metrics, tracing-punkter.

## Acceptanskriterier (AC)
<lista>

## DoD (checklista)
<lista>
"""
    },
    "ADR": {
        "title": "ADR (Architecture Decision Record)",
        "content": """# ADR: <beslutstitel>
SRS-ID: <kopplingar>

## Kontext
Varför behövs beslutet?

## Alternativ
A/B/C med trade-offs.

## Beslut
Detta väljs och varför.

## Konsekvenser
Tekniska/operativa följder + hur utfallet mäts.

## Länkar
SRS-ID, PR, mätningar.
"""
    },
    "TICKET": {
        "title": "Ticket-mall",
        "content": """# Ticket
Titel: [Y10K-<PROJ>-<AREA>-<TYPE>-<NNN>] Kort beskrivning

## Beskrivning
Syfte, scope.

## Länkar
HL/LL/ADR/PR.

## AC
- [ ] <kriterium>

## DoR/DoD
- [ ] DoR uppfyllt
- [ ] DoD uppfyllt

## Testnoter
Vad verifieras i PR/QA.
"""
    }
}

# English (en): base content
TEMPLATE_ENGLISH = BASE_TEMPLATE_ENGLISH

# For the remaining languages, default to English structure/content.
# These can be localized later without changing consumers.
TEMPLATE_SPANISH = BASE_TEMPLATE_ENGLISH
TEMPLATE_PORTUGUESE = BASE_TEMPLATE_ENGLISH
TEMPLATE_FRENCH = BASE_TEMPLATE_ENGLISH
TEMPLATE_GERMAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_ITALIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_DUTCH = BASE_TEMPLATE_ENGLISH
TEMPLATE_DANISH = BASE_TEMPLATE_ENGLISH
TEMPLATE_NORWEGIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_FINNISH = BASE_TEMPLATE_ENGLISH
TEMPLATE_ICELANDIC = BASE_TEMPLATE_ENGLISH
TEMPLATE_POLISH = BASE_TEMPLATE_ENGLISH
TEMPLATE_CZECH = BASE_TEMPLATE_ENGLISH
TEMPLATE_SLOVAK = BASE_TEMPLATE_ENGLISH
TEMPLATE_HUNGARIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_ROMANIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_BULGARIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_GREEK = BASE_TEMPLATE_ENGLISH
TEMPLATE_RUSSIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_UKRAINIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_SERBIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_CROATIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_BOSNIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_SLOVENIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_TURKISH = BASE_TEMPLATE_ENGLISH
TEMPLATE_ARABIC = BASE_TEMPLATE_ENGLISH
TEMPLATE_HEBREW = BASE_TEMPLATE_ENGLISH
TEMPLATE_PERSIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_HINDI = BASE_TEMPLATE_ENGLISH
TEMPLATE_URDU = BASE_TEMPLATE_ENGLISH
TEMPLATE_BENGALI = BASE_TEMPLATE_ENGLISH
TEMPLATE_PUNJABI = BASE_TEMPLATE_ENGLISH
TEMPLATE_TAMIL = BASE_TEMPLATE_ENGLISH
TEMPLATE_TELUGU = BASE_TEMPLATE_ENGLISH
TEMPLATE_MARATHI = BASE_TEMPLATE_ENGLISH
TEMPLATE_GUJARATI = BASE_TEMPLATE_ENGLISH
TEMPLATE_KANNADA = BASE_TEMPLATE_ENGLISH
TEMPLATE_MALAYALAM = BASE_TEMPLATE_ENGLISH
TEMPLATE_SINHALA = BASE_TEMPLATE_ENGLISH
TEMPLATE_THAI = BASE_TEMPLATE_ENGLISH
TEMPLATE_LAO = BASE_TEMPLATE_ENGLISH
TEMPLATE_KHMER = BASE_TEMPLATE_ENGLISH
TEMPLATE_VIETNAMESE = BASE_TEMPLATE_ENGLISH
TEMPLATE_MONGOLIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_CHINESE_SIMPLIFIED = BASE_TEMPLATE_ENGLISH
TEMPLATE_CHINESE_TRADITIONAL = BASE_TEMPLATE_ENGLISH
TEMPLATE_JAPANESE = BASE_TEMPLATE_ENGLISH
TEMPLATE_KOREAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_TAGALOG = BASE_TEMPLATE_ENGLISH
TEMPLATE_MALAY = BASE_TEMPLATE_ENGLISH
TEMPLATE_INDONESIAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_SWAHILI = BASE_TEMPLATE_ENGLISH
TEMPLATE_ZULU = BASE_TEMPLATE_ENGLISH
TEMPLATE_XHOSA = BASE_TEMPLATE_ENGLISH
TEMPLATE_AMHARIC = BASE_TEMPLATE_ENGLISH
TEMPLATE_YORUBA = BASE_TEMPLATE_ENGLISH
TEMPLATE_HAUSA = BASE_TEMPLATE_ENGLISH
TEMPLATE_IGBO = BASE_TEMPLATE_ENGLISH
TEMPLATE_AFRIKAANS = BASE_TEMPLATE_ENGLISH
TEMPLATE_MAORI = BASE_TEMPLATE_ENGLISH
TEMPLATE_SAMOAN = BASE_TEMPLATE_ENGLISH
TEMPLATE_TONGAN = BASE_TEMPLATE_ENGLISH
