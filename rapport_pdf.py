# ============================================================
# rapport_pdf.py — Generation des rapports PDF
# ------------------------------------------------------------
# Deux rapports disponibles :
#   1. Fiche individuelle d'une joueuse (tests + ACWR + graphique)
#   2. Rapport de synthese de l'equipe (tableau + alertes)
#
# Bibliotheques : reportlab (mise en page) + matplotlib (graphiques)
# ============================================================

import io

import matplotlib
matplotlib.use("Agg")  # rendu sans ecran (obligatoire sur un serveur)
import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Image
)

from donnees import COLONNES_TESTS, LIBELLES_TESTS
from calculs import (
    calculer_acwr_equipe, calculer_progression, extraire_tests,
    interpreter_acwr, construire_synthese_equipe
)

# Couleurs du club (jaune / noir — modifiables ici)
COULEUR_PRINCIPALE = colors.HexColor("#12303F")
COULEUR_ACCENT = colors.HexColor("#FFFFFF")
COULEUR_GRIS = colors.HexColor("#5F6368")


# ------------------------------------------------------------
# 1. OUTILS DE MISE EN PAGE
# ------------------------------------------------------------

def creer_styles():
    """Prepare les styles de paragraphes utilises dans les rapports."""
    base = getSampleStyleSheet()

    titre = ParagraphStyle(
        "TitreRapport", parent=base["Title"],
        fontSize=20, textColor=COULEUR_PRINCIPALE, spaceAfter=4,
    )
    sous_titre = ParagraphStyle(
        "SousTitre", parent=base["Normal"],
        fontSize=10, textColor=COULEUR_GRIS, spaceAfter=12,
    )
    section = ParagraphStyle(
        "Section", parent=base["Heading2"],
        fontSize=13, textColor=COULEUR_PRINCIPALE,
        spaceBefore=14, spaceAfter=6,
    )
    normal = ParagraphStyle(
        "NormalFR", parent=base["Normal"], fontSize=10, leading=14,
    )
    return titre, sous_titre, section, normal


def figure_vers_image(figure, largeur_cm):
    """Convertit une figure matplotlib en Image reportlab."""
    tampon = io.BytesIO()
    figure.savefig(tampon, format="png", dpi=150, bbox_inches="tight")
    plt.close(figure)
    tampon.seek(0)

    largeur_points = largeur_cm * cm
    # Conserver le ratio de la figure
    ratio = figure.get_figheight() / figure.get_figwidth()
    hauteur_points = largeur_points * ratio
    return Image(tampon, width=largeur_points, height=hauteur_points)


# ------------------------------------------------------------
# 2. GRAPHIQUES POUR LES RAPPORTS
# ------------------------------------------------------------

def graphique_evolution_tests(df, nom):
    """Figure matplotlib : evolution des 4 tests pour une joueuse."""
    tests = extraire_tests(df, nom)

    nb_tests = len(COLONNES_TESTS)
    nb_lignes = (nb_tests + 1) // 2
    figure, axes = plt.subplots(nb_lignes, 2, figsize=(9, 2.6 * nb_lignes))
    figure.suptitle("Evolution des tests — " + nom, fontsize=12)

    position = 0
    for colonne in COLONNES_TESTS:
        axe = axes[position // 2][position % 2]
        valeurs = tests.dropna(subset=[colonne])
        if len(valeurs) > 0:
            axe.plot(
                valeurs["date"], valeurs[colonne],
                marker="o", color="#12303F", linewidth=1.5, markersize=4,
            )
            axe.fill_between(
                valeurs["date"], valeurs[colonne],
                valeurs[colonne].min(), alpha=0.10, color="#5FA8D3",
            )
        axe.set_title(LIBELLES_TESTS[colonne], fontsize=9)
        axe.tick_params(axis="x", labelrotation=30, labelsize=7)
        axe.tick_params(axis="y", labelsize=7)
        axe.grid(True, alpha=0.3)
        position = position + 1

    # Masquer la derniere case si le nombre de tests est impair
    if nb_tests % 2 == 1:
        axes[nb_lignes - 1][1].axis("off")

    figure.tight_layout()
    return figure


def graphique_acwr(acwr_equipe, nom):
    """Figure matplotlib : courbe ACWR avec zones colorees."""
    donnees = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])

    figure, axe = plt.subplots(figsize=(9, 3.2))

    if len(donnees) > 0:
        # Zones de fond
        axe.axhspan(0.0, 0.8, color="#4A90D9", alpha=0.10)
        axe.axhspan(0.8, 1.3, color="#2E9E5B", alpha=0.12)
        axe.axhspan(1.3, 1.5, color="#E8A13C", alpha=0.12)
        axe.axhspan(1.5, 2.2, color="#D64545", alpha=0.10)

        axe.plot(
            donnees["date"], donnees["acwr"],
            color="#12303F", linewidth=1.8,
        )
        axe.set_ylim(0, 2.2)

    axe.set_title("Ratio charge aigue / chronique (ACWR) — " + nom, fontsize=10)
    axe.tick_params(labelsize=7)
    axe.grid(True, alpha=0.3)
    figure.tight_layout()
    return figure


