from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import logging

from helper.db_helper import get_connection

# Setup bcrypt and Blueprint
bcrypt = Bcrypt()
list_field_endpoints = Blueprint('list_field', __name__)  # Blueprint name corrected for clarity

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Route to read user data
@list_field_endpoints.route('/read', methods=['GET'])
@jwt_required()
def read():
    """
    Route to fetch all data from the list_field table.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        select_query = "SELECT * FROM list_field"
        cursor.execute(select_query)
        results = cursor.fetchall()
        logger.info("Fetched data from list_field successfully.")
    except Exception as e:
        logger.error(f"Error fetching data from list_field: {str(e)}")
        return jsonify({"message": "Error fetching data", "error": str(e)}), 500
    finally:
        # Ensure resources are released even in case of an error
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return jsonify({"message": "OK", "data": results}), 200

@list_field_endpoints.route('/create', methods=['POST'])
@jwt_required()
def create():
    """
    Route to create a new field in the `list_field` table using form-data.
    """
    try:
        # Get required fields from the form
        field_name = request.form.get("field_name")
        address = request.form.get("address")

        # Ensure required fields are present
        if not field_name or not address:
            return jsonify({"message": "Missing required fields: field_name or address"}), 400

        # Get optional fields from the form (using .get to avoid key errors)
        description = request.form.get("description", "")  # Default to empty string if not provided
        field_type = request.form.get("field_type", "Unknown")  # Default to "Unknown" if not provided
        capacity = request.form.get("capacity", 0)  # Default to 0 if not provided
        price = request.form.get("price", 0.0)  # Default to 0.0 if not provided
        image_url = request.form.get("image_url", "")  # Default to empty string if not provided

        # Database connection (use context manager for proper resource handling)
        connection = get_connection()
        cursor = connection.cursor()

        # Insert query
        insert_query = """
        INSERT INTO list_field (field_name, address, description, field_type, capacity, price, image_url) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (field_name, address, description, field_type, capacity, price, image_url))
        connection.commit()  # Commit changes to the database

        # Get the newly inserted field ID
        new_id = cursor.lastrowid
        cursor.close()

        # Check if insertion was successful
        if new_id:
            return jsonify({
                "message": "Field created successfully",
                "id_field": new_id,
                "field_name": field_name
            }), 201
        return jsonify({"message": "Cannot insert data"}), 500

    except ValueError as ve:
        # Handle missing required fields or invalid data
        return jsonify({"message": "Validation error", "error": str(ve)}), 400
    except Exception as e:
        # Handle other errors
        return jsonify({"message": "Error creating field", "error": str(e)}), 500

@list_field_endpoints.route('/update/<id_field>', methods=['PUT'])
@jwt_required()
def update(id_field):
    """
    Route to update a specific field in the list_field table.
    """
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        # Check if the data exists
        check_query = "SELECT * FROM list_field WHERE id_field = %s"
        cursor.execute(check_query, (id_field,))
        existing_field = cursor.fetchone()

        if not existing_field:
            logger.warning(f"Data with id_field {id_field} not found.")
            return jsonify({"error": "Data not found or has been deleted"}), 404

        # If data is found, proceed with the update
        data = request.get_json()

        field_name = data.get('field_name')
        address = data.get('address')
        description = data.get('description')
        field_type = data.get('field_type')
        price = data.get('price')
        image_url = data.get('image_url')

        # Check if all required fields are provided
        if not all([field_name, address, description, field_type, price, image_url]):
            return jsonify({"error": "All fields must be provided"}), 400

        # Prepare the update query
        update_query = """
        UPDATE list_field
        SET field_name=%s, address=%s, description=%s, field_type=%s, price=%s, image_url=%s
        WHERE id_field=%s
        """
        update_request = (field_name, address, description, field_type, price, image_url, id_field)
        cursor.execute(update_query, update_request)
        connection.commit()

        logger.info(f"Updated data for id_field {id_field}.")
        return jsonify({"message": "Updated successfully", "id_field": id_field}), 200

    except Exception as e:
        logger.error(f"Error updating data for id_field {id_field}: {str(e)}")
        return jsonify({"message": "Error updating data", "error": str(e)}), 500

    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@list_field_endpoints.route('/delete/<int:id_field>', methods=['DELETE'])
@jwt_required()
def delete(id_field):
    """
    Route to delete a field from the `list_field` table.a
    """
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)

        # Check if the record exists
        check_query = "SELECT * FROM list_field WHERE id_field = %s"
        cursor.execute(check_query, (id_field,))
        existing_field = cursor.fetchone()

        if not existing_field:
            logger.warning(f"Field with ID {id_field} not found.")
            return jsonify({"message": "Field not found or already deleted"}), 404

        # Proceed with deletion
        delete_query = "DELETE FROM list_field WHERE id_field = %s"
        cursor.execute(delete_query, (id_field,))
        connection.commit()

        logger.info(f"Deleted field with ID {id_field}.")
        return jsonify({"message": "Field deleted successfully", "id_field": id_field}), 200
    except Exception as e:
        logger.error(f"Error deleting field with ID {id_field}: {str(e)}")
        return jsonify({"message": "Error deleting field", "error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

