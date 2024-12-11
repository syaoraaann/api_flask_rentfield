"""Static endpoint to show image"""
from flask import Blueprint, send_from_directory

static_file_server = Blueprint('static_file_server', __name__)
UPLOAD_FOLDER = 'img'


@static_file_server.route("/show_image/<image_name>", methods=["GET"])
def show_image(image_name):
    """Show file"""
    return send_from_directory(UPLOAD_FOLDER, image_name)
