from flask import Flask, render_template, request, redirect, flash
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Directory where files will be uploaded
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Make sure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/")
def index():
    return render_template("index.html")


# Handle the GET and POST request for the dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        # Check if the POST request has a file
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]

        # If the user does not select a file, browser may also
        # submit an empty part without filename
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        # Save the file if it has a filename
        if file:
            # Save the file to the upload folder
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)

            # Flash a success message
            flash("File successfully uploaded")

            # Proceed to render the dashboard with card data
            card_data = [
                {
                    "title": "Overview",
                    "content": "This section provides an overview of the tender.",
                },
                {
                    "title": "Cost Information",
                    "content": "Here are the details about the cost structure and payment terms.",
                },
                {
                    "title": "Key Objectives",
                    "content": "These are the primary goals of the tender.",
                },
                {
                    "title": "General Requirements",
                    "content": "These are the basic requirements for the system.",
                },
            ]

            return render_template("dashboard.html", card_data=card_data)

    # If it's a GET request, simply render the dashboard
    card_data = [
        {
            "title": "Overview",
            "content": "This section provides an overview of the tender.",
        },
        {
            "title": "Cost Information",
            "content": "Here are the details about the cost structure and payment terms.",
        },
        {
            "title": "Key Objectives",
            "content": "These are the primary goals of the tender.",
        },
        {
            "title": "General Requirements",
            "content": "These are the basic requirements for the system.",
        },
    ]
    return render_template("dashboard.html", card_data=card_data)


if __name__ == "__main__":
    app.run(debug=True)
