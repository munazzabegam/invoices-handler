from flask import Flask, request, render_template
from extractor import extract_invoice_details
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file uploaded"
        file = request.files["file"]
        if file.filename == "":
            return "No file selected"

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        details = extract_invoice_details(file_path)
        return render_template("result.html", details=details)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
