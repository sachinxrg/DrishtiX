"""
DrishtiX ReID Microservice — Person Re-Identification using OSNet

A lightweight FastAPI service that extracts 512-dimensional feature embeddings
from person images using the OSNet (Omni-Scale Network) model for cross-camera
person re-identification.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8100

Endpoints:
    GET  /health   → Service health check
    POST /extract  → Extract embedding from a person crop image
"""

import io
import logging
import time
from contextlib import asynccontextmanager

import numpy as np
import torch
import torchvision.transforms as T
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

# ─── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("reid-service")

# ─── Global Model State ─────────────────────────────────────────────
model = None
device = None
transform = None


def load_model():
    """Load the OSNet model for feature extraction."""
    global model, device, transform

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    try:
        from torchreid.utils import FeatureExtractor

        extractor = FeatureExtractor(
            model_name="osnet_x1_0",
            model_path="",  # auto-downloads pretrained weights
            device=str(device),
        )
        model = extractor
        logger.info("OSNet model loaded successfully via torchreid FeatureExtractor")
    except ImportError:
        logger.warning(
            "torchreid not found, falling back to torchvision MobileNetV3 for embedding extraction"
        )
        # Fallback: use a lightweight torchvision model for embeddings
        import torchvision.models as models

        backbone = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        # Remove classifier, keep feature extractor
        backbone.classifier = torch.nn.Identity()
        backbone = backbone.to(device)
        backbone.eval()
        model = backbone
        logger.info("Fallback MobileNetV3-Small loaded for embedding extraction")

    # Standard ImageNet normalization + ReID-standard input size (256x128)
    transform = T.Compose([
        T.Resize((256, 128)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    logger.info("Image transform pipeline initialized (256x128, ImageNet normalization)")


# ─── Application Lifespan ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    logger.info("Starting DrishtiX ReID Service...")
    load_model()
    logger.info("ReID Service ready — accepting requests")
    yield
    logger.info("Shutting down ReID Service")


app = FastAPI(
    title="DrishtiX ReID Service",
    description="Person Re-Identification embedding extraction using OSNet",
    version="1.0.0",
    lifespan=lifespan,
)


# ─── Health Check ───────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Returns service health status and model information."""
    model_name = "osnet_x1_0"
    if not hasattr(model, "model_name"):
        model_name = "mobilenet_v3_small (fallback)"

    return {
        "status": "ok",
        "model": model_name,
        "device": str(device),
        "gpu_available": torch.cuda.is_available(),
    }


# ─── Embedding Extraction ──────────────────────────────────────────
@app.post("/extract")
async def extract_embedding(file: UploadFile = File(...)):
    """
    Extracts a 512-dimensional feature embedding from a person crop image.

    Args:
        file: JPEG or PNG image of a person (ideally upper-body crop)

    Returns:
        JSON with 'embedding' (list of floats) and 'dimensions' (int)
    """
    # Validate content type
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {file.content_type}. Use JPEG or PNG.",
        )

    start_time = time.time()

    try:
        # Read and decode image
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        logger.debug("Image loaded: %s, size=%s", file.filename, image.size)

        # Extract embedding based on model type
        if hasattr(model, "__call__") and hasattr(model, "model_name"):
            # torchreid FeatureExtractor path
            # FeatureExtractor expects list of image paths or numpy arrays
            img_np = np.array(image)
            features = model([img_np])  # Returns tensor of shape [1, 512]
            embedding = features[0].cpu().numpy().tolist()
        else:
            # Fallback torchvision model path
            img_tensor = transform(image).unsqueeze(0).to(device)
            with torch.no_grad():
                features = model(img_tensor)
            # L2 normalize the feature vector
            features = torch.nn.functional.normalize(features, p=2, dim=1)
            embedding = features[0].cpu().numpy().tolist()

        elapsed_ms = (time.time() - start_time) * 1000
        dimensions = len(embedding)

        logger.info(
            "Embedding extracted: dims=%d, latency=%.1fms, file=%s",
            dimensions,
            elapsed_ms,
            file.filename,
        )

        return JSONResponse(
            content={
                "embedding": embedding,
                "dimensions": dimensions,
                "latency_ms": round(elapsed_ms, 1),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Embedding extraction failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Embedding extraction failed: {str(e)}",
        )


# ─── Entry Point ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100, log_level="info")
