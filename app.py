from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, messaging
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import whisper

# Initialize Flask app
app = Flask(__name__)

# Load Pretrained LLaMA Model from Hugging Face
MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"  # Replace with preferred model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"  # Auto-detect GPU/CPU
)

# Define Diagnosis Prediction Function
def predict_diagnosis(symptoms: str):
    prompt = f"Patient symptoms: {symptoms}\nPossible medical diagnosis:"
    inputs = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(inputs, max_new_tokens=100)
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Load Whisper for Speech Processing
whisper_model = whisper.load_model("base")

def speech_to_text(audio_path: str):
    result = whisper_model.transcribe(audio_path)
    return result["text"]

# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/diagnose", methods=["POST"])
def diagnose_patient():
    data = request.get_json()
    symptoms = data.get("symptoms", "")

    if not symptoms:
        return jsonify({"error": "Symptoms are required"}), 400

    diagnosis = predict_diagnosis(symptoms)

    # Find relevant hospitals
    hospitals_ref = db.collection("hospitals").where("services", "array_contains", diagnosis)
    hospitals = hospitals_ref.get()
    hospital_list = [{"name": h.to_dict()["name"], "location": h.to_dict()["location"], "contact": h.to_dict()["contact"]} for h in hospitals]

    # Send notification to hospitals
    for hospital in hospital_list:
        message = messaging.Message(
            notification=messaging.Notification(
                title="New Patient Referral",
                body=f"A patient with {diagnosis} is looking for treatment. Contact: {hospital['contact']}"
            ),
            topic=hospital["name"]
        )
        messaging.send(message)

    return jsonify({"diagnosis": diagnosis, "hospitals": hospital_list})

@app.route("/register_hospital", methods=["POST"])
def register_hospital():
    data = request.get_json()
    
    if not all(k in data for k in ["name", "location", "contact", "services"]):
        return jsonify({"error": "All fields (name, location, contact, services) are required"}), 400

    db.collection("hospitals").add(data)
    return jsonify({"message": "Hospital registered successfully"}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
