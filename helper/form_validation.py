"""Helper to validate form request required"""
from flask import request, jsonify
from werkzeug.exceptions import BadRequest


def get_form_data(required_fields):
    """
    Extracts form data and performs basic validation.

    Args:
        required_fields (list): A list of strings representing the required form fields.

    Returns:
        dict: A dictionary containing the extracted form data or raises a BadRequest exception.

    Raises:
        BadRequest: If any required field is missing or empty.
    """

    data = {}
    for field in required_fields:
        field_value = request.form.get(field)
        if not field_value:
            err_message = jsonify(
                {"err_message": f"Missing required field: {field}"})
            raise BadRequest(response=err_message)
        data[field] = field_value

    return data
