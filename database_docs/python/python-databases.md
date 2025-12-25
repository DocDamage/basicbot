# Python Database Programming

## Overview
Python has excellent support for various databases through dedicated libraries and drivers. This document covers the most popular database libraries for Python.

## PostgreSQL with psycopg2

### Installation
```bash
pip install psycopg2-binary
```

### Basic Usage
```python
import psycopg2

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="myuser",
    password="mypassword"
)

# Create a cursor
cur = conn.cursor()

# Execute a query
cur.execute("SELECT * FROM users WHERE age > %s", (18,))

# Fetch results
rows = cur.fetchall()
for row in rows:
    print(row)

# Close connection
cur.close()
conn.close()
```

### Advanced Features
- Connection pooling
- Asynchronous operations
- Server-side cursors for large result sets
- COPY command support
- Transaction management

## MongoDB with PyMongo

### Installation
```bash
pip install pymongo
```

### Basic Usage
```python
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Access database
db = client['mydatabase']

# Access collection
collection = db['users']

# Insert document
user = {"name": "John", "age": 30, "city": "New York"}
result = collection.insert_one(user)
print(f"Inserted ID: {result.inserted_id}")

# Find documents
users = collection.find({"age": {"$gt": 25}})
for user in users:
    print(user)

# Update document
collection.update_one(
    {"name": "John"},
    {"$set": {"age": 31}}
)

# Delete document
collection.delete_one({"name": "John"})
```

### Features
- BSON document handling
- GridFS for large files
- Aggregation pipelines
- Geospatial queries
- Text search
- Change streams

## Redis with redis-py

### Installation
```bash
pip install redis
```

### Basic Usage
```python
import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Strings
r.set('key', 'value')
value = r.get('key')
print(value)  # b'value'

# Lists
r.rpush('mylist', 'item1', 'item2', 'item3')
items = r.lrange('mylist', 0, -1)
print(items)  # [b'item1', b'item2', b'item3']

# Hashes
r.hset('user:1', 'name', 'John')
r.hset('user:1', 'age', '30')
user = r.hgetall('user:1')
print(user)  # {b'name': b'John', b'age': b'30'}

# Sets
r.sadd('myset', 'member1', 'member2', 'member3')
members = r.smembers('myset')
print(members)

# Sorted Sets
r.zadd('myzset', {'member1': 1, 'member2': 2, 'member3': 3})
scores = r.zrange('myzset', 0, -1, withscores=True)
print(scores)
```

### Advanced Features
- Connection pooling
- Pipelines for atomic operations
- Pub/Sub messaging
- Lua scripting
- Transactions
- Sentinel support

## SQLite with sqlite3 (Built-in)

### Basic Usage
```python
import sqlite3

# Connect to database (creates file if it doesn't exist)
conn = sqlite3.connect('example.db')

# Create a cursor
cur = conn.cursor()

# Create table
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER
    )
''')

# Insert data
cur.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("John", 30))
conn.commit()

# Query data
cur.execute("SELECT * FROM users WHERE age > ?", (25,))
rows = cur.fetchall()
for row in rows:
    print(row)

# Close connection
conn.close()
```

## SQLAlchemy (ORM)

### Installation
```bash
pip install sqlalchemy
```

### Basic Usage
```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create engine
engine = create_engine('sqlite:///example.db')

# Define model
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

# Create tables
Base.metadata.create_all(engine)

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Add user
user = User(name="John", age=30)
session.add(user)
session.commit()

# Query users
users = session.query(User).filter(User.age > 25).all()
for user in users:
    print(f"{user.name}: {user.age}")

session.close()
```

## Best Practices

1. **Connection Management**: Always close connections properly
2. **Parameterized Queries**: Use parameterized queries to prevent SQL injection
3. **Error Handling**: Implement proper exception handling
4. **Connection Pooling**: Use connection pools for better performance
5. **Transactions**: Use transactions for data consistency
6. **Prepared Statements**: Reuse prepared statements when possible
7. **Indexing**: Create appropriate indexes for query performance</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\python\python-databases.md