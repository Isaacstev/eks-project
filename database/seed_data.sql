-- Seed data for E-commerce Application

-- Insert categories
INSERT INTO categories (id, name, description) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Electronics', 'Electronic devices and accessories'),
('550e8400-e29b-41d4-a716-446655440001', 'Clothing', 'Fashion and apparel'),
('550e8400-e29b-41d4-a716-446655440002', 'Books', 'Books and educational materials'),
('550e8400-e29b-41d4-a716-446655440003', 'Home & Garden', 'Home improvement and garden supplies'),
('550e8400-e29b-41d4-a716-446655440004', 'Sports & Outdoors', 'Sports equipment and outdoor gear'),
('550e8400-e29b-41d4-a716-446655440005', 'Smartphones', 'Mobile phones and accessories'),
('550e8400-e29b-41d4-a716-446655440006', 'Laptops', 'Computers and laptops'),
('550e8400-e29b-41d4-a716-446655440007', "Men's Clothing", 'Clothing for men'),
('550e8400-e29b-41d4-a716-446655440008', "Women's Clothing", 'Clothing for women');

-- Set parent categories for subcategories
UPDATE categories SET parent_id = '550e8400-e29b-41d4-a716-446655440000' 
WHERE id IN ('550e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440006');

UPDATE categories SET parent_id = '550e8400-e29b-41d4-a716-446655440001' 
WHERE id IN ('550e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440008');

-- Insert sample products
INSERT INTO products (id, name, description, sku, category_id, price, cost, stock_quantity, min_stock_level, images, tags, featured) VALUES
('660e8400-e29b-41d4-a716-446655440000', 'iPhone 15 Pro', 'Latest Apple smartphone with advanced camera system', 'IPHONE-15-PRO-128', '550e8400-e29b-41d4-a716-446655440005', 999.00, 700.00, 50, 10, '["https://example.com/iphone15-1.jpg", "https://example.com/iphone15-2.jpg"]', ARRAY['smartphone', 'apple', 'ios', 'premium'], true),
('660e8400-e29b-41d4-a716-446655440001', 'Samsung Galaxy S24', 'Android smartphone with excellent display', 'SAMSUNG-S24-256', '550e8400-e29b-41d4-a716-446655440005', 899.00, 650.00, 75, 15, '["https://example.com/galaxy-s24-1.jpg"]', ARRAY['smartphone', 'samsung', 'android'], true),
('660e8400-e29b-41d4-a716-446655440002', 'MacBook Air M3', '13-inch laptop with M3 chip', 'MACBOOK-AIR-M3-256', '550e8400-e29b-41d4-a716-446655440006', 1299.00, 900.00, 30, 5, '["https://example.com/macbook-air-1.jpg"]', ARRAY['laptop', 'apple', 'macbook', 'm3'], true),
('660e8400-e29b-41d4-a716-446655440003', 'Dell XPS 13', 'Premium Windows laptop', 'DELL-XPS-13-512', '550e8400-e29b-41d4-a716-446655440006', 1199.00, 850.00, 25, 5, '["https://example.com/dell-xps-1.jpg"]', ARRAY['laptop', 'dell', 'windows', 'premium'], false),
('660e8400-e29b-41d4-a716-446655440004', 'Classic White T-Shirt', 'Comfortable cotton t-shirt', 'TSHIRT-WHITE-M', '550e8400-e29b-41d4-a716-446655440007', 29.99, 15.00, 200, 50, '["https://example.com/tshirt-white-1.jpg"]', ARRAY['tshirt', 'cotton', 'casual', 'white'], false),
('660e8400-e29b-41d4-a716-446655440005', 'Denim Jeans', 'Classic blue denim jeans', 'JEANS-BLUE-32', '550e8400-e29b-41d4-a716-446655440007', 79.99, 40.00, 150, 30, '["https://example.com/jeans-blue-1.jpg"]', ARRAY['jeans', 'denim', 'casual', 'blue'], false),
('660e8400-e29b-41d4-a716-446655440006', 'Wireless Headphones', 'Noise-canceling wireless headphones', 'HEADPHONES-WL-001', '550e8400-e29b-41d4-a716-446655440000', 199.99, 100.00, 80, 20, '["https://example.com/headphones-1.jpg"]', ARRAY['headphones', 'wireless', 'audio', 'noise-canceling'], true),
('660e8400-e29b-41d4-a716-446655440007', 'Running Shoes', 'Comfortable athletic running shoes', 'SHOES-RUN-42', '550e8400-e29b-41d4-a716-446655440004', 129.99, 70.00, 100, 25, '["https://example.com/running-shoes-1.jpg"]', ARRAY['shoes', 'running', 'athletic', 'comfortable'], false),
('660e8400-e29b-41d4-a716-446655440008', 'Programming Book', 'Complete guide to Python programming', 'BOOK-PYTHON-001', '550e8400-e29b-41d4-a716-446655440002', 49.99, 25.00, 60, 15, '["https://example.com/python-book-1.jpg"]', ARRAY['book', 'programming', 'python', 'education'], false),
('660e8400-e29b-41d4-a716-446655440009', 'Coffee Maker', 'Automatic drip coffee maker', 'COFFEE-MAKER-001', '550e8400-e29b-41d4-a716-446655440003', 89.99, 50.00, 40, 10, '["https://example.com/coffee-maker-1.jpg"]', ARRAY['coffee', 'kitchen', 'appliance', 'home'], false);

