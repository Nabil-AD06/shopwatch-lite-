
import re
from src.contrat import Signal


def masquer_donnees(texte: str) -> str:
    """Masque les données sensibles courantes."""
    # Masquer les adresses e-mail
    texte = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL_MASQUE]",
        texte
    )

    # Masquer les numéros de carte de 13 à 19 chiffres,
    # avec éventuellement des espaces ou des tirets
    texte = re.sub(
        r"\b(?:\d[ -]?){13,19}\b",
        "[CARTE_MASQUEE]",
        texte
    )

    # Masquer les valeurs des champs sensibles
    texte = re.sub(
        r"(?i)\b(password|mot_de_passe|token|secret)\s*[:=]\s*\S+",
        r"\1=[MASQUE]",
        texte
    )

    # Hotfix : masquer le jeton Bearer
    texte = re.sub(
        r"(Bearer\s+)\S+",
        r"\1[MASQUE]",
        texte,
        flags=re.IGNORECASE
    )

    return texte

def lire_journal(
    ligne: str,
    numero: int,
    origine: str = "PAIEMENT",
    env: str = "production"
) -> Signal:
    """Transforme une ligne de journal en Signal."""
    texte = masquer_donnees(ligne)

    # Déterminer la gravité à partir des mots présents
    contenu = texte.lower()

    if "bloquant" in contenu or "critical" in contenu:
        gravite = "BLOQUANT"
    elif "error" in contenu or "erreur" in contenu:
        gravite = "MAJEUR"
    elif "warning" in contenu or "warn" in contenu:
        gravite = "MODERE"
    else:
        gravite = "MINEUR"

    if "timeout" in contenu:
        service = "PAIEMENT"
    else:
        service = origine

    return Signal(
        ref=f"JOURNAL-{numero}",
        date="",
        origine=origine,
        service=service,
        env=env,
        categorie="JOURNAL",
        gravite=gravite,
        texte=texte
    )



def lire_scan(rapport: dict, numero: int, env: str = "production") -> Signal:
    """Transforme un rapport de scan en Signal."""
    texte = masquer_donnees(str(rapport))

    gravite_brute = str(
        rapport.get(
            "risque",
            rapport.get("severity", rapport.get("gravite", "MODERE"))
        )
    ).upper()

    correspondances = {
        "LOW": "MINEUR",
        "INFO": "MINEUR",
        "MEDIUM": "MODERE",
        "MODERATE": "MODERE",
        "HIGH": "MAJEUR",
        "CRITICAL": "BLOQUANT",
        "CRITIQUE": "BLOQUANT",
    }

    gravite = correspondances.get(gravite_brute, gravite_brute)

    if gravite not in ["MINEUR", "MODERE", "MAJEUR", "BLOQUANT"]:
        gravite = "MODERE"

    return Signal(
        ref=f"SCAN-{numero}",
        date=str(rapport.get("date", "")),
        origine="SCANNER",
        service=str(rapport.get("service", rapport.get("paquet", "SCANNER"))),
        env=env,
        categorie="FAILLE",
        gravite=gravite,
        texte=texte,
    )



def lire_build(rapport: dict, numero: int, env: str = "production") -> Signal:
    """Transforme un rapport de build en Signal."""
    texte = masquer_donnees(str(rapport))

    statut = str(
        rapport.get(
            "resultat",
            rapport.get("status", rapport.get("statut", ""))
        )
    ).upper()

    echecs = {"FAILED", "FAILURE", "ERROR", "KO", "ECHEC", "ÉCHEC"}
    echec = statut in echecs

    return Signal(
        ref=f"BUILD-{numero}",
        date=str(rapport.get("date", "")),
        origine="BUILD",
        service=str(rapport.get("service", rapport.get("etape", "BUILD"))),
        env=env,
        categorie="BUILD_ECHEC" if echec else "BUILD_OK",
        gravite="MAJEUR" if echec else "MINEUR",
        texte=texte,
    )
