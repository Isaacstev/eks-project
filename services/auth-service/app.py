from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
import psycopg2
import psycopg2.extras
import uuid
from functools import wraps
import logging

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(days=7)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'ecommerce_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.connection.autocommit = True
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_cursor(self):
        if not self.connection or self.connection.closed:
            if not self.connect():
                return None
        return self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    def close(self):
        if self.connection and not self.connection.closed:
            self.connection.close()

db = DatabaseConnection()

# JWT token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            
            # Get user from database
            cursor = db.get_cursor()
            if not cursor:
                return jsonify({'error': 'Database connection failed'}), 500
                
            cursor.execute(
                "SELECT id, email, first_name, last_name, role, is_active FROM users WHERE id = %s",
                (current_user_id,)
            )
            current_user = cursor.fetchone()
            
            if not current_user or not current_user['is_active']:
                return jsonify({'error': 'User not found or inactive'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = 'connected' if db.connect() else 'disconnected'
    return jsonify({
        'status': 'healthy',
        'service': 'auth-service',
        'database': db_status,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        phone = data.get('phone', '').strip()
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, phone)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, email, first_name, last_name, role, created_at
        """, (user_id, email, password_hash, first_name, last_name, phone))
        
        user = cursor.fetchone()
        
        # Generate JWT token
        token_payload = {
            'user_id': user['id'],
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role']
            },
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get user from database
        cursor.execute("""
            SELECT id, email, password_hash, first_name, last_name, role, is_active
            FROM users WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        
        if not user or not user['is_active']:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check password
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate JWT token
        token_payload = {
            'user_id': user['id'],
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + app.config['JWT_EXPIRATION_DELTA']
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role']
            },
            'token': token
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get current user profile"""
    return jsonify({
        'user': {
            'id': current_user['id'],
            'email': current_user['email'],
            'first_name': current_user['first_name'],
            'last_name': current_user['last_name'],
            'role': current_user['role']
        }
    })

@app.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update current user profile"""
    try:
        data = request.get_json()
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        allowed_fields = ['first_name', 'last_name', 'phone']
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        update_values.append(current_user['id'])
        
        query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, email, first_name, last_name, phone, role
        """
        
        cursor.execute(query, update_values)
        updated_user = cursor.fetchone()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': dict(updated_user)
        })
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'error': 'Profile update failed'}), 500

@app.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get current password hash
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (current_user['id'],))
        user_data = cursor.fetchone()
        
        # Verify current password
        if not check_password_hash(user_data['password_hash'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_password_hash, current_user['id']))
        
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({'error': 'Password change failed'}), 500

@app.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token validity"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'valid': False, 'error': 'Token is missing'}), 401
    
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        return jsonify({
            'valid': True,
            'user_id': data['user_id'],
            'email': data['email'],
            'role': data['role']
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Token is invalid'}), 401

if __name__ == '__main__':
    print("🔐 Starting Authentication Service...")
    print("📡 Endpoints available:")
    print("   POST /register         - User registration")
    print("   POST /login           - User login")
    print("   GET  /profile         - Get user profile")
    print("   PUT  /profile         - Update user profile")
    print("   POST /change-password - Change password")
    print("   POST /verify-token    - Verify JWT token")
    print("   GET  /health          - Health check")
    print("🌐 Access at: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
