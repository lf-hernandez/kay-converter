import os
import pandas as pd
from datetime import datetime
import tabula


def read_pdf_to_df(file_path):
    try:
        df_list = tabula.read_pdf(
            input_path=file_path,
            pages="all",
            multiple_tables=True,
            pandas_options={"header": None},
        )
        return df_list
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []


def preprocess_df(df_list):
    if not df_list or len(df_list) <= 1:
        return pd.DataFrame()

    df = pd.concat(df_list[:-1])
    df.dropna(how="all", inplace=True)

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

    # Convert to numeric and handle errors
    for col in ["Deposits/Credits", "Withdrawals/Debits"]:
        df[col] = df[col].replace({",": ""}, regex=True)
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Amount"] = df["Deposits/Credits"] - df["Withdrawals/Debits"]
    df = df[["Date", "Description", "Amount"]]

    # Handle word-wrapped lines
    indices_to_drop = []
    for i, row in df[::-1].iterrows():
        if pd.isna(row["Date"]) or row["Date"] == "":
            if i > 0 and i - 1 in df.index:
                df.at[i - 1, "Description"] += " " + row["Description"]
            indices_to_drop.append(i)

    df.drop(indices_to_drop, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def standardize_date(date_str):
    try:
        # Assuming the previous year for the date - Tax returns
        previous_year = datetime.now().year - 1
        full_date_str = f"{date_str}/{previous_year}"
        return pd.to_datetime(full_date_str, format="%m/%d/%Y", errors="coerce")
    except ValueError:
        return pd.NaT


def aggregate_pdf_data(pdf_files):
    all_data = pd.DataFrame()
    for file in pdf_files:
        df_list = read_pdf_to_df(file)
        df = preprocess_df(df_list)
        all_data = pd.concat([all_data, df], ignore_index=True)

    all_data["Date"] = all_data["Date"].apply(standardize_date)
    all_data.sort_values(by="Date", inplace=True)
    return all_data


def main():
    pdf_files = [f for f in os.listdir(".") if f.endswith(".pdf")]
    all_data = aggregate_pdf_data(pdf_files)

    csv_file_path = "aggregated_data.csv"
    all_data.to_csv(csv_file_path, index=False)
    print(f"Data aggregated and written to {csv_file_path}")


if __name__ == "__main__":
    main()
