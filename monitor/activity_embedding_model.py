import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.decomposition import PCA
import joblib
import os

def build_embeddings():
    """Build 4D embeddings for activity sessions using category, intent, duration."""
    try:
        csv_path = "data/usage_sessions.csv"
        if not os.path.exists(csv_path):
            print(f"{csv_path} not found")
            return
        
        df = pd.read_csv(csv_path)
        
        if df.empty:
            print("No data in usage_sessions.csv")
            return
        
        # Feature engineering
        df = df.copy()
        df['duration_norm'] = df['duration_sec'] / df['duration_sec'].max()
        
        # Encode categoricals
        cat_encoder = LabelEncoder()
        intent_encoder = LabelEncoder()
        
        df['category_id'] = pd.Series(cat_encoder.fit_transform(df['category'].fillna('Unknown').astype(str)))
        df['intent_id'] = pd.Series(intent_encoder.fit_transform(df['activity_intent'].fillna('Unknown').astype(str)))
        
        # Features: [category_id, intent_id, duration_norm]
        feature_cols = ['category_id', 'intent_id', 'duration_norm']
        X = df[feature_cols].values
        
        # Pipeline
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        pca = PCA(n_components=4)
        embeddings = pca.fit_transform(X_scaled)
        
        # Assign embeddings (use .assign to avoid type issues)
        embedding_df = pd.DataFrame({
            'e1': embeddings[:, 0],
            'e2': embeddings[:, 1],
            'e3': embeddings[:, 2],
            'e4': embeddings[:, 3]
        })
        
        df = pd.concat([df, embedding_df], axis=1)
        
        # Save embeddings
        output_path = "data/activity_embeddings.csv"
        df.to_csv(output_path, index=False)
        
        # Ensure models dir
        os.makedirs('models', exist_ok=True)
        
        # Save models
        model_data = {
            'pca': pca,
            'scaler': scaler,
            'cat_encoder': cat_encoder,
            'intent_encoder': intent_encoder,
            'feature_cols': feature_cols
        }
        joblib.dump(model_data, 'models/activity_embedding_models.pkl')
        
        print(f"✅ Embeddings saved to {output_path}")
        print(f"Explained variance ratio: {pca.explained_variance_ratio_}")
        print(f"Total variance explained: {pca.explained_variance_ratio_.sum():.3f}")
        
    except Exception as e:
        print(f"❌ Error building embeddings: {str(e)}")
        raise

if __name__ == "__main__":
    build_embeddings()
