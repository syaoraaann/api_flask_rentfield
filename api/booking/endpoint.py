from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import Bcrypt
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from helper.db_helper import get_connection

# Setup bcrypt and Blueprint
bcrypt = Bcrypt()
booking_endpoints = Blueprint('booking', __name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@booking_endpoints.route('/read', methods=['GET'])
@jwt_required()
def read():
    """
    Route to fetch all bookings.
    """
    identity = get_jwt_identity()
    id_users = identity.get('id_users')
    jwt_claims = get_jwt()
    role = jwt_claims.get('roles')

    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        if role == 'Owner':
            query = "SELECT * FROM booking WHERE id_users = %s"
            cursor.execute(query, (id_users,))
        else:
            query = "SELECT * FROM booking"
            cursor.execute(query)
        results = cursor.fetchall()
        logger.info(f"Fetched bookings for role {role}.")
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        return jsonify({"message": "Error fetching bookings", "error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": "OK", "data": results}), 200

@booking_endpoints.route('/read_by_owner', methods=['GET'])
@jwt_required()
def get_bookings_by_owner():
    connection = None
    cursor = None
    try:
        # Ambil id_users dan role dari JWT
        identity = get_jwt_identity()
        if not identity:
            return jsonify({"message": "Invalid token. Identity not found."}), 401
        
        id_users = identity.get('id_users')
        jwt_claims = get_jwt()  # Mengambil additional_claims dari token JWT
        role = jwt_claims.get('roles')  # Ambil roles dari klaim tambahan

        if role != "Owner":
            return jsonify({"message": "Access denied. Only owners can view this data."}), 403

        # Buka koneksi ke database
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Ambil data booking berdasarkan id_field yang dimiliki owner
        select_query = """
        SELECT 
            b.id_booking, 
            b.booking_date, 
            b.start_time, 
            b.end_time, 
            b.total_price, 
            b.status, 
            lf.field_name
        FROM 
            booking b
        JOIN 
            list_field lf ON b.id_field = lf.id_field
        WHERE 
            lf.id_users = %s
        ORDER BY 
            b.booking_date DESC, b.start_time ASC
        """
        cursor.execute(select_query, (id_users,))
        bookings = cursor.fetchall()

        # Cek apakah ada hasil
        if not bookings:
            return jsonify({"message": "No bookings found for this owner."}), 404

        # Format the results
        for booking in bookings:
            # Format datetime fields
            if isinstance(booking['booking_date'], datetime):
                booking['booking_date'] = booking['booking_date'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(booking['start_time'], datetime):
                booking['start_time'] = booking['start_time'].strftime('%H:%M:%S')
            if isinstance(booking['end_time'], datetime):
                booking['end_time'] = booking['end_time'].strftime('%H:%M:%S')

            # If the time fields are timedelta, convert to hours and format as HH:MM:SS
            if isinstance(booking['start_time'], timedelta):
                hours = booking['start_time'].seconds // 3600
                minutes = (booking['start_time'].seconds // 60) % 60
                booking['start_time'] = f"{hours:02}:{minutes:02}:00"
            if isinstance(booking['end_time'], timedelta):
                hours = booking['end_time'].seconds // 3600
                minutes = (booking['end_time'].seconds // 60) % 60
                booking['end_time'] = f"{hours:02}:{minutes:02}:00"

            # Format total_price with 3 decimal places
            if isinstance(booking['total_price'], Decimal):
                booking['total_price'] = f"{booking['total_price']:.3f}"

        return jsonify(bookings), 200

    except Exception as e:
        return jsonify({"message": "Error fetching bookings", "error": str(e)}), 500

    finally:
        # Pastikan koneksi database ditutup
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
@booking_endpoints.route('/create', methods=['POST'])
@jwt_required()
def create_booking():
    """
    Route to create a new booking using form-data.
    """
    connection = None
    cursor = None

    try:
        # Ambil identitas pengguna dari JWT
        identity = get_jwt_identity()
        id_users = identity.get('id_users')  # Renter yang membuat booking

        # Ambil data dari form
        id_field = request.form.get("id_field")
        booking_date = request.form.get("booking_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        # Validasi input wajib
        if not id_field or not booking_date or not start_time or not end_time:
            return jsonify({"message": "Missing required fields"}), 400

        # Hitung durasi booking dalam jam
        fmt = "%H:%M:%S"  # Format waktu
        start_dt = datetime.strptime(start_time, fmt)
        end_dt = datetime.strptime(end_time, fmt)
        duration = (end_dt - start_dt).seconds / 3600  # Konversi ke jam

        if duration <= 0:
            return jsonify({"message": "Invalid booking duration"}), 400

        # Buka koneksi database
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        # Ambil harga per jam dan id_owner dari tabel list_field
        select_field_query = """
        SELECT 
            lf.price, 
            u.id_users AS id_owner 
        FROM 
            list_field lf 
        JOIN 
            users u ON lf.id_users = u.id_users 
        WHERE 
            lf.id_field = %s AND u.role = 'OWNER'
        """
        cursor.execute(select_field_query, (id_field,))
        field = cursor.fetchone()

        if not field:
            return jsonify({"message": "Field not found or no owner assigned"}), 404

        price_per_hour = field["price"]
        id_owner = field["id_owner"]
        total_price = Decimal(price_per_hour) * Decimal(duration)

        # Tentukan status booking
        today_date = datetime.now().date()
        booking_status = "UPCOMING" if datetime.strptime(booking_date, "%Y-%m-%d").date() > today_date else "ONGOING"

        # Simpan booking ke database
        insert_booking_query = """
        INSERT INTO booking (id_field, id_users, booking_date, start_time, end_time, total_price, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_booking_query, (id_field, id_users, booking_date, start_time, end_time, total_price, booking_status))
        connection.commit()

        # Ambil ID booking yang baru dibuat
        new_booking_id = cursor.lastrowid

        # Format total_price menjadi tiga digit desimal
        formatted_total_price = f"{total_price:.3f}"

        # Kembalikan respons berhasil
        return jsonify({
            "message": "Booking created successfully",
            "id_booking": new_booking_id,
            "total_price": formatted_total_price,
            "status": booking_status,
            "id_owner": id_owner
        }), 201

    except Exception as e:
        # Tangani error
        return jsonify({"message": "Error creating booking", "error": str(e)}), 500

    finally:
        # Tutup cursor dan koneksi
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@booking_endpoints.route('/update/<int:id_booking>', methods=['PUT'])
@jwt_required()
def update(id_booking):
    """
    Route to update an existing booking.
    """
    try:
        data = request.get_json()
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        check_query = "SELECT * FROM booking WHERE id_booking = %s"
        cursor.execute(check_query, (id_booking,))
        existing_booking = cursor.fetchone()

        if not existing_booking:
            return jsonify({"error": "Booking not found"}), 404

        update_query = """
        UPDATE booking
        SET booking_date=%s, start_time=%s, end_time=%s, status=%s, total_price=%s
        WHERE id_booking=%s
        """
        cursor.execute(update_query, (
            data.get('booking_date'), data.get('start_time'),
            data.get('end_time'), data.get('status'),
            data.get('total_price'), id_booking
        ))
        connection.commit()

        return jsonify({"message": "Booking updated successfully", "id_booking": id_booking}), 200
    except Exception as e:
        return jsonify({"message": "Error updating booking", "error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@booking_endpoints.route('/delete/<int:id_booking>', methods=['DELETE'])
@jwt_required()
def delete(id_booking):
    """
    Route to delete a booking.
    """
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        check_query = "SELECT * FROM booking WHERE id_booking = %s"
        cursor.execute(check_query, (id_booking,))
        existing_booking = cursor.fetchone()

        if not existing_booking:
            return jsonify({"message": "Booking not found"}), 404

        delete_query = "DELETE FROM booking WHERE id_booking = %s"
        cursor.execute(delete_query, (id_booking,))
        connection.commit()

        return jsonify({"message": "Booking deleted successfully", "id_booking": id_booking}), 200
    except Exception as e:
        return jsonify({"message": "Error deleting booking", "error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()
