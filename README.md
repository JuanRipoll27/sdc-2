# FastAPI Tutorial and Image Generation Assignment

Repository for the **Solution Deployment & Communication** course at **FH Technikum Wien**.

It contains the FastAPI tutorial materials and a completed assignment implementing a text-to-image REST API using FastAPI and Stability AI (Stable Diffusion).

## Repository structure

- `0_uv_tutorial/` — introductory materials for `uv`
- `1_fast_api_tutorial/` — FastAPI examples and exercises
- `assignment/` — image generation API implementation and documentation
- `tests/` — automated regression tests

The tutorial and assignment are separate Python projects with their own `pyproject.toml`, `uv.lock` and virtual environment.

**Requirements:** Python 3.11+ and [uv](https://docs.astral.sh/uv/).

## Run the image generation assignment

From the repository root:

```powershell
cd assignment
uv sync --locked
```

Create an `assignment/.env` file containing your own Stability AI API key:

```dotenv
STABILITY_KEY=your-stability-key
OPENAI_API_KEY=
PROFANITY_PROMPT_FILE=./profanity_prompt.txt
```

The OpenAI profanity filter is optional. Leave `OPENAI_API_KEY` empty to disable it.

Start the API:

```powershell
uv run --locked uvicorn app:app --reload
```

Open [Swagger UI](http://127.0.0.1:8000/docs) to test it:

1. Send a valid prompt to **POST /images**.
2. Copy the returned `image_id`.
3. Call **GET /image/{image_id}** with that ID (without quotes).
4. If the response is `processing`, try again after a short wait. When ready, the endpoint returns the generated PNG image.
5. Call **GET /images** to list all stored requests, including their prompts, statuses, and metadata.

For setup details, examples, request validation, response states, and persistence, see the **[assignment README](assignment/README.md)**.

## Run the FastAPI tutorial

From the repository root:

```powershell
cd 1_fast_api_tutorial
uv sync --locked
uv run --locked uvicorn inclass_fastapi_app:app --reload
```

Open [Swagger UI](http://127.0.0.1:8000/docs). For example, send `{"name": "Ada"}` to `POST /class`.

To explore the notebook, run `uv run --locked jupyter notebook` from the tutorial directory.

**Note:** Stop one server with Ctrl+C before starting the other; both use port 8000 by default.

## Run automated tests

From either `assignment/` or `1_fast_api_tutorial/`:

```powershell
uv run --locked python -m unittest discover -s ../tests -v
```

The tests include offline checks using mocked external responses. An end-to-end image generation check with a valid Stability AI key is a separate manual test.

## Security and local files

Do not commit real API keys, generated images, or local environments.

The assignment reads its credentials from `assignment/.env`; this file is ignored by Git. The generated PNG files and the local JSON metadata database are also ignored.

## Dev container

The repository includes a dev container that installs both locked environments. The default interpreter is `1_fast_api_tutorial/.venv/bin/python`; select `assignment/.venv/bin/python` for the assignment.
