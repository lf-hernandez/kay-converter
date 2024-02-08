import os
import re
import csv
import sys
from datetime import datetime
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage


def extract_text_from_page(pdf_path, page_number):
    with open(pdf_path, "rb") as file:
        for page in PDFPage.get_pages(
            file, pagenos=[page_number - 1], check_extractable=True
        ):
            return extract_text(
                file, laparams=LAParams(), page_numbers=[page_number - 1]
            )


def is_header_line(line):
    header_keywords = ["Date", "Description", "Amount"]
    return any(keyword in line for keyword in header_keywords)


def extract_table_data(extracted_text, table_title):
    date_pattern = re.compile(r"\d{2}/\d{2}/\d{2}")
    capturing = False
    records = []
    temp_records = []
    previous_was_date = False
    curr_temp_record = 0

    lines = [line for line in extracted_text.split("\n") if line.strip()]
    lines = lines[lines.index(table_title) :]

    for i, line in enumerate(lines):
        if table_title in line:
            capturing = True
            continue

        if "Total" in line and capturing:
            if temp_records:
                records.extend(temp_records)
            capturing = False
            continue

        if capturing and not is_header_line(line):
            date_match = date_pattern.match(line.strip())
            if date_match:
                if previous_was_date:
                    temp_records.append({"date": date_match.group(), "desc": ""})
                else:
                    if temp_records:
                        records.extend(temp_records)
                        temp_records = []
                    previous_was_date = True
                    temp_records.append({"date": date_match.group(), "desc": ""})
            else:
                previous_was_date = False
                if temp_records:
                    if len(temp_records) > 1:
                        if "DES:" in line and temp_records[0]["desc"]:
                            curr_temp_record += 1

                        temp_records[curr_temp_record]["desc"] += line.strip() + " "
                    else:
                        temp_records[0]["desc"] += line.strip() + " "
                elif records:
                    records[-1]["desc"] += line.strip() + " "

    return records


def extract_amounts(extracted_text, start_keyword="Amount"):
    lines = [line for line in extracted_text.split("\n") if line.strip()]
    amounts_lists = []
    current_list = []
    capturing = False

    for line in lines:
        if start_keyword in line:
            if capturing:
                amounts_lists.append(current_list)
                current_list = []
            capturing = True
            continue

        if capturing:
            current_list.append(line)

    if current_list:
        amounts_lists.append(current_list)

    return amounts_lists


def parse_date(d):
    return datetime.strptime(d["date"], "%m/%d/%y")


def process_pdf_files(directory):
    aggregated_deposits_records = []
    aggregated_withdrawals_records = []

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            extracted_text = extract_text_from_page(pdf_path, 3)

            deposits_records = extract_table_data(
                extracted_text, "Deposits and other credits"
            )
            withdrawals_records = extract_table_data(
                extracted_text, "Withdrawals and other debits"
            )

            deposits_amounts, withdrawals_amounts = extract_amounts(extracted_text)

            for i, record in enumerate(deposits_records):
                if i < len(deposits_amounts):
                    record["amount"] = deposits_amounts[i]
                else:
                    break

            for i, record in enumerate(withdrawals_records):
                if i < len(withdrawals_amounts):
                    record["amount"] = withdrawals_amounts[i]
                else:
                    break

            aggregated_deposits_records.extend(deposits_records)
            aggregated_withdrawals_records.extend(withdrawals_records)
    merged_records = aggregated_deposits_records + aggregated_withdrawals_records
    return sorted(merged_records, key=parse_date)


def write_to_csv(records, filename):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Description", "Amount"])
        for record in records:
            writer.writerow([record["date"], record["desc"], record["amount"]])


if __name__ == "__main__":
    print(
        """
     | |/ /           / ____|                        | |           
     | ' / __ _ _   _| |     ___  _ ____   _____ _ __| |_ ___ _ __ 
     |  < / _` | | | | |    / _  | '_ \ \ / / _ \ '__| __/ _ \ '__|
     | . \ (_| | |_| | |___| (_) | | | \ V /  __/ |  | ||  __/ |   
     |_|\_\__,_|\__, |\_____\___/|_| |_|\_/ \___|_|   \__\___|_|   
                 __/ |                                             
                |___/                                     
          """
    )
    print("@Author: Luis Felipe Hernandez")
    print("Processing bank statements...")

    if getattr(sys, "frozen", False):
        script_directory = os.path.dirname(sys.executable)
    else:
        script_directory = os.path.dirname(os.path.realpath(__file__))

    os.chdir(script_directory)

    directory = "."
    aggregated_records = process_pdf_files(directory)

    write_to_csv(aggregated_records, "aggregated_records.csv")
    print("Process complete.\nCSV file generated: aggregated_records.csv")
