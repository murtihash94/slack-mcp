"""Entry point for running the Slack MCP server locally."""

import uvicorn


def main():
    """Run the server locally with uvicorn."""
    uvicorn.run(
        "slack_server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
