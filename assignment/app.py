import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from image_generator import ImageGenerator

app = FastAPI()

load_dotenv()

stability_key = os.getenv("STABILITY_KEY")

if not stability_key:
    raise RuntimeError("STABILITY_KEY is missing from .env")

image_generator = ImageGenerator(stability_key)

images = {}

generated_dir = Path("generated_images")
generated_dir.mkdir(exist_ok=True)

class ImageRequest(BaseModel):
    prompt: str = Field(min_length=1)

def gen_image_task(image_id: str, prompt: str):
    try:
        image_bytes = image_generator.generate_image(prompt)

        if image_bytes is None:
            raise RuntimeError("Image generation returned no image")

        image_path = generated_dir / f"{image_id}.png"

        with open(image_path, "wb") as file:
            file.write(image_bytes)

        images[image_id]["status"] = "ready"
        images[image_id]["path"] = str(image_path)

    except Exception as error:
        print("IMAGE GENERATION ERROR:", error)

        images[image_id]["status"] = "failed"
        images[image_id]["error"] = str(error)
            

@app.post("/images")
async def create_image(
    request: ImageRequest,
    background_tasks: BackgroundTasks
):
    image_id = str(uuid.uuid4())

    images[image_id] = {
        "status": "processing",
        "path": None
    }

    background_tasks.add_task(
        gen_image_task,
        image_id,
        request.prompt
    )

    return {
        "image_id": image_id,
        "status": "processing"
    }

@app.get("/image/{image_id}")
async def get_image(image_id: str):
    if image_id not in images:
        raise HTTPException(status_code=404, detail="Image not found")

    image_info = images[image_id]

    if image_info["status"] == "processing":
        return {
            "image_id": image_id,
            "status": "processing"
        }

    if image_info["status"] == "failed":
        return {
            "image_id": image_id,
            "status": "failed",
            "error": image_info.get("error")
        }

    if image_info["status"] == "ready":
        return FileResponse(
            image_info["path"],
            media_type="image/png"
        )

# Function to be run as a background task.
# This is just a placeholder function for demonstration.
# In your application, this could be a function that generates an image.
def write_log(message: str):
    # Example of a time-consuming task: Writing a message to a file.
    # Replace this with the logic of your image generation task.
    with open("log.txt", "a") as file:
        file.write(f"{message}\n")

@app.get("/example")
async def example_endpoint(background_tasks: BackgroundTasks):
    # This endpoint demonstrates how to add a background task.
    # The `write_log` function will be executed after the response is sent.
    # Note: The task runs in the same process but does not block the response.
    background_tasks.add_task(write_log, "Example endpoint was visited")
    return {"message": "This is an example endpoint"}

# TODO: Define your POST /images endpoint for asynchronous image generation
# This endpoint should accept a custom prompt, process it asynchronously,
# and return an image ID for later retrieval.

# TODO: Implement the background task function for image generation
# This function will use the ImageGenerator service to generate images
# based on the provided custom prompt and save them.

# TODO: Create an endpoint for retrieving generated images
# The endpoint should take an image ID and return the corresponding image
# if it's ready, or an appropriate status message otherwise.

# TODO: Implement error handling for various possible failure scenarios

# OPTIONAL: Implement any necessary profanity checking or validation for the user prompts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
