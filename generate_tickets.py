import random
from datetime import datetime, timedelta
import json
import csv
import os
import dotenv
from openai import OpenAI
import ssl

#source env
dotenv.load_dotenv()
OpenAI.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

# Définir les catégories d'incidents et les label possibles
categories = {
    "MEC": {
        "category": "Non-conformités Mécaniques",
        "label": [
            "Défaut d'alignement détecté lors de l'assemblage",
            "Couple de serrage incorrect sur le moteur",
            "Pièce endommagée constatée pendant le contrôle",
            "Usure prématurée d'un composant mécanique",
            "Fuite hydraulique détectée dans le système",
            "Vibration excessive observée lors des tests",
            "Corrosion prématurée sur une pièce métallique",
            "Déformation structurelle identifiée",
            "Problème d'équilibrage sur une pièce rotative",
            "Surchauffe d'un composant mécanique"
        ],
        "ticket_status": ["Ouvert", "En cours d'analyse", "Correction en cours", "En validation", "Fermé"],
        "weight": 0.25  # 25% du total des tickets
    },
    "ELE": {
        "category": "Non-conformités Électriques",
        "label": [
            "Erreur de câblage dans le système de navigation",
            "Connecteur défectueux entraînant une perte de signal",
            "Court-circuit détecté lors des tests électriques",
            "Batterie défaillante nécessitant un remplacement",
            "Acategoryalie dans le système d'alimentation électrique",
            "Interférence électromagnétique observée",
            "Problème de mise à la terre sur un composant",
            "Fusible grillé lors de l'activation du système",
            "Survoltage détecté dans le circuit principal",
            "Défaut d'isolation sur un câble électrique"
        ],
        "ticket_status": ["Ouvert", "En cours d'analyse", "Correction en cours", "En validation", "Fermé"],
        "weight": 0.20  # 20% du total des tickets
    },
    "LOG": {
        "category": "Non-conformités Logicielles",
        "label": [
            "Bug critique dans le logiciel de pilotage automatique",
            "Incompatibilité entre les versions du firmware",
            "Erreur de configuration du système embarqué",
            "Temps de réponse anormalement long du système",
            "Crash du système lors de l'exécution de certaines commandes",
            "Mémoire insuffisante provoquant des ralentissements",
            "Erreur dans les calculs de navigation",
            "Problème de sécurité dans le logiciel embarqué",
            "Mise à jour échouée du logiciel système",
            "Fonctionnalité manquante dans le module de communication"
        ],
        "ticket_status": ["Ouvert", "Analyse par l'ingénieur logiciel", "Développement en cours", "Tests de validation", "Fermé"],
        "weight": 0.15  # 15% du total des tickets
    },
    "DOC": {
        "category": "Non-conformités Documentaires",
        "label": [
            "Manuel d'utilisation manquant pour un équipement",
            "Procédure obsolète détectée dans la documentation",
            "Erreur d'étiquetage sur les composants",
            "Incohérence entre le schéma et la description textuelle",
            "Page manquante dans le rapport technique",
            "Mauvaise traduction dans la documentation fournie",
            "Référence incorrecte à une norme industrielle",
            "Table des matières incomplète ou erronée",
            "Illustrations manquantes pour certaines procédures",
            "Instructions de sécurité absentes du manuel"
        ],
        "ticket_status": ["Ouvert", "Vérification par le responsable documentation", "Mise à jour en cours", "Diffusion de la nouvelle version", "Fermé"],
        "weight": 0.10  # 10% du total des tickets
    },
    "QUAL": {
        "category": "Non-conformités de Contrôle Qualité",
        "label": [
            "Mesures incorrectes relevées lors du contrôle",
            "Calibration erronée d'un instrument de mesure",
            "Contrôle qualité manquant sur une série de pièces",
            "Non-respect des tolérances spécifiées",
            "Procédure de contrôle non appliquée correctement",
            "Échantillonnage insuffisant pour les tests",
            "Rapport de contrôle qualité incomplet",
            "Non-conformité aux normes ISO détectée",
            "Erreur humaine lors de l'inspection visuelle",
            "Non-respect du plan de contrôle établi"
        ],
        "ticket_status": ["Ouvert", "Analyse par l'ingénieur qualité", "Action corrective en cours", "Suivi et vérification", "Fermé"],
        "weight": 0.15  # 15% du total des tickets
    },
    "SUP": {
        "category": "Non-conformités de Chaîne d'Approvisionnement",
        "label": [
            "Livraison tardive de composants critiques",
            "Réception de pièces non conformes aux spécifications",
            "Composants contrefaits détectés dans le lot",
            "Erreur dans la quantité de pièces livrées",
            "Documentation du fournisseur incomplète",
            "Changement de fournisseur sans notification",
            "Problèmes de qualité récurrents avec un fournisseur",
            "Non-respect des conditions d'emballage",
            "Étiquetage incorrect sur les lots reçus",
            "Non-conformité aux réglementations d'importation"
        ],
        "ticket_status": ["Ouvert", "Analyse par l'acheteur", "Communication avec le fournisseur", "Action corrective du fournisseur", "Fermé"],
        "weight": 0.10  # 10% du total des tickets
    },
    "SEC": {
        "category": "Non-conformités de Sécurité",
        "label": [
            "Équipement de protection individuelle manquant",
            "Danger non résolu signalé sur le site",
            "Procédure de sécurité non respectée par le personnel",
            "Zone de travail non conforme aux normes de sécurité",
            "Incident de sécurité sans blessure signalé",
            "Signalisation de sécurité absente ou insuffisante",
            "Formation à la sécurité non suivie par un employé",
            "Matériel de premiers secours non disponible",
            "Exercice d'évacuation non réalisé dans les délais",
            "Utilisation inappropriée d'équipements dangereux"
        ],
        "ticket_status": ["Ouvert", "Analyse par le responsable sécurité", "Action immédiate en cours", "Mise en place de mesures préventives", "Fermé"],
        "weight": 0.05  # 5% du total des tickets
    }
}

