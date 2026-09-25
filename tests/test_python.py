"""Check the assignment's required API operations using requests.

Start the API first, then run:
    python tests/test_python.py

Each run creates a unique test user. Test tasks are removed afterwards;
the user remains because the API does not expose a user deletion endpoint.
"""

import argparse
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
        user_id = response.json()["id"]

        response = request("POST", "/auth/login", data=credentials)
        expect_status(response, 200)
        session.headers["Authorization"] = (
            f"Bearer {response.json()['access_token']}"
        )

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
        finally:
            # Remove only tasks created by this run, including after a failed check.
            for task_id in task_ids:
                try:
                    response = request("DELETE", f"/tasks/{task_id}")
                    if response.status_code not in (204, 404):
                        print(f"WARNING: could not remove test task {task_id}.")
                except requests.RequestException:
                    print(f"WARNING: could not remove test task {task_id}.")

    print("All assignment checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        run_tests(args.base_url)
    except (requests.RequestException, AssertionError, KeyError, ValueError) as exc:
        raise SystemExit(f"FAIL: {exc}") from exc
