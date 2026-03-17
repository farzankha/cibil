# CIBIL Score Predictor Web Application

## Features
✨ **5 Slides with 4 Features Each** - Organized input collection
🎨 **Bright Matte Background** - Modern gradient design
📊 **Real-time Credit Score Prediction** - Instant results
🎯 **Risk Category Display** - Clear risk assessment
📱 **Responsive Design** - Works on all devices

## Setup Instructions

### 1. Start the Flask Backend
```bash
python app.py
```
The server will start on `http://localhost:5000`

### 2. Open the Frontend
Simply open `index.html` in your web browser, or use a local server:

```bash
# Using Python's built-in server
python -m http.server 8000
```
Then visit `http://localhost:8000`

## File Structure
```
├── index.html      # Main HTML structure with 5 slides
├── style.css       # Bright matte styling
├── script.js       # Form logic and API calls
├── app.py          # Flask backend API
└── Demo.py         # Model training script
```

## Slide Breakdown

### Slide 1: Enquiry Behaviour (4 features)
- Personal Loan Enquiries (Last 12 months)
- Time Since Recent Enquiry
- Total Enquiries
- Credit Card Enquiries (Last 12 months)

### Slide 2: Loan Status & Credit Strength (4 features)
- Home Loan Status
- Personal Loan Status
- Credit Card Status
- Active Trade Lines Percentage

### Slide 3: Delinquency History (4 features)
- Time Since Recent Delinquency
- Recent Delinquency Level
- Number of Times Delinquent
- Maximum Delinquency Level

### Slide 4: Additional Delinquency & Personal Info (4 features)
- Delinquencies in Last 12 Months
- Times 60+ Days Past Due
- Age
- Time With Current Employer

### Slide 5: Credit Utilization (4 features)
- Max Unsecured Exposure
- Current Balance of All Trade Lines
- Personal Loan Utilization
- Credit Card Utilization

## Risk Categories
- **High Risk**: Score < 580 (Red)
- **Medium Risk**: Score 580-670 (Orange)
- **Low Risk**: Score 670-740 (Teal)
- **Very Low Risk**: Score > 740 (Green)

## Technologies Used
- HTML5, CSS3, JavaScript (Vanilla)
- Flask + Flask-CORS (Backend)
- XGBoost (Machine Learning Model)
