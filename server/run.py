import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Use PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get("PORT", 10000))

    # In production (like on Render), you typically don't want to run in debug mode
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    app.run(host="0.0.0.0", port=port, debug=debug)
