import random
from datetime import datetime, timedelta
import json
import csv
import os
import dotenv
from openai import OpenAI
import ssl

# Load environment variables
dotenv.load_dotenv()
OpenAI.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

# Define incident categories and possible labels
categories = {
    "MEC": {
        "category": "Mechanical Non-Conformities",
        "label": [
            "Alignment defect detected during assembly",
            "Incorrect torque on the engine",
            "Damaged part identified during inspection",
            "Premature wear of a mechanical component",
            "Hydraulic leak detected in the system",
            "Excessive vibration observed during testing",
            "Premature corrosion on a metal part",
            "Structural deformation identified",
            "Balancing problem on a rotating part",
            "Overheating of a mechanical component"
        ],
        "ticket_status": ["Open", "Under Analysis", "Correction In Progress", "Under Validation", "Closed"],
        "weight": 0.25  # 25% of total tickets
    },
    "ELE": {
        "category": "Electrical Non-Conformities",
        "label": [
            "Wiring error in the navigation system",
            "Defective connector causing signal loss",
            "Short circuit detected during electrical tests",
            "Faulty battery requiring replacement",
            "Anomaly in the power supply system",
            "Electromagnetic interference observed",
            "Grounding problem on a component",
            "Blown fuse during system activation",
            "Overvoltage detected in the main circuit",
            "Insulation defect on an electrical cable"
        ],
        "ticket_status": ["Open", "Under Analysis", "Correction In Progress", "Under Validation", "Closed"],
        "weight": 0.20  # 20% of total tickets
    },
    "LOG": {
        "category": "Software Non-Conformities",
        "label": [
            "Critical bug in the autopilot software",
            "Incompatibility between firmware versions",
            "Configuration error in the embedded system",
            "Abnormally long system response time",
            "System crash during execution of certain commands",
            "Insufficient memory causing slowdowns",
            "Error in navigation calculations",
            "Security issue in the embedded software",
            "Failed software update",
            "Missing functionality in the communication module"
        ],
        "ticket_status": ["Open", "Software Engineer Analysis", "Development In Progress", "Validation Testing", "Closed"],
        "weight": 0.15  # 15% of total tickets
    },
    "DOC": {
        "category": "Documentation Non-Conformities",
        "label": [
            "Missing user manual for a piece of equipment",
            "Obsolete procedure detected in the documentation",
            "Labeling error on components",
            "Inconsistency between diagram and text description",
            "Missing page in the technical report",
            "Poor translation in the provided documentation",
            "Incorrect reference to an industry standard",
            "Incomplete or erroneous table of contents",
            "Missing illustrations for some procedures",
            "Missing safety instructions in the manual"
        ],
        "ticket_status": ["Open", "Document Officer Verification", "Update In Progress", "New Version Release", "Closed"],
        "weight": 0.10  # 10% of total tickets
    },
    "QUAL": {
        "category": "Quality Control Non-Conformities",
        "label": [
            "Incorrect measurements taken during inspection",
            "Incorrect calibration of a measuring instrument",
            "Missing quality control on a batch of parts",
            "Non-compliance with specified tolerances",
            "Improper application of control procedure",
            "Insufficient sampling for tests",
            "Incomplete quality control report",
            "ISO standard non-compliance detected",
            "Human error during visual inspection",
            "Non-compliance with the established control plan"
        ],
        "ticket_status": ["Open", "Quality Engineer Analysis", "Corrective Action In Progress", "Follow-up and Verification", "Closed"],
        "weight": 0.15  # 15% of total tickets
    },
    "SUP": {
        "category": "Supply Chain Non-Conformities",
        "label": [
            "Late delivery of critical components",
            "Receipt of parts not meeting specifications",
            "Counterfeit components detected in the batch",
            "Error in the quantity of parts delivered",
            "Incomplete supplier documentation",
            "Supplier change without notification",
            "Recurrent quality issues with a supplier",
            "Non-compliance with packaging conditions",
            "Incorrect labeling on received batches",
            "Non-compliance with import regulations"
        ],
        "ticket_status": ["Open", "Buyer Analysis", "Supplier Communication", "Supplier Corrective Action", "Closed"],
        "weight": 0.10  # 10% of total tickets
    },
    "SEC": {
        "category": "Safety Non-Conformities",
        "label": [
            "Missing personal protective equipment",
            "Unresolved hazard reported on site",
            "Safety procedure not followed by personnel",
            "Work area not meeting safety standards",
            "Safety incident reported without injury",
            "Insufficient or missing safety signage",
            "Safety training not completed by an employee",
            "First aid equipment not available",
            "Evacuation drill not conducted on time",
            "Improper use of hazardous equipment"
        ],
        "ticket_status": ["Open", "Safety Officer Analysis", "Immediate Action In Progress", "Preventive Measures Implementation", "Closed"],
        "weight": 0.05  # 5% of total tickets
    }
}

