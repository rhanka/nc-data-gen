import random
from datetime import datetime, timedelta
import json
import csv
import os
import dotenv
from openai import OpenAI

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
        "weight": 0.05  # 5% of total tickets
    }
}

# Define the ticket status steps & prompts with enhanced instructions for realism
ticket_status_steps_prompts = [
    {
        "status": "Open",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": (
            "As the technician involved in the A220 aircraft manufacturing process who opened the ticket, "
            "provide a detailed and realistic description of the non-conformity. "
            "Include specific observations, measurements, or issues noted, using professional and technical language appropriate for a technician."
        )
    },
    {
        "status": "Technical Analysis",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": (
            "As a technical analyst in the A220 aircraft manufacturing process, analyze the issue described. "
            "Provide insights based on previous comments and the ticket description, using professional language appropriate for an engineer. "
            "Include possible causes, affected systems, and any immediate recommendations."
        )
    },
    {
        "status": "Technical Analysis - expertise",
        "type": "optional",
        "recurrence": "many",
        "prompt": (
            "As an expert in the A220 aircraft manufacturing domain, offer specialized input on the issue. "
            "Expand on the analysis and previous comments with advanced technical insights, maintaining a professional tone."
        )
    },
    {
        "status": "Technical Analysis - validation",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": (
            "As the technical manager overseeing the A220 aircraft manufacturing, validate the analysis provided. "
            "Offer feedback or approval, addressing any concerns in a professional manner appropriate for management."
        )
    },
    {
        "status": "Calculation Analysis",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": "As a calculation engineer specialist, perform calculation analysis related to the issue and document your findings."
    },
    {
        "status": "Calculation Analysis - expertise",
        "type": "optional",
        "recurrence": "many",
        "prompt": "As a calculation engineer expert in the domain, contribute specialized calculations or validations as needed."
    },
    {
        "status": "Calculation Analysis - validation",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": "As the calculation engineer manager, validate the calculation analysis and provide approval or request further action."
    },
    {
        "status": "Analysis & Calculation - workpackage validation",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": "As the work package responsible, review all analyses and provide your signature with any additional comments."
    },
    {
        "status": "Root-cause analysis",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": "Conduct a root-cause analysis to determine the underlying issue and document your findings."
    },
    {
        "status": "Classification: Impact assessment (minor, major, critical)",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": "Assess the impact of the non-conformity and classify it as minor, major, or critical."
    },
    {
        "status": "Decision of corrective actions required",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": "Decide on the necessary corrective actions and document the decisions made."
    },
    {
        "status": "Correction Action Plan Definition",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": "Define a corrective action plan detailing the steps required to resolve the issue."
    },
    {
        "status": "Correction Action Plan Execution - per action",
        "type": "mandatory",
        "recurrence": "many",
        "prompt": "Execute the corrective action plan and document progress and any challenges faced."
    },
    {
        "status": "Validation of corrective actions",
        "type": "mandatory",
        "recurrence": "many",
        "prompt": "Validate that the corrective actions have resolved the issue and document your approval."
    },
    {
        "status": "Closure",
        "type": "mandatory",
        "recurrence": "once",
        "prompt": (
            "As the final reviewer, confirm that all steps have been completed satisfactorily and close the ticket. "
            "Provide a summary of the resolution, ensuring all documentation is complete, and maintain a professional tone."
        )
    }
]

