"""Routes for module auth"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, decode_token
from flask_bcrypt import Bcrypt

from helper.db_helper import get_connection

bcrypt = Bcrypt()
auth_endpoints = Blueprint('auth', __name__)

@auth_endpoints.route('/read', methods=['GET'])
def read():
    """Routes for module get list auth"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    select_query = "SELECT * FROM users"
    cursor.execute(select_query)
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify({"message": "OK", "datas": results}), 200


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

    # Buat access token
    access_token = create_access_token(
        identity={'username': username, 'role': role}
    )
    decoded_token = decode_token(access_token)
    expires = decoded_token['exp']

    return jsonify({
        "access_token": access_token,
        "expires_in": expires,
        "type": "Bearer",
        "username": user.get('username'),
        "role": role
    })


@auth_endpoints.route('/register', methods=['POST'])
def register():
    """Routes for register"""
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    connection = get_connection()
    cursor = connection.cursor()
    insert_query = "INSERT INTO users (username, password, role) values (%s, %s, %s)"
    request_insert = (username, hashed_password, role)
    cursor.execute(insert_query, request_insert)
    connection.commit()
    cursor.close()
    new_id = cursor.lastrowid
    if new_id:
        return jsonify({"message": "OK",
                        "description": "User created",
                        "username": username}), 201
    return jsonify({"message": "Failed, cant register user"}), 501

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
    cursor = connection.cursor()

    # Query untuk cek apakah user dengan username tersebut ada
    check_user_query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(check_user_query, (username,))
    user = cursor.fetchone()

    if user:
        # Jika user ditemukan, update password
        update_query = "UPDATE users SET password = %s WHERE username = %s"
        cursor.execute(update_query, (hashed_password, username))
        connection.commit()
        cursor.close()
        
        # Mengembalikan respons sukses
        return jsonify({"message": "OK", "description": "Password updated successfully"}), 200
    else:
        cursor.close()
        # Jika user tidak ditemukan
        return jsonify({"message": "Failed", "description": "User not found"}), 404