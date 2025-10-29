from flask import Flask, request, render_template, redirect, url_for, send_file
from extractor import extract_invoice_details
import os
import pandas as pd

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🔹 Global Storage for Extracted Data
invoice_data_storage = []

# Define the path for the Excel file
EXCEL_PATH = os.path.join(OUTPUT_FOLDER, "extracted_data.xlsx")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No files uploaded"
        
        # Get list of all files selected by the user
        files = request.files.getlist("file")
        
        if not files or files[0].filename == "":
            return "No files selected"
        
        # List to store details of all files processed in this batch
        batch_details = []
        
        # Loop through and process each file
        for file in files:
            if file.filename:
                # 1. Save the file
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)

                # 2. Extract details
                details = extract_invoice_details(file_path)
                
                # 3. Store the extracted details (Only if no major error occurred)
                if "Extraction Error" not in details:
                    details_with_file = {"Filename": file.filename, **details}
                    invoice_data_storage.append(details_with_file)
                    batch_details.append(details_with_file)
                else:
                    # Store error details for feedback
                    batch_details.append({"Filename": file.filename, "Error": details.get("Extraction Error", "Unknown Error")})


        # Pass the details of the LAST file processed for display, 
        # and the total count of stored files.
        last_file_details = batch_details[-1] if batch_details else {"Error": "No valid files processed"}

        return render_template("result.html", 
                               details=last_file_details,
                               storage_count=len(invoice_data_storage),
                               batch_count=len(batch_details)) # Used for conditional display logic

    return render_template("index.html")


# 🔹 Route for Excel Download
@app.route("/download", methods=["GET"])
def download_excel():
    if not invoice_data_storage:
        return redirect(url_for('index'))

    try:
        # Convert the list of dicts to a pandas DataFrame
        df = pd.DataFrame(invoice_data_storage)

        # Save the DataFrame to the Excel file
        df.to_excel(EXCEL_PATH, index=False)

        # Serve the file for download
        return send_file(EXCEL_PATH, 
                         as_attachment=True,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         download_name="extracted_invoices.xlsx")

    except Exception as e:
        return f"An error occurred during Excel generation: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)