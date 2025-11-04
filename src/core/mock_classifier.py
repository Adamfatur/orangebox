"""
Mock Classifier untuk testing tanpa model TFLite.
Digunakan saat --test mode atau fallback ketika model tidak tersedia.
"""

import random
import time


class MockClassifier:
    """
    Mock classifier yang memberikan prediksi random untuk testing.
    Compatible dengan interface WasteClassifier.
    """
    
    def __init__(self):
        self.labels = ['ORGANIC', 'ANORGANIC']
    
    def predict_with_all_scores(self, image):
        """
        Simulasi prediksi dengan hasil random.
        
        Args:
            image: Frame gambar (numpy array) - tidak digunakan dalam mock
            
        Returns:
            Dict dengan label, confidence, dan all_scores
        """
        time.sleep(0.1)  # Simulasi inference time
        
        is_organic = random.choice([True, False])
        confidence = random.uniform(0.65, 0.98)
        
        if is_organic:
            return {
                'label': 'ORGANIC',
                'confidence': confidence,
                'all_scores': {
                    'ORGANIC': confidence,
                    'ANORGANIC': 1.0 - confidence
                }
            }
        else:
            return {
                'label': 'ANORGANIC',
                'confidence': confidence,
                'all_scores': {
                    'ORGANIC': 1.0 - confidence,
                    'ANORGANIC': confidence
                }
            }
