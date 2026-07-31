# DrishtiX ReID Service

> Person Re-Identification microservice using OSNet for cross-camera tracking.

## Prerequisites

- **Python 3.9+**
- **pip** (Python package manager)
- **GPU** (optional but recommended — falls back to CPU automatically)

## Setup

```bash
# Navigate to the service directory
cd services/reid-service

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Service

```bash
# Start on default port 8100
uvicorn main:app --host 0.0.0.0 --port 8100

# Or run directly
python main.py
```

## Endpoints

### `GET /health`
Returns service health status.

```json
{
  "status": "ok",
  "model": "osnet_x1_0",
  "device": "cpu",
  "gpu_available": false
}
```

### `POST /extract`
Extracts a 512-dimensional feature embedding from a person crop image.

**Request**: `multipart/form-data` with `file` field (JPEG/PNG image)

```bash
curl -X POST http://localhost:8100/extract \
  -F "file=@person_crop.jpg"
```

**Response**:
```json
{
  "embedding": [0.0123, -0.0456, 0.0789, ...],
  "dimensions": 512,
  "latency_ms": 45.2
}
```

## Configuration

The service runs on port `8100` by default. To change:

```bash
uvicorn main:app --host 0.0.0.0 --port 9000
```

Update the `reid_service_url` config in DrishtiX's MongoDB `alert_config` collection accordingly.

## Notes

- The OSNet model weights are auto-downloaded on first startup (~7MB)
- If `torchreid` is not available, the service falls back to MobileNetV3-Small
- The service is stateless — scale horizontally if needed
