import re
import csv
from datetime import datetime
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams


def convert_bank_of_america(files):
    records = process_pdf_files(files)
    csv_content = generate_csv_content(records)
    return csv_content


def generate_csv_content(records):
    csv_content = ""
    csv_content += "Date,Description,Amount\n"
    for record in records:
        csv_content += f"{record.get('date', 'N/A')},{record.get('desc', 'N/A')},{record.get('amount', 'N/A')}\n"
    return csv_content


def process_pdf_files(files):
    aggregated_deposits_records = []
    aggregated_withdrawals_records = []
    fees = []
    record_counter = 0  # Add a counter for easier tracking of records

    for filename in files:
        if filename.endswith(".pdf"):
            extracted_text = extract_text_from_pdf(filename)

            # Extracting records
            deposits_records = extract_table_data(
                extracted_text, "Deposits and other credits", "deposit"
            )
            withdrawals_records = extract_table_data(
                extracted_text, "Withdrawals and other debits", "withdrawal"
            )
            fee_records = extract_table_data(
                extracted_text, "Transaction description", "fee"
            )

            # Extracting and categorizing amounts
            amounts = extract_amounts(extracted_text)

            # Debugging: Print the number of records and amounts
            print(
                f"Deposits Records: {len(deposits_records)}, Amounts: {sum(1 for a in amounts if a[1] == 'deposit')}"
            )
            print(
                f"Withdrawals Records: {len(withdrawals_records)}, Amounts: {sum(1 for a in amounts if a[1] == 'withdrawal')}"
            )
            print(
                f"Fee Records: {len(fee_records)}, Amounts: {sum(1 for a in amounts if a[1] == 'fee')}"
            )

            # Assigning amounts to respective records
            for amount, category in amounts:
                if category == "deposit" and deposits_records:
                    assign_amount_to_record(deposits_records, amount)
                elif category == "withdrawal" and withdrawals_records:
                    assign_amount_to_record(withdrawals_records, amount)
                elif category == "fee" and fee_records:
                    assign_amount_to_record(fee_records, amount)

            # Aggregating records and adding a counter
            for record in deposits_records + withdrawals_records + fee_records:
                record["record_id"] = record_counter
                record_counter += 1
                if "amount" not in record:
                    print(
                        f"Missing amount in record ID {record['record_id']}: {record}"
                    )
                (
                    aggregated_deposits_records.append(record)
                    if record["category"] == "deposit"
                    else None
                )
                (
                    aggregated_withdrawals_records.append(record)
                    if record["category"] == "withdrawal"
                    else None
                )
                fees.append(record) if record["category"] == "fee" else None

    merged_records = aggregated_deposits_records + aggregated_withdrawals_records + fees
    return sorted(merged_records, key=parse_date)


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        return extract_text(file, laparams=LAParams())


def extract_table_data(extracted_text, table_title, category):
    if table_title not in extracted_text:
        return []
    date_pattern = re.compile(r"\d{2}/\d{2}/\d{2}")
    card_number_pattern = re.compile(r"X{12}\d{4}(\s+X{4}){3}")
    capturing = False
    records = []
    temp_records = []
    previous_was_date = False
    curr_temp_record = 0

    lines = [line for line in extracted_text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        if table_title == "Transaction description":
            if "Date" in line and i < len(lines) - 1 and table_title in lines[i + 1]:
                capturing = True
                continue
        elif i < len(lines) - 1 and table_title in line and lines[i + 1] == "Date":
            capturing = True
            continue

        if "Total" in line and capturing:
            if temp_records:
                records.extend(temp_records)
            capturing = False
            continue

        if capturing and not is_header_line(line):
            date_match = date_pattern.match(line.strip())
            cc_match = card_number_pattern.search(line.strip())
            if cc_match and "CHECKCARD" not in line:
                continue
            if date_match:
                if previous_was_date:
                    temp_records.append(
                        {"date": date_match.group(), "desc": "", "category": category}
                    )
                else:
                    if temp_records:
                        records.extend(temp_records)
                        temp_records = []
                    previous_was_date = True
                    temp_records.append(
                        {"date": date_match.group(), "desc": "", "category": category}
                    )
            else:
                previous_was_date = False

                if temp_records:
                    if len(temp_records) > 1:
                        if (
                            "DES:" in line or "CHECKCARD" in line or "CKCD" in line
                        ) and temp_records[0]["desc"]:
                            curr_temp_record += 1

                        if "DES:" in line or "CHECKCARD" in line or "CKCD" in line:
                            temp_records[curr_temp_record]["desc"] += line.strip()
                    else:
                        temp_records[0]["desc"] += line.strip()

                    if curr_temp_record >= len(temp_records):
                        records.extend(temp_records)
                        temp_records = []
                        curr_temp_record = 0

                elif records:
                    records[-1]["desc"] += line.strip() + " "

    return records


def is_header_line(line):
    header_keywords = ["Date", "Description", "Amount", "Transaction description"]
    return any(keyword in line for keyword in header_keywords)


def extract_amounts(extracted_text):
    valid_amount_pattern = re.compile(r"-?\d{1,3}(,\d{3})*\.\d{2}")
    lines = [line.strip() for line in extracted_text.split("\n") if line.strip()]
    amounts_with_categories = []
    last_amount_index = -1  # Initialize to an invalid index
    capturing = False

    for i, line in enumerate(lines):
        if "Amount" in line:
            capturing = True
            last_amount_index = len(
                amounts_with_categories
            )  # Update index to current length of amounts list
            continue

        if capturing and valid_amount_pattern.match(line):
            amount = line.replace(",", "")  # Remove commas
            category = "withdrawal" if amount.startswith("-") else "deposit"
            amounts_with_categories.append((amount, category))
            continue

        # Exit the amount section upon encountering a non-valid amount
        if capturing and not valid_amount_pattern.match(line):
            capturing = False

    # Update the category to 'fee' for the last set of amounts
    if last_amount_index != -1:
        for i in range(last_amount_index, len(amounts_with_categories)):
            amount = amounts_with_categories[i][0]
            amounts_with_categories[i] = (amount, "fee")

    return amounts_with_categories


def parse_date(d):
    return datetime.strptime(d["date"], "%m/%d/%y")


def assign_amount_to_record(records, amount):
    for record in records:
        if "amount" not in record:
            record["amount"] = amount
            break


def write_to_csv(records, filename):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Description", "Amount"])

        for record in records:
            if "amount" in record:
                writer.writerow(
                    [
                        record.get("date", "N/A"),
                        record.get("desc", "N/A"),
                        record["amount"],
                    ]
                )
