# Qimen Dunjia AI Backend

This project implements the backend for a web application that combines the ancient
Chinese divination system **Qimen Dunjia** (奇门遁甲) with modern large language
models (LLMs).  The system exposes a REST API that allows front‑end clients to
authenticate users, manage point balances, generate Qimen charts and forward
questions to an LLM.  It is designed to be easy to extend and replace the
placeholder components with production services (e.g. Supabase authentication
and a real Qimen algorithm) as the product matures.

## Purpose

According to classical sources, a Qimen Dunjia chart is a **3 × 3 magic square**
divided into nine palaces and populated with a variety of symbols (heavenly
stems, earthly branches, eight gates, nine stars and spirit plate).  The
configuration of these symbols changes every two hours, yielding **1,080
possible boards** that repeat four times per year and are sensitive to the
24 solar terms【232079094909397†L287-L299】.  When a person poses a question,
the chart corresponding to that exact moment forms the basis for divination.
This backend encapsulates the chart generation behind an abstract interface so
that a more accurate algorithm can be integrated later.

## High‑level architecture

The service is written in **Python** using [FastAPI](https://fastapi.tiangolo.com/).
It is organised into a set of modules under the `app/` package:

| Module | Responsibility |
|-------|---------------|
| `main.py` | Entry point that instantiates the FastAPI app and includes API routes. |
| `models.py` | Pydantic models defining request/response schemas. |
| `database.py` | A lightweight JSON‑based user store used during early development.  In production this should be replaced by Supabase or another database. |
| `points.py` | Logic for earning and spending points (e.g. daily sign‑in, inquiry cost). |
| `qimen.py` | Abstraction over the Qimen Dunjia charting algorithm.  By default it produces a dummy board; you should replace `generate_chart()` with a real implementation. |
| `llm.py` | Client code to call the LLM.  It uses the `openai` Python package when an API key is configured and returns a placeholder answer otherwise. |
| `utils.py` | Helper functions used across modules. |

The system follows a **waterfall development process**.  The current version
demonstrates the key components and includes clear extension points for
substituting proper services.  For example, the user store can be replaced by
Supabase and the dummy Qimen chart generator can call an external library
(`kinqimen`) once dependencies are available.

## Endpoints

All endpoints accept and return JSON.  Timestamps are interpreted in
`America/Los_Angeles` (UTC−8/UTC−7 depending on daylight saving).

### Authentication

Authentication is simplified during the prototype phase and uses a JSON file
(`users.json`) to persist users.  Each user has an `id`, `email`, `password`
(plain text in development; **never store plain passwords in production**),
current point balance and last sign‑in date.

#### `POST /auth/signup`

Registers a new user.

**Request body:**

```json
{
  "email": "alice@example.com",
  "password": "secret"
}
```

**Response:**

```json
{
  "id": "f9df1e48-...",
  "email": "alice@example.com",
  "points": 30
}
```

By default, new users start with 30 points.  Replace `database.py` with
Supabase integration to persist users securely.

#### `POST /auth/login`

Authenticates a user.  In the prototype this merely verifies the email and
password in the JSON store and returns the stored user record.  Implement
token‑based authentication (e.g. JWT) when connecting to Supabase.

### Points

#### `GET /points`

Returns the current point balance for the authenticated user.

**Response:**

```json
{
  "user_id": "f9df1e48-...",
  "points": 25
}
```

#### `POST /points/earn`

Allows a user to perform a daily sign‑in.  If the user hasn’t signed in today,
they receive 5 points.  The response contains the updated balance.  If the user
already signed in today, the endpoint returns an error message.

#### `POST /points/spend`

Deducts a specified number of points from the user’s balance.  This is called
internally by inquiry endpoints to charge for questions.  If the user has
insufficient points the request fails.

### Universal inquiry

#### `POST /inquiry`

The universal inquiry endpoint accepts a natural‑language question from a user.
It generates the current Qimen chart, formulates a prompt that combines the
chart and the question, calls the LLM and returns the answer.  Each call costs
**1 point**.

**Request body:**

```json
{
  "question": "Should I change my job?"
}
```

**Response:**

```json
{
  "answer": "Based on the current Qimen chart, it is advisable to…",
  "points_remaining": 24
}
```

### Featured analyses

Three specialised endpoints demonstrate how to build higher‑level tools on top
of the universal inquiry mechanism:

* `POST /analysis/quantification` – Accepts a cryptocurrency symbol (`btc`
  or `eth`) and returns a bullish/bearish opinion derived from the chart and
  LLM.
* `POST /analysis/finance` – Returns general investment guidance based on the
  current time and chart.
* `POST /analysis/destiny` – Accepts a birth date/time and returns insights
  about career, romance, wealth and health.  These endpoints also cost
  **1 point** each.

## Local development

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run the server:

```bash
uvicorn app.main:app --reload
```

3. The API will be available at `http://localhost:8000`.  You can use tools
such as [HTTPie](https://httpie.io/) or [curl](https://curl.se/) to test the
endpoints.

## Integration notes for front‑end developers

* **Authentication:** Replace the prototype JSON store with Supabase.  For
  example, use the Supabase `auth.sign_up` and `auth.sign_in` methods on
  the client side and pass the resulting `access_token` to the backend via
  the `Authorization` header.  The backend can verify the token using
  Supabase’s JWT secret and extract the `sub` (user id).

* **Time zones:** All time calculations are performed in the user’s locale
  (America/Los_Angeles).  When sending a birth date/time to `/analysis/destiny`,
  include the time in 24‑hour format.  The backend converts it to a Qimen chart
  using the placeholder algorithm.  In production, the algorithm should
  calculate the appropriate chart based on the 24 solar terms and sexagenary
  cycle【232079094909397†L287-L299】.

* **LLM integration:** The `llm.py` module wraps calls to OpenAI’s API.  Set
  the environment variable `OPENAI_API_KEY` to enable real answers.  Without a
  key, the backend returns a canned response that echoes the input.  To avoid
  unexpected charges, configure request limits and caching on the server.

* **Extending analysis tools:** Each featured analysis endpoint demonstrates
  how to combine chart data with domain‑specific context.  You can add new
  endpoints (e.g. property selection, match‑making, health advice) by following
  the same pattern: gather inputs, generate the relevant chart, assemble a
  prompt and dispatch to the LLM.

## Caveats

* The Qimen algorithm provided here is a **placeholder**.  The repository
  [`kinqimen`](https://github.com/kentang2017/kinqimen) implements a complete
  charting engine, but it depends on external packages (`sxtwl`, `ephem` and
  `bidict`) which may not be available in restricted environments.  You should
  integrate a robust implementation before going live.

* User authentication and point management are simplified for demonstration.
  Production code must hash passwords, enforce input validation, handle
  concurrency and protect against abuse.

* Error handling is intentionally verbose to aid development.  Once the system
  stabilises you should refine error messages and avoid leaking internal
  details.