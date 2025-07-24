import sqlite3
import os

def create_database_schema(db_path):
    """Create the products table schema for a given database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            discount_percentage REAL DEFAULT 0,
            availability BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

def populate_zepto_data():
    """Populate Zepto database with sample data."""
    db_path = os.path.join('databases', 'zepto.db')
    create_database_schema(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM products')
    
    zepto_products = [
        ('Organic Bananas', 'Fruits', 45.99, 10.0, True),
        ('Red Onions', 'Vegetables', 28.50, 5.0, True),
        ('Basmati Rice 1kg', 'Groceries', 89.99, 15.0, True),
        ('Fresh Tomatoes', 'Vegetables', 35.75, 8.0, True),
        ('Green Apples', 'Fruits', 125.00, 12.0, True),
        ('Potato Chips', 'Snacks', 25.99, 20.0, True),
        ('Fresh Milk 1L', 'Dairy', 65.00, 0.0, True),
        ('Carrots', 'Vegetables', 42.50, 7.0, True),
        ('Mango (Alphonso)', 'Fruits', 180.00, 5.0, False),
        ('Chocolate Cookies', 'Snacks', 45.50, 25.0, True),
        ('Bell Peppers', 'Vegetables', 85.99, 10.0, True),
        ('Orange Juice 1L', 'Beverages', 95.00, 15.0, True),
        ('Cauliflower', 'Vegetables', 38.75, 12.0, True),
        ('Grapes (Green)', 'Fruits', 95.50, 8.0, True),
        ('Instant Noodles', 'Snacks', 15.99, 30.0, True)
    ]
    
    cursor.executemany('''
        INSERT INTO products (name, category, price, discount_percentage, availability)
        VALUES (?, ?, ?, ?, ?)
    ''', zepto_products)
    
    conn.commit()
    conn.close()
    print("Zepto database populated successfully!")

def populate_blinkit_data():
    """Populate Blinkit database with sample data."""
    db_path = os.path.join('databases', 'blinkit.db')
    create_database_schema(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM products')
    
    blinkit_products = [
        ('Premium Bananas', 'Fruits', 52.99, 8.0, True),
        ('White Onions', 'Vegetables', 32.00, 10.0, True),
        ('Jasmine Rice 1kg', 'Groceries', 95.50, 12.0, True),
        ('Cherry Tomatoes', 'Vegetables', 48.25, 15.0, True),
        ('Red Apples', 'Fruits', 135.00, 10.0, True),
        ('Spicy Chips', 'Snacks', 28.99, 18.0, True),
        ('Organic Milk 1L', 'Dairy', 72.00, 5.0, True),
        ('Baby Carrots', 'Vegetables', 55.50, 12.0, True),
        ('Kesar Mango', 'Fruits', 195.00, 8.0, True),
        ('Cream Biscuits', 'Snacks', 38.75, 22.0, True),
        ('Yellow Bell Peppers', 'Vegetables', 92.50, 15.0, True),
        ('Apple Juice 1L', 'Beverages', 105.00, 12.0, True),
        ('Broccoli', 'Vegetables', 65.99, 18.0, True),
        ('Red Grapes', 'Fruits', 110.00, 12.0, True),
        ('Cup Noodles', 'Snacks', 22.50, 25.0, True)
    ]
    
    cursor.executemany('''
        INSERT INTO products (name, category, price, discount_percentage, availability)
        VALUES (?, ?, ?, ?, ?)
    ''', blinkit_products)
    
    conn.commit()
    conn.close()
    print("Blinkit database populated successfully!")

def populate_swiggy_data():
    """Populate Swiggy Instamart database with sample data."""
    db_path = os.path.join('databases', 'swiggy.db')
    create_database_schema(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM products')
    
    swiggy_products = [
        ('Fresh Bananas', 'Fruits', 48.50, 12.0, True),
        ('Purple Onions', 'Vegetables', 29.99, 8.0, True),
        ('Brown Rice 1kg', 'Groceries', 82.75, 10.0, True),
        ('Roma Tomatoes', 'Vegetables', 41.00, 12.0, True),
        ('Fuji Apples', 'Fruits', 145.00, 15.0, True),
        ('Masala Chips', 'Snacks', 24.50, 15.0, True),
        ('Toned Milk 1L', 'Dairy', 58.00, 8.0, True),
        ('Orange Carrots', 'Vegetables', 38.99, 5.0, True),
        ('Badami Mango', 'Fruits', 165.00, 10.0, True),
        ('Digestive Biscuits', 'Snacks', 42.25, 20.0, True),
        ('Red Bell Peppers', 'Vegetables', 88.00, 8.0, True),
        ('Mixed Fruit Juice', 'Beverages', 88.50, 10.0, True),
        ('Green Cauliflower', 'Vegetables', 45.75, 15.0, True),
        ('Black Grapes', 'Fruits', 88.99, 6.0, True),
        ('Maggi Noodles', 'Snacks', 18.75, 28.0, True)
    ]
    
    cursor.executemany('''
        INSERT INTO products (name, category, price, discount_percentage, availability)
        VALUES (?, ?, ?, ?, ?)
    ''', swiggy_products)
    
    conn.commit()
    conn.close()
    print("Swiggy Instamart database populated successfully!")

def main():
    """Main function to create and populate all databases."""
    # Ensure databases directory exists
    os.makedirs('databases', exist_ok=True)
    
    print("Creating and populating databases...")
    populate_zepto_data()
    populate_blinkit_data()
    populate_swiggy_data()
    print("\nAll databases created and populated successfully!")
    print("Database files created:")
    print("- databases/zepto.db")
    print("- databases/blinkit.db") 
    print("- databases/swiggy.db")

if __name__ == "__main__":
    main()
