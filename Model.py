
import pandas as pd
import numpy as np
import os
import joblib
import logging
import warnings
from typing import List, Dict, Any

from xgboost import XGBRegressor
from sklearn.model_selection import KFold, cross_validate
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.base import BaseEstimator, TransformerMixin

# ---------------------------------------------------------
# 1. Configuration & Logging
# ---------------------------------------------------------

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

CONFIG = {
    'file_path': 'External_Cibil_Dataset.xlsx',
    'model_path': 'cibil_score_model_v2.pkl',
    'importance_path': 'feature_importance_v2.csv',
    'target_col': 'Credit_Score',
    
    # Model Hyperparameters
    'model_params': {
        'n_estimators': 300,
        'learning_rate': 0.05,
        'max_depth': 6,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'n_jobs': -1  # Use all available cores
    },
    
    # CV Settings
    'cv_folds': 5
}

SELECTED_FEATURES = [
    # Top 20 features based on importance ranking
    # Enquiry Behaviour (Top 2)
    'PL_enq_L12m',              # Importance: 0.189
    'time_since_recent_enq',    # Importance: 0.169
    # Credit Strength Indicators
    'pct_of_active_TLs_ever',   # Importance: 0.079
    # Loan Flags
    'HL_Flag',                  # Importance: 0.074
    'PL_Flag',                  # Importance: 0.051
    'CC_Flag',                  # Importance: 0.025
    # Delinquency Behaviour
    'time_since_recent_deliquency',  # Importance: 0.062
    'recent_level_of_deliq',    # Importance: 0.044
    'num_times_delinquent',     # Importance: 0.039
    'max_delinquency_level',    # Importance: 0.018
    'num_deliq_12mts',          # Importance: 0.016
    'num_times_60p_dpd',        # Importance: 0.013
    # Income & Stability
    'AGE',                      # Importance: 0.044
    # Enquiry Behaviour
    'tot_enq',                  # Importance: 0.038
    'CC_enq_L12m',              # Importance: 0.013
    # Utilization Behaviour
    'max_unsec_exposure_inPct', # Importance: 0.036
    'pct_currentBal_all_TL',    # Importance: 0.031
    'PL_utilization',           # Importance: 0.015
    'CC_utilization',           # Importance: 0.014
    # Income & Stability
    'Time_With_Curr_Empr'       # Importance: 0.011
]

# ---------------------------------------------------------
# 2. Custom Preprocessing Transformer
# ---------------------------------------------------------

class CreditDataCleaner(BaseEstimator, TransformerMixin):
    """
    Handles imputation of missing values (-99999) and NaN, 
    and applies log transformations.
    Ensures no data leakage during Cross-Validation.
    """
    def __init__(self, features: List[str]):
        self.features = features
        self.medians_ = {}

    def fit(self, X: pd.DataFrame, y=None):
        print("Fitting Preprocessor...")
        X_subset = X[self.features]
        
        for col in self.features:
            if col not in X_subset.columns:
                continue
            
            # Calculate median ignoring the special missing value code
            valid_data = X_subset[X_subset[col] != -99999][col]
            
            if len(valid_data) > 0:
                self.medians_[col] = valid_data.median()
            else:
                # Fallback if column is entirely empty
                self.medians_[col] = 0 
                
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_subset = X[self.features].copy()
        
        for col in self.features:
            if col not in X_subset.columns:
                continue
                
            median_val = self.medians_.get(col, 0)
            
            # Replace -99999 with NaN, then fill NaN with median
            X_subset[col] = X_subset[col].replace(-99999, np.nan)
            X_subset[col] = X_subset[col].fillna(median_val)

        # Note: Log transform removed as NETMONTHLYINCOME is no longer in top 20 features

        return X_subset

# ---------------------------------------------------------
# 3. Main Pipeline Functions
# ---------------------------------------------------------