# ------------------------------------------------------------
# 3. RAPPORT INDIVIDUEL (fiche joueuse)
# ------------------------------------------------------------

def generer_rapport_joueuse(df, nom, nom_club="CLUB", df_bien_etre=None):
    """Construit le PDF de la fiche joueuse. Retourne les octets du PDF."""
    tampon = io.BytesIO()
    document = SimpleDocTemplate(
        tampon, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    titre, sous_titre, section, normal = creer_styles()

    donnees_joueuse = df[df["nom"] == nom]
    poste = donnees_joueuse["poste"].iloc[-1]
    date_min = donnees_joueuse["date"].min().strftime("%d/%m/%Y")
    date_max = donnees_joueuse["date"].max().strftime("%d/%m/%Y")

    elements = []
    elements.append(Paragraph("Fiche de suivi — " + nom, titre))
    elements.append(Paragraph(
        "Poste : " + poste + "   |   Periode : " + date_min + " → " + date_max
        + "   |   " + nom_club + " — Preparation physique", sous_titre,
    ))

    # --- Tableau de progression -----------------------------
    elements.append(Paragraph("Progression sur les tests physiques", section))

    progression = calculer_progression(df, nom)
    lignes_tableau = [["Test", "1er releve", "Dernier", "Evolution", "Bilan"]]

    for colonne in COLONNES_TESTS:
        if colonne not in progression:
            continue
        info = progression[colonne]

        if info["en_progres"]:
            bilan = "Progres"
        else:
            bilan = "A surveiller"

        signe = ""
        if info["delta"] > 0:
            signe = "+"

        lignes_tableau.append([
            LIBELLES_TESTS[colonne],
            str(round(info["premier"], 2)),
            str(round(info["dernier"], 2)),
            signe + str(round(info["delta"], 2))
            + " (" + signe + str(round(info["delta_pct"], 1)) + " %)",
            bilan,
        ])

    tableau = Table(lignes_tableau, colWidths=[6.2 * cm, 2.6 * cm, 2.6 * cm, 3.6 * cm, 2.6 * cm])
    tableau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COULEUR_PRINCIPALE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COULEUR_ACCENT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DADCE0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(tableau)

    # --- Graphique d'evolution ------------------------------
    elements.append(Paragraph("Evolution dans le temps", section))
    figure_tests = graphique_evolution_tests(df, nom)
    elements.append(figure_vers_image(figure_tests, largeur_cm=16.5))

    # --- ACWR ----------------------------------------------
    elements.append(Paragraph("Charge d'entrainement (ACWR)", section))

    acwr_equipe = calculer_acwr_equipe(df)
    donnees_acwr = acwr_equipe[acwr_equipe["nom"] == nom].dropna(subset=["acwr"])

    if len(donnees_acwr) > 0:
        acwr_actuel = float(donnees_acwr["acwr"].iloc[-1])
        etiquette, couleur, emoji = interpreter_acwr(acwr_actuel)
        elements.append(Paragraph(
            "ACWR actuel : <b>" + str(round(acwr_actuel, 2)) + "</b> — "
            + etiquette + ". Zone habituelle de reference : 0,80 a 1,30 "
            + "(methode seance-RPE, charge = RPE x duree). Indicateur "
            + "descriptif de variation de charge, pas une prediction "
            + "de blessure.", normal,
        ))
        figure_charge = graphique_acwr(acwr_equipe, nom)
        elements.append(figure_vers_image(figure_charge, largeur_cm=16.5))
    else:
        elements.append(Paragraph(
            "Historique insuffisant pour calculer l'ACWR "
            + "(28 jours de donnees minimum).", normal,
        ))

    # --- Bien-etre (si donnees disponibles) -----------------
    if df_bien_etre is not None:
        donnees_bien_etre = df_bien_etre[df_bien_etre["nom"] == nom]
        if len(donnees_bien_etre) > 0:
            from calculs import calculer_hooper, interpreter_hooper

            elements.append(Paragraph("Bien-etre (questionnaire de Hooper)", section))

            df_h = calculer_hooper(donnees_bien_etre).sort_values("date")
            derniere = df_h.iloc[-1]
            hooper_actuel = int(derniere["hooper"])
            etiquette_h, emoji_h = interpreter_hooper(float(hooper_actuel))

            sept_derniers = df_h.tail(7)
            moyenne_7j = float(sept_derniers["hooper"].mean())

            elements.append(Paragraph(
                "Dernier indice : <b>" + str(hooper_actuel) + "</b> ("
                + etiquette_h + ") — moyenne des 7 derniers jours : "
                + str(round(moyenne_7j, 1))
                + ". Echelle de 4 (excellent) a 28 (tres degrade) ; "
                + "sommeil, fatigue, courbatures et stress notes de 1 a 7.",
                normal,
            ))

    document.build(elements)
    tampon.seek(0)
    return tampon.getvalue()


# ------------------------------------------------------------
# 4. RAPPORT DE SYNTHESE EQUIPE
# ------------------------------------------------------------

def generer_rapport_equipe(df, nom_club="CLUB"):
    """Construit le PDF de synthese de l'equipe. Retourne les octets."""
    tampon = io.BytesIO()
    document = SimpleDocTemplate(
        tampon, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    titre, sous_titre, section, normal = creer_styles()

    date_min = df["date"].min().strftime("%d/%m/%Y")
    date_max = df["date"].max().strftime("%d/%m/%Y")

    elements = []
    elements.append(Paragraph("Rapport d'equipe — " + nom_club, titre))
    elements.append(Paragraph(
        "Periode : " + date_min + " → " + date_max
        + "   |   Suivi de preparation physique", sous_titre,
    ))

    synthese, acwr_equipe = construire_synthese_equipe(df)

    # --- Alertes en premier (l'information la plus utile) ----
    elements.append(Paragraph("Alertes de charge", section))

    alertes = []
    for indice in range(len(synthese)):
        ligne = synthese.iloc[indice]
        valeur = ligne["ACWR"]
        if pd.notna(valeur) and (valeur > 1.30 or valeur < 0.80):
            alertes.append(ligne)

    if len(alertes) == 0:
        elements.append(Paragraph(
            "Aucune alerte : toutes les joueuses sont dans leur zone habituelle de charge.", normal,
        ))
    else:
        for ligne in alertes:
            etiquette, couleur, emoji = interpreter_acwr(float(ligne["ACWR"]))
            elements.append(Paragraph(
                "• <b>" + str(ligne["Joueuse"]) + "</b> ("
                + str(ligne["Poste"]) + ") — ACWR "
                + str(round(float(ligne["ACWR"]), 2)) + " : " + etiquette,
                normal,
            ))

    # --- Tableau de synthese --------------------------------
    elements.append(Paragraph("Synthese par joueuse", section))

    lignes_tableau = [["Joueuse", "Poste", "CMJ (cm)", "Attaque (cm)",
                       "Sprint 10 m (s)", "ACWR", "Statut"]]
    for indice in range(len(synthese)):
        ligne = synthese.iloc[indice]

        cmj_texte = "—"
        if pd.notna(ligne["CMJ (cm)"]):
            cmj_texte = str(round(float(ligne["CMJ (cm)"]), 1))

        attaque_texte = "—"
        if pd.notna(ligne["Attaque (cm)"]):
            attaque_texte = str(int(round(float(ligne["Attaque (cm)"]))))

        vitesse_texte = "—"
        if pd.notna(ligne["Sprint 10 m (s)"]):
            vitesse_texte = str(round(float(ligne["Sprint 10 m (s)"]), 2))

        acwr_texte = "—"
        if pd.notna(ligne["ACWR"]):
            acwr_texte = str(round(float(ligne["ACWR"]), 2))

        statut_sans_emoji = str(ligne["Statut"])
        # Retirer l'emoji pour le PDF (polices PDF standard sans emoji)
        morceaux = statut_sans_emoji.split(" ", 1)
        if len(morceaux) == 2:
            statut_sans_emoji = morceaux[1]

        lignes_tableau.append([
            str(ligne["Joueuse"]), str(ligne["Poste"]),
            cmj_texte, attaque_texte, vitesse_texte, acwr_texte,
            statut_sans_emoji,
        ])

    tableau = Table(
        lignes_tableau,
        colWidths=[2.9 * cm, 2.7 * cm, 1.8 * cm, 2.2 * cm,
                   2.5 * cm, 1.6 * cm, 3.1 * cm],
    )
    tableau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COULEUR_PRINCIPALE),
        ("TEXTCOLOR", (0, 0), (-1, 0), COULEUR_ACCENT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DADCE0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(tableau)

    # --- Note methodologique --------------------------------
    elements.append(Paragraph("Methode", section))
    elements.append(Paragraph(
        "Charge d'entrainement calculee par la methode seance-RPE "
        + "(Foster) : charge = RPE (1-10) x duree en minutes. "
        + "ACWR = charge des 7 derniers jours / moyenne hebdomadaire "
        + "des 28 derniers jours. Zone habituelle de reference : 0,80 - 1,30. "
        + "L'ACWR est un signal de vigilance descriptif, pas un predicteur "
        + "individuel de blessure (Impellizzeri et al., 2020).", normal,
    ))

    document.build(elements)
    tampon.seek(0)
    return tampon.getvalue()
