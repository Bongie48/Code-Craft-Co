"""
AI Model for detecting Gender-Based Violence (GBV) or rape incidents
from audio recordings in the DangerAlert system.
"""

import numpy as np
import joblib
import librosa
import os

# Path to trained model (once available)
MODEL_PATH = os.path.join("models", "gbv_audio_classifier.pkl")

class GBVAudioModel:
    def __init__(self):
        # If a trained model exists, load it — else use a mock classifier
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.is_trained = True
        else:
            print("⚠️ Warning: Using mock AI model (no trained model found).")
            self.is_trained = False

    def extract_features(self, audio_path_or_array, sr=22050):
        """
        Extracts MFCCs (Mel-Frequency Cepstral Coefficients)
        — standard audio features for voice/emotion recognition.
        """
        try:
            if isinstance(audio_path_or_array, str):  # path
                y, sr = librosa.load(audio_path_or_array, sr=sr)
            else:
                y = np.array(audio_path_or_array)

            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features = np.mean(mfccs.T, axis=0)
            return features.reshape(1, -1)
        except Exception as e:
            print("❌ Error extracting features:", e)
            return np.zeros((1, 13))

    def predict(self, audio_data):
        """
        Predicts whether the audio indicates a GBV/rape incident.
        Returns either:
        - "Gender Based Violence"
        - "Normal Conversation"
        """
        # Simulate prediction for testing (real model not trained yet)
        if not self.is_trained:
            import random
            return random.choice(["Gender Based Violence", "Normal Conversation"])

        # Otherwise, predict using the trained classifier
        features = self.extract_features(audio_data)
        prediction = self.model.predict(features)[0]

        return "Gender Based Violence" if prediction == 1 else "Normal Conversation"

# Create an instance for easy import in other files
ai_model = GBVAudioModel()
