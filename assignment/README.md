# FastAPI Image Generation Service

**Course:** Solution Deployment & Communication — FH Technikum Wien

This assignment implements a text-to-image **REST API** using **FastAPI**, **Stable Diffusion XL (SDXL)** and the **Stability AI SDK**. It accepts a text prompt, starts image generation as a background task, records progress, and lets the client retrieve the resulting PNG by ID.

The implementation focuses on integrating an external ML service with request validation, asynchronous request handling, local persistence, and error reporting.

## Main features

- `POST /images` to submit a text prompt for image generation
- `GET /image/{image_id}` to check the request status or retrieve the PNG
- FastAPI `BackgroundTasks` so the POST can return without waiting for generation
- Pydantic input validation (at least two words and three characters)
- UUID identifiers for individual requests
- Stable Diffusion XL image generation through Stability AI
- Local PNG storage and JSON-based metadata persistence
- `processing` / `ready` / `failed` request states
- Optional OpenAI-based profanity checking
- Interactive OpenAPI / Swagger documentation

## Architecture and request lifecycle

1. The client sends JSON containing a `prompt` to `POST /images`.
2. Pydantic validates the input. If OpenAI filtering is configured, the prompt is checked for inappropriate content.
3. The API generates a UUID, stores the initial `processing` record in `generated_images/images_db.json`, and schedules a background task.
4. The POST responds immediately with the UUID and a URL for checking the result.
5. The background task sends a formatted prompt to Stability AI using the configured Stable Diffusion XL model.
6. If generation succeeds, it writes `generated_images/<image_id>.png` and marks the record `ready`. If it fails, it records `failed` and the error message.
7. The client calls `GET /image/{image_id}`. While processing, it receives JSON; when ready, it receives the PNG.

FastAPI BackgroundTasks runs work in the API process, **not** in a separate durable task queue. For this coursework, this avoids additional infrastructure.

## Requirements

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/)
- A valid **Stability AI API key** for real image generation
- Optional: an OpenAI API key if profanity checking is enabled

## Installation and configuration

From the `assignment/` directory:

```powershell
uv sync --locked
```

Create a local file named `.env` inside `assignment/` (next to `app.py`):

```dotenv
STABILITY_KEY=your-stability-key
OPENAI_API_KEY=
PROFANITY_PROMPT_FILE=./profanity_prompt.txt
```

- `STABILITY_KEY` is required. The application raises an error on startup if it is missing.
- `OPENAI_API_KEY` is optional. Leave it empty to skip the OpenAI filter.
- `PROFANITY_PROMPT_FILE` specifies the optional filter instructions. Its default is `./profanity_prompt.txt`.
- The application's `.env` loader explicitly reads the file beside `app.py`. Run the commands below from `assignment/` so relative paths resolve as intended.

**Security:** Never commit actual API keys. The assignment's local `.env` is covered by the repository's `.gitignore`. A separate `.env` at the repository root is not used by `assignment/app.py`.

## Run the API

```powershell
uv run --locked uvicorn app:app --reload
```

The server runs locally at `http://127.0.0.1:8000`. Open the interactive documentation:

**http://127.0.0.1:8000/docs**

## Live demo using Swagger UI

The API can be demonstrated without a custom client script:

1. In Swagger UI, expand **POST /images** and click **Try it out**.
2. Enter a single prompt, for example:

   ```json
   {
     "prompt": "A Viennese tram in front of Schönbrunn Palace in winter"
   }
   ```

3. Click **Execute**. A successful request returns HTTP `200` with an `image_id` and `processing` status.
4. Expand **GET /image/{image_id}**. Paste the returned ID **without quotation marks** and click **Execute**.
5. If the response is JSON containing `"status": "processing"`, wait and execute the GET again.
6. When generation finishes, the GET response contains the generated **PNG image** (`image/png`). You can open the URL or download the returned image from Swagger.

The model implementation appends a sketch-style prompt template to the user's text, so generated pictures are intentionally styled like detailed drawings.

### Example initial response

