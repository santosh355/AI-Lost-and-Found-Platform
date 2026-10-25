import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity

print("Initializing MobileNetV2 Deep Learning Model...")
base_model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

def extract_image_features(img_path):
    """Extracts 1280-dimensional feature vector using MobileNetV2 transfer learning."""
    try:
        img = image.load_img(img_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        features = base_model.predict(x, verbose=0)
        return features.flatten()
    except Exception as e:
        print(f"Error in ML feature extraction: {e}")
        return None

def compute_match_score(lost_item, found_item):
    """Computes hybrid score combining Category, Colour, Manual Location, and DL Cosine Similarity."""
    score = 0
    
    # Category match (40 pts)
    if lost_item['item_category'].lower() in found_item['item_category'].lower() or \
       found_item['item_category'].lower() in lost_item['item_category'].lower():
        score += 40
        
    # Colour match (20 pts)
    if lost_item.get('colour') and found_item.get('colour') and \
       lost_item['colour'].lower() in found_item['colour'].lower():
        score += 20
        
    # Manual Location match (20 pts)
    if lost_item.get('location') and found_item.get('location') and \
       lost_item['location'].lower() in found_item['location'].lower():
        score += 20
        
    # DL Image Cosine Similarity match (20 pts)
    dl_similarity = 0.0
    if lost_item.get('feature_vector') and found_item.get('feature_vector'):
        vec1 = np.array(lost_item['feature_vector']).reshape(1, -1)
        vec2 = np.array(found_item['feature_vector']).reshape(1, -1)
        sim = cosine_similarity(vec1, vec2)[0][0]
        dl_similarity = float(sim)
        score += int(sim * 20)
        
    return score, round(dl_similarity * 100, 1)