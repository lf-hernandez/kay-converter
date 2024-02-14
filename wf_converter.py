from datetime import datetime
import os
import tabula
import pandas as pd


def process_pdf(file_path):
    df_list = tabula.read_pdf(
        input_path=file_path,
        pages="all",
        multiple_tables=True,
        pandas_options={"header": None},
    )

    df = df_list[0]

    columns = [
        "Date",
        "Description",
        "Deposits/Credits",
        "Withdrawals/Debits",
        "Ending daily balance",
    ]

    if len(df.columns) == 6:
        columns.insert(1, "Check Number")

    df.columns = columns

    df["Deposits/Credits"] = pd.to_numeric(
        df["Deposits/Credits"], errors="coerce"
    ).fillna(0)
    df["Withdrawals/Debits"] = pd.to_numeric(
        df["Withdrawals/Debits"], errors="coerce"
    ).fillna(0)
    df["Amount"] = df["Deposits/Credits"] - df["Withdrawals/Debits"]
    df = df[["Date", "Description", "Amount"]]

    # Processing for word-wrapped lines
    indices_to_drop = []
    for i in range(len(df) - 1, 0, -1):
        if pd.isna(df.at[i, "Date"]) or df.at[i, "Date"] == "":
            df.at[i - 1, "Description"] += " " + df.at[i, "Description"]
            indices_to_drop.append(i)
    df = df.drop(indices_to_drop).reset_index(drop=True)

    return df


pdf_files = [f for f in os.listdir(".") if f.endswith(".pdf")]

all_data = pd.DataFrame()
for file in pdf_files:
    df = process_pdf(file)
    all_data = pd.concat([all_data, df], ignore_index=True)


def standardize_date(date_str):
    if pd.isna(date_str) or date_str == "":
        return None
    # Assuming the previous year for the date - Tax returns*
    previous_year = datetime.now().year - 1
    full_date_str = f"{date_str}/{previous_year}"
    return pd.to_datetime(full_date_str, format="%m/%d/%Y", errors="coerce")


all_data["Date"] = all_data["Date"].apply(standardize_date)
all_data.sort_values(by="Date", inplace=True)

csv_file_path = "aggregated_data.csv"
all_data.to_csv(csv_file_path, index=False)

print(f"Data aggregated and written to {csv_file_path}")
