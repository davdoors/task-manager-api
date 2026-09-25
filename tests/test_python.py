"""Check the assignment's required API operations using requests.

Start the API first, then run:
    python tests/test_python.py

Each run creates two unique test users. Test tasks are removed afterwards;
the users remain because the API does not expose a user deletion endpoint.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import requests


def check(condition: bool, message: str) -> None:
    """Fail explicitly even when Python is run with optimization enabled."""
    if not condition:
        raise AssertionError(message)


def expect_status(response: requests.Response, expected: int) -> None:
    """Check HTTP status without printing credentials or response bodies."""
    check(
        response.status_code == expected,
        f"{response.request.method} {response.request.url}: "
        f"expected HTTP {expected}, received {response.status_code}.",
    )


def run_tests(base_url: str) -> None:
    """Exercise the required operations against a running local API."""
    base_url = base_url.rstrip("/")
    task_ids = []

    with requests.Session() as session:
        def request(method: str, path: str, **kwargs) -> requests.Response:
            # A timeout prevents the script from waiting indefinitely.
            return session.request(
                method, f"{base_url}{path}", timeout=10, **kwargs
            )

        # Authentication is setup for the protected task endpoints.
        suffix = uuid4().hex[:16]
        credentials = {
            "username": f"test_{suffix}",
            "password": f"Test password {suffix}!",
        }
        response = request(
            "POST", "/users",
            json={**credentials, "email": f"test_{suffix}@example.com"},
        )
        expect_status(response, 201)
        user = response.json()
        user_id = user["id"]
        check(type(user_id) is int and user_id > 0, "Expected a positive user ID.")
        check(user["username"] == credentials["username"], "Unexpected username.")
        check(not {"password", "password_hash"} & user.keys(), "User response exposes credentials.")
        expect_status(request("GET", "/users/me"), 401)
        expect_status(request("POST", "/auth/login", data={**credentials, "password": "wrong-password"}), 401)

        response = request("POST", "/auth/login", data=credentials)
        expect_status(response, 200)
        token = response.json()
        check(isinstance(token.get("access_token"), str) and bool(token["access_token"]), "Expected a nonempty access token.")
        check(token.get("token_type", "").lower() == "bearer", "Expected Bearer token type.")
        session.headers["Authorization"] = f"Bearer {token['access_token']}"
        response = request("GET", "/users/me")
        expect_status(response, 200)
        check(response.json() == user, "Authenticated identity differs from registered user.")
        print("PASS: registration, login, authenticated identity and invalid credentials.")

        try:
            # 1. Create a task with the required title, content and deadline.
            now = datetime.now(timezone.utc)
            future_deadline = now + timedelta(days=2)
            payload = {
                "title": "Assignment test task",
                "content": "Check the required task operations.",
                "deadline": future_deadline.isoformat(),
            }
            response = request("POST", "/tasks", json=payload)
            expect_status(response, 201)
            task_id = response.json()["id"]
            task_ids.append(task_id)
            print("PASS: create a task (201).")

            # 2. Retrieve the task and verify the response data, not only its status.
            response = request("GET", f"/tasks/{task_id}")
            expect_status(response, 200)
            task = response.json()
            for field in ("title", "content"):
                check(task[field] == payload[field], f"Unexpected {field}.")
            check(task["id"] == task_id, "Unexpected task ID.")
            check(task["user_id"] == user_id, "Unexpected task owner.")
            actual_deadline = datetime.fromisoformat(
                task["deadline"].replace("Z", "+00:00")
            )
            check(actual_deadline == future_deadline, "Unexpected deadline.")
            print("PASS: retrieve the task and verify its data (200).")

            # 3. Mark it as completed and verify the change was persisted.
            response = request(
                "PATCH", f"/tasks/{task_id}", json={"status": "Done"}
            )
            expect_status(response, 200)
            check(response.json()["status"] == "Done", "Task was not completed.")
            response = request("GET", f"/tasks/{task_id}")
            expect_status(response, 200)
            check(response.json()["status"] == "Done", "Status was not saved.")
            print("PASS: mark the task as completed and retrieve it (200).")

            # 4. Create an expired task and check the expired-task list.
            expired_payload = {
                "title": "Expired assignment test task",
                "content": "This task has a deadline in the past.",
                "deadline": (now - timedelta(days=2)).isoformat(),
            }
            response = request("POST", "/tasks", json=expired_payload)
            expect_status(response, 201)
            expired_id = response.json()["id"]
            task_ids.append(expired_id)

            response = request("GET", "/tasks/expired")
            expect_status(response, 200)
            expired_tasks = response.json()
            check(isinstance(expired_tasks, list), "Expected a list of tasks.")
            check(
                {item["id"] for item in expired_tasks} == {expired_id},
                "The expired-task list must include only the expired test task.",
            )
            check(
                expired_tasks[0]["content"] == expired_payload["content"],
                "Unexpected expired task content.",
            )
            print("PASS: retrieve expired tasks and exclude the future task (200).")

            # 5. The assignment explicitly requires an invalid request returning 400.
            response = request("PATCH", f"/tasks/{task_id}", json={})
            expect_status(response, 400)
            check(
                response.json().get("detail") == "At least one field must be provided.",
                "Unexpected error message for an empty update.",
            )
            print("PASS: reject an empty update (400).")
            # Every list must contain only the authenticated user's tasks.
            response = request("GET", "/tasks")
            expect_status(response, 200)
            tasks = response.json()
            check(isinstance(tasks, list), "Expected a task list.")
            check({item["id"] for item in tasks} == set(task_ids), "Unexpected task list.")
            check(all(item["user_id"] == user_id for item in tasks), "Unexpected task owner in list.")
            print("PASS: list all tasks belonging to the current user.")

            # A second session prevents credentials from leaking between users.
            with requests.Session() as other:
                def other_request(method: str, path: str, **kwargs) -> requests.Response:
                    return other.request(method, f"{base_url}{path}", timeout=10, **kwargs)

                other_credentials = {
                    "username": f"other_{suffix}",
                    "password": f"Other test password {suffix}!",
                }
                response = other_request("POST", "/users", json={
                    **other_credentials, "email": f"other_{suffix}@example.com",
                })
                expect_status(response, 201)
                other_id = response.json()["id"]
                check(other_id != user_id, "Users must have distinct IDs.")
                response = other_request("POST", "/auth/login", data=other_credentials)
                expect_status(response, 200)
                other.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
                for path in ("/tasks", "/tasks/expired"):
                    response = other_request("GET", path)
                    expect_status(response, 200)
                    check(response.json() == [], "Another user's tasks are visible.")
                expect_status(other_request("GET", f"/tasks/{task_id}"), 404)
                expect_status(other_request("PATCH", f"/tasks/{task_id}", json={"title": "Unauthorized change"}), 404)
                expect_status(other_request("DELETE", f"/tasks/{task_id}"), 404)

            response = request("GET", f"/tasks/{task_id}")
            expect_status(response, 200)
            check(response.json()["title"] == payload["title"], "Unauthorized update changed the task.")
            check(response.json()["status"] == "Done", "Unexpected task status after isolation checks.")
            print("PASS: users cannot list, read, modify or delete another user's tasks.")

            # Invalid input must leave the existing task unchanged.
            before = response.json()
            for invalid in (
                {"status": "Completed"}, {"priority": "Urgent"},
                {"title": "   "}, {"title": None}, {"user_id": other_id},
                {"deadline": "2030-01-01T12:00:00"},
            ):
                expect_status(request("PATCH", f"/tasks/{task_id}", json=invalid), 422)
            response = request("GET", f"/tasks/{task_id}")
            expect_status(response, 200)
            check(response.json() == before, "Rejected updates changed the task.")
            print("PASS: invalid updates return 422 without changing stored data.")

            # DELETE is a test in its own right, not just best-effort cleanup.
            response = request("DELETE", f"/tasks/{task_id}")
            expect_status(response, 204)
            check(response.content == b"", "DELETE must return an empty body.")
            task_ids.remove(task_id)
            expect_status(request("GET", f"/tasks/{task_id}"), 404)
            expect_status(request("PATCH", f"/tasks/{task_id}", json={"status": "Done"}), 404)
            expect_status(request("DELETE", f"/tasks/{task_id}"), 404)
            response = request("GET", "/tasks")
            expect_status(response, 200)
            check({item["id"] for item in response.json()} == {expired_id}, "Deleted task is still listed.")
            print("PASS: deletion returns an empty 204; missing resources return 404.")
        finally:
            # Attempt every cleanup even if one fails. Preserve any original failure.
            original_error = sys.exc_info()[1]
            cleanup_errors = []
            for task_id in task_ids:
                try:
                    response = request("DELETE", f"/tasks/{task_id}")
                    expect_status(response, 204)
                    check(response.content == b"", "Cleanup DELETE must have no body.")
                    expect_status(request("GET", f"/tasks/{task_id}"), 404)
                except (requests.RequestException, AssertionError) as exc:
                    cleanup_errors.append(f"Task {task_id}: {exc}")
            if cleanup_errors:
                message = "Cleanup failed: " + "; ".join(cleanup_errors)
                if original_error is not None:
                    print(f"FAIL: {message}", file=sys.stderr)
                else:
                    raise AssertionError(message)

    print("All assignment checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        run_tests(args.base_url)
    except (requests.RequestException, AssertionError, KeyError, ValueError) as exc:
        raise SystemExit(f"FAIL: {exc}") from exc
