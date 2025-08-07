# Co-DETR Object Detection API

A FastAPI server that exposes the Co-DETR object detection model via REST API endpoints. This allows you to perform object detection on images by sending HTTP requests instead of running command-line scripts.

## Features

- **Fast and Scalable**: Built with FastAPI for high performance
- **Docker Support**: Fully containerized for easy deployment
- **Image Upload**: Accept various image formats via HTTP POST
- **Configurable**: Adjustable detection thresholds and output formats
- **Health Monitoring**: Built-in health check endpoints
- **CORS Enabled**: Ready for web frontend integration

## API Endpoints

### Health Check

```
GET /
GET /health
```

Returns server status and model loading state.

### Object Detection

```
POST /detect
```

Upload an image and receive the image with detection overlays.

**Parameters:**

- `file` (required): Image file (JPEG, PNG, etc.)
- `score_threshold` (optional): Detection confidence threshold (0.0-1.0, default: 0.2)
- `output_format` (optional): Output format ("JPEG" or "PNG", default: "JPEG")

**Response:** Image with detection bounding boxes and labels

## Quick Start

### 1. Local Development Setup

```bash
# Install API dependencies
pip install -r requirements.txt

# Run the server
python api_server.py
```

The server will be available at `http://localhost:8000`

### 2. Docker Deployment

#### Option A: Docker Compose (Recommended)

```bash
# Build and start the service
docker-compose up --build

# Run in background
docker-compose up -d --build
```

#### Option B: Docker Build & Run

```bash
# Build the image
docker build -t co-detr-api -f Dockerfile.api .

# Run the container
docker run --gpus all -p 8000:8000 \
  -v $(pwd)/pytorch_model.pth:/Co-DETR/pytorch_model.pth:ro \
  co-detr-api
```

### 3. Using the API

#### Test with curl

```bash
# Health check
curl http://localhost:8000/health

# Object detection
curl -X POST "http://localhost:8000/detect?score_threshold=0.3" \
  -H "accept: image/jpeg" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_image.jpg" \
  --output detected_image.jpg
```

#### Test with Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Object detection
url = "http://localhost:8000/detect"
params = {"score_threshold": 0.3, "output_format": "JPEG"}

with open("your_image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files, params=params)

# Save result
with open("result.jpg", "wb") as f:
    f.write(response.content)
```

#### Test with JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

fetch("http://localhost:8000/detect?score_threshold=0.3", {
  method: "POST",
  body: formData,
})
  .then((response) => response.blob())
  .then((blob) => {
    const url = URL.createObjectURL(blob);
    document.getElementById("result-image").src = url;
  });
```

## Configuration

### Model Configuration

The server uses these model files by default:

- **Config**: `projects/configs/co_dino_vit/co_dino_5scale_vit_large_coco.py`
- **Checkpoint**: `pytorch_model.pth`

To use different model files, modify the paths in `api_server.py`:

```python
config_path = "path/to/your/config.py"
checkpoint_path = "path/to/your/checkpoint.pth"
```

> Note: The checkpoint I used can be found [here](https://huggingface.co/zongzhuofan/co-detr-vit-large-coco/tree/main) but any checkpoint referenced in the main [README.md](README.md) should work.

### Environment Variables

- `CUDA_VISIBLE_DEVICES`: GPU device selection (default: "0")
- `PYTHONPATH`: Should include Co-DETR project path

### Docker Volumes

Mount your model files if they're stored externally:

```yaml
volumes:
  - ./your_model.pth:/Co-DETR/pytorch_model.pth:ro
  - ./your_config.py:/Co-DETR/projects/configs/your_config.py:ro
```

## Performance Considerations

1. **GPU Memory**: The model requires significant GPU memory. Ensure adequate VRAM.
2. **Model Loading**: Model loading happens on startup and takes ~30 seconds.
3. **Concurrent Requests**: FastAPI handles concurrent requests efficiently.
4. **Image Size**: Large images may take longer to process. Consider resizing if needed.

## Troubleshooting

### Common Issues

**Model Not Found**

```
RuntimeError: Model loading failed: No such file or directory
```

Solution: Ensure `pytorch_model.pth` and config files exist in the correct paths.

**CUDA Out of Memory**

```
RuntimeError: CUDA out of memory
```

Solution: Use CPU inference by setting `device = 'cpu'` in the startup event.

**Port Already in Use**

```
OSError: [Errno 98] Address already in use
```

Solution: Change the port in `uvicorn.run(app, host="0.0.0.0", port=8001)`

### Logs and Debugging

View logs for debugging:

```bash
# Docker logs
docker-compose logs -f co-detr-api

# Local development
python api_server.py  # Logs appear in console
```

## API Documentation

Once the server is running, visit:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## Opportunities for Improvement

For production deployment:

1. Add authentication/authorization
2. Implement rate limiting
3. Add input validation and sanitization
4. Use HTTPS with proper certificates

General:

1. Create API test suite
2. Create new endpoints to cover more functionality of Co-DETR