def generate_comment(ticket_id, status_info, category_name, description, previous_comments):
    status = status_info["status"]
    prompt_injection = status_info["prompt"]

    # Decide on a word limit for the comment
    word_limit = random.randint(50, 500)

    # Generate a comment using OpenAI API based on the description and previous comments
    full_prompt = (
        f"Role: {prompt_injection}\n"
        f"Ticket ID: {ticket_id}\n"
        f"Category: {category_name}\n"
        f"Status: {status}\n"
        f"Ticket Description: {description}\n"
        f"Previous Comments:\n"
        f"{'-'*20}\n"
        f"{chr(10).join(previous_comments)}\n"
        f"{'-'*20}\n"
        f"Please write your comment, using professional and technical language appropriate for your role. "
        f"Ensure the response is realistic and aligns with the context provided. "
        f"Limit your response to approximately {word_limit} words."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": full_prompt,
        }],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_description(category_name, description_hint):
    # Decide on a word limit for the description
    word_limit = random.randint(50, 150)

    # Generate a description using OpenAI API based on the category and hint
    prompt = (
        f"You are a technician working on the A220 aircraft manufacturing process in the {category_name} domain.\n"
        f"Based on the hint '{description_hint}', provide a detailed and realistic description of a non-conformity event. "
        f"Include specific observations, measurements, or issues noted, using professional and technical language appropriate for a technician.\n"
        f"Please limit your response to approximately {word_limit} words."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def determine_complexity(description, first_technical_analysis):
    prompt = (
        f"Based on the following non-conformity description and technical analysis, "
        f"determine the complexity level of the issue on a scale from 1 (low) to 3 (high). "
        "Provide only the complexity level as a number (1, 2, or 3), and no additional text.\n\n"
        f"Description: {description}\n"
        f"Technical Analysis: {first_technical_analysis}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        max_tokens=1,
        temperature=0
    )
    complexity_str = response.choices[0].message.content.strip()
    try:
        complexity = int(complexity_str)
        if complexity in [1, 2, 3]:
            return complexity
        else:
            return random.randint(1, 3)
    except ValueError:
        return random.randint(1, 3)

def determine_action_plan_length(ticket_history):
    prompt = (
        f"Given the ticket history below, estimate a realistic number of actions required "
        f"for the corrective action plan. Provide only the number of actions as an integer between 1 and 5.\n\n"
        f"Ticket History:\n"
        f"{'-'*20}\n"
        f"{chr(10).join(ticket_history)}\n"
        f"{'-'*20}\n"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        max_tokens=1,
        temperature=0
    )
    num_actions_str = response.choices[0].message.content.strip()
    try:
        num_actions = int(num_actions_str)
        if 1 <= num_actions <= 5:
            return num_actions
        else:
            return random.randint(1, 5)
    except ValueError:
        return random.randint(1, 5)

def generate_ticket_dates(num_tickets, start_date, end_date):
    total_days = (end_date - start_date).days + 1
    dates = []
    for _ in range(num_tickets):
        random_day = random.randint(0, total_days - 1)
        date = start_date + timedelta(days=random_day)
        dates.append(date)
    return dates

def generate_tickets(category_code, category_info, ticket_dates):
    tickets = []
    category_name = category_info["category"]
    labels = category_info["label"]
    for i, date_opened in enumerate(ticket_dates):
        ticket_id = f"{category_code}-{i+1:04d}"
        description_hint = random.choice(labels)
        description = generate_description(category_name, description_hint)
        status_history = []
        previous_comments = []

        current_date = date_opened
        action_plan_actions = []
        first_technical_analysis = ""

        for status_info in ticket_status_steps_prompts:
            status = status_info["status"]
            count = 1
            if status_info["type"] == "optional":
                if random.choice([True, False]):
                    continue  # Skip optional steps randomly
            if status_info["recurrence"] == "many":
                complexity = determine_complexity(description, first_technical_analysis)
                count = random.randint(1, complexity) if complexity > 1 else 1

            for _ in range(count):
                comment = generate_comment(ticket_id, status_info, category_name, description, previous_comments)
                previous_comments.append(comment)
                status_entry = {
                    "Status": status_info["status"],
                    "Date": current_date.strftime("%Y-%m-%d"),
                    "Comment": comment
                }
                status_history.append(status_entry)
                if status_info["status"] == "Technical Analysis" and not first_technical_analysis:
                    first_technical_analysis = comment
                # Adjust date progression
                delta_days = random.randint(1, 5)
                current_date += timedelta(days=delta_days)

            # Special handling for action plan steps
            if status_info["status"] == "Correction Action Plan Definition":
                num_actions = determine_action_plan_length(previous_comments)
                action_plan_actions = [f"Action {j+1}" for j in range(num_actions)]
            elif status_info["status"] == "Correction Action Plan Execution - per action":
                for action in action_plan_actions:
                    delta_days = random.randint(5, 15)
                    current_date += timedelta(days=delta_days)
                    action_comment = generate_comment(
                        ticket_id,
                        status_info,
                        category_name,
                        description,
                        previous_comments + [f"Action: {action}"]
                    )
                    previous_comments.append(action_comment)
                    status_entry = {
                        "Status": f"{status_info['status']} - {action}",
                        "Date": current_date.strftime("%Y-%m-%d"),
                        "Comment": action_comment
                    }
                    status_history.append(status_entry)
                continue
            elif status_info["status"] == "Validation of corrective actions":
                for action in action_plan_actions:
                    delta_days = random.randint(1, 5)
                    current_date += timedelta(days=delta_days)
                    validation_comment = generate_comment(
                        ticket_id,
                        status_info,
                        category_name,
                        description,
                        previous_comments + [f"Action: {action}"]
                    )
                    previous_comments.append(validation_comment)
                    status_entry = {
                        "Status": f"{status_info['status']} - {action}",
                        "Date": current_date.strftime("%Y-%m-%d"),
                        "Comment": validation_comment
                    }
                    status_history.append(status_entry)
                continue

        ticket = {
            "Ticket ID": ticket_id,
            "Category": category_name,
            "Open Date": date_opened.strftime("%Y-%m-%d"),
            "Initial Description": description,
            "Status History": status_history
        }
        tickets.append(ticket)
        print(ticket)
        if (i + 1) % 1 == 0:
            print(f"{i + 1}/{len(ticket_dates)} tickets generated for category {category_info['category']}")
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
                    'Open Date': ticket['Open Date'],
                    'Initial Description': ticket['Initial Description'],
                    'Status': status['Status'],
                    'Status Date': status['Date'],
                    'Comment': status['Comment']
                })

def main():
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 10, 31)
    total_tickets = 10  # Total number of tickets to generate
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
