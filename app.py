"""Small apps to demonstrate endpoints with basic feature - CRUD"""

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import jwt
from api.auth.endpoints import auth_endpoints
from api.data_protected.endpoints import protected_endpoints
from api.list_field.endpoints import list_field_endpoints
from api.booking.endpoint import booking_endpoints
from config import Config
from static.static_file_server import static_file_server


# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)


jwt.init_app(app)

# register the blueprint
app.register_blueprint(auth_endpoints, url_prefix='/api/v1/auth')
app.register_blueprint(list_field_endpoints, url_prefix='/api/v1/list_field')
app.register_blueprint(booking_endpoints, url_prefix='/api/v1/booking')
app.register_blueprint(protected_endpoints, url_prefix='/api/v1/protected')
app.register_blueprint(static_file_server, url_prefix='/static/')


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
