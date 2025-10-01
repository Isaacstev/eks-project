from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage for demo purposes
visitors = []
counter = 0

@app.route('/')
def hello_world():
    global counter
    counter += 1
    return f'Hello from the backend! You are visitor #{counter}'

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'development')
    })

@app.route('/api/visitors', methods=['GET'])
def get_visitors():
    return jsonify({
        'total_visitors': counter,
        'recent_visitors': visitors[-10:],  # Last 10 visitors
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/visitors', methods=['POST'])
def add_visitor():
    global counter
    data = request.get_json() or {}
    visitor_name = data.get('name', f'Anonymous_{counter}')
    
    visitor_info = {
        'id': counter,
        'name': visitor_name,
        'timestamp': datetime.datetime.now().isoformat(),
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    
    visitors.append(visitor_info)
    counter += 1
    
    return jsonify({
        'message': f'Welcome, {visitor_name}!',
        'visitor': visitor_info
    }), 201

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'total_requests': counter,
        'unique_visitors': len(set(v['name'] for v in visitors)),
        'uptime': 'Running since server start',
        'endpoints': {
            'GET /': 'Main greeting endpoint',
            'GET /api/health': 'Health check',
            'GET /api/visitors': 'Get visitor statistics',
            'POST /api/visitors': 'Add a new visitor',
            'GET /api/stats': 'Get API statistics'
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Flask backend server...")
    print("📡 API endpoints available:")
    print("   GET  /                 - Main greeting")
    print("   GET  /api/health       - Health check")
    print("   GET  /api/visitors     - Visitor stats")
    print("   POST /api/visitors     - Add visitor")
    print("   GET  /api/stats        - API statistics")
    print("🌐 Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

