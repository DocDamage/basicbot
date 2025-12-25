# Ruby Database Programming

## Overview
Ruby has excellent database support through ActiveRecord (Rails), DataMapper, Sequel, and various database-specific gems. This document covers the most popular database solutions for Ruby applications.

## ActiveRecord (Rails ORM)

### Model Definition
```ruby
# app/models/user.rb
class User < ApplicationRecord
  # Validations
  validates :name, presence: true, length: { maximum: 100 }
  validates :email, presence: true, uniqueness: true
  validates :age, presence: true, numericality: { only_integer: true, greater_than: 0 }

  # Associations
  has_many :posts
  has_many :comments

  # Scopes
  scope :adults, -> { where('age >= ?', 18) }
  scope :by_name, -> { order(:name) }

  # Callbacks
  before_save :normalize_email

  private

  def normalize_email
    self.email = email.downcase.strip
  end
end
```

### Basic CRUD Operations
```ruby
# Create
user = User.create(name: "John Doe", email: "john@example.com", age: 30)
# or
user = User.new(name: "John Doe", email: "john@example.com", age: 30)
user.save

# Read
user = User.find(1)
users = User.all
adults = User.adults
users_by_name = User.by_name.limit(10)

# Update
user = User.find(1)
user.update(age: 31)
# or
user.age = 31
user.save

# Delete
user = User.find(1)
user.destroy
# or
User.destroy(1)
```

### Query Interface
```ruby
# Basic queries
users = User.where(age: 25..35)
users = User.where('age > ?', 25)
users = User.where.not(age: nil)

# Joins and includes
posts_with_users = Post.joins(:user).where(users: { age: 18..65 })
users_with_posts = User.includes(:posts).where('posts.created_at > ?', 1.week.ago)

# Aggregations
user_count = User.count
average_age = User.average(:age)
min_age = User.minimum(:age)
max_age = User.maximum(:age)

# Complex queries
users = User.select(:name, :email)
             .where(age: 20..40)
             .order(:name)
             .limit(50)
             .offset(100)
```

### Associations
```ruby
# app/models/post.rb
class Post < ApplicationRecord
  belongs_to :user
  has_many :comments
  has_many :tags, through: :post_tags

  validates :title, presence: true
  validates :content, presence: true
end

# app/models/comment.rb
class Comment < ApplicationRecord
  belongs_to :user
  belongs_to :post

  validates :content, presence: true
end

# Usage
user = User.find(1)
posts = user.posts
post = Post.find(1)
author = post.user
comments = post.comments.includes(:user)
```

## PostgreSQL with pg gem

### Installation
```bash
gem install pg
```

### Basic Usage
```ruby
require 'pg'

begin
  # Connect to database
  conn = PG.connect(
    host: 'localhost',
    port: 5432,
    dbname: 'mydb',
    user: 'myuser',
    password: 'mypassword'
  )

  puts "Connected to PostgreSQL"

  # Create table
  conn.exec("CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
  )")

  # Insert data
  conn.exec_params("INSERT INTO users (name, age, email) VALUES ($1, $2, $3)",
                   ["John Doe", 30, "john@example.com"])

  # Query data
  result = conn.exec_params("SELECT * FROM users WHERE age > $1", [25])

  result.each do |row|
    puts "User: #{row['id']}, #{row['name']}, #{row['age']}, #{row['email']}"
  end

  # Prepared statements
  conn.prepare('insert_user', "INSERT INTO users (name, age, email) VALUES ($1, $2, $3)")

  conn.exec_prepared('insert_user', ["Jane Doe", 25, "jane@example.com"])

ensure
  conn.close if conn
end
```

## MySQL with mysql2 gem

### Installation
```bash
gem install mysql2
```

### Basic Usage
```ruby
require 'mysql2'

begin
  # Connect to database
  client = Mysql2::Client.new(
    host: 'localhost',
    username: 'root',
    password: '',
    database: 'mydb'
  )

  puts "Connected to MySQL"

  # Create table
  client.query("CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
  )")

  # Insert data
  stmt = client.prepare("INSERT INTO users (name, age, email) VALUES (?, ?, ?)")
  stmt.execute("John Doe", 30, "john@example.com")

  # Query data
  results = client.query("SELECT * FROM users WHERE age > 25")

  results.each do |row|
    puts "User: #{row['id']}, #{row['name']}, #{row['age']}, #{row['email']}"
  end

ensure
  client.close if client
end
```

## SQLite with sqlite3 gem

### Installation
```bash
gem install sqlite3
```

### Basic Usage
```ruby
require 'sqlite3'

begin
  # Connect to database (creates file if it doesn't exist)
  db = SQLite3::Database.new 'mydb.db'

  puts "Connected to SQLite"

  # Create table
  db.execute <<-SQL
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      age INTEGER NOT NULL,
      email TEXT UNIQUE NOT NULL
    );
  SQL

  # Insert data
  db.execute("INSERT INTO users (name, age, email) VALUES (?, ?, ?)",
             ["John Doe", 30, "john@example.com"])

  # Query data
  db.execute("SELECT * FROM users WHERE age > ?", [25]) do |row|
    puts "User: #{row[0]}, #{row[1]}, #{row[2]}, #{row[3]}"
  end

  # Prepared statements
  stmt = db.prepare("INSERT INTO users (name, age, email) VALUES (?, ?, ?)")
  stmt.execute("Jane Doe", 25, "jane@example.com")
  stmt.close

ensure
  db.close if db
end
```

