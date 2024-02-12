import tabula
import pandas as pd

df_list = tabula.read_pdf(
    input_path="wells_fargo.pdf",
    pages="all",
    multiple_tables=True,
    pandas_options={"header": None},
)

df = df_list[0]

df.columns = [
    "Date",
    "Description",
    "Deposits/Credits",
    "Withdrawals/Debits",
    "Ending daily balance",
]

df["Deposits/Credits"] = pd.to_numeric(df["Deposits/Credits"], errors="coerce").fillna(
    0
)
df["Withdrawals/Debits"] = pd.to_numeric(
    df["Withdrawals/Debits"], errors="coerce"
).fillna(0)

df["Amount"] = df["Deposits/Credits"] - df["Withdrawals/Debits"]

df = df[["Date", "Description", "Amount"]]

# Create a copy of the DataFrame to avoid SettingWithCopyWarning
df_processed = df.copy()

# Processing for word-wrapped lines
for i in range(len(df_processed) - 1, 0, -1):
    # Check if the 'Date' field is empty
    if pd.isna(df_processed.at[i, "Date"]) or df_processed.at[i, "Date"] == "":
        # Concatenate the 'Description' with the previous row
        df_processed.at[i - 1, "Description"] += " " + df_processed.at[i, "Description"]
        # Drop the current row
        df_processed.drop(i, inplace=True)

df_processed.reset_index(drop=True, inplace=True)


csv_file_path = "filtered_data.csv"
df_processed.to_csv(csv_file_path, index=False)

print(f"Data written to {csv_file_path}")
