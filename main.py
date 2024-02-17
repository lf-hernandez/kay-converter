import os
import re
import csv
import sys
from datetime import datetime
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams


def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        return extract_text(file, laparams=LAParams())


def is_header_line(line):
    header_keywords = ["Date", "Description", "Amount", "Transaction description"]
    return any(keyword in line for keyword in header_keywords)


def extract_table_data(extracted_text, table_title):
    if table_title not in extracted_text:
        return []
    date_pattern = re.compile(r"\d{2}/\d{2}/\d{2}")
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
    valid_amount_pattern = re.compile(r"-?\d+\.\d{2}")  # Pattern for valid amounts
    lines = [line for line in extracted_text.split("\n") if line.strip()]
    amounts_lists = []
    current_list = []
    capturing = False

    for line in lines:
        if start_keyword in line:
            if capturing and current_list:
                # Append the current list to amounts_lists before starting a new one
                amounts_lists.append(current_list)
                current_list = []
            capturing = True
            continue

        if capturing:
            if valid_amount_pattern.match(line.strip()):
                current_list.append(line)
            else:
                # Stop capturing and append the current list if it has elements
                if current_list:
                    amounts_lists.append(current_list)
                    current_list = []
                capturing = False

    # Append the last list if it hasn't been appended yet
    if current_list:
        amounts_lists.append(current_list)

    return amounts_lists


def parse_date(d):
    return datetime.strptime(d["date"], "%m/%d/%y")


def process_pdf_files(directory):
    aggregated_deposits_records = []
    aggregated_withdrawals_records = []
    fees = []

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            extracted_text = extract_text_from_pdf(pdf_path)
            deposits_records = extract_table_data(
                extracted_text, "Deposits and other credits"
            )
            withdrawals_records = extract_table_data(
                extracted_text, "Withdrawals and other debits"
            )
            withdrawals_records_cont = extract_table_data(
                extracted_text, "Withdrawals and other debits - continued"
            )
            deposits_records_cont = extract_table_data(
                extracted_text, "Deposits and other credits - continued"
            )

            withdrawals_records += withdrawals_records_cont
            deposits_records += deposits_records_cont

            fee_records = extract_table_data(extracted_text, "Transaction description")
            amounts = extract_amounts(extracted_text)
            if len(amounts) == 3:
                deposits_amounts, withdrawals_amounts, fee_amounts = amounts
            else:
                print("Error parsing pdf")
                sys.exit()

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

            for i, record in enumerate(fee_records):
                if i < len(fee_amounts):
                    record["amount"] = fee_amounts[i]
                else:
                    break

            aggregated_deposits_records.extend(deposits_records)
            aggregated_withdrawals_records.extend(withdrawals_records)
            fees.extend(fee_records)

    merged_records = (
        aggregated_deposits_records + aggregated_withdrawals_records + fee_records
    )
    return sorted(merged_records, key=parse_date)


def write_to_csv(records, filename):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Description", "Amount"])

        for record in records:
            writer.writerow([record["date"], record["desc"], record["amount"]])


if __name__ == "__main__":
    print(
        r"""
      _  _              ____                          _
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
