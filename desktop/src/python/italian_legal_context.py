"""
Italian Legal Context - Allow/Deny Lists

Provides Italian legal-specific entity lists to reduce false positives in legal documents.

Key Features:
- Court names that should NOT be redacted
- Government institutions that should NOT be redacted
- Historical figures that should NOT be redacted
- Legal roles that should NOT be redacted

Expected Impact: 50% reduction in false positives on Italian legal documents

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

from typing import Dict, List, Set


# ============================================================
# ALLOW LISTS - Entities that should NEVER be anonymized
# ============================================================

ITALIAN_LEGAL_ALLOW_LISTS = {
    "courts": [
        # Supreme Courts
        "Corte di Cassazione",
        "Corte Costituzionale",
        "Consiglio di Stato",
        "Corte dei Conti",

        # Major Courts of Appeal
        "Corte d'Appello di Roma",
        "Corte d'Appello di Milano",
        "Corte d'Appello di Napoli",
        "Corte d'Appello di Torino",
        "Corte d'Appello di Firenze",
        "Corte d'Appello di Bologna",
        "Corte d'Appello di Venezia",
        "Corte d'Appello di Palermo",
        "Corte d'Appello di Bari",
        "Corte d'Appello di Catania",

        # Major Tribunals
        "Tribunale di Milano",
        "Tribunale di Roma",
        "Tribunale di Napoli",
        "Tribunale di Torino",
        "Tribunale di Firenze",
        "Tribunale di Bologna",
        "Tribunale di Venezia",
        "Tribunale di Palermo",
        "Tribunale di Bari",
        "Tribunale di Genova",

        # Administrative Courts
        "TAR Lazio",
        "TAR Lombardia",
        "TAR Campania",
        "TAR Piemonte",
        "TAR Toscana",
        "TAR Emilia-Romagna",
        "TAR Veneto",
        "TAR Sicilia",
        "TAR Puglia",

        # Special Courts
        "Tribunale per i Minorenni",
        "Tribunale di Sorveglianza",
        "Giudice di Pace",
        "Tribunale Superiore delle Acque Pubbliche"
    ],

    "institutions": [
        # Social Security & Employment
        "INPS",
        "Istituto Nazionale Previdenza Sociale",
        "INAIL",
        "Istituto Nazionale Assicurazione Infortuni sul Lavoro",

        # Tax & Finance
        "Agenzia delle Entrate",
        "Agenzia delle Entrate-Riscossione",
        "Guardia di Finanza",
        "Ministero dell'Economia e delle Finanze",
        "MEF",
        "Banca d'Italia",
        "CONSOB",

        # Justice & Interior
        "Ministero della Giustizia",
        "Ministero dell'Interno",
        "Polizia di Stato",
        "Carabinieri",
        "Polizia Penitenziaria",
        "Corpo Forestale dello Stato",

        # Legal Authorities
        "Consiglio Nazionale Forense",
        "CNF",
        "Ordine degli Avvocati",
        "Consiglio dell'Ordine",
        "Consiglio Superiore della Magistratura",
        "CSM",
        "Procura della Repubblica",

        # Professional Orders
        "Ordine dei Dottori Commercialisti",
        "Ordine dei Consulenti del Lavoro",
        "Ordine dei Notai",
        "Ordine degli Ingegneri",
        "Ordine degli Architetti",

        # Other Institutions
        "Camera di Commercio",
        "Agenzia per l'Italia Digitale",
        "AGID",
        "Garante per la Protezione dei Dati Personali",
        "GPDP",
        "ANAC",
        "Autorità Nazionale Anticorruzione"
    ],

    "legal_roles": [
        # Judges & Magistrates
        "Giudice",
        "Giudice Monocratico",
        "Presidente del Tribunale",
        "Presidente della Corte",
        "Consigliere",
        "Magistrato",

        # Prosecutors
        "Pubblico Ministero",
        "PM",
        "Procuratore della Repubblica",
        "Procuratore Generale",
        "Sostituto Procuratore",

        # Court Officers
        "Cancelliere",
        "Cancelliere Capo",
        "Ufficiale Giudiziario",
        "Segretario Giudiziario",

        # Legal Professionals
        "Avvocato dello Stato",
        "Notaio",
        "Avvocato",
        "Difensore",
        "Consulente Tecnico",
        "CTU",
        "Perito",
        "Custode Giudiziario"
    ],

    "legal_entities": [
        "Consiglio dell'Ordine degli Avvocati",
        "Cassa Forense",
        "Camera degli Avvocati",
        "Ordine dei Dottori Commercialisti",
        "Camera Arbitrale",
        "Consiglio Nazionale del Notariato"
    ],

    "universities": [
        # Major Italian Universities (often cited in legal documents)
        "Università di Bologna",
        "Università La Sapienza",
        "Università Bocconi",
        "Università Cattolica",
        "Università di Padova",
        "Università di Firenze",
        "Università di Pisa",
        "Università di Milano",
        "Università di Torino",
        "Università di Napoli Federico II"
    ]
}

# ============================================================
# DENY LISTS - Names that appear frequently but aren't PII
# ============================================================

ITALIAN_LEGAL_DENY_LISTS = {
    "historical_figures": [
        "Giuseppe Garibaldi",
        "Dante Alighieri",
        "Leonardo da Vinci",
        "Giuseppe Verdi",
        "Alessandro Manzoni",
        "Galileo Galilei",
        "Marco Polo",
        "Cristoforo Colombo",
        "Michelangelo Buonarroti",
        "Raffaello Sanzio"
    ],

    "legal_scholars": [
        # Classic Italian legal scholars (often cited)
        "Francesco Carnelutti",
        "Piero Calamandrei",
        "Emilio Betti",
        "Salvatore Satta",
        "Giuseppe Chiovenda",
        "Enrico Redenti",
        "Ludovico Mortara",
        "Giuseppe Zanobini",
        "Santi Romano",
        "Vittorio Emanuele Orlando",
        "Francesco Messineo",
        "Antonio Segni",
        "Ciro Mezzanotte",
        "Enrico Tullio Liebman"
    ],

    "common_legal_terms": [
        # Common role terms that might be detected as names
        "ricorrente",
        "convenuto",
        "attore",
        "imputato",
        "parte civile",
        "responsabile civile",
        "resistente",
        "appellante",
        "appellato",
        "ricorrente in cassazione",
        "controricorrente",

        # Document labels/headers that are NOT PII
        "firmato da",
        "sottoscritto da",
        "redatto da",
        "compilato da",
        "emesso da",
        "rilasciato da",
        "approvato da",
        "certificato da",
        "vistato da",
        "controfirmato da",
        "vidimato da"
    ],

    "organizational_terms": [
        # Generic organizational and governmental terms
        "Intergovernativi",
        "Intergovernativo",
        "Intergovernativa",
        "Governativo",
        "Governativa",
        "Istituzionale",
        "Organizzazione",
        "Federazione",
        "Confederazione",
        "Associazione",
        "Comitato",
        "Commissione",
        "Dipartimento",
        "Ufficio",
        "Servizio",
        "Agenzia",
        "Ente",
        "Istituto",
        "Centro",
        "Sezione",
        "Divisione"
    ],

    "job_titles": [
        # Common job titles that should NOT be treated as PII
        # Executive titles (English)
        "Chief Executive Officer",
        "Chief Technology Officer",
        "Chief Financial Officer",
        "Chief Operating Officer",
        "Chief Information Officer",
        "Chief Marketing Officer",
        "Chief Human Resources Officer",
        "Chief Legal Officer",
        "Chief Compliance Officer",
        "Chief Data Officer",
        "Chief Product Officer",
        "Chief Strategy Officer",
        "Chief Security Officer",
        "Chief Investment Officer",
        "Chief Risk Officer",

        # Executive titles (Italian)
        "Amministratore Delegato",
        "Direttore Generale",
        "Direttore Tecnico",
        "Direttore Finanziario",
        "Direttore Operativo",
        "Direttore Marketing",
        "Direttore Commerciale",
        "Direttore Risorse Umane",
        "Direttore Legale",
        "Direttore IT",
        "Direttore Acquisti",
        "Direttore Produzione",
        "Direttore Vendite",

        # Management titles
        "Managing Director",
        "General Manager",
        "Project Manager",
        "Program Manager",
        "Product Manager",
        "Account Manager",
        "Sales Manager",
        "Marketing Manager",
        "Operations Manager",
        "HR Manager",
        "IT Manager",
        "Finance Manager",
        "Legal Manager",

        # Professional titles
        "Senior Vice President",
        "Vice President",
        "Senior Director",
        "Director",
        "Senior Manager",
        "Manager",
        "Senior Consultant",
        "Consultant",
        "Senior Analyst",
        "Analyst",
        "Coordinator",
        "Specialist",
        "Officer",
        "Executive",
        "Associate",
        "Assistant",

        # Academic titles
        "Professor",
        "Associate Professor",
        "Assistant Professor",
        "Lecturer",
        "Researcher",
        "Research Fellow",
        "Professore Ordinario",
        "Professore Associato",
        "Ricercatore",

        # Generic organizational terms
        "Board Member",
        "Board of Directors",
        "Chairman",
        "President",
        "Vice Chairman",
        "Secretary",
        "Treasurer",
        "Member",
        "Presidente del Consiglio",
        "Consigliere di Amministrazione",
        "Sindaco",
        "Revisore dei Conti"
    ]
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_all_allow_list_terms() -> List[str]:
    """
    Get all terms from allow lists (entities that should NOT be redacted).

    Returns:
        Flat list of all allow-listed terms
    """
    all_terms = []
    for category_terms in ITALIAN_LEGAL_ALLOW_LISTS.values():
        all_terms.extend(category_terms)
    return all_terms


def get_all_deny_list_terms() -> List[str]:
    """
    Get all terms from deny lists (patterns to ignore).

    Returns:
        Flat list of all deny-listed terms
    """
    all_terms = []
    for category_terms in ITALIAN_LEGAL_DENY_LISTS.values():
        all_terms.extend(category_terms)
    return all_terms


def create_allow_deny_recognizers() -> Dict[str, List[str]]:
    """
    Create allow/deny list data structures for Italian legal context.

    Returns:
        Dictionary with allow and deny lists for integration with PII detector
    """
    return {
        "allow_lists": ITALIAN_LEGAL_ALLOW_LISTS,
        "deny_lists": ITALIAN_LEGAL_DENY_LISTS
    }


def is_allowed_entity(text: str) -> bool:
    """
    Check if text matches any allow-listed entity.

    Args:
        text: Text to check

    Returns:
        True if entity should NOT be redacted
    """
    text_lower = text.lower()
    all_terms = get_all_allow_list_terms()

    for term in all_terms:
        if term.lower() in text_lower or text_lower in term.lower():
            return True

    return False


def is_denied_pattern(text: str) -> bool:
    """
    Check if text matches any denied pattern.

    Args:
        text: Text to check

    Returns:
        True if pattern should be ignored
    """
    text_lower = text.lower()
    all_terms = get_all_deny_list_terms()

    for term in all_terms:
        if term.lower() in text_lower or text_lower in term.lower():
            return True

    return False


# Testing/example usage
if __name__ == "__main__":
    print("Italian Legal Context - Test")
    print("="*60)

    # Test allow lists
    test_courts = ["Tribunale di Milano", "Corte di Cassazione", "TAR Lazio"]
    print("\nTest: Courts (should NOT be redacted)")
    for court in test_courts:
        result = is_allowed_entity(court)
        print(f"  - '{court}': {'[OK] Not redacted' if result else '[FAIL] Would be redacted'}")

    # Test institutions
    test_institutions = ["INPS", "Agenzia delle Entrate", "Guardia di Finanza"]
    print("\nTest: Institutions (should NOT be redacted)")
    for inst in test_institutions:
        result = is_allowed_entity(inst)
        print(f"  - '{inst}': {'[OK] Not redacted' if result else '[FAIL] Would be redacted'}")

    # Test legal scholars
    test_scholars = ["Francesco Carnelutti", "Piero Calamandrei"]
    print("\nTest: Legal Scholars (should be ignored in citations)")
    for scholar in test_scholars:
        result = is_denied_pattern(scholar)
        print(f"  - '{scholar}': {'[OK] Ignored' if result else '[FAIL] Would be detected'}")

    # Test actual PII (should be detected)
    test_pii = ["Mario Rossi", "Via Roma 123"]
    print("\nTest: Actual PII (SHOULD be redacted)")
    for pii in test_pii:
        allowed = is_allowed_entity(pii)
        denied = is_denied_pattern(pii)
        print(f"  - '{pii}': {'[FAIL] Incorrectly allowed' if (allowed or denied) else '[OK] Would be redacted'}")

    # Statistics
    print(f"\n{'='*60}")
    print("Statistics:")
    print(f"  - Total allow-listed terms: {len(get_all_allow_list_terms())}")
    print(f"  - Total deny-listed terms: {len(get_all_deny_list_terms())}")
    print(f"  - Courts: {len(ITALIAN_LEGAL_ALLOW_LISTS['courts'])}")
    print(f"  - Institutions: {len(ITALIAN_LEGAL_ALLOW_LISTS['institutions'])}")
    print(f"  - Legal Roles: {len(ITALIAN_LEGAL_ALLOW_LISTS['legal_roles'])}")
    print(f"  - Legal Scholars: {len(ITALIAN_LEGAL_DENY_LISTS['legal_scholars'])}")
