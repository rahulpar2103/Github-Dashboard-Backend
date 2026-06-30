# GitDash Backend

The backend for **GitDash**, a real-time GitHub activity dashboard. Built with **FastAPI**, it serves a REST API and a WebSocket endpoint to stream live GitHub repository events to connected clients. Background polling is handled by **Celery Beat**, and all event state and pub/sub messaging is stored in **Redis**. User accounts are persisted in **PostgreSQL**.

---

## What This Service Does

- Authenticates users via username/password or GitHub OAuth 2.0
- Issues JWT access tokens for all protected routes
- Lets authenticated users track or untrack any public GitHub repository
- Fetches and caches repository events from the GitHub Events API
- Polls all globally tracked repositories every 10 seconds through a Celery Beat schedule
- Publishes new events to Redis channels so connected WebSocket clients receive them instantly
- Maintains a per-user list of tracked repositories in Redis and stores up to 100 recent events per repository

---

## Architecture Overview

```
Browser / Frontend
       |
       |  REST (HTTP)          WebSocket (/ws)
       v                            v
  FastAPI (Uvicorn)  <-------  WebSocketService
       |                            |
  Auth / GitHub Routers        Redis Pub/Sub
       |                            ^
  PostgreSQL (users)           Celery Worker
                                    |
                               GitHub Events API
                                    |
                               Celery Beat (every 10s)
```

Three processes run concurrently:
- **Uvicorn** serves the FastAPI app (REST + WebSocket)
- **Celery Worker** executes the polling tasks
- **Celery Beat** triggers the polling task every 10 seconds

---

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | FastAPI |
| ASGI server | Uvicorn |
| Background tasks | Celery + Celery Beat |
| Message broker / cache | Redis (also used for pub/sub) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| HTTP client | httpx (async) |
| Auth | JWT (PyJWT) + bcrypt |
| GitHub OAuth | GitHub OAuth 2.0 App |
| Settings | pydantic-settings |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
.
├── app/
│   ├── main.py                  # FastAPI app factory, CORS, router registration
│   ├── tasks.py                 # Celery task definitions (polling logic)
│   ├── core/
│   │   ├── config.py            # All settings loaded from .env via pydantic-settings
│   │   ├── database.py          # SQLAlchemy engine and session factory
│   │   ├── redis.py             # Async Redis client instance
│   │   ├── celery.py            # Celery app config and Beat schedule (10s interval)
│   │   └── security.py          # Password hashing, JWT creation/verification, auth dependencies
│   ├── models/
│   │   └── userModel.py         # SQLAlchemy User table definition
│   ├── schemas/
│   │   ├── userSchema.py        # Pydantic schemas for registration/login/token responses
│   │   └── github.py            # Pydantic schemas for track/untrack request bodies
│   ├── routers/
│   │   ├── authRouter.py        # /auth/* endpoints (register, login, GitHub OAuth)
│   │   ├── githubRouter.py      # /github/* endpoints (track, untrack, events)
│   │   └── webSocket.py         # /ws WebSocket endpoint
│   ├── services/
│   │   ├── authService.py       # Username/password registration and login logic
│   │   ├── githubAuthService.py # GitHub OAuth flow (state, code exchange, user upsert)
│   │   ├── githubService.py     # GitHub Events API calls, event caching and watermarking
│   │   ├── repoStoreService.py  # Redis CRUD for tracked repos and event storage
│   │   └── websocketService.py  # WebSocket connection handler with Redis pub/sub listener
│   └── dependencies/
│       └── db.py                # get_db dependency for SQLAlchemy session injection
├── Dockerfile                   # Single image used for all three services
├── docker-compose.yaml          # Runs uvicorn, celery worker, and celery beat
├── entrypoint.sh                # Shell script that starts all three processes in one container
├── requirements.txt             # All Python dependencies
└── .env                         # Environment variables (not committed)
```

---

## API Endpoints

### Auth (`/auth`)

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Login with username and password, returns JWT |
| GET | `/auth/github/login` | Redirects to GitHub OAuth authorization |
| GET | `/auth/github/callback` | Handles OAuth callback, issues JWT, redirects to frontend |

All `/github/*` and `/ws` routes require a valid JWT in the `Authorization: Bearer <token>` header.

### GitHub (`/github`)

| Method | Path | Description |
|---|---|---|
| POST | `/github/track` | Start tracking a repository. Body: `{ "repo": "owner/name" }` |
| GET | `/github/tracked` | Get all repos tracked by the current user with their cached events |
| DELETE | `/github/track` | Stop tracking a repository. Body: `{ "repo": "owner/name" }` |
| GET | `/github/{repo_name}/events` | Get cached events for a specific repository |

### WebSocket

| Path | Description |
|---|---|
| `ws://host/ws?repo_name=owner/repo&user_id=<id>` | Opens a real-time event stream for a repository |

On connection:
1. The repo is added to the user's tracked list
2. Existing cached events are sent immediately as the initial payload
3. The socket subscribes to the Redis channel `channel:events:<repo_name>`
4. Whenever the Celery worker publishes new events to that channel, they are forwarded to the client instantly

---

## How the Event Pipeline Works

1. **Tracking a repo**: When a user calls `POST /github/track`, the service fetches the current events from the GitHub Events API, stores them in Redis (`github:<repo>:events`), and records the highest event ID as a watermark (`github:<repo>:max_id`).

2. **Background polling**: Celery Beat fires `poll_tracked_repositories_events` every 10 seconds. This task calls `poll_repo_events` for every globally tracked repository (repositories tracked by at least one user).

3. **Watermarking**: `poll_repo_events` fetches the latest events from GitHub and filters out any events with an ID less than or equal to the stored watermark. Only genuinely new events are processed.

4. **Pub/Sub push**: If new events are found, they are saved to Redis and published to `channel:events:<repo_name>`.

5. **WebSocket delivery**: Any open WebSocket connections subscribed to that channel receive the new events in real time.

6. **Reference counting**: Redis tracks how many users are following each repository (`global:tracked_repos_refcount`). When the last user untracks a repository, all Redis keys for that repository (events, watermark, global set membership) are cleaned up.

---

## Environment Variables

Create a `.env` file in the project root. All variables are loaded by `pydantic-settings`.

```env
# GitHub personal access token for API calls (increases rate limit from 60 to 5000 req/hr)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Redis connection string (supports rediss:// for TLS)
REDIS_URL=redis://localhost:6379/0

# PostgreSQL connection string
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Secret key for signing JWT tokens (use a long random string in production)
SECRET_KEY=your-long-secret-key

# JWT algorithm
ALGORITHM=HS256

# Token lifetime in minutes
ACCESS_TOKEN_EXPIRE_MINUTES=180

# GitHub OAuth App credentials
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# The callback URL registered in your GitHub OAuth App settings
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/auth/github/callback

# The frontend URL where the user is redirected after GitHub OAuth completes
FRONTEND_URL=http://localhost:5173
```

### Setting up a GitHub OAuth App

1. Go to **GitHub Settings > Developer settings > OAuth Apps > New OAuth App**
2. Set **Homepage URL** to `http://localhost:5173`
3. Set **Authorization callback URL** to `http://localhost:8000/auth/github/callback`
4. Copy the **Client ID** and generate a **Client Secret**, then paste them into your `.env`

---

## Running Locally (Without Docker)

### Prerequisites

- Python 3.11+
- PostgreSQL (running and accessible)
- Redis (running on `localhost:6379` or update `REDIS_URL`)

### Steps

**1. Clone and install dependencies**

```bash
git clone <repo-url>
cd "Github Dashboard Backend"
python -m venv venv
venv\Scripts\activate      # Windows
# or: source venv/bin/activate  (macOS/Linux)
pip install -r requirements.txt
```

**2. Configure environment**

Copy the example and fill in your values:

```bash
cp .env.example .env
# Edit .env with your credentials
```

**3. Run the FastAPI server**

```bash
uvicorn app.main:app --reload --port 8000
```

**4. Run the Celery worker** (in a separate terminal)

```bash
celery -A app.core.celery worker --loglevel=info --pool=solo
```

The `--pool=solo` flag is required on Windows because Celery's default multiprocessing pool does not work there.

**5. Run Celery Beat** (in a third terminal)

```bash
celery -A app.core.celery beat --loglevel=info
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

## Running with Docker Compose

Docker Compose runs three services from a single image: `uvicorn`, `celery_worker`, and `celery_beat`. Redis and PostgreSQL must be accessible from within the containers. The `extra_hosts: host.docker.internal:host-gateway` setting allows the containers to reach services running on the host machine.

**1. Make sure your `.env` is configured**

For the DATABASE_URL, replace `localhost` with `host.docker.internal` so containers can reach your host's PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@host.docker.internal:5432/dbname
```

**2. Build and start**

```bash
docker-compose up --build
```

**3. Stop**

```bash
docker-compose down
```

The API will be available at `http://localhost:8000`.

---

## Database

The service uses PostgreSQL with a single `users` table managed by SQLAlchemy. The table is created automatically on startup via `Base.metadata.create_all(bind=engine)`.

### `users` table

| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-incremented primary key |
| `username` | String (unique) | Username for credential-based login |
| `password` | String | bcrypt-hashed password |
| `email` | String (unique) | User email address |
| `github_id` | String (unique, nullable) | GitHub user ID for OAuth users |
| `github_access_token` | String (nullable) | Stored GitHub OAuth token |
| `is_github_user` | Boolean | True when the account was created via GitHub OAuth |

GitHub OAuth users are assigned a randomly generated password so they still have a valid `password` field. They log in exclusively through the OAuth flow.

---

## Redis Key Schema

| Key | Type | Description |
|---|---|---|
| `user:<user_id>:tracked_repos` | Set | Repos tracked by a specific user |
| `global:tracked_repos` | Set | All repos tracked by at least one user |
| `global:tracked_repos_refcount` | Hash | `{ "owner/repo": count }` tracks how many users follow each repo |
| `github:<repo>:events` | String (JSON) | Cached list of up to 100 recent events |
| `github:<repo>:max_id` | String | The highest event ID seen so far (watermark) |
| `channel:events:<repo>` | Pub/Sub channel | New events are published here for WebSocket delivery |
| `oauth:state:<state>` | String | Short-lived (300s) CSRF state token for GitHub OAuth |

---

## Security Notes

- All protected routes require a valid JWT in the `Authorization: Bearer` header
- Passwords are hashed with bcrypt before storage
- GitHub OAuth uses a cryptographically random `state` parameter stored in Redis to prevent CSRF attacks. The state expires after 5 minutes
- JWT tokens are signed with HS256 using the `SECRET_KEY` from your `.env`
- Do not commit your `.env` file. The `.gitignore` already excludes it

---

## Testing

A basic test file is included:

```bash
python test_api.py
```

For interactive API exploration, visit `http://localhost:8000/docs` after starting the server.
