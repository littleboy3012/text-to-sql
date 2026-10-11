"""
generate_dummy_data.py
Creates a realistic e-commerce and retail analytics dummy database for Text-to-SQL.
Can generate a standalone .sql dump file or seed directly into MySQL.
"""

import random
from datetime import datetime, timedelta

# Sample data constants
CATEGORIES = [
    (1, "Smartphones & Accessories", "Electronics"),
    (2, "Laptops & Computing", "Electronics"),
    (3, "Home Appliances", "Home & Living"),
    (4, "Men's Apparel", "Fashion"),
    (5, "Women's Apparel", "Fashion"),
    (6, "Fitness & Sports Equipment", "Sports"),
]

PRODUCTS = [
    (1, "iPhone 15 Pro", 1, 95000, 134900, 45),
    (2, "Samsung Galaxy S24 Ultra", 1, 90000, 129999, 38),
    (3, "OnePlus 12", 1, 48000, 64999, 60),
    (4, "Sony WH-1000XM5 Headphones", 1, 20000, 29990, 75),
    (5, "Anker 65W Fast Charger", 1, 1500, 2999, 180),
    (6, "Spigen MagSafe Armor Case", 1, 800, 1999, 250),
    (7, "MacBook Air M3 15-inch", 2, 98000, 134900, 30),
    (8, "Dell XPS 13 Plus", 2, 85000, 119990, 25),
    (9, "Lenovo Legion Pro 5", 2, 92000, 124990, 20),
    (10, "Logitech MX Master 3S Mouse", 2, 6000, 9995, 95),
    (11, "LG 55-inch 4K OLED Smart TV", 3, 75000, 114990, 18),
    (12, "Dyson V12 Cordless Vacuum", 3, 35000, 49900, 22),
    (13, "Philips Air Fryer XL", 3, 6500, 9999, 110),
    (14, "Nespresso Vertuo Coffee Maker", 3, 14000, 21999, 40),
    (15, "Men's Slim Fit Chinos", 4, 900, 2499, 150),
    (16, "Levi's 511 Slim Jeans", 4, 1800, 3999, 120),
    (17, "Nike Dri-FIT Running T-shirt", 4, 1100, 2295, 200),
    (18, "Zara Textured Cotton Shirt", 4, 1400, 2990, 90),
    (19, "Women's Floral Maxi Dress", 5, 1200, 3499, 130),
    (20, "H&M Oversized Trench Coat", 5, 2800, 5999, 65),
    (21, "Lululemon Align High-Rise Leggings", 5, 4500, 8900, 80),
    (22, "Mango Pleated Midi Skirt", 5, 1600, 3590, 75),
    (23, "Bowflex SelectTech Adjustable Dumbbells", 6, 18000, 28500, 35),
    (24, "Manduka Pro Yoga Mat", 6, 4000, 7800, 90),
    (25, "Garmin Forerunner 265 GPS Watch", 6, 28000, 42990, 40),
    (26, "Decathlon Resistance Bands Set", 6, 500, 1299, 300),
]

CITIES_STATES = [
    ("Mumbai", "Maharashtra", "India"),
    ("Bengaluru", "Karnataka", "India"),
    ("New Delhi", "Delhi", "India"),
    ("Hyderabad", "Telangana", "India"),
    ("Pune", "Maharashtra", "India"),
    ("Chennai", "Tamil Nadu", "India"),
    ("Ahmedabad", "Gujarat", "India"),
    ("Kolkata", "West Bengal", "India"),
    ("Jaipur", "Rajasthan", "India"),
    ("Chandigarh", "Punjab", "India"),
]

