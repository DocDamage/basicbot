# JavaScript/Node.js Database Programming

## Overview
JavaScript, particularly with Node.js, has excellent database support through various drivers and ORMs. This document covers popular database solutions for JavaScript applications.

## MongoDB with Mongoose

### Installation
```bash
npm install mongoose
```

### Basic Usage
```javascript
const mongoose = require('mongoose');

// Connect to MongoDB
mongoose.connect('mongodb://localhost:27017/mydatabase')
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('Connection error:', err));

// Define schema
const userSchema = new mongoose.Schema({
  name: { type: String, required: true },
  age: { type: Number, min: 0 },
  email: { type: String, unique: true },
  createdAt: { type: Date, default: Date.now }
});

// Create model
const User = mongoose.model('User', userSchema);

// Create and save user
const user = new User({
  name: 'John Doe',
  age: 30,
  email: 'john@example.com'
});

user.save()
  .then(savedUser => console.log('User saved:', savedUser))
  .catch(err => console.error('Save error:', err));

// Find users
User.find({ age: { $gte: 18 } })
  .then(users => console.log('Users:', users))
  .catch(err => console.error('Find error:', err));

// Update user
User.findOneAndUpdate(
  { name: 'John Doe' },
  { age: 31 },
  { new: true }
)
  .then(updatedUser => console.log('Updated user:', updatedUser))
  .catch(err => console.error('Update error:', err));

// Delete user
User.findOneAndDelete({ name: 'John Doe' })
  .then(deletedUser => console.log('Deleted user:', deletedUser))
  .catch(err => console.error('Delete error:', err));
```

### Advanced Features
- Schema validation
- Middleware (pre/post hooks)
- Population (joining documents)
- Virtual properties
- Plugins
- Aggregation pipelines

## PostgreSQL with pg

### Installation
```bash
npm install pg
```

### Basic Usage
```javascript
const { Client } = require('pg');

// Create client
const client = new Client({
  host: 'localhost',
  port: 5432,
  database: 'mydb',
  user: 'myuser',
  password: 'mypassword'
});

// Connect
client.connect()
  .then(() => console.log('Connected to PostgreSQL'))
  .catch(err => console.error('Connection error:', err));

// Execute query
client.query('SELECT * FROM users WHERE age > $1', [18])
  .then(result => {
    console.log('Users:', result.rows);
  })
  .catch(err => console.error('Query error:', err));

// Insert data
client.query(
  'INSERT INTO users (name, age, email) VALUES ($1, $2, $3)',
  ['Jane Doe', 25, 'jane@example.com']
)
  .then(result => console.log('User inserted'))
  .catch(err => console.error('Insert error:', err));

// Close connection
client.end()
  .then(() => console.log('Connection closed'))
  .catch(err => console.error('Close error:', err));
```

## MySQL with mysql2

### Installation
```bash
npm install mysql2
```

### Basic Usage
```javascript
const mysql = require('mysql2');

// Create connection
const connection = mysql.createConnection({
  host: 'localhost',
  user: 'myuser',
  password: 'mypassword',
  database: 'mydb'
});

// Connect
connection.connect(err => {
  if (err) {
    console.error('Connection error:', err);
    return;
  }
  console.log('Connected to MySQL');
});

// Execute query
connection.query('SELECT * FROM users WHERE age > ?', [18], (err, results) => {
  if (err) {
    console.error('Query error:', err);
    return;
  }
  console.log('Users:', results);
});

// Insert data
connection.query(
  'INSERT INTO users (name, age, email) VALUES (?, ?, ?)',
  ['Bob Smith', 35, 'bob@example.com'],
  (err, result) => {
    if (err) {
      console.error('Insert error:', err);
      return;
    }
    console.log('User inserted with ID:', result.insertId);
  }
);

// Close connection
connection.end(err => {
  if (err) {
    console.error('Close error:', err);
    return;
  }
  console.log('Connection closed');
});
```

## Redis with ioredis

### Installation
```bash
npm install ioredis
```

