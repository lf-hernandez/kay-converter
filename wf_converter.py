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

    # Concatenate all but the last DataFrame
    df = pd.concat(df_list[:-1])

    # Drop rows where all elements are NaN
    df.dropna(how="all", inplace=True)

    # Define columns based on expected format
    columns = [
        "Date",
        "Description",
        "Deposits/Credits",
        "Withdrawals/Debits",
        "Ending daily balance",
    ]

    # Adjust columns based on actual data format
    if len(df.columns) == 6:
        columns.insert(1, "Check Number")

    df.columns = columns

    # Remove commas and convert to numeric
    df["Deposits/Credits"] = df["Deposits/Credits"].replace({",": ""}, regex=True)
    df["Withdrawals/Debits"] = df["Withdrawals/Debits"].replace({",": ""}, regex=True)
    df["Deposits/Credits"] = pd.to_numeric(
        df["Deposits/Credits"], errors="coerce"
    ).fillna(0)
    df["Withdrawals/Debits"] = pd.to_numeric(
        df["Withdrawals/Debits"], errors="coerce"
    ).fillna(0)

    # Calculate new Amount column
    df["Amount"] = df["Deposits/Credits"] - df["Withdrawals/Debits"]

    # Select only the needed columns
    df = df[["Date", "Description", "Amount"]]

    # Processing for word-wrapped lines
    indices_to_drop = []
    for i in range(len(df) - 1, -1, -1):
        if pd.isna(df.at[i, "Date"]) or df.at[i, "Date"] == "":
            if i > 0:  # Check to ensure index i-1 exists
                df.at[i - 1, "Description"] += " " + df.at[i, "Description"]
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
