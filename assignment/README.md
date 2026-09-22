# FastAPI Image Generation Service

This project implements an asynchronous image generation API using **FastAPI**
and **Stable Diffusion through Stability AI**.

It was developed as part of the *Solution Deployment & Communication* course at
FH Technikum Wien.

The main goal was to take an external ML service and expose it through a simple
API while handling asynchronous execution, request validation, persistence, and
error handling.

---

## How it works

A user sends a text prompt to the API through:

```http
POST /images
```

The API immediately creates an `image_id`, stores the request, and starts image
generation as a FastAPI background task.

This means that the client does not need to wait for Stable Diffusion to finish
before receiving a response.

The generated image can later be retrieved using:

```http
GET /image/{image_id}
```

Depending on the current state of the request, the endpoint returns:

- `processing` while the image is being generated
- the generated PNG when the image is ready
- `failed` together with an error message if generation fails
- `404` when the supplied image ID does not exist

---

## Features

The implementation includes:

- asynchronous image generation using FastAPI `BackgroundTasks`
- integration with Stability AI
- unique image IDs using UUIDs
- persistent request metadata using a local JSON file
- local storage of generated images
- prompt validation
- minimum prompt length of two words
- optional profanity checking using OpenAI
- error handling for external API failures
- direct status/image URL returned when an image request is created
- automatic interactive API documentation through Swagger

---

## Example

A request can be sent with a prompt such as:

```json
{
  "prompt": "Buenos Aires café on a rainy evening"
}
```

Or, combining Argentina and Vienna:

```json
{
  "prompt": "an Argentine mate next to the Danube in Vienna"
}
```

The API responds immediately with something similar to:

```json
{
  "image_id": "6c0874fe-2655-4b97-8395-e7110abaad16",
  "status": "processing",
  "status_url": "http://127.0.0.1:8000/image/6c0874fe-2655-4b97-8395-e7110abaad16",
  "image_url": "http://127.0.0.1:8000/image/6c0874fe-2655-4b97-8395-e7110abaad16"
}
```

The returned URL can then be opened again after a few seconds.

While generation is still running, the response looks like:

```json
{
  "image_id": "6c0874fe-2655-4b97-8395-e7110abaad16",
  "status": "processing",
  "prompt": "an Argentine mate next to the Danube in Vienna"
}
```

Once generation finishes, the same endpoint returns the generated PNG image.

---

## Prompt validation

Prompts must contain at least two words.

For example:

```json
{
  "prompt": "Buenos Aires"
}
```

is valid, while:

```json
{
  "prompt": "Buenos"
}
```

is rejected automatically by FastAPI/Pydantic with HTTP status `422`.

If an OpenAI API key is configured, the application can also check prompts for
profanity before sending them to the image generation service.

---

## Local setup

The project uses **Python 3.11+** and **uv** for dependency management.

From the `assignment` directory, install the locked dependencies with:

```bash
uv sync --locked
```

Start the API with:

```bash
uv run --locked uvicorn app:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Environment variables

Create a local `.env` file inside the `assignment` directory:

```env
OPENAI_API_KEY="your-openai-key"
STABILITY_KEY="your-stability-key"
PROFANITY_PROMPT_FILE="./profanity_prompt.txt"
```

API keys are kept outside the source code and are excluded from Git.

---

## Image persistence

Generated images are stored locally inside:

```text
generated_images/
```

Request metadata is also stored locally so that generated image IDs and their
status are not lost when the application is restarted.

A stored request contains information such as:

```json
{
  "status": "ready",
  "path": "generated_images/example-id.png",
  "prompt": "an Argentine mate next to the Danube in Vienna",
  "error": null,
  "created_at": "...",
  "updated_at": "..."
}
```

Generated files and local runtime data are excluded from Git.

---

## Error handling

Errors from the external image generation service are caught by the background
task and stored together with the corresponding image request.

For example, if the external provider rejects a request, the API can return:

```json
{
  "image_id": "...",
  "status": "failed",
  "error": "External image generation service error"
}
```

This allows the initial `POST /images` request to remain asynchronous while
still giving the client a way to inspect failures afterwards.

---

## Tests

The repository tests can be executed from the `assignment` directory with:

```bash
uv run --locked python -m unittest discover -s ../tests -v
```

The implementation was checked against the provided test suite.

---

## Main design decisions

For this assignment, I kept the architecture intentionally simple.

FastAPI `BackgroundTasks` was used instead of introducing an external queue such
as Redis. This keeps the focus on asynchronous model integration without adding
infrastructure that is not necessary for the scope of the exercise.

A lightweight JSON-based storage mechanism was added to keep generated image IDs
and their status between application restarts.

The API also returns the image/status URL directly when a request is created, so
the client immediately knows where to retrieve the result.

Prompt validation was added to avoid sending very short or empty prompts to the
external service, and optional OpenAI-based profanity checking can be used as an
additional validation step before image generation.