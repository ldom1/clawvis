"""Run the API server: python -m kanban_api or kanban-api."""

import uvicorn


def main():
    uvicorn.run("kanban_api.server:app", host="0.0.0.0", port=8090)


if __name__ == "__main__":
    main()
