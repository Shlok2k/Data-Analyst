from app import app
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# This is the application that Gunicorn will use
application = app.server

# For local development
if __name__ == "__main__":
    from waitress import serve
    print("Starting production server...")
    print("Server will be available at:")
    print("http://127.0.0.1:8050")
    print("http://192.168.29.243:8050")
    print("Press CTRL+C to stop the server")
    serve(application, host='0.0.0.0', port=8050, threads=4) 