def load_data(file_path: str) -> pd.DataFrame:
    """Loads data and checks for basic integrity."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        raise FileNotFoundError(f"Dataset file missing: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
        print(f"Data loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        raise

def train_model(X: pd.DataFrame, y: pd.Series) -> XGBRegressor:
    """
    Trains the model with Cross-Validation and returns the fitted final model.
    """
    # 1. Define Preprocessor
    preprocessor = CreditDataCleaner(features=SELECTED_FEATURES)
    
    # 2. Prepare X (Feature Selection)
    # Check if all features exist
    missing_feats = [f for f in SELECTED_FEATURES if f not in X.columns]
    if missing_feats:
        print(f"Missing features in dataset: {missing_feats}")
    
    # Filter X to only features that actually exist
    valid_features = [f for f in SELECTED_FEATURES if f in X.columns]
    X_filtered = X[valid_features]

    # 3. Initialize Model
    model = XGBRegressor(**CONFIG['model_params'])

    # 4. Cross Validation
    # Note: We cannot use a direct pipeline here if we want to easily extract 
    # feature importances later without custom wrappers. 
    # Instead, we manually perform the CV loop to apply the preprocessor correctly 
    # on train/val splits to prevent leakage.
    
    print(f"Starting {CONFIG['cv_folds']}-Fold Cross Validation...")
    
    kf = KFold(n_splits=CONFIG['cv_folds'], shuffle=True, random_state=42)
    
    r2_scores = []
    mae_scores = []
    rmse_scores = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X_filtered)):
        X_train, X_val = X_filtered.iloc[train_idx], X_filtered.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        # Fit preprocessor on Training Data Only
        preprocessor.fit(X_train)
        
        # Transform Train and Val
        X_train_proc = preprocessor.transform(X_train)
        X_val_proc = preprocessor.transform(X_val)

        # Train Model
        model.fit(X_train_proc, y_train)
        
        # Predict
        preds = model.predict(X_val_proc)

        # Metrics
        r2 = r2_score(y_val, preds)
        mae = mean_absolute_error(y_val, preds)
        rmse = np.sqrt(mean_squared_error(y_val, preds))

        r2_scores.append(r2)
        mae_scores.append(mae)
        rmse_scores.append(rmse)
        
        print(f"Fold {fold+1}: R2={r2:.4f} | MAE={mae:.2f} | RMSE={rmse:.2f}")

    # Log Average Scores
    print("-" * 30)
    print(f"Average R2 Score: {np.mean(r2_scores):.4f} ({np.std(r2_scores):.4f})")
    print(f"Average MAE:      {np.mean(mae_scores):.2f} pts")
    print(f"Average RMSE:     {np.mean(rmse_scores):.2f} pts")
    print("-" * 30)

    # 5. Train Final Model on Full Dataset
    print("Training Final Model on 100% of data...")
    preprocessor.fit(X_filtered) # Refit preprocessor on all data
    X_full_proc = preprocessor.transform(X_filtered)
    
    final_model = XGBRegressor(**CONFIG['model_params'])
    final_model.fit(X_full_proc, y)
    
    return final_model, preprocessor, valid_features

def save_artifacts(model: XGBRegressor, preprocessor, features: List[str]):
    """Saves model, preprocessor, and feature importance."""
    # Save Model and Preprocessor together
    artifacts = {
        'model': model,
        'preprocessor': preprocessor,
        'features': features
    }
    
    joblib.dump(artifacts, CONFIG['model_path'])
    print(f"Model artifacts saved to {CONFIG['model_path']}")

    """Feature Importance
    importance = model.feature_importances_
    feat_imp_df = pd.DataFrame({
        'Feature': features,
        'Importance': importance
    }).sort_values(by='Importance', ascending=False)

    feat_imp_df.to_csv(CONFIG['importance_path'], index=False)
    print("Feature importance saved.")
    
    print("\n--- Top 10 Features ---")
    print(feat_imp_df.head(10))"""

# ---------------------------------------------------------
# 4. Main Execution
# ---------------------------------------------------------

def main():
    try:
        # Load
        df = load_data(CONFIG['file_path'])
        
        # Define Target
        target = CONFIG['target_col']
        if target not in df.columns:
            print(f"Target column '{target}' not found in dataframe.")
            return

        X = df.drop(columns=[target])
        y = df[target]

        # Train
        model, preprocessor, valid_feats = train_model(X, y)

        # Save
        save_artifacts(model, preprocessor, valid_feats)
        
        print("Process completed successfully.")
       

    except Exception as e:
        print(f"Critical error in execution pipeline: {e}")
        raise

if __name__ == "__main__":
    main()