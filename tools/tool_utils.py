from mimetypes import guess_type
import base64
from pydantic import BaseModel, Field

class BOutput(BaseModel):
    """Banner ad score output"""
    score: int = Field(ge=1, le=5)
    explanation: str

    class Config:
        extra = "forbid"  # Prevents additional fields
        
def prepare_image_message(image_path: str) -> dict:
    """
    Get the url of a local image
    """
    try:
        mime_type, _ = guess_type(image_path)

        if mime_type is None:
            mime_type = "application/octet-stream"

        with open(image_path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")

        return f"data:{mime_type};base64,{base64_encoded_data}"
    except Exception as e:
        raise ValueError(f"Failed to process image at {image_path}: {str(e)}")