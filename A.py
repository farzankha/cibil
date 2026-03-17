from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import os
from sklearn.base import BaseEstimator, TransformerMixin
from typing import List

# ---------------------------------------------------------
# 1. Custom Preprocessor (MUST be here for joblib to load)
# ---------------------------------------------------------
class CreditDataCleaner(BaseEstimator, TransformerMixin):
    def __init__(self, features: List[str]):
        self.features = features
        self.medians_ = {}

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_subset = X[self.features].copy()
        for col in self.features:
            if col not in X_subset.columns:
                continue
            median_val = self.medians_.get(col, 0)
            X_subset[col] = X_subset[col].replace(-99999, np.nan)
            X_subset[col] = X_subset[col].fillna(median_val)
        return X_subset

# ---------------------------------------------------------
# 2. Flask Setup & Model Loading
# ---------------------------------------------------------
app = Flask(__name__, static_folder='.')
CORS(app)

model = None
preprocessor = None
feature_list = None

def load_model():
    global model, preprocessor, feature_list
    # Make sure this matches the file output by your training script!
    model_path = 'cibil_score_model_v2.pkl' 
    
    if os.path.exists(model_path):
        try:
            artifacts = joblib.load(model_path)
            model = artifacts['model']
            preprocessor = artifacts['preprocessor']
            feature_list = artifacts['features']
            print("Model and Preprocessor loaded successfully!")
           
        except Exception as e:
            print(f"ERROR Loading Model: {e}")
    else:
        print(f"ERROR: {model_path} not found. Please run training script first.")

load_model()

def get_risk_category(score):
    if score < 580: return "High Risk"
    elif score < 670: return "Medium Risk"
    elif score < 740: return "Low Risk"
    else: return "Very Low Risk"

# ---------------------------------------------------------
# 3. Routes
# ---------------------------------------------------------
@app.route("/")
def home():
    return send_from_directory('.', 'index.html')

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or preprocessor is None:
        return jsonify({'error': 'Model not loaded'}), 500

    try:
        data = request.get_json()
        
        # Handle empty fields from frontend
        input_data = {}
        for feature in feature_list:
            val = data.get(feature)
            if val is None or val == "":
                input_data[feature] = np.nan
            else:
                input_data[feature] = float(val)

        # Convert to DataFrame and apply preprocessor
        input_df = pd.DataFrame([input_data])
        processed_input = preprocessor.transform(input_df)

        # Predict and clamp between 300 and 900
        prediction = model.predict(processed_input)[0]
        final_score = float(max(300, min(900, prediction)))
        
        # Match the exact keys expected by script.js!
        return jsonify({
            'Predicted_Credit_Score': round(final_score, 0),
            'Risk_Category': get_risk_category(final_score)
        })

    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)