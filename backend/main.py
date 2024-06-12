from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from io import BytesIO
from PIL import Image
import torch
from ultralytics import YOLO

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Update to match the port your Svelte app runs on
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

model = YOLO('best_061124.pt')

class ImageData(BaseModel):
    image: str

@app.post("/detect")
async def detect_objects(image_data: ImageData):
    try:
        image_base64 = image_data.image.split(",")[1]
        image = Image.open(BytesIO(base64.b64decode(image_base64)))
        
        # Run the YOLO model on the image
        results = model.track(image, conf=0.5, persist=True)  
                
        # Process results to extract bounding boxes and other information
        detections = []
        for result in results:
            for r in result.boxes:
                detections.append({
                    "object": model.names[int(r.cls)],  # Use model.names to get class names
                    "confidence": float(r.conf),
                    "xmin": float(r.xyxy[0][0]),
                    "ymin": float(r.xyxy[0][1]),
                    "xmax": float(r.xyxy[0][2]),
                    "ymax": float(r.xyxy[0][3])
                })
        
        return detections
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
