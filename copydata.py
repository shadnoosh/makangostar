import pandas as pd

# Define file paths
excel_file_path = 'آپارتمان.xlsx'
csv_file_path = 'houses.csv'
output_csv_path = 'houses.csv'  # Save to a new file first

print(f"Reading Excel file: {excel_file_path}")
try:
    excel_df = pd.read_excel(excel_file_path)
    print(f"Successfully read {len(excel_df)} rows from Excel file.")
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit()

print(f"Reading CSV file: {csv_file_path}")
try:
    # Use utf-8 encoding as determined earlier
    csv_df = pd.read_csv(csv_file_path, encoding='utf-8')
    print(f"Successfully read {len(csv_df)} rows from CSV file.")
except Exception as e:
    print(f"Error reading CSV file: {e}")
    exit()

# Ensure all columns from Excel exist in the CSV DataFrame for proper concatenation
# Pandas concat handles this automatically by aligning on column names.
# Columns present only in excel_df will be added to csv_df with NaN for existing rows.
# Columns present only in csv_df will have NaN for rows coming from excel_df.

print("Concatenating dataframes...")
# Concatenate the two dataframes. Rows from excel_df will be appended to csv_df.
# Columns are aligned automatically. ignore_index=True creates a new continuous index.
combined_df = pd.concat([csv_df, excel_df], ignore_index=True)

print(f"Combined dataframe has {len(combined_df)} rows.")

# Save the combined dataframe to a new CSV file
print(f"Saving updated data to: {output_csv_path}")
try:
    # Use 'utf-8-sig' encoding for better compatibility with Excel if needed
    combined_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print("Successfully saved updated CSV file.")
except Exception as e:
    print(f"Error saving updated CSV file: {e}")

print("\nScript finished.")

