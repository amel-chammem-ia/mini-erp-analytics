"""La facture PDF d'une vente validée (épisode 11, US-05).

Ne dépend ni de FastAPI ni de la base : on lui donne une FactureDocument, il renvoie les octets
du PDF. Les tests le vérifient sans serveur.

Mentions présentes (factures entre professionnels, France) : numéro unique, date d'émission,
identité et n° de TVA du vendeur et du client, désignation, quantité, prix unitaire HT,
taux de TVA, totaux HT, TVA par taux et TTC, date d'échéance, pénalités de retard,
indemnité forfaitaire de 40 € et absence d'escompte.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .montants import Totaux, format_euros

ENCRE = colors.HexColor("#1F2340")
GRIS = colors.HexColor("#6B7090")
FILET = colors.HexColor("#D9DBE8")
FOND = colors.HexColor("#F3F4FA")
ACCENT = colors.HexColor("#5B4BDB")

TEXTE = ParagraphStyle("texte", fontName="Helvetica", fontSize=9, leading=12, textColor=ENCRE)
PETIT = ParagraphStyle("petit", parent=TEXTE, fontSize=8, leading=10.5, textColor=GRIS)
GRAS = ParagraphStyle("gras", parent=TEXTE, fontName="Helvetica-Bold")
EMETTEUR = ParagraphStyle("emetteur", parent=TEXTE, fontName="Helvetica-Bold", fontSize=14, leading=18)
TITRE = ParagraphStyle("titre", parent=TEXTE, fontName="Helvetica-Bold", fontSize=22, leading=26,
                       textColor=ACCENT, alignment=TA_RIGHT)
DROITE = ParagraphStyle("droite", parent=TEXTE, alignment=TA_RIGHT)


@dataclass(frozen=True)
class Partie:
    nom: str
    lignes_adresse: tuple[str, ...] = ()
    numero_tva: str | None = None
    siret: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class LigneFacture:
    reference: str
    designation: str
    quantite: int
    prix_unitaire_ht: Decimal
    taux_tva: Decimal
    montant_ht: Decimal


@dataclass(frozen=True)
class FactureDocument:
    numero: str
    date_emission: date
    numero_commande: str
    emetteur: Partie
    client: Partie
    lignes: tuple[LigneFacture, ...]
    totaux: Totaux
    delai_paiement_jours: int = 30


def format_taux(taux: Decimal) -> str:
    """Decimal('20.00') → « 20 % », Decimal('5.50') → « 5,5 % »."""
    texte = f"{taux.normalize():f}".replace(".", ",")
    return f"{texte} %"


def format_date(jour: date) -> str:
    return jour.strftime("%d/%m/%Y")


def _echapper(texte: str) -> str:
    return texte.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _partie(partie: Partie, style_nom: ParagraphStyle) -> list:
    blocs = [Paragraph(_echapper(partie.nom), style_nom)]
    details = list(partie.lignes_adresse)
    if partie.email:
        details.append(partie.email)
    if partie.numero_tva:
        details.append(f"N° TVA : {partie.numero_tva}")
    if partie.siret:
        details.append(f"SIRET : {partie.siret}")
    blocs += [Paragraph(_echapper(ligne), TEXTE) for ligne in details]
    return blocs


def generer_facture_pdf(facture: FactureDocument) -> bytes:
    tampon = BytesIO()
    # pageCompression=0 : le texte reste lisible dans le fichier (les tests le vérifient) ;
    # invariant=1 : deux générations de la même facture donnent exactement le même fichier.
    doc = SimpleDocTemplate(tampon, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm, pageCompression=0, invariant=1,
                            title=f"Facture {facture.numero}", author=facture.emetteur.nom)
    largeur = A4[0] - 36 * mm
    echeance = facture.date_emission + timedelta(days=facture.delai_paiement_jours)

    infos = [Paragraph("FACTURE", TITRE), Spacer(1, 4)] + [
        Paragraph(f"{libelle} <b>{valeur}</b>", DROITE) for libelle, valeur in (
            ("N°", facture.numero),
            ("Date d'émission :", format_date(facture.date_emission)),
            ("Commande :", _echapper(facture.numero_commande)),
            ("Échéance :", format_date(echeance)),
        )]
    entete = Table([[_partie(facture.emetteur, EMETTEUR), infos]], colWidths=[largeur * 0.55, largeur * 0.45])
    entete.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))

    client = Table([[[Paragraph("FACTURÉ À", PETIT), Spacer(1, 2)] + _partie(facture.client, GRAS)]],
                   colWidths=[largeur * 0.45], hAlign="RIGHT")
    client.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FOND), ("BOX", (0, 0), (-1, -1), 0.6, FILET),
                                ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))

    lignes = [["Réf.", "Désignation", "Qté", "PU HT", "TVA", "Montant HT"]]
    for ligne in facture.lignes:
        lignes.append([ligne.reference, Paragraph(_echapper(ligne.designation), TEXTE), str(ligne.quantite),
                       format_euros(ligne.prix_unitaire_ht), format_taux(ligne.taux_tva),
                       format_euros(ligne.montant_ht)])
    tableau = Table(lignes, colWidths=[largeur * f for f in (0.12, 0.40, 0.07, 0.15, 0.09, 0.17)], repeatRows=1)
    tableau.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), ENCRE), ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), ENCRE), ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 1), (-1, -1), 0.4, FILET),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FOND]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    totaux = [["Total HT", format_euros(facture.totaux.total_ht)]]
    for tva in facture.totaux.tva_par_taux:
        totaux.append([f"TVA {format_taux(tva.taux)} sur {format_euros(tva.base_ht)}", format_euros(tva.montant_tva)])
    if len(facture.totaux.tva_par_taux) > 1:
        totaux.append(["Total TVA", format_euros(facture.totaux.total_tva)])
    totaux.append(["Total TTC", format_euros(facture.totaux.total_ttc)])
    bloc_totaux = Table(totaux, colWidths=[largeur * 0.30, largeur * 0.17], hAlign="RIGHT")
    bloc_totaux.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9), ("TEXTCOLOR", (0, 0), (-1, -1), ENCRE),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("LINEABOVE", (0, -1), (-1, -1), 0.8, ENCRE),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 11), ("BACKGROUND", (0, -1), (-1, -1), FOND),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    conditions = (f"Paiement à {facture.delai_paiement_jours} jours, au plus tard le {format_date(echeance)}. "
                  "En cas de retard : pénalités au taux de 3 fois le taux d'intérêt légal, et indemnité "
                  "forfaitaire de 40 € pour frais de recouvrement. Pas d'escompte pour paiement anticipé.")

    def pied_de_page(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GRIS)
        mentions = " · ".join(x for x in (facture.emetteur.nom, facture.emetteur.siret and
                                          f"SIRET {facture.emetteur.siret}", f"Facture {facture.numero}") if x)
        canvas.drawString(18 * mm, 11 * mm, mentions)
        canvas.drawRightString(A4[0] - 18 * mm, 11 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build([entete, Spacer(1, 10 * mm), client, Spacer(1, 8 * mm), tableau, Spacer(1, 6 * mm),
               bloc_totaux, Spacer(1, 10 * mm), Paragraph(conditions, PETIT)],
              onFirstPage=pied_de_page, onLaterPages=pied_de_page)
    return tampon.getvalue()
