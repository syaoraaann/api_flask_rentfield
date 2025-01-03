from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, decode_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import logging

from helper.db_helper import get_connection

# Setup untuk bcrypt dan Blueprint
bcrypt = Bcrypt()
auth_endpoints = Blueprint('auth', __name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Route untuk membaca data user
@auth_endpoints.route('/read', methods=['GET'])
def read():
    """Routes for module get list auth"""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        select_query = "SELECT * FROM users"
        cursor.execute(select_query)
        results = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
    return jsonify({"message": "OK", "datas": results}), 200


# Route untuk login
@auth_endpoints.route('/login', methods=['POST'])
def login():
    """Routes for authentication"""
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s AND deleted_at IS NULL"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not bcrypt.check_password_hash(user.get('password'), password):
        return jsonify({"msg": "Incorrect password"}), 401

    # Ambil role dari database
    role = user.get('role')
    print(role)

    # Buat access token
    access_token = create_access_token(
        identity={'username': username}, additional_claims={'roles': role})
    decoded_token = decode_token(access_token)
    expires = decoded_token['exp']

    return jsonify({
        "access_token": access_token,
        "expires_in": expires,
        "type": "Bearer",
        "username": user.get('username'),
        "role": role
    })


# Route untuk registrasi user baru
@auth_endpoints.route('/register', methods=['POST'])
def register():
    """Routes for register"""
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    connection = get_connection()
    try:
        cursor = connection.cursor()
        insert_query = "INSERT INTO users (username, password, role) values (%s, %s, %s)"
        request_insert = (username, hashed_password, role)
        cursor.execute(insert_query, request_insert)
        connection.commit()
        new_id = cursor.lastrowid
    finally:
        cursor.close()
        connection.close()

    if new_id:
        return jsonify({"message": "OK",
                        "description": "User created",
                        "username": username}), 201
    return jsonify({"message": "Failed, cant register user"}), 501


# Route untuk reset password
@auth_endpoints.route('/reset-password', methods=['POST'])
def reset_password():
    """Routes for resetting password"""
    # Ambil data dari request
    username = request.form['username']
    new_password = request.form['new_password']

    # Hash password baru
    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

    # Cek apakah username ada dalam database
    connection = get_connection()
    try:
        cursor = connection.cursor()
        check_user_query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(check_user_query, (username,))
        user = cursor.fetchone()

        if user:
            update_query = "UPDATE users SET password = %s WHERE username = %s"
            cursor.execute(update_query, (hashed_password, username))
            connection.commit()
        else:
            return jsonify({"message": "Failed", "description": "User not found"}), 404
    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": "OK", "description": "Password updated successfully"}), 200


# Route untuk logout
@auth_endpoints.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Routes for logging out the user"""
    current_user = get_jwt_identity()

    # Log aktivitas logout
    logger.info(f"User {current_user['username']} logged out")

    # Biasanya untuk logout, cukup beri tahu client untuk menghapus tokennya.
    # Jika Anda ingin mengimplementasikan blacklist, Anda bisa menyimpan token yang dicabut.
    return jsonify({"message": "Successfully logged out", "user": current_user}), 200