### Basic Usage
```javascript
const Redis = require('ioredis');

// Create Redis instance
const redis = new Redis({
  host: 'localhost',
  port: 6379
});

// Set value
redis.set('key', 'value')
  .then(() => console.log('Value set'))
  .catch(err => console.error('Set error:', err));

// Get value
redis.get('key')
  .then(value => console.log('Value:', value))
  .catch(err => console.error('Get error:', err));

// Work with hashes
redis.hset('user:1', 'name', 'John')
  .then(() => redis.hset('user:1', 'age', '30'))
  .then(() => redis.hgetall('user:1'))
  .then(user => console.log('User:', user))
  .catch(err => console.error('Hash error:', err));

// Work with lists
redis.rpush('mylist', 'item1', 'item2', 'item3')
  .then(() => redis.lrange('mylist', 0, -1))
  .then(items => console.log('List items:', items))
  .catch(err => console.error('List error:', err));

// Work with sets
redis.sadd('myset', 'member1', 'member2', 'member3')
  .then(() => redis.smembers('myset'))
  .then(members => console.log('Set members:', members))
  .catch(err => console.error('Set error:', err));

// Close connection
redis.quit()
  .then(() => console.log('Redis connection closed'))
  .catch(err => console.error('Quit error:', err));
```

## SQLite with sqlite3

### Installation
```bash
npm install sqlite3
```

### Basic Usage
```javascript
const sqlite3 = require('sqlite3').verbose();

// Open database
const db = new sqlite3.Database(':memory:', (err) => {
  if (err) {
    console.error('Open error:', err.message);
    return;
  }
  console.log('Connected to SQLite database');
});

// Create table
db.run(`
  CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    email TEXT UNIQUE
  )
`, (err) => {
  if (err) {
    console.error('Create table error:', err.message);
    return;
  }
  console.log('Table created');
});

// Insert data
db.run(
  'INSERT INTO users (name, age, email) VALUES (?, ?, ?)',
  ['Alice Johnson', 28, 'alice@example.com'],
  function(err) {
    if (err) {
      console.error('Insert error:', err.message);
      return;
    }
    console.log(`User inserted with ID: ${this.lastID}`);
  }
);

// Query data
db.all('SELECT * FROM users WHERE age > ?', [20], (err, rows) => {
  if (err) {
    console.error('Query error:', err.message);
    return;
  }
  console.log('Users:', rows);
});

// Close database
db.close((err) => {
  if (err) {
    console.error('Close error:', err.message);
    return;
  }
  console.log('Database closed');
});
```

## Sequelize (ORM)

### Installation
```bash
npm install sequelize mysql2
# or for PostgreSQL: npm install sequelize pg pg-hstore
```

### Basic Usage
```javascript
const { Sequelize, DataTypes } = require('sequelize');

// Create Sequelize instance
const sequelize = new Sequelize('mydb', 'myuser', 'mypassword', {
  host: 'localhost',
  dialect: 'mysql' // or 'postgres', 'sqlite', etc.
});

// Define model
const User = sequelize.define('User', {
  name: {
    type: DataTypes.STRING,
    allowNull: false
  },
  age: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true
  }
});

// Sync database
sequelize.sync()
  .then(() => console.log('Database synced'))
  .catch(err => console.error('Sync error:', err));

// Create user
User.create({
  name: 'John Doe',
  age: 30,
  email: 'john@example.com'
})
  .then(user => console.log('User created:', user.toJSON()))
  .catch(err => console.error('Create error:', err));

// Find users
User.findAll({
  where: {
    age: {
      [Op.gt]: 25
    }
  }
})
  .then(users => console.log('Users:', users.map(u => u.toJSON())))
  .catch(err => console.error('Find error:', err));

// Update user
User.update(
  { age: 31 },
  { where: { name: 'John Doe' } }
)
  .then(([affectedCount]) => console.log(`${affectedCount} user(s) updated`))
  .catch(err => console.error('Update error:', err));

// Delete user
User.destroy({
  where: { name: 'John Doe' }
})
  .then(deletedCount => console.log(`${deletedCount} user(s) deleted`))
  .catch(err => console.error('Delete error:', err));

// Close connection
sequelize.close()
  .then(() => console.log('Connection closed'))
  .catch(err => console.error('Close error:', err));
```

## Best Practices

1. **Connection Pooling**: Use connection pools for better performance
2. **Prepared Statements**: Use parameterized queries to prevent SQL injection
3. **Error Handling**: Implement comprehensive error handling
4. **Transactions**: Use transactions for data consistency
5. **Connection Limits**: Set appropriate connection limits
6. **Async/Await**: Use async/await for cleaner asynchronous code
7. **Environment Variables**: Store database credentials securely
8. **Migrations**: Use migration tools for schema changes</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\javascript\javascript-databases.md