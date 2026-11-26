"""Tests de la facture PDF (épisode 11) : sans serveur ni base."""
import re
from datetime import date
from decimal import Decimal as D

from app.facture_pdf import FactureDocument, LigneFacture, Partie, format_taux, generer_facture_pdf
from app.montants import LigneMontant, calculer_totaux

LIGNES = [("P-001", "Ordinateur portable 14 pouces", 2, "899.00", "20.00"),
          ("P-005", "Clavier sans fil", 3, "49.90", "20.00"),
          ("L-001", "Guide de prompt engineering", 1, "24.90", "5.50")]


def facture(nombre_de_lignes=None):
    lignes = LIGNES if nombre_de_lignes is None else [
        (f"P-{i:03d}", f"Article {i}", 1, "10.00", "20.00") for i in range(1, nombre_de_lignes + 1)]
    montants = [LigneMontant(q, D(p), D(t)) for _, _, q, p, t in lignes]
    return FactureDocument(
        numero="FAC-2026-00042", date_emission=date(2026, 11, 26), numero_commande="V-2026-0042",
        emetteur=Partie("Entreprise de demo", ("12 rue de l'Exemple", "69002 Lyon"), "FR00123456789"),
        client=Partie("Atelier Numerique", ("Lyon",), "FR01000000001"),
        lignes=tuple(LigneFacture(r, d, q, D(p), D(t), m.montant_ht)
                     for (r, d, q, p, t), m in zip(lignes, montants, strict=True)),
        totaux=calculer_totaux(montants))


def test_c_est_un_pdf_qui_porte_les_mentions_cles():
    pdf = generer_facture_pdf(facture())
    assert pdf.startswith(b"%PDF-")
    for texte in (b"FAC-2026-00042", b"V-2026-0042", b"FR01000000001", b"FR00123456789", b"26/12/2026"):
        assert texte in pdf, texte             # échéance : 30 jours après le 26/11/2026


def test_meme_facture_meme_fichier():
    assert generer_facture_pdf(facture()) == generer_facture_pdf(facture())


def nombre_de_pages(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", pdf))


def test_une_longue_facture_continue_sur_plusieurs_pages():
    assert nombre_de_pages(generer_facture_pdf(facture())) == 1
    assert nombre_de_pages(generer_facture_pdf(facture(nombre_de_lignes=80))) >= 2


def test_format_des_taux():
    assert format_taux(D("20.00")) == "20 %"
    assert format_taux(D("5.50")) == "5,5 %"