```json
{
  "image_id": "6c0874fe-2655-4b97-8395-e7110abaad16",
  "status": "processing",
  "status_url": "http://127.0.0.1:8000/image/6c0874fe-2655-4b97-8395-e7110abaad16",
  "image_url": "http://127.0.0.1:8000/image/6c0874fe-2655-4b97-8395-e7110abaad16"
}
```

The ID is illustrative; each request generates a new UUID. The URL is for both **status checking** and **image retrieval**.

## API reference

| Method | Endpoint | Behavior |
| --- | --- | --- |
| `POST` | `/images` | Validate the prompt, queue generation, return UUID and status URL |
| `GET` | `/image/{image_id}` | Return status JSON or the generated PNG |
| `GET` | `/example` | Tutorial endpoint that schedules a simple background log entry |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/openapi.json` | OpenAPI specification |

### Request validation

`POST /images` expects:

```json
{
  "prompt": "Buenos Aires at sunset"
}
```

Prompts must be strings of at least three characters and at least **two words** after whitespace is trimmed. Empty input or a one-word prompt (for example, `"Buenos"`) produces HTTP **422**.

When the optional OpenAI profanity filter is active, a flagged prompt is rejected with HTTP **400**. If the OpenAI service or its credentials fail, this implementation may produce HTTP **500** before image generation begins; for the demonstration, leave the OpenAI key empty unless the filter has been configured and tested successfully.

### Image retrieval states

`GET /image/{image_id}` behaves as follows:

| State | HTTP response | Body |
| --- | --- | --- |
| Processing | `200` | JSON containing `image_id`, `status`, `prompt`, `created_at` |
| Ready | `200` | Binary PNG with `Content-Type: image/png` |
| Failed | `200` | JSON containing `status: failed` and the stored error |
| Unknown ID | `404` | JSON error message |
| Ready record but missing file | `500` | JSON error message |

**Important:** `200 OK` alone does not prove that an image was generated. Confirm that the final response is a PNG, not a `processing` or `failed` JSON response.

## Image storage and metadata

The application creates the following directory relative to the working directory:

```text
generated_images/
    images_db.json
    <image-id-1>.png
    <image-id-2>.png
```

`images_db.json` stores an entry per request with its prompt, status, image path, error (if any), and timestamps. For example:

```json
{
  "example-image-id": {
    "status": "ready",
    "path": "generated_images/example-image-id.png",
    "prompt": "Buenos Aires at sunset",
    "error": null,
    "created_at": "2026-10-20T12:00:00",
    "updated_at": "2026-10-20T12:00:15"
  }
}
```

The dates and ID above are illustrative. Records are loaded again when the app restarts. Generated images and metadata are local runtime files and are ignored by Git.

The directory `generated_images/` is **not** served as a public static URL. Use `GET /image/{image_id}` to access an individual generated image. The current committed API does not expose a `GET /generated_images` route.

## External service and failure handling

The background function catches errors raised during Stability AI generation. It records the request as `failed` and stores the error text for subsequent retrieval via `GET /image/{image_id}`.

A missing Stability key prevents application startup. The optional GPT-based profanity check runs before the background task is scheduled and is a separate dependency.

Because the implementation uses in-process background tasks and a local JSON file, it is designed for a course project and local demonstration, not as a multi-worker production queue or database.

## Automated tests

From `assignment/`, run:

```powershell
uv run --locked python -m unittest discover -s ../tests -v
```

The repository test suite includes FastAPI regression checks and **mocked** OpenAI responses for the GPT service. These automated tests do not prove that Stability AI accepts your real key or successfully returns an image.

For end-to-end validation, complete the Swagger demo above and confirm that the resulting response is a PNG file. Also try an invalid one-word prompt (`422`) and an unknown image ID (`404`).

## Design choices

- **FastAPI + Pydantic:** compact REST implementation with automatic request validation and interactive documentation.
- **BackgroundTasks:** decouples the initial POST response from time-consuming image generation without introducing Redis, Celery, or a separate worker.
- **UUIDs:** distinguish requests and provide stable retrieval URLs.
- **Local JSON and PNG files:** simple persistence that is sufficient for this assignment.
- **Optional GPT validation:** the image generation workflow can run independently of OpenAI when the filter is not configured.
