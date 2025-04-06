import os
from flask import Flask, request, redirect, url_for, render_template, jsonify
from werkzeug.utils import secure_filename
import json

from RAG_21 import get_RAG
from Conv_RAG import ChatManager, ChatWithoutTopic

import yaml

from complexity import get_assesment

from flask_sqlalchemy import SQLAlchemy


import re

# Initialize the Flask app
app = Flask(__name__)

# Configure the app and set the upload folder
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tenders.db"  # Correct database URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
    False  # Disable SQLAlchemy event system for performance
)

# Initialize SQLAlchemy
db = SQLAlchemy(app)


# Define the Tender model
class Tender(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    json_data = db.Column(db.Text, nullable=False)  # Store JSON data as text
    metrics = db.Column(db.Text, nullable=True)  # Any metrics stored as text


# Initialize the database and create tables if they don't exist
def init_db():
    with app.app_context():
        db.create_all()


# Call init_db() to create tables
init_db()


@app.route("/", methods=["GET", "POST"])
def dashboard():
    tenders = Tender.query.all()
    return render_template("dashboard.html", tenders=tenders)  # index.html


@app.route("/create_tender", methods=["POST"])
def create_tender():
    name = request.form["name"]
    file = request.files["file"]

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        # Ensure the uploads directory exists
        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

        file.save(file_path)

        # Send file to RAG and get response (simulate here)
        rag_output = send_to_rag_application(file_path)

        json_string = json.dumps(rag_output)
        json_data_string = re.sub(r"\bnull\b", '"Not Provided"', json_string)

        rag_graph_output = get_assesment(file_path)
        # parsed_graph_yaml = yaml.safe_load(rag_graph_output)

        # Update the tender with the RAG output (json data)
        json_graph_string = json.dumps(rag_graph_output)
        json_graph_string = re.sub(r"\bnull\b", '"Not Provided"', json_graph_string)

        # Create new Tender object with the parsed data
        new_tender = Tender(
            name=name, json_data=json_data_string, metrics=json_graph_string
        )

        # Save to database
        db.session.add(new_tender)
        db.session.commit()

    return redirect(url_for("dashboard"))


def send_to_rag_application(filename):
    # Get the YAML content (from RAG)
    yaml_string = get_RAG(filename)
    data = yaml.safe_load(yaml_string)

    if isinstance(data, list):
        data = data[0]

    return data


"""def yaml_to_json_html(yaml_input):
    parsed_yaml = yaml.safe_load(yaml_input)
    json_string = json.dumps(json_content)

    json_string = re.sub(r'\bnull\b', '"Not Provided"', json_string)

    return json_string"""


# Reusable store function
def store_tender_data(tender_id, json_data):
    tender = Tender.query.get_or_404(tender_id)
    tender.json_data = json.dumps(json_data, ensure_ascii=False)
    db.session.commit()


@app.route("/get_tender_data/<int:tender_id>", methods=["GET"])
def get_tender_data(tender_id):
    tender = Tender.query.get_or_404(tender_id)
    tender_data = json.loads(tender.json_data)

    card_data = []
    for i, (title, content) in enumerate(tender_data.items()):
        if i >= 4:  # Only display the first 4 key-value pairs
            break
        card_data.append({"title": title, "content": content})

    print(card_data)

    return jsonify({"card_data": card_data})


@app.route("/process_addons", methods=["POST"])
def process_addons():
    data = request.json
    print(data)

    tender_id = data.get("tender_id")
    selected_addons = data.get("addons", [])

    # Assuming you have a Tender model
    tender = Tender.query.get_or_404(tender_id)

    # Load the tender's JSON data (assuming it's stored as text in the database)
    tender_data = json.loads(tender.json_data)

    # Collect selected addons data
    card_data_addons = []
    for addon in selected_addons:
        if addon in tender_data:
            card_data_addons.append({"title": addon, "content": tender_data[addon]})
    print(card_data_addons)
    return jsonify({"card_data_addons": card_data_addons})


@app.route("/graph_data/<int:tender_id>")
def graph_data(tender_id):
    # Fetch the tender data based on tender_id
    tender = Tender.query.get_or_404(tender_id)

    # Assuming the `json_data` field contains the parsed JSON string as shown in your example
    tender_data = json.loads(tender.metrics)

    print(tender_data)
    # Ensure the data structure matches the frontend expectations
    formatted_data = {
        "Complexity": {
            "Rating": tender_data.get("Complexity", {}).get("Rating", "Not Provided"),
            "Verification_Sentence": tender_data.get("Complexity", {}).get(
                "Verification Sentence", "."
            ),
        },
        "Scalability": {
            "Rating": tender_data.get("Scalability", {}).get("Rating", "Not Provided"),
            "Verification_Sentence": tender_data.get("Scalability", {}).get(
                "Verification Sentence", "."
            ),
        },
        "Integration_Requirements": {
            "Rating": tender_data.get("Integration Requirements", {}).get(
                "Rating", "Not Provided"
            ),
            "Verification_Sentence": tender_data.get(
                "Integration Requirements", {}
            ).get("Verification Sentence", "."),
        },
        "Time_Feasibility": {
            "Rating": tender_data.get("Time Feasibility", {}).get(
                "Rating", "Not Provided"
            ),
            "Verification_Sentence": tender_data.get("Time Feasibility", {}).get(
                "Verification Sentence", "."
            ),
        },
        "Days_Left": tender_data.get(
            "Days Left to Submit the Proposal", "Not Available"
        ),
    }

    # Return the formatted data as JSON response
    return jsonify(formatted_data)


@app.route("/start_conversation", methods=["POST"])
def start_conversation():
    global current_chat_manager, current_conversation_type, current_topic

    vector_store_path = "store/vectorstore"
    embedding_model = "embed-multilingual-v2.0"
    yaml_path = "uploads/structured_tender_CPQ_Ausschreibung2.yaml"
    data = request.json
    topic = data.get("topic")

    if not topic:
        return jsonify({"error": "Topic is required to start a conversation."}), 400

    chat_manager = ChatManager(vector_store_path, embedding_model, yaml_path)
    message = chat_manager.start_conversation(topic)

    # Set global conversation state
    current_chat_manager = chat_manager
    current_conversation_type = "topic"
    current_topic = topic

    return jsonify({"message": message})


@app.route("/start_on_the_fly", methods=["POST"])
def start_conversation_on_the_fly():
    global current_chat_manager, current_conversation_type, current_topic

    vector_store_path = "store/vectorstore"
    embedding_model = "embed-multilingual-v2.0"
    chat_manager_general = ChatWithoutTopic(vector_store_path, embedding_model)
    message = chat_manager_general.start_conversation()
    print("message is ", message)

    # Set global conversation state
    current_chat_manager = chat_manager_general
    current_conversation_type = "general"
    current_topic = None

    return jsonify({"message": message})


@app.route("/get_response", methods=["POST"])
def get_response():
    global current_chat_manager, current_conversation_type, current_topic

    data = request.json
    user_message = data.get("message")

    if not current_chat_manager:
        return jsonify(
            {"error": "No active conversation. Please start a conversation first."}
        ), 400

    if current_conversation_type == "topic":
        if not current_topic:
            return jsonify(
                {"error": "Topic is not set for the current conversation."}
            ), 400
        response_data = current_chat_manager.send_message(current_topic, user_message)
    elif current_conversation_type == "general":
        response_data = current_chat_manager.send_message(user_message)
    else:
        return jsonify({"error": "Invalid conversation type."}), 400

    if "error" in response_data:
        return jsonify({"error": response_data["error"]}), 400
    else:
        return jsonify(
            {
                "response": response_data["ai_response"],
                "source": response_data[
                    "references"
                ],  # References returned as 'source'
            }
        )


@app.route("/end_conversation", methods=["POST"])
def end_conversation():
    global current_chat_manager, current_conversation_type, current_topic

    if not current_chat_manager:
        return jsonify({"message": "No active conversation to end."})

    if current_conversation_type == "topic":
        if not current_topic:
            return jsonify(
                {"error": "Topic is not set for the current conversation."}
            ), 400
        message = current_chat_manager.end_conversation(current_topic)
    elif current_conversation_type == "general":
        message = current_chat_manager.end_conversation()
    else:
        message = "Invalid conversation type."

    # Clear global conversation state
    current_chat_manager = None
    current_conversation_type = None
    current_topic = None

    return jsonify({"message": message})


if __name__ == "__main__":
    app.run(debug=True)
