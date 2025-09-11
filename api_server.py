#!/usr/bin/env python3
"""
Co-DETR FastAPI Server

A FastAPI server that exposes Co-DETR object detection model via REST API.
Accepts image uploads and returns images with detection overlays.
"""

import io
import os
import tempfile
import logging
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from mmdet.apis import inference_detector, init_detector
from mmdet.apis import show_result_pyplot
from auth import create_api_key_authenticator, ApiKey

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoDetrInferenceService:
    """Service class for Co-DETR model inference following SOLID principles."""
    
    def __init__(self, config_path: str, checkpoint_path: str, device: str = 'cuda:0'):
        """Initialize the inference service with model configuration."""
        self.config_path = config_path
        self.checkpoint_path = checkpoint_path
        self.device = device
        self.model = None
        self.class_names = None
        
    def load_model(self):
        """Load the Co-DETR model."""
        logger.info(f"Loading Co-DETR model from {self.checkpoint_path}")
        try:
            self.model = init_detector(self.config_path, self.checkpoint_path, device=self.device)
            # Use None for class_names - imshow_det_bboxes will use COCO classes by default
            self.class_names = None
            logger.info("Co-DETR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise RuntimeError(f"Model loading failed: {str(e)}")
    
    def predict(self, image_array: np.ndarray, score_threshold: float = 0.2) -> np.ndarray:
        """
        Run inference on image and return image with detection overlays.
        
        Args:
            image_array: Input image as numpy array
            score_threshold: Detection confidence threshold
            
        Returns:
            Processed image with detection overlays as numpy array
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        try:
            # Run inference
            result = inference_detector(self.model, image_array)
            
            # Create a temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            try:
                # Use show_result_pyplot like the original demo
                show_result_pyplot(
                    self.model,
                    image_array,
                    result,
                    score_thr=score_threshold,
                    out_file=temp_path
                )
                
                # Read the result image back
                output_image = cv2.imread(temp_path)
                
                return output_image
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        except Exception as e:
            logger.error(f"Inference failed: {str(e)}")
            raise RuntimeError(f"Inference failed: {str(e)}")

class ImageProcessor:
    """Utility class for image processing operations."""
    
    @staticmethod
    def validate_image(file: UploadFile) -> None:
        """Validate uploaded image file."""
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (limit to 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
    
    @staticmethod
    def load_image_from_upload(file: UploadFile) -> np.ndarray:
        """Convert uploaded file to numpy array."""
        try:
            # Read image file
            image_bytes = file.file.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array (OpenCV format: BGR)
            image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            return image_array
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    
    @staticmethod
    def encode_image_to_bytes(image_array: np.ndarray, format: str = 'JPEG') -> bytes:
        """Encode numpy array to image bytes."""
        try:
            # Convert BGR to RGB for PIL
            image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image_rgb)
            
            # Encode to bytes
            img_byte_arr = io.BytesIO()
            image_pil.save(img_byte_arr, format=format)
            img_byte_arr.seek(0)
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image encoding failed: {str(e)}")

# Initialize FastAPI app
app = FastAPI(
    title="Co-DETR Object Detection API",
    description="API server for Co-DETR object detection model",
    version="1.0.0"
)

# Add CORS middleware for web frontend support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global inference service instance
inference_service: Optional[CoDetrInferenceService] = None
image_processor = ImageProcessor()

# Initialize API key authentication
api_key_auth = create_api_key_authenticator()

@app.on_event("startup")
async def startup_event():
    """Initialize the model on startup."""
    global inference_service
    
    # Model paths - adjust these if your model files are in different locations
    config_path = "projects/configs/co_dino_vit/co_dino_5scale_vit_large_coco.py"
    checkpoint_path = "pytorch_model.pth"
    
    # Check if files exist
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        raise RuntimeError(f"Config file not found: {config_path}")
    
    if not os.path.exists(checkpoint_path):
        logger.error(f"Checkpoint file not found: {checkpoint_path}")
        raise RuntimeError(f"Checkpoint file not found: {checkpoint_path}")
    
    # Initialize inference service
    device = 'cuda:0' if os.environ.get('CUDA_VISIBLE_DEVICES') else 'cpu'
    inference_service = CoDetrInferenceService(config_path, checkpoint_path, device)
    inference_service.load_model()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Co-DETR Object Detection API is running",
        "status": "healthy",
        "model_loaded": inference_service is not None and inference_service.model is not None
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": inference_service is not None and inference_service.model is not None,
        "device": inference_service.device if inference_service else "unknown"
    }

@app.post("/detect")
async def detect_objects(
    file: UploadFile = File(..., description="Image file for object detection"),
    score_threshold: float = Query(0.2, ge=0.0, le=1.0, description="Detection confidence threshold"),
    output_format: str = Query("JPEG", regex="^(JPEG|PNG)$", description="Output image format"),
    api_key: ApiKey = Depends(api_key_auth)
):
    """
    Detect objects in uploaded image and return image with detection overlays.
    
    Args:
        file: Uploaded image file
        score_threshold: Confidence threshold for detections (0.0-1.0)
        output_format: Output image format (JPEG or PNG)
        api_key: Authenticated API key (automatically injected)
        
    Returns:
        Image with detection overlays
    """
    logger.info(f"Detection request from API key: {api_key.name}")
    if inference_service is None or inference_service.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Validate image
    image_processor.validate_image(file)
    
    try:
        # Process image
        image_array = image_processor.load_image_from_upload(file)
        
        # Run inference
        result_image = inference_service.predict(image_array, score_threshold)
        
        # Encode result
        image_bytes = image_processor.encode_image_to_bytes(result_image, output_format)
        
        # Return response
        media_type = f"image/{output_format.lower()}"
        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"inline; filename=detection_result.{output_format.lower()}"}
        )
        
    except Exception as e:
        logger.error(f"Detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
