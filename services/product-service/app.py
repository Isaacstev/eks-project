from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import psycopg2.extras
import uuid
import logging
import math
from datetime import datetime

app = Flask(__name__)
CORS(app)

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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = 'connected' if db.connect() else 'disconnected'
    return jsonify({
        'status': 'healthy',
        'service': 'product-service',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    try:
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor.execute("""
            SELECT c.*, 
                   COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id AND p.is_active = true
            WHERE c.is_active = true
            GROUP BY c.id, c.name, c.description, c.parent_id, c.is_active, c.created_at
            ORDER BY c.name
        """)
        
        categories = cursor.fetchall()
        
        # Organize categories with hierarchy
        category_dict = {}
        root_categories = []
        
        for cat in categories:
            cat_dict = dict(cat)
            category_dict[cat['id']] = cat_dict
            cat_dict['children'] = []
        
        # Build hierarchy
        for cat in categories:
            if cat['parent_id']:
                if cat['parent_id'] in category_dict:
                    category_dict[cat['parent_id']]['children'].append(category_dict[cat['id']])
            else:
                root_categories.append(category_dict[cat['id']])
        
        return jsonify({
            'categories': root_categories,
            'total_categories': len(categories)
        })
        
    except Exception as e:
        logger.error(f"Get categories error: {e}")
        return jsonify({'error': 'Failed to fetch categories'}), 500

@app.route('/products', methods=['GET'])
def get_products():
    """Get products with filtering, search, and pagination"""
    try:
        # Query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category_id = request.args.get('category_id')
        search = request.args.get('search')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        featured_only = request.args.get('featured') == 'true'
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validate sorting
        valid_sort_fields = ['name', 'price', 'created_at', 'stock_quantity']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        offset = (page - 1) * limit
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Build WHERE conditions
        where_conditions = ["p.is_active = true"]
        params = []
        
        if category_id:
            where_conditions.append("p.category_id = %s")
            params.append(category_id)
        
        if search:
            where_conditions.append("""
                (p.name ILIKE %s OR p.description ILIKE %s OR 
                 EXISTS (SELECT 1 FROM unnest(p.tags) AS tag WHERE tag ILIKE %s))
            """)
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        if min_price:
            where_conditions.append("p.price >= %s")
            params.append(float(min_price))
        
        if max_price:
            where_conditions.append("p.price <= %s")
            params.append(float(max_price))
        
        if featured_only:
            where_conditions.append("p.featured = true")
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {where_clause}
        """
        
        cursor.execute(count_query, params)
        total_products = cursor.fetchone()['total']
        
        # Get products with pagination
        products_query = f"""
            SELECT p.*, c.name as category_name,
                   COALESCE(AVG(pr.rating), 0) as avg_rating,
                   COUNT(pr.id) as review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_reviews pr ON p.id = pr.product_id AND pr.is_approved = true
            {where_clause}
            GROUP BY p.id, c.name
            ORDER BY p.{sort_by} {sort_order.upper()}
            LIMIT %s OFFSET %s
        """
        
        params.extend([limit, offset])
        cursor.execute(products_query, params)
        products = cursor.fetchall()
        
        # Format products
        formatted_products = []
        for product in products:
            product_dict = dict(product)
            product_dict['avg_rating'] = round(float(product_dict['avg_rating']), 1)
            product_dict['images'] = product_dict['images'] if product_dict['images'] else []
            product_dict['tags'] = product_dict['tags'] if product_dict['tags'] else []
            formatted_products.append(product_dict)
        
        total_pages = math.ceil(total_products / limit)
        
        return jsonify({
            'products': formatted_products,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_products': total_products,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        logger.error(f"Get products error: {e}")
        return jsonify({'error': 'Failed to fetch products'}), 500

@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    try:
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor.execute("""
            SELECT p.*, c.name as category_name,
                   COALESCE(AVG(pr.rating), 0) as avg_rating,
                   COUNT(pr.id) as review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_reviews pr ON p.id = pr.product_id AND pr.is_approved = true
            WHERE p.id = %s AND p.is_active = true
            GROUP BY p.id, c.name
        """, (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        product_dict = dict(product)
        product_dict['avg_rating'] = round(float(product_dict['avg_rating']), 1)
        product_dict['images'] = product_dict['images'] if product_dict['images'] else []
        product_dict['tags'] = product_dict['tags'] if product_dict['tags'] else []
        
        # Get product reviews
        cursor.execute("""
            SELECT pr.*, u.first_name, u.last_name
            FROM product_reviews pr
            LEFT JOIN users u ON pr.user_id = u.id
            WHERE pr.product_id = %s AND pr.is_approved = true
            ORDER BY pr.created_at DESC
            LIMIT 10
        """, (product_id,))
        
        reviews = cursor.fetchall()
        product_dict['reviews'] = [dict(review) for review in reviews]
        
        return jsonify({'product': product_dict})
        
    except Exception as e:
        logger.error(f"Get product error: {e}")
        return jsonify({'error': 'Failed to fetch product'}), 500

@app.route('/products/search', methods=['GET'])
def search_products():
    """Advanced product search"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'products': [], 'suggestions': []})
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Search in products and categories
        cursor.execute("""
            SELECT p.*, c.name as category_name,
                   COALESCE(AVG(pr.rating), 0) as avg_rating,
                   COUNT(pr.id) as review_count,
                   ts_rank(to_tsvector('english', p.name || ' ' || COALESCE(p.description, '') || ' ' || array_to_string(p.tags, ' ')), 
                           plainto_tsquery('english', %s)) as rank
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_reviews pr ON p.id = pr.product_id AND pr.is_approved = true
            WHERE p.is_active = true AND (
                p.name ILIKE %s OR 
                p.description ILIKE %s OR
                c.name ILIKE %s OR
                EXISTS (SELECT 1 FROM unnest(p.tags) AS tag WHERE tag ILIKE %s)
            )
            GROUP BY p.id, c.name
            ORDER BY rank DESC, p.name
            LIMIT 50
        """, (query, f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        
        products = cursor.fetchall()
        
        # Format products
        formatted_products = []
        for product in products:
            product_dict = dict(product)
            product_dict['avg_rating'] = round(float(product_dict['avg_rating']), 1)
            product_dict['images'] = product_dict['images'] if product_dict['images'] else []
            product_dict['tags'] = product_dict['tags'] if product_dict['tags'] else []
            del product_dict['rank']  # Remove rank from response
            formatted_products.append(product_dict)
        
        # Get search suggestions (similar products/categories)
        cursor.execute("""
            (SELECT DISTINCT name as suggestion, 'product' as type FROM products 
             WHERE name ILIKE %s AND is_active = true LIMIT 5)
            UNION ALL
            (SELECT DISTINCT name as suggestion, 'category' as type FROM categories 
             WHERE name ILIKE %s AND is_active = true LIMIT 3)
            ORDER BY suggestion
        """, (f"%{query}%", f"%{query}%"))
        
        suggestions = cursor.fetchall()
        
        return jsonify({
            'products': formatted_products,
            'suggestions': [dict(s) for s in suggestions],
            'total_found': len(formatted_products),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Search products error: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/products/featured', methods=['GET'])
def get_featured_products():
    """Get featured products"""
    try:
        limit = int(request.args.get('limit', 8))
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor.execute("""
            SELECT p.*, c.name as category_name,
                   COALESCE(AVG(pr.rating), 0) as avg_rating,
                   COUNT(pr.id) as review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_reviews pr ON p.id = pr.product_id AND pr.is_approved = true
            WHERE p.is_active = true AND p.featured = true
            GROUP BY p.id, c.name
            ORDER BY p.created_at DESC
            LIMIT %s
        """, (limit,))
        
        products = cursor.fetchall()
        
        # Format products
        formatted_products = []
        for product in products:
            product_dict = dict(product)
            product_dict['avg_rating'] = round(float(product_dict['avg_rating']), 1)
            product_dict['images'] = product_dict['images'] if product_dict['images'] else []
            product_dict['tags'] = product_dict['tags'] if product_dict['tags'] else []
            formatted_products.append(product_dict)
        
        return jsonify({
            'featured_products': formatted_products,
            'count': len(formatted_products)
        })
        
    except Exception as e:
        logger.error(f"Get featured products error: {e}")
        return jsonify({'error': 'Failed to fetch featured products'}), 500

@app.route('/categories/<category_id>/products', methods=['GET'])
def get_category_products(category_id):
    """Get products by category"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')
        
        offset = (page - 1) * limit
        
        cursor = db.get_cursor()
        if not cursor:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get category info
        cursor.execute("SELECT * FROM categories WHERE id = %s AND is_active = true", (category_id,))
        category = cursor.fetchone()
        
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Get products
        cursor.execute(f"""
            SELECT p.*, c.name as category_name,
                   COALESCE(AVG(pr.rating), 0) as avg_rating,
                   COUNT(pr.id) as review_count
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_reviews pr ON p.id = pr.product_id AND pr.is_approved = true
            WHERE p.category_id = %s AND p.is_active = true
            GROUP BY p.id, c.name
            ORDER BY p.{sort_by} {sort_order.upper()}
            LIMIT %s OFFSET %s
        """, (category_id, limit, offset))
        
        products = cursor.fetchall()
        
        # Format products
        formatted_products = []
        for product in products:
            product_dict = dict(product)
            product_dict['avg_rating'] = round(float(product_dict['avg_rating']), 1)
            product_dict['images'] = product_dict['images'] if product_dict['images'] else []
            product_dict['tags'] = product_dict['tags'] if product_dict['tags'] else []
            formatted_products.append(product_dict)
        
        return jsonify({
            'category': dict(category),
            'products': formatted_products,
            'count': len(formatted_products)
        })
        
    except Exception as e:
        logger.error(f"Get category products error: {e}")
        return jsonify({'error': 'Failed to fetch category products'}), 500

if __name__ == '__main__':
    print("🛍️ Starting Product Service...")
    print("📡 Endpoints available:")
    print("   GET  /health                     - Health check")
    print("   GET  /categories                 - Get all categories")
    print("   GET  /products                   - Get products (with filtering)")
    print("   GET  /products/<id>              - Get single product")
    print("   GET  /products/search            - Search products")
    print("   GET  /products/featured          - Get featured products")
    print("   GET  /categories/<id>/products   - Get products by category")
    print("🌐 Access at: http://localhost:5002")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
