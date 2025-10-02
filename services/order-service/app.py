from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras
import uuid
import logging
import requests
from datetime import datetime
from decimal import Decimal
import json

app = Flask(__name__)
CORS(app)

# Configuration
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5001')
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:5002')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://localhost:5004')

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

db = DatabaseConnection()

def verify_user_token(token):
    """Verify user token with auth service"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(f'{AUTH_SERVICE_URL}/verify-token', headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

def get_product_info(product_id):
    """Get product information from product service"""
    try:
        response = requests.get(f'{PRODUCT_SERVICE_URL}/products/{product_id}')
        if response.status_code == 200:
            return response.json()['product']
        return None
    except Exception as e:
        logger.error(f"Failed to get product info: {e}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = 'connected' if db.connect() else 'disconnected'
    return jsonify({
        'status': 'healthy',
        'service': 'order-service',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/cart', methods=['GET'])
def get_cart():
    """Get user's shopping cart"""
    try:
        # Get auth token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header[7:]
        user_info = verify_user_token(token)
        if not user_info or not user_info.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['user_id']
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get or create cart
        cursor.execute("SELECT id FROM shopping_carts WHERE user_id = %s", (user_id,))
        cart = cursor.fetchone()
        
        if not cart:
            # Create new cart
            cart_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO shopping_carts (id, user_id) 
                VALUES (%s, %s)
                RETURNING id
            """, (cart_id, user_id))
            cart = cursor.fetchone()
        
        cart_id = cart['id']
        
        # Get cart items with product information
        cursor.execute("""
            SELECT ci.*, p.name, p.description, p.images, p.stock_quantity
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.cart_id = %s AND p.is_active = true
            ORDER BY ci.created_at DESC
        """, (cart_id,))
        
        cart_items = cursor.fetchall()
        
        # Calculate totals
        subtotal = sum(Decimal(str(item['unit_price'])) * item['quantity'] for item in cart_items)
        
        return jsonify({
            'cart_id': cart_id,
            'items': [dict(item) for item in cart_items],
            'item_count': len(cart_items),
            'subtotal': float(subtotal)
        })
        
    except Exception as e:
        logger.error(f"Get cart error: {e}")
        return jsonify({'error': 'Failed to get cart'}), 500

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to shopping cart"""
    try:
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header[7:]
        user_info = verify_user_token(token)
        if not user_info or not user_info.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['user_id']
        data = request.get_json()
        
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id or quantity <= 0:
            return jsonify({'error': 'Valid product_id and quantity required'}), 400
        
        # Get product information
        product = get_product_info(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        if product['stock_quantity'] < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get or create cart
        cursor.execute("SELECT id FROM shopping_carts WHERE user_id = %s", (user_id,))
        cart = cursor.fetchone()
        
        if not cart:
            cart_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO shopping_carts (id, user_id) 
                VALUES (%s, %s)
            """, (cart_id, user_id))
        else:
            cart_id = cart['id']
        
        # Check if item already exists in cart
        cursor.execute("""
            SELECT id, quantity FROM cart_items 
            WHERE cart_id = %s AND product_id = %s
        """, (cart_id, product_id))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item['quantity'] + quantity
            if product['stock_quantity'] < new_quantity:
                return jsonify({'error': 'Insufficient stock for requested quantity'}), 400
            
            cursor.execute("""
                UPDATE cart_items 
                SET quantity = %s, unit_price = %s
                WHERE id = %s
            """, (new_quantity, product['price'], existing_item['id']))
        else:
            # Add new item
            cursor.execute("""
                INSERT INTO cart_items (id, cart_id, product_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s, %s)
            """, (str(uuid.uuid4()), cart_id, product_id, quantity, product['price']))
        
        return jsonify({'message': 'Item added to cart successfully'})
        
    except Exception as e:
        logger.error(f"Add to cart error: {e}")
        return jsonify({'error': 'Failed to add item to cart'}), 500

@app.route('/cart/update', methods=['PUT'])
def update_cart_item():
    """Update cart item quantity"""
    try:
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header[7:]
        user_info = verify_user_token(token)
        if not user_info or not user_info.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['user_id']
        data = request.get_json()
        
        item_id = data.get('item_id')
        quantity = data.get('quantity', 1)
        
        if not item_id or quantity < 0:
            return jsonify({'error': 'Valid item_id and quantity required'}), 400
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        if quantity == 0:
            # Remove item from cart
            cursor.execute("""
                DELETE FROM cart_items 
                WHERE id = %s AND cart_id IN (
                    SELECT id FROM shopping_carts WHERE user_id = %s
                )
            """, (item_id, user_id))
        else:
            # Update quantity
            cursor.execute("""
                UPDATE cart_items 
                SET quantity = %s
                WHERE id = %s AND cart_id IN (
                    SELECT id FROM shopping_carts WHERE user_id = %s
                )
            """, (quantity, item_id, user_id))
        
        return jsonify({'message': 'Cart updated successfully'})
        
    except Exception as e:
        logger.error(f"Update cart error: {e}")
        return jsonify({'error': 'Failed to update cart'}), 500

@app.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    """Clear user's shopping cart"""
    try:
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header[7:]
        user_info = verify_user_token(token)
        if not user_info or not user_info.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['user_id']
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor.execute("""
            DELETE FROM cart_items 
            WHERE cart_id IN (SELECT id FROM shopping_carts WHERE user_id = %s)
        """, (user_id,))
        
        return jsonify({'message': 'Cart cleared successfully'})
        
    except Exception as e:
        logger.error(f"Clear cart error: {e}")
        return jsonify({'error': 'Failed to clear cart'}), 500

@app.route('/orders', methods=['POST'])
def create_order():
    """Create new order from cart"""
    try:
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header[7:]
        user_info = verify_user_token(token)
        if not user_info or not user_info.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['user_id']
        data = request.get_json()
        
        shipping_address = data.get('shipping_address')
        billing_address = data.get('billing_address', shipping_address)
        payment_method = data.get('payment_method', 'credit_card')
        
        if not shipping_address:
            return jsonify({'error': 'Shipping address is required'}), 400
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get cart items
        cursor.execute("""
            SELECT ci.*, p.name, p.price, p.stock_quantity
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.cart_id IN (SELECT id FROM shopping_carts WHERE user_id = %s)
            AND p.is_active = true
        """, (user_id,))
        
        cart_items = cursor.fetchall()
        
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Check stock availability
        for item in cart_items:
            if item['stock_quantity'] < item['quantity']:
                return jsonify({
                    'error': f'Insufficient stock for {item["name"]}. Available: {item["stock_quantity"]}'
                }), 400
        
        # Calculate totals
        subtotal = sum(Decimal(str(item['unit_price'])) * item['quantity'] for item in cart_items)
        tax_rate = Decimal('0.08')  # 8% tax
        tax_amount = subtotal * tax_rate
        shipping_cost = Decimal('15.00') if subtotal < 100 else Decimal('0.00')
        total_amount = subtotal + tax_amount + shipping_cost
        
        # Generate order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create order
        order_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO orders (
                id, user_id, order_number, status, subtotal, tax_amount, 
                shipping_cost, total_amount, shipping_address, billing_address, 
                payment_method
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, order_number, created_at
        """, (
            order_id, user_id, order_number, 'pending', 
            float(subtotal), float(tax_amount), float(shipping_cost), float(total_amount),
            json.dumps(shipping_address), json.dumps(billing_address), payment_method
        ))
        
        order = cursor.fetchone()
        
        # Create order items and update inventory
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (
                    id, order_id, product_id, product_sku, product_name,
                    quantity, unit_price, total_price
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), order_id, item['product_id'], '', item['name'],
                item['quantity'], float(item['unit_price']), 
                float(Decimal(str(item['unit_price'])) * item['quantity'])
            ))
            
            # Update product stock
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity - %s
                WHERE id = %s
            """, (item['quantity'], item['product_id']))
            
            # Record inventory movement
            cursor.execute("""
                INSERT INTO inventory_movements (
                    id, product_id, movement_type, quantity_change, 
                    reference_id, notes
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), item['product_id'], 'sale', -item['quantity'],
                order_id, f'Sold via order {order_number}'
            ))
        
        # Clear cart
        cursor.execute("""
            DELETE FROM cart_items 
            WHERE cart_id IN (SELECT id FROM shopping_carts WHERE user_id = %s)
        """, (user_id,))
        
        return jsonify({
            'message': 'Order created successfully',
            'order': {
                'id': order['id'],
                'order_number': order['order_number'],
                'total_amount': float(total_amount),
                'created_at': order['created_at'].isoformat(),
                'status': 'pending'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Create order error: {e}")
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/orders', methods=['GET'])
def get_user_orders():
    """Get user's order history"""
    try:
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header[7:]
        user_info = verify_user_token(token)
        if not user_info or not user_info.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['user_id']
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get orders with item count
        cursor.execute("""
            SELECT o.*, COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, limit, offset))
        
        orders = cursor.fetchall()
        
        return jsonify({
            'orders': [dict(order) for order in orders],
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Get orders error: {e}")
        return jsonify({'error': 'Failed to get orders'}), 500

@app.route('/orders/<order_id>', methods=['GET'])
def get_order_details(order_id):
    """Get detailed order information"""
    try:
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header[7:]
        user_info = verify_user_token(token)
        if not user_info or not user_info.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['user_id']
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get order
        cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
        order = cursor.fetchone()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get order items
        cursor.execute("""
            SELECT oi.*, p.images
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        
        order_items = cursor.fetchall()
        
        order_dict = dict(order)
        order_dict['items'] = [dict(item) for item in order_items]
        
        return jsonify({'order': order_dict})
        
    except Exception as e:
        logger.error(f"Get order details error: {e}")
        return jsonify({'error': 'Failed to get order details'}), 500

if __name__ == '__main__':
    print("🛒 Starting Order Service...")
    print("📡 Endpoints available:")
    print("   GET    /health           - Health check")
    print("   GET    /cart             - Get shopping cart")
    print("   POST   /cart/add         - Add item to cart")
    print("   PUT    /cart/update      - Update cart item")
    print("   DELETE /cart/clear       - Clear cart")
    print("   POST   /orders           - Create order from cart")
    print("   GET    /orders           - Get user order history")
    print("   GET    /orders/<id>      - Get order details")
    print("🌐 Access at: http://localhost:5003")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