def generate_comment(ticket_id, status, category_name):
    # Generate a comment using templates
    comment_templates = {
        "Open": f"Ticket {ticket_id} was opened following a detected non-conformity",
        "Under Analysis": f"The team is currently analyzing ticket {ticket_id}",
        "Correction In Progress": f"Corrective measures are in progress for ticket {ticket_id}",
        "Under Validation": f"Ticket {ticket_id} is in the validation phase",
        "Closed": f"Ticket {ticket_id} has been resolved and closed",
        "Software Engineer Analysis": f"The software engineer is examining ticket {ticket_id}",
        "Development In Progress": f"Software corrections are in progress for ticket {ticket_id}",
        "Validation Testing": f"Validation tests are in progress for ticket {ticket_id}",
        "Document Officer Verification": f"The document officer is verifying ticket {ticket_id}",
        "Update In Progress": f"Documentation is being updated for ticket {ticket_id}",
        "New Version Release": f"The new documentation for ticket {ticket_id} has been released",
        "Quality Engineer Analysis": f"The quality engineer is analyzing ticket {ticket_id}",
        "Corrective Action In Progress": f"Corrective actions are being implemented for ticket {ticket_id}",
        "Follow-up and Verification": f"Follow-up is in progress for ticket {ticket_id}",
        "Buyer Analysis": f"The buyer is analyzing ticket {ticket_id}",
        "Supplier Communication": f"The supplier has been contacted regarding ticket {ticket_id}",
        "Supplier Corrective Action": f"The supplier is implementing actions for ticket {ticket_id}",
        "Safety Officer Analysis": f"The safety officer is examining ticket {ticket_id}",
        "Immediate Action In Progress": f"Immediate measures are being taken for ticket {ticket_id}",
        "Preventive Measures Implementation": f"Preventive measures are being implemented for ticket {ticket_id}"
    }
    comment = comment_templates.get(status, f"Status {status} for ticket {ticket_id}")
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
        f"You are an expert in non-conformity management in the {category_name} domain. "
        f"Please generate a detailed and realistic description for a non-conformity. "
        f"Here is an example of a description: {description_hint}. "
        f"Ensure that the description is relevant and realistic."
    )
    max_tokens = random.randint(30, 100)  # Variable length for description
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
        description_hint = random.choice(category_info['label'])
        description = generate_description(category_info['category'], description_hint)
        status_history = []
        current_date = date_opened
        category_name = category_info["category"]
        statuses = category_info["ticket_status"]
        for status in statuses:
            comment = generate_comment(ticket_id, status, category_name)
            status_entry = {
                "Status": status,
                "Date": current_date.strftime("%Y-%m-%d"),
                "Comment": comment
            }
            status_history.append(status_entry)
            if category_code == "LOG":
                delta_days = random.randint(3, 7)  # Longer delays for software
            elif category_code == "SEC":
                delta_days = random.randint(1, 2)  # Shorter delays for safety
            else:
                delta_days = random.randint(1, 5)
            current_date += timedelta(days=delta_days)
        ticket = {
            "Ticket ID": ticket_id,
            "Category": category_name,
            "Open Date": date_opened.strftime("%Y-%m-%d"),
            "Initial Description": description,
            "Status History": status_history
        }
        tickets.append(ticket)
        if (i + 1) % 10 == 0:
            print(f"{i + 1}/{len(tickets)} tickets generated for category {category_info['category']}")
    return tickets

def save_tickets_to_csv(tickets, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Ticket ID', 'Category', 'Open Date', 'Initial Description', 'Status', 'Status Date', 'Comment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for ticket in tickets:
            for status in ticket['Status History']:
                writer.writerow({
                    'Ticket ID': ticket['Ticket ID'],
                    'Category': ticket['Category'],
                    "Open Date": ticket["Open Date"],
                    'Initial Description': ticket['Initial Description'],
                    'Status': status['Status'],
                    'Status Date': status['Date'],
                    'Comment': status['Comment']
                })

def main():
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 10, 31)
    total_tickets = 50  # total number of tickets to generate
    all_tickets = []
    for category_code, category_info in categories.items():
        num_tickets = int(total_tickets * category_info["weight"])
        print(f"Generating {num_tickets} tickets for category {category_info['category']}...")
        ticket_dates = generate_ticket_dates(num_tickets, start_date, end_date)
        tickets = generate_tickets(
            category_code=category_code,
            category_info=category_info,
            ticket_dates=ticket_dates
        )
        all_tickets.extend(tickets)
    with open('non_conformities.json', 'w', encoding='utf-8') as f:
        json.dump(all_tickets, f, ensure_ascii=False, indent=4)
    save_tickets_to_csv(all_tickets, 'non_conformities.csv')
    print("Generation complete. Data saved to 'non_conformities.json' and 'non_conformities.csv'")

if __name__ == "__main__":
    main()
