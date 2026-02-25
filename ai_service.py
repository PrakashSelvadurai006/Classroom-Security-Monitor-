import requests
import base64
import json
import numpy as np
import cv2
from PIL import Image
import io
import os
from config import Config

class AIService:
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.base_url = Config.OPENROUTER_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Using free models from OpenRouter that are good for image analysis
        self.vision_model = "google/gemini-flash-1.5"  # Free and good for vision tasks
        self.backup_model = "meta-llama/llama-3.2-11b-vision-instruct:free"  # Free backup

    def encode_image_to_base64(self, image_path_or_array):
        """Convert image file or numpy array to base64 string"""
        try:
            if isinstance(image_path_or_array, str):
                # It's a file path
                with open(image_path_or_array, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            elif isinstance(image_path_or_array, np.ndarray):
                # It's a numpy array (from OpenCV)
                _, buffer = cv2.imencode('.jpg', image_path_or_array)
                return base64.b64encode(buffer).decode('utf-8')
            else:
                raise ValueError("Invalid image input type")
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None

    def detect_faces_in_image(self, image_data):
        """
        Detect faces in an image using OpenRouter AI
        Returns list of face bounding boxes and confidence scores
        """
        try:
            base64_image = self.encode_image_to_base64(image_data)
            if not base64_image:
                return []

            payload = {
                "model": self.vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this image and detect all human faces. For each face detected, provide:
1. Bounding box coordinates (x, y, width, height) as percentages of image dimensions
2. Confidence score (0.0 to 1.0)
3. Basic facial features description for comparison

Format your response as JSON:
{
  "faces": [
    {
      "bbox": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
      "confidence": 0.95,
      "features": "description of key facial features"
    }
  ],
  "total_faces": 1
}

If no faces are detected, return: {"faces": [], "total_faces": 0}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from the response
                try:
                    # Find JSON in the response
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        face_data = json.loads(json_str)
                        return face_data.get('faces', [])
                except json.JSONDecodeError:
                    print("Error parsing AI response JSON")
                    return []
            else:
                print(f"AI API Error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []

    def extract_face_features(self, image_data):
        """
        Extract facial features for comparison using AI
        Returns a feature vector/description for face matching
        """
        try:
            base64_image = self.encode_image_to_base64(image_data)
            if not base64_image:
                return None

            payload = {
                "model": self.vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this face image and extract detailed facial features for identification purposes. Provide:

1. Facial structure: face shape, jawline, cheekbones
2. Eyes: shape, size, color, eyebrow shape
3. Nose: shape, size, bridge characteristics
4. Mouth: lip shape, size, smile characteristics
5. Distinctive features: any unique marks, facial hair, etc.
6. Overall facial proportions and key measurements

Create a detailed feature descriptor that could be used to match this face against others. Format as JSON:

{
  "feature_vector": "detailed textual description of all facial features",
  "key_features": ["feature1", "feature2", "feature3"],
  "face_hash": "unique identifier based on features"
}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.1
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        feature_data = json.loads(json_str)
                        return feature_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, return the raw content as feature vector
                    return {
                        "feature_vector": content,
                        "key_features": [],
                        "face_hash": str(hash(content))
                    }
            else:
                print(f"AI API Error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error extracting face features: {e}")
            return None

    def compare_faces(self, face1_features, face2_features):
        """
        Compare two face feature sets using AI
        Returns similarity score between 0.0 and 1.0
        """
        try:
            if not face1_features or not face2_features:
                return 0.0

            payload = {
                "model": self.vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Compare these two facial feature descriptions and determine how similar they are:

Face 1 Features: {json.dumps(face1_features, indent=2)}

Face 2 Features: {json.dumps(face2_features, indent=2)}

Analyze the similarity based on:
1. Facial structure and proportions
2. Eye characteristics
3. Nose features
4. Mouth and lip features
5. Overall facial geometry
6. Distinctive features

Provide a similarity score from 0.0 (completely different) to 1.0 (identical match).
Consider a score above 0.7 as a likely match for the same person.

Return only a JSON response:
{{
  "similarity_score": 0.85,
  "confidence": 0.9,
  "reasoning": "brief explanation of the comparison"
}}"""
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        comparison_data = json.loads(json_str)
                        return comparison_data.get('similarity_score', 0.0)
                except json.JSONDecodeError:
                    return 0.0
            else:
                print(f"AI API Error: {response.status_code} - {response.text}")
                return 0.0

        except Exception as e:
            print(f"Error comparing faces: {e}")
            return 0.0

    def process_frame_for_faces(self, frame):
        """
        Process a video frame to detect and extract faces
        Returns list of face data with features
        """
        faces = self.detect_faces_in_image(frame)
        processed_faces = []
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        for face in faces:
            try:
                # Extract face region based on bounding box
                bbox = face.get('bbox', {})
                x = int(bbox.get('x', 0) * width)
                y = int(bbox.get('y', 0) * height)
                w = int(bbox.get('width', 0) * width)
                h = int(bbox.get('height', 0) * height)
                
                # Extract face region
                face_region = frame[y:y+h, x:x+w]
                
                if face_region.size > 0:
                    # Extract features for this face
                    features = self.extract_face_features(face_region)
                    
                    processed_faces.append({
                        'bbox': bbox,
                        'confidence': face.get('confidence', 0.0),
                        'features': features,
                        'face_region': face_region
                    })
            except Exception as e:
                print(f"Error processing face: {e}")
                continue
        
        return processed_faces