def generate_comment(ticket_id, status, category_name):
    # Génère un commentaire en utilisant des templates
    commentaires_templates = {
        "Ouvert": f"Le ticket {ticket_id} a été ouvert suite à une non-conformité détectée",
        "En cours d'analyse": f"L'équipe analyse actuellement le ticket {ticket_id}",
        "Correction en cours": f"Des mesures correctives sont en cours pour le ticket {ticket_id}",
        "En validation": f"Le ticket {ticket_id} est en phase de validation",
        "Fermé": f"Le ticket {ticket_id} a été résolu et fermé",
        "Analyse par l'ingénieur logiciel": f"L'ingénieur logiciel examine le ticket {ticket_id}",
        "Développement en cours": f"Les corrections logicielles sont en cours pour le ticket {ticket_id}",
        "Tests de validation": f"Les tests de validation sont en cours pour le ticket {ticket_id}",
        "Vérification par le responsable documentation": f"Le responsable documentation vérifie le ticket {ticket_id}",
        "Mise à jour en cours": f"La documentation est en cours de mise à jour pour le ticket {ticket_id}",
        "Diffusion de la nouvelle version": f"La nouvelle documentation pour le ticket {ticket_id} a été diffusée",
        "Analyse par l'ingénieur qualité": f"L'ingénieur qualité analyse le ticket {ticket_id}",
        "Action corrective en cours": f"Des actions correctives sont mises en place pour le ticket {ticket_id}",
        "Suivi et vérification": f"Un suivi est en cours pour le ticket {ticket_id}",
        "Analyse par l'acheteur": f"L'acheteur analyse le ticket {ticket_id}",
        "Communication avec le fournisseur": f"Le fournisseur a été contacté concernant le ticket {ticket_id}",
        "Action corrective du fournisseur": f"Le fournisseur met en place des actions pour le ticket {ticket_id}",
        "Analyse par le responsable sécurité": f"Le responsable sécurité examine le ticket {ticket_id}",
        "Action immédiate en cours": f"Des mesures immédiates sont prises pour le ticket {ticket_id}",
        "Mise en place de mesures préventives": f"Des mesures préventives sont instaurées pour le ticket {ticket_id}"
    }
    comment = commentaires_templates.get(status, f"Statut {status} pour le ticket {ticket_id}")
    return comment

