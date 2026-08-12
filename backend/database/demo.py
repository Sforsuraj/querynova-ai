import os
from pathlib import Path
from sqlalchemy import create_engine, text
from backend.config import DATABASE_URL

DDL = '''
CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, city TEXT);
CREATE TABLE products (id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL, name TEXT NOT NULL, price REAL NOT NULL, FOREIGN KEY(category_id) REFERENCES categories(id));
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, order_date TEXT NOT NULL, status TEXT NOT NULL, FOREIGN KEY(customer_id) REFERENCES customers(id));
CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL, FOREIGN KEY(order_id) REFERENCES orders(id), FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE payments (id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, amount REAL NOT NULL, status TEXT NOT NULL, paid_at TEXT, FOREIGN KEY(order_id) REFERENCES orders(id));
CREATE TABLE inventory (id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, quantity_on_hand INTEGER NOT NULL, FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE shipments (id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, status TEXT NOT NULL, shipped_at TEXT, FOREIGN KEY(order_id) REFERENCES orders(id));
'''

def ensure_demo_database():
    if not DATABASE_URL.startswith('sqlite'):
        return
    path = Path(DATABASE_URL.replace('sqlite:///', ''))
    if path.exists(): return
    # The bundled database is read-only on Vercel. Do not seed or create files
    # in a serverless invocation if the packaged asset is missing.
    if os.getenv('VERCEL'): return
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(DATABASE_URL)
    with engine.begin() as con:
        for statement in DDL.split(';'):
            if statement.strip(): con.execute(text(statement))
        con.execute(text("INSERT INTO categories VALUES (1,'Electronics'),(2,'Home'),(3,'Outdoors')"))
        con.execute(text("INSERT INTO customers VALUES (1,'Ava Patel','ava@example.com','Mumbai'),(2,'Noah Smith','noah@example.com','Delhi'),(3,'Mia Chen','mia@example.com','Bengaluru'),(4,'Liam Khan','liam@example.com','Pune')"))
        con.execute(text("INSERT INTO products VALUES (1,1,'Laptop Pro',1200),(2,1,'Wireless Headphones',180),(3,2,'Ergo Chair',350),(4,3,'Trail Backpack',95),(5,1,'4K Monitor',600),(6,2,'Desk Lamp',45)"))
        con.execute(text("INSERT INTO orders VALUES (1,1,'2026-01-15','delivered'),(2,2,'2026-02-04','delivered'),(3,1,'2026-03-12','delivered'),(4,3,'2026-04-08','shipped'),(5,4,'2026-05-21','delivered'),(6,2,'2026-06-10','delivered'),(7,3,'2026-07-19','processing'),(8,1,'2026-08-02','paid')"))
        con.execute(text("INSERT INTO order_items VALUES (1,1,1,1,1200),(2,1,2,2,180),(3,2,3,1,350),(4,2,4,3,95),(5,3,5,2,600),(6,3,2,1,180),(7,4,1,1,1200),(8,4,6,4,45),(9,5,3,2,350),(10,6,5,1,600),(11,6,4,2,95),(12,7,2,5,180),(13,8,1,1,1200)"))
        con.execute(text("INSERT INTO payments SELECT id,id,100,'paid','2026-01-01' FROM orders"))
        con.execute(text("INSERT INTO inventory VALUES (1,1,12),(2,2,55),(3,3,21),(4,4,44),(5,5,16),(6,6,80)"))
        con.execute(text("INSERT INTO shipments SELECT id,id,'shipped','2026-01-02' FROM orders"))