## MongoDB with mongo gem

### Installation
```bash
gem install mongo
```

### Basic Usage
```ruby
require 'mongo'

# Connect to MongoDB
client = Mongo::Client.new(['127.0.0.1:27017'], database: 'mydb')

# Get collection
collection = client[:users]

# Insert document
user = {
  name: 'John Doe',
  age: 30,
  email: 'john@example.com',
  created_at: Time.now
}

result = collection.insert_one(user)
puts "Inserted user with ID: #{result.inserted_id}"

# Find documents
users = collection.find(age: { '$gt' => 25 })

users.each do |user|
  puts "User: #{user['name']}, Age: #{user['age']}"
end

# Update document
collection.update_one(
  { name: 'John Doe' },
  { '$set' => { age: 31 } }
)

# Delete document
collection.delete_one(name: 'John Doe')

# Close connection
client.close
```

## Redis with redis gem

### Installation
```bash
gem install redis
```

### Basic Usage
```ruby
require 'redis'

begin
  # Connect to Redis
  redis = Redis.new(host: '127.0.0.1', port: 6379)

  # Strings
  redis.set('key', 'value')
  value = redis.get('key')
  puts "Value: #{value}"

  # Hashes
  redis.hset('user:1', 'name', 'John')
  redis.hset('user:1', 'age', '30')

  user = redis.hgetall('user:1')
  puts user.inspect

  # Lists
  redis.rpush('mylist', ['item1', 'item2', 'item3'])
  items = redis.lrange('mylist', 0, -1)
  puts "List items: #{items.inspect}"

  # Sets
  redis.sadd('myset', ['member1', 'member2', 'member3'])
  members = redis.smembers('myset')
  puts "Set members: #{members.inspect}"

  # Sorted Sets
  redis.zadd('myzset', [[1, 'member1'], [2, 'member2'], [3, 'member3']])
  scores = redis.zrange('myzset', 0, -1, with_scores: true)
  puts "Sorted set: #{scores.inspect}"

ensure
  redis.close if redis
end
```

## Sequel ORM

### Installation
```bash
gem install sequel
```

### Basic Usage
```ruby
require 'sequel'

# Connect to database
DB = Sequel.connect('sqlite://mydb.db')

# Create table
DB.create_table? :users do
  primary_key :id
  String :name, null: false
  Integer :age, null: false
  String :email, unique: true, null: false
end

# Define model
class User < Sequel::Model
  # Validations
  def validate
    super
    errors.add(:name, 'cannot be empty') if name.nil? || name.empty?
    errors.add(:age, 'must be positive') if age.nil? || age <= 0
  end
end

# CRUD Operations
# Create
user = User.create(name: 'John Doe', age: 30, email: 'john@example.com')

# Read
user = User[1]
users = User.all
adults = User.where { age > 25 }

# Update
user = User[1]
user.update(age: 31)

# Delete
user = User[1]
user.delete

# Complex queries
users = User.select(:name, :email)
             .where(age: 20..40)
             .order(:name)
             .limit(10)
```

## DataMapper ORM

### Installation
```bash
gem install data_mapper dm-sqlite-adapter
```

### Basic Usage
```ruby
require 'data_mapper'

# Setup database
DataMapper.setup(:default, 'sqlite:mydb.db')

# Define model
class User
  include DataMapper::Resource

  property :id, Serial
  property :name, String, required: true
  property :age, Integer, required: true
  property :email, String, required: true, unique: true
  property :created_at, DateTime

  # Validations
  validates_presence_of :name, :age, :email
  validates_numericality_of :age, greater_than: 0
end

# Finalize models
DataMapper.finalize
DataMapper.auto_upgrade!

# CRUD Operations
# Create
user = User.create(name: 'John Doe', age: 30, email: 'john@example.com')

# Read
user = User.get(1)
users = User.all
adults = User.all(age: 18..65)

# Update
user = User.get(1)
user.update(age: 31)

# Delete
user = User.get(1)
user.destroy

# Queries
users = User.all(age.gt => 25, order: [:name.asc], limit: 10)
```

## Sinatra with Database

### Basic Sinatra App with ActiveRecord
```ruby
# app.rb
require 'sinatra'
require 'sinatra/activerecord'

# Database configuration
set :database, { adapter: 'sqlite3', database: 'mydb.db' }

# Model
class User < ActiveRecord::Base
  validates :name, presence: true
  validates :email, presence: true, uniqueness: true
end

# Routes
get '/users' do
  @users = User.all
  erb :users
end

post '/users' do
  user = User.new(params[:user])
  if user.save
    redirect '/users'
  else
    @errors = user.errors.full_messages
    erb :new_user
  end
end

get '/users/:id' do
  @user = User.find(params[:id])
  erb :user
end
```

## Best Practices

1. **Connection Management**: Use connection pooling for production applications
2. **Prepared Statements**: Always use parameterized queries to prevent SQL injection
3. **Transactions**: Use database transactions for data consistency
4. **Migrations**: Use migration scripts for schema changes
5. **Error Handling**: Implement comprehensive error handling
6. **Validation**: Validate data at the model level
7. **Indexing**: Create appropriate database indexes for performance
8. **Caching**: Implement caching strategies for frequently accessed data
9. **Security**: Store database credentials securely using environment variables
10. **Testing**: Write comprehensive tests for database operations</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\ruby\ruby-databases.md