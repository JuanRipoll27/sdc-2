import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from image_generator import ImageGenerator
from gpt_service import GPTService

app = FastAPI()

env_path = Path(__file__).with_name(".env")
load_dotenv(env_path, override=True)

stability_key = os.getenv("STABILITY_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
profanity_prompt_file = os.getenv("PROFANITY_PROMPT_FILE", "./profanity_prompt.txt")

if not stability_key:
    raise RuntimeError("STABILITY_KEY is missing from .env")

image_generator = ImageGenerator(stability_key)

gpt_service = None
if openai_key and Path(profanity_prompt_file).exists():
    profanity_prompt = Path(profanity_prompt_file).read_text(encoding="utf-8")
    gpt_service = GPTService(openai_key, profanity_prompt)

generated_dir = Path("generated_images")
generated_dir.mkdir(exist_ok=True)

db_path = generated_dir / "images_db.json"


def load_images_db() -> dict:
    if db_path.exists():
        try:
            with open(db_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}
    return {}


def save_images_db():
    with open(db_path, "w", encoding="utf-8") as file:
        json.dump(images, file, indent=2, ensure_ascii=False)


images = load_images_db()


class ImageRequest(BaseModel):
    prompt: str = Field(min_length=3)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        value = value.strip()
        if len(value.split()) < 2:
            raise ValueError("Prompt must contain at least 2 words.")
        return value


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
        images[image_id]["updated_at"] = datetime.utcnow().isoformat()
        save_images_db()

    except Exception as error:
        images[image_id]["status"] = "failed"
        images[image_id]["error"] = str(error)
        images[image_id]["updated_at"] = datetime.utcnow().isoformat()
        save_images_db()


@app.post("/images")
async def create_image(
    request_body: ImageRequest,
    request: Request,
    background_tasks: BackgroundTasks
):
    prompt = request_body.prompt

    if gpt_service and gpt_service.contains_profanity(prompt):
        raise HTTPException(
            status_code=400,
            detail="Prompt rejected because it contains profanity or unsafe content."
        )

    image_id = str(uuid.uuid4())
    image_endpoint = str(request.base_url).rstrip("/") + f"/image/{image_id}"

    images[image_id] = {
        "status": "processing",
        "path": None,
        "prompt": prompt,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    save_images_db()

    background_tasks.add_task(gen_image_task, image_id, prompt)

    return {
        "image_id": image_id,
        "status": "processing",
        "status_url": image_endpoint,
        "image_url": image_endpoint
    }


@app.get("/image/{image_id}")
async def get_image(image_id: str):
    if image_id not in images:
        raise HTTPException(status_code=404, detail="Image not found")

    image_info = images[image_id]
    status = image_info["status"]

    if status == "processing":
        return {
            "image_id": image_id,
            "status": "processing",
            "prompt": image_info.get("prompt"),
            "created_at": image_info.get("created_at")
        }

    if status == "failed":
        return {
            "image_id": image_id,
            "status": "failed",
            "error": image_info.get("error"),
            "prompt": image_info.get("prompt"),
            "created_at": image_info.get("created_at")
        }

    if status == "ready":
        image_path = image_info.get("path")

        if not image_path or not Path(image_path).exists():
            raise HTTPException(status_code=500, detail="Image file missing")

        return FileResponse(image_path, media_type="image/png")

    raise HTTPException(status_code=500, detail="Unknown image status")


def write_log(message: str):
    with open("log.txt", "a", encoding="utf-8") as file:
        file.write(f"{message}\n")


@app.get("/example")
async def example_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, "Example endpoint was visited")
    return {"message": "This is an example endpoint"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)