FIRST_NAMES = ["Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Sneha", "Aditya", "Neha", "Arjun", "Pooja", "Rahul", "Tanvi", "Karan", "Kavya", "Siddharth", "Ishita", "Varun", "Rhea", "Manish", "Divya"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Mehta", "Nair", "Reddy", "Rao", "Gupta", "Joshi", "Singhania", "Chopra", "Deshmukh", "Iyer", "Banerjee", "Bhat"]
CUSTOMER_SEGMENTS = ["Consumer", "Corporate", "Small Business"]
ORDER_STATUSES = ["Delivered", "Delivered", "Delivered", "Delivered", "Shipped", "Processing", "Cancelled"]
PAYMENT_METHODS = ["UPI", "Credit Card", "Net Banking", "Cash on Delivery", "Debit Card"]

def build_schema_sql(db_name="retail_analytics_db"):
    return f"""-- Retail Analytics Dummy Database Schema
CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `{db_name}`;

DROP TABLE IF EXISTS `product_reviews`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `customers`;

CREATE TABLE `customers` (
    `customer_id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `phone` VARCHAR(20),
    `city` VARCHAR(50) NOT NULL,
    `state` VARCHAR(50) NOT NULL,
    `country` VARCHAR(50) NOT NULL DEFAULT 'India',
    `customer_segment` VARCHAR(30) NOT NULL DEFAULT 'Consumer',
    `created_at` DATETIME NOT NULL
) ENGINE=InnoDB;

CREATE TABLE `categories` (
    `category_id` INT PRIMARY KEY,
    `category_name` VARCHAR(100) NOT NULL,
    `department` VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE `products` (
    `product_id` INT PRIMARY KEY,
    `product_name` VARCHAR(150) NOT NULL,
    `category_id` INT NOT NULL,
    `cost_price` DECIMAL(10, 2) NOT NULL,
    `selling_price` DECIMAL(10, 2) NOT NULL,
    `stock_quantity` INT NOT NULL DEFAULT 0,
    CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `orders` (
    `order_id` INT AUTO_INCREMENT PRIMARY KEY,
    `customer_id` INT NOT NULL,
    `order_date` DATETIME NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'Delivered',
    `payment_method` VARCHAR(30) NOT NULL,
    `shipping_fee` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `order_items` (
    `item_id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `quantity` INT NOT NULL DEFAULT 1,
    `unit_price` DECIMAL(10, 2) NOT NULL,
    `discount_percent` DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT `fk_items_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_items_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `product_reviews` (
    `review_id` INT AUTO_INCREMENT PRIMARY KEY,
    `product_id` INT NOT NULL,
    `customer_id` INT NOT NULL,
    `rating` INT NOT NULL CHECK (`rating` BETWEEN 1 AND 5),
    `review_text` VARCHAR(255),
    `review_date` DATETIME NOT NULL,
    CONSTRAINT `fk_reviews_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_reviews_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE
) ENGINE=InnoDB;
"""

def generate_sql_file(filepath="dummy_data.sql", db_name="retail_analytics_db", num_customers=100, num_orders=400):
    """Generates a complete standalone SQL file with schema and insert queries."""
    random.seed(42)
    start_time = datetime(2025, 1, 1, 9, 0, 0)
    end_time = datetime(2026, 10, 10, 20, 0, 0)
    total_seconds = int((end_time - start_time).total_seconds())

    lines = [build_schema_sql(db_name)]
    
    # 1. Categories
    lines.append("\n-- Insert Categories")
    for cat in CATEGORIES:
        lines.append(f"INSERT INTO `categories` (`category_id`, `category_name`, `department`) VALUES ({cat[0]}, '{cat[1]}', '{cat[2]}');")
        
    # 2. Products
    lines.append("\n-- Insert Products")
    for prod in PRODUCTS:
        lines.append(f"INSERT INTO `products` (`product_id`, `product_name`, `category_id`, `cost_price`, `selling_price`, `stock_quantity`) "
                     f"VALUES ({prod[0]}, '{prod[1]}', {prod[2]}, {prod[3]}, {prod[4]}, {prod[5]});")
        
    # 3. Customers
    lines.append("\n-- Insert Customers")
    for i in range(1, num_customers + 1):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        phone = f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"
        city, state, country = random.choice(CITIES_STATES)
        seg = random.choice(CUSTOMER_SEGMENTS)
        reg_date = start_time + timedelta(seconds=random.randint(0, total_seconds // 2))
        lines.append(f"INSERT INTO `customers` (`customer_id`, `full_name`, `email`, `phone`, `city`, `state`, `country`, `customer_segment`, `created_at`) "
                     f"VALUES ({i}, '{name}', '{email}', '{phone}', '{city}', '{state}', '{country}', '{seg}', '{reg_date.strftime('%Y-%m-%d %H:%M:%S')}');")
        
    # 4. Orders & Order Items
    lines.append("\n-- Insert Orders and Items")
    item_id = 1
    for o_id in range(1, num_orders + 1):
        cust_id = random.randint(1, num_customers)
        ord_date = start_time + timedelta(seconds=random.randint(total_seconds // 4, total_seconds))
        status = random.choice(ORDER_STATUSES)
        pay_method = random.choice(PAYMENT_METHODS)
        shipping = random.choice([0.0, 50.0, 100.0, 150.0])
        lines.append(f"INSERT INTO `orders` (`order_id`, `customer_id`, `order_date`, `status`, `payment_method`, `shipping_fee`) "
                     f"VALUES ({o_id}, {cust_id}, '{ord_date.strftime('%Y-%m-%d %H:%M:%S')}', '{status}', '{pay_method}', {shipping});")
        
        # Order items
        items_count = random.choices([1, 2, 3, 4], weights=[0.4, 0.35, 0.15, 0.1])[0]
        chosen_products = random.sample(PRODUCTS, items_count)
        for prod in chosen_products:
            qty = random.choices([1, 2, 3], weights=[0.75, 0.2, 0.05])[0]
            unit_price = prod[4] # selling price
            discount = random.choice([0.0, 5.0, 10.0, 15.0])
            lines.append(f"INSERT INTO `order_items` (`item_id`, `order_id`, `product_id`, `quantity`, `unit_price`, `discount_percent`) "
                         f"VALUES ({item_id}, {o_id}, {prod[0]}, {qty}, {unit_price}, {discount});")
            item_id += 1

    # 5. Reviews
    lines.append("\n-- Insert Reviews")
    review_comments = [
        "Excellent product quality, highly recommend!",
        "Good value for money, fast delivery.",
        "Average experience, could be better built.",
        "Exceeded expectations, great design.",
        "Satisfied with the purchase.",
        "Not up to the mark, had some issues.",
        "Fantastic performance, love it!"
    ]
    for r_id in range(1, 150):
        prod = random.choice(PRODUCTS)
        cust_id = random.randint(1, num_customers)
        rating = random.choices([5, 4, 3, 2, 1], weights=[0.45, 0.3, 0.12, 0.08, 0.05])[0]
        comment = random.choice(review_comments).replace("'", "''")
        r_date = start_time + timedelta(seconds=random.randint(total_seconds // 3, total_seconds))
        lines.append(f"INSERT INTO `product_reviews` (`review_id`, `product_id`, `customer_id`, `rating`, `review_text`, `review_date`) "
                     f"VALUES ({r_id}, {prod[0]}, {cust_id}, {rating}, '{comment}', '{r_date.strftime('%Y-%m-%d %H:%M:%S')}');")

    sql_content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(sql_content)
    print(f"Successfully generated {filepath} with {num_customers} customers, {num_orders} orders, and {item_id-1} order items.")
    return filepath

def seed_database(host="localhost", port=3306, user="root", password="", db_name="retail_analytics_db"):
    """Directly connects to MySQL and creates & populates the schema."""
    import pymysql
    conn = pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        autocommit=True,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
    )
    try:
        sql_file = generate_sql_file("dummy_data.sql", db_name=db_name)
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_statements = f.read()

        with conn.cursor() as cursor:
            # Execute statements
            for statement in sql_statements.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
        return True, f"Successfully created and seeded database '{db_name}'!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

if __name__ == "__main__":
    generate_sql_file("dummy_data.sql")
