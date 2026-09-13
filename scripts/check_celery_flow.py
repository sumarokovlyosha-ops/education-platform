from app.celery_app import celery_app


def main() -> None:
    result = celery_app.send_task("app.tasks.health.ping")
    print("TASK ID:", result.id, flush=True)

    response = result.get(timeout=15)

    if response != "pong":
        raise RuntimeError(f"Unexpected task result: {response!r}")

    print("Result:", response)
    result.forget()
    print("Celery check passed")


if __name__ == "__main__":
    main()
