import pandas as pd

# Read the CSV file
csv_file = "houses.csv"
df = pd.read_csv(csv_file)

# Save to Excel file
excel_file = "آپارتمان.xlsx"
df.to_excel(excel_file, index=False)

print(f"Converted '{csv_file}' to '{excel_file}' successfully.")