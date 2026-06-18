import asyncio
import httpx
import time
from app.main import app

async def test_health(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("[OK] Health check endpoint passed")

async def test_auth(client):
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    email = f"test_{timestamp}@example.com"
    password = "testpassword123"

    # Register
    resp = await client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert resp.status_code in [200, 201], f"Registration failed: {resp.text}"
    print("[OK] Register user passed")

    # Login
    resp = await client.post("/auth/login", data={
        "username": username,
        "password": password
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token_data = resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    print("[OK] Login user passed")

    # Set Authorization header for subsequent requests
    client.headers.update({"Authorization": f"Bearer {token}"})

async def test_tracking(client):
    repo = "fastapi/fastapi"
    response = await client.post("/github/track", json={"repo": repo})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "events" in data
    print("[OK] Track repo endpoint passed")

    response = await client.get("/github/tracked")
    assert response.status_code == 200
    tracked_data = response.json()
    assert "tracked_repositories" in tracked_data
    assert repo in tracked_data["tracked_repositories"]
    print("[OK] Tracked list (with events) endpoint passed")

    response = await client.get(f"/github/{repo}/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    print("[OK] Get repo events endpoint passed")

    response = await client.request("DELETE", "/github/track", json={"repo": repo})
    assert response.status_code == 200
    untrack_data = response.json()
    assert untrack_data["status"] == "success"
    assert untrack_data["message"] == f"Stopped tracking {repo}"
    print("[OK] Untrack repo (DELETE) endpoint passed")

    response = await client.get("/github/tracked")
    assert response.status_code == 200
    tracked_data_after = response.json()
    assert repo not in tracked_data_after["tracked_repositories"]
    print("[OK] Untracked verification endpoint passed")

async def main():
    print("Starting API integration tests...\n")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        await test_health(client)
        await test_auth(client)
        await test_tracking(client)
    print("\nAll HTTP tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