-- Insert admin user (password: admin123 - hashed with bcrypt)
INSERT INTO users (id, email, password_hash, first_name, last_name, role) VALUES
('770e8400-e29b-41d4-a716-446655440000', 'admin@ecommerce.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewnoEI7tKQWUCyO6', 'Admin', 'User', 'admin');

-- Insert sample customers
INSERT INTO users (id, email, password_hash, first_name, last_name, phone) VALUES
('770e8400-e29b-41d4-a716-446655440001', 'john.doe@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewnoEI7tKQWUCyO6', 'John', 'Doe', '+1234567890'),
('770e8400-e29b-41d4-a716-446655440002', 'jane.smith@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewnoEI7tKQWUCyO6', 'Jane', 'Smith', '+0987654321'),
('770e8400-e29b-41d4-a716-446655440003', 'bob.wilson@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewnoEI7tKQWUCyO6', 'Bob', 'Wilson', '+1122334455');

-- Insert sample user addresses
INSERT INTO user_addresses (user_id, address_line_1, city, state, postal_code, country, is_default) VALUES
('770e8400-e29b-41d4-a716-446655440001', '123 Main St', 'New York', 'NY', '10001', 'USA', true),
('770e8400-e29b-41d4-a716-446655440002', '456 Oak Ave', 'Los Angeles', 'CA', '90210', 'USA', true),
('770e8400-e29b-41d4-a716-446655440003', '789 Pine Rd', 'Chicago', 'IL', '60601', 'USA', true);

-- Insert sample product reviews
INSERT INTO product_reviews (product_id, user_id, rating, title, comment, is_verified_purchase, is_approved) VALUES
('660e8400-e29b-41d4-a716-446655440000', '770e8400-e29b-41d4-a716-446655440001', 5, 'Excellent phone!', 'Great camera quality and battery life. Highly recommended!', true, true),
('660e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 4, 'Good value', 'Nice Android phone with good performance.', true, true),
('660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440003', 5, 'Perfect for work', 'Fast and lightweight. Perfect for development work.', true, true),
('660e8400-e29b-41d4-a716-446655440006', '770e8400-e29b-41d4-a716-446655440001', 4, 'Great sound quality', 'Excellent noise cancellation and sound quality.', true, true);

-- Insert sample order (completed)
INSERT INTO orders (id, user_id, order_number, status, subtotal, tax_amount, shipping_cost, total_amount, payment_status, shipping_address, billing_address, payment_method) VALUES
('880e8400-e29b-41d4-a716-446655440000', '770e8400-e29b-41d4-a716-446655440001', 'ORD-2024-001', 'delivered', 1198.99, 95.92, 15.00, 1309.91, 'paid',
'{"address_line_1": "123 Main St", "city": "New York", "state": "NY", "postal_code": "10001", "country": "USA"}',
'{"address_line_1": "123 Main St", "city": "New York", "state": "NY", "postal_code": "10001", "country": "USA"}',
'credit_card');

-- Insert order items for the sample order
INSERT INTO order_items (order_id, product_id, product_sku, product_name, quantity, unit_price, total_price) VALUES
('880e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440000', 'IPHONE-15-PRO-128', 'iPhone 15 Pro', 1, 999.00, 999.00),
('880e8400-e29b-41d4-a716-446655440000', '660e8400-e29b-41d4-a716-446655440006', 'HEADPHONES-WL-001', 'Wireless Headphones', 1, 199.99, 199.99);

-- Insert payment transaction
INSERT INTO payment_transactions (order_id, transaction_id, payment_method, amount, status, gateway_response, processed_at) VALUES
('880e8400-e29b-41d4-a716-446655440000', 'TXN-2024-001', 'credit_card', 1309.91, 'completed', 
'{"transaction_id": "ch_1234567890", "status": "succeeded", "amount": 130991, "currency": "usd"}', 
CURRENT_TIMESTAMP);

-- Update inventory for sold items
INSERT INTO inventory_movements (product_id, movement_type, quantity_change, reference_id, notes) VALUES
('660e8400-e29b-41d4-a716-446655440000', 'sale', -1, '880e8400-e29b-41d4-a716-446655440000', 'Sold via order ORD-2024-001'),
('660e8400-e29b-41d4-a716-446655440006', 'sale', -1, '880e8400-e29b-41d4-a716-446655440000', 'Sold via order ORD-2024-001');

-- Update product stock quantities
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id = '660e8400-e29b-41d4-a716-446655440000';
UPDATE products SET stock_quantity = stock_quantity - 1 WHERE id = '660e8400-e29b-41d4-a716-446655440006';