def generate_ticket_dates(num_tickets, start_date, end_date):
    total_days = (end_date - start_date).days + 1
    dates = []
    for _ in range(num_tickets):
        random_day = random.randint(0, total_days - 1)
        date = start_date + timedelta(days=random_day)
        dates.append(date)
    return dates

def generate_description(category_name, description_hint):
    prompt = (
        f"Vous êtes un expert en gestion de non-conformités dans le domaine {category_name}. "
        f"Veuillez générer une description détaillée et réaliste pour une non-conformité. "
        f"Voici un exemple de description : {description_hint}. "
        f"Assurez-vous que la description est pertinente et réaliste"
    )
    max_tokens = random.randint(30, 100)  # Longueur variable pour la description
    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model="gpt-4o-mini",
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def generate_tickets(category_code, category_info, ticket_dates):
    tickets = []
    for i, date_opened in enumerate(ticket_dates):
        ticket_id = f"NC-{category_code}-{i+1:05d}"
        # Sélectionner une description d'exemple aléatoire pour le prompt
        description_hint = random.choice(category_info['label'])
        # Utiliser l'IA pour générer une description
        description = generate_description(category_info['category'], description_hint)
        status_history = []
        current_date = date_opened
        category_name = category_info["category"]
        statuses = category_info["ticket_status"]
        for status in statuses:
            comment = generate_comment(ticket_id, status, category_name)
            status_entry = {
                "Statut": status,
                "Date": current_date.strftime("%Y-%m-%d"),
                "Commentaire": comment
            }
            status_history.append(status_entry)
            # Délais aléatoires entre les statuts, ajustés selon la catégorie
            if category_code == "LOG":
                delta_days = random.randint(3, 7)  # Délais plus longs pour le logiciel
            elif category_code == "SEC":
                delta_days = random.randint(1, 2)  # Délais plus courts pour la sécurité
            else:
                delta_days = random.randint(1, 5)
            current_date += timedelta(days=delta_days)
        ticket = {
            "Ticket ID": ticket_id,
            "Catégorie": category_name,
            "Date d'ouverture": date_opened.strftime("%Y-%m-%d"),
            "Description Initiale": description,
            "Historique des Statuts": status_history
        }
        tickets.append(ticket)
        # Affichage de la progression
        if (i + 1) % 10 == 0:  # Affiche tous les 100 tickets
            print(f"{i + 1}/{len(tickets)} tickets générés pour la catégorie {category_info['category']}")
    return tickets

def save_tickets_to_csv(tickets, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Ticket ID', 'Catégorie', 'Date d\'ouverture', 'Description Initiale', 'Statut', 'Date Statut', 'Commentaire']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for ticket in tickets:
            for status in ticket['Historique des Statuts']:
                writer.writerow({
                    'Ticket ID': ticket['Ticket ID'],
                    'Catégorie': ticket['Catégorie'],
                    "Date d'ouverture": ticket["Date d'ouverture"],  # Correction ici
                    'Description Initiale': ticket['Description Initiale'],
                    'Statut': status['Statut'],
                    'Date Statut': status['Date'],
                    'Commentaire': status['Commentaire']
                })

def main():
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 10, 31)
    total_tickets = 50  # categorybre total de tickets à générer
    all_tickets = []
    # Calculer le categorybre de tickets par catégorie
    for category_code, category_info in categories.items():
        num_tickets = int(total_tickets * category_info["weight"])
        print(f"Génération de {num_tickets} tickets pour la catégorie {category_info['category']}...")
        ticket_dates = generate_ticket_dates(num_tickets, start_date, end_date)
        tickets = generate_tickets(
            category_code=category_code,
            category_info=category_info,
            ticket_dates=ticket_dates
        )
        all_tickets.extend(tickets)
    # Enregistrer les tickets dans un fichier JSON
    with open('non_conformites.json', 'w', encoding='utf-8') as f:
        json.dump(all_tickets, f, ensure_ascii=False, indent=4)
    # Enregistrer les tickets dans un fichier CSV
    save_tickets_to_csv(all_tickets, 'non_conformites.csv')
    print("Génération terminée. Les données sont enregistrées dans 'non_conformites.json' et 'non_conformites.csv'")

if __name__ == "__main__":
    main()