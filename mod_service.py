from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import sqlite3
from flasgger import Swagger, swag_from

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'le renard saute la barriere'  # Set a secure key here
jwt = JWTManager(app)
app.config['SWAGGER'] = {
    'title': 'Parking Ticket API',
    'uiversion': 3
}
swagger = Swagger(app)

def connect_db():
    return sqlite3.connect('parking_tickets.db')

# First Route: Retrieve Outstanding Tickets
@app.route('/tickets/<string:license_plate>', methods=['GET'])
@jwt_required()
def get_tickets(license_plate):
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch outstanding tickets based on license plate
    cursor.execute("SELECT * FROM tickets WHERE license_plate = ? AND paid = 0", (license_plate,))
    tickets = cursor.fetchall()
    conn.close()
    # Check if any tickets were found
    if not tickets:
        return jsonify({"message": "No outstanding tickets found for this license plate."}), 404

    # Structure response
    response = [{'ticket_id': t[0], 'license_plate': t[1], 'amount': t[2]} for t in tickets]

    return jsonify(response), 200


@app.route('/tickets/pay', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Tickets'],
    'description': 'Pay a ticket',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'ticket_id': {'type': 'integer', 'example': 1},
                    'amount': {'type': 'number', 'example': 100.0}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Ticket paid successfully'},
        400: {'description': 'Invalid request or payment issue'},
        404: {'description': 'Ticket not found'}
    }
})
def pay_ticket():
    # Parse JSON data from request
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    payment_amount = data.get('amount')

    if not ticket_id or not payment_amount:
        return jsonify({"error": "Missing ticket_id or amount in the request"}), 400

    conn = connect_db()
    cursor = conn.cursor()

    # Check if the ticket exists and is unpaid
    cursor.execute("SELECT amount, paid FROM tickets WHERE ticket_id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    if not ticket:
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404
    if ticket[1] == 1:
        conn.close()
        return jsonify({"error": "Ticket has already been paid"}), 400
    if payment_amount < ticket[0]:
        conn.close()
        return jsonify({"error": "Insufficient payment amount"}), 400

    # Mark ticket as paid
    cursor.execute("UPDATE tickets SET paid = 1 WHERE ticket_id = ?", (ticket_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Ticket paid successfully"}), 200


# User registration route
@app.route('/register', methods=['POST'])
@swag_from({
    'tags': ['Users'],
    'description': 'Register a new user',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'example': 'user1'},
                    'password': {'type': 'string', 'example': 'password123'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'User registered successfully'},
        400: {'description': 'Username already exists or missing data'}
    }
})
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    password_hash = generate_password_hash(password)
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "User registered successfully"}), 201


# User login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user is None or not check_password_hash(user[1], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Generate JWT
    access_token = create_access_token(identity=user[0])  # Use user ID as identity
    return jsonify(access_token=access_token), 200

if __name__ == '__main__':
    app.run(debug=True)