# Rust Database Programming

## Overview
Rust has excellent database support through crates like `rusqlite`, `diesel`, `sqlx`, and `tokio-postgres`. This document covers the most popular database solutions for Rust applications.

## rusqlite (SQLite)

### Installation
```toml
[dependencies]
rusqlite = { version = "0.29", features = ["bundled"] }
```

### Basic Usage
```rust
use rusqlite::{Connection, Result};
use std::collections::HashMap;

#[derive(Debug)]
struct User {
    id: i32,
    name: String,
    age: i32,
    email: String,
}

fn main() -> Result<()> {
    // Open database connection
    let conn = Connection::open("mydb.db")?;

    // Create table
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL
        )",
        [],
    )?;

    // Insert user
    conn.execute(
        "INSERT INTO users (name, age, email) VALUES (?1, ?2, ?3)",
        ["John Doe", "30", "john@example.com"],
    )?;

    // Query users
    let mut stmt = conn.prepare("SELECT id, name, age, email FROM users WHERE age > ?1")?;
    let user_iter = stmt.query_map([25], |row| {
        Ok(User {
            id: row.get(0)?,
            name: row.get(1)?,
            age: row.get(2)?,
            email: row.get(3)?,
        })
    })?;

    for user in user_iter {
        println!("Found user: {:?}", user.unwrap());
    }

    Ok(())
}
```

### Prepared Statements
```rust
use rusqlite::{Connection, Result};

fn main() -> Result<()> {
    let conn = Connection::open("mydb.db")?;

    // Prepare statement
    let mut stmt = conn.prepare("INSERT INTO users (name, age, email) VALUES (?1, ?2, ?3)")?;

    // Execute multiple times
    let users = vec![
        ("John Doe", 30, "john@example.com"),
        ("Jane Smith", 25, "jane@example.com"),
        ("Bob Johnson", 35, "bob@example.com"),
    ];

    for (name, age, email) in users {
        stmt.execute([name, &age.to_string(), email])?;
    }

    println!("All users inserted successfully");
    Ok(())
}
```

## Diesel ORM

### Installation
```toml
[dependencies]
diesel = { version = "2.1", features = ["sqlite", "r2d2"] }
dotenvy = "0.15"
```

### Schema Definition
```rust
// migrations/2023-01-01-000000_create_users/up.sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Model Definition
```rust
// src/models.rs
use diesel::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Queryable, Selectable, Serialize, Deserialize, Debug)]
#[diesel(table_name = crate::schema::users)]
#[diesel(check_for_backend(diesel::sqlite::Sqlite))]
pub struct User {
    pub id: i32,
    pub name: String,
    pub age: i32,
    pub email: String,
    pub created_at: String,
}

#[derive(Insertable, Serialize, Deserialize)]
#[diesel(table_name = crate::schema::users)]
pub struct NewUser<'a> {
    pub name: &'a str,
    pub age: i32,
    pub email: &'a str,
}

#[derive(AsChangeset, Serialize, Deserialize)]
#[diesel(table_name = crate::schema::users)]
pub struct UpdateUser {
    pub name: Option<String>,
    pub age: Option<i32>,
    pub email: Option<String>,
}
```

### Schema
```rust
// src/schema.rs
diesel::table! {
    users (id) {
        id -> Integer,
        name -> Text,
        age -> Integer,
        email -> Text,
        created_at -> Text,
    }
}
```

### Database Operations
```rust
// src/lib.rs or main.rs
use diesel::prelude::*;
use dotenvy::dotenv;
use std::env;

pub fn establish_connection() -> SqliteConnection {
    dotenv().ok();

    let database_url = env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");
    SqliteConnection::establish(&database_url)
        .unwrap_or_else(|_| panic!("Error connecting to {}", database_url))
}

use crate::models::{NewUser, User, UpdateUser};
use crate::schema::users;

pub fn create_user(conn: &mut SqliteConnection, name: &str, age: i32, email: &str) -> User {
    let new_user = NewUser { name, age, email };

    diesel::insert_into(users::table)
        .values(&new_user)
        .returning(User::as_returning())
        .get_result(conn)
        .expect("Error saving new user")
}

pub fn get_user(conn: &mut SqliteConnection, user_id: i32) -> Option<User> {
    users::table
        .find(user_id)
        .select(User::as_select())
        .first(conn)
        .optional()
        .expect("Error loading user")
}

pub fn get_all_users(conn: &mut SqliteConnection) -> Vec<User> {
    users::table
        .select(User::as_select())
        .load(conn)
        .expect("Error loading users")
}

pub fn update_user(conn: &mut SqliteConnection, user_id: i32, changes: UpdateUser) -> User {
    diesel::update(users::table.find(user_id))
        .set(&changes)
        .returning(User::as_returning())
        .get_result(conn)
        .expect("Error updating user")
}

pub fn delete_user(conn: &mut SqliteConnection, user_id: i32) -> usize {
    diesel::delete(users::table.find(user_id))
        .execute(conn)
        .expect("Error deleting user")
}

pub fn get_adult_users(conn: &mut SqliteConnection) -> Vec<User> {
    users::table
        .filter(users::age.gt(18))
        .select(User::as_select())
        .load(conn)
        .expect("Error loading adult users")
}
```

### Usage
```rust
use std::env;
use diesel_demo::*;

fn main() {
    dotenv().ok();
    let mut conn = establish_connection();

    // Create user
    let user = create_user(&mut conn, "John Doe", 30, "john@example.com");
    println!("Created user: {:?}", user);

    // Get user
    if let Some(user) = get_user(&mut conn, user.id) {
        println!("Found user: {:?}", user);
    }

    // Update user
    let updated_user = update_user(&mut conn, user.id, UpdateUser {
        name: Some("John Smith".to_string()),
        age: Some(31),
        email: None,
    });
    println!("Updated user: {:?}", updated_user);

    // Get all users
    let users = get_all_users(&mut conn);
    println!("All users: {:?}", users);

    // Get adult users
    let adults = get_adult_users(&mut conn);
    println!("Adult users: {:?}", adults);

    // Delete user
    let deleted_count = delete_user(&mut conn, user.id);
    println!("Deleted {} user(s)", deleted_count);
}
```

## PostgreSQL with tokio-postgres

### Installation
```toml
[dependencies]
tokio-postgres = "0.7"
tokio = { version = "1", features = ["full"] }
```

### Basic Usage
```rust
use tokio_postgres::{NoTls, Error};

#[derive(Debug)]
struct User {
    id: i32,
    name: String,
    age: i32,
    email: String,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Connect to database
    let (client, connection) =
        tokio_postgres::connect("host=localhost user=myuser password=mypassword dbname=mydb", NoTls).await?;

    // Spawn connection handling task
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("connection error: {}", e);
        }
    });

    // Create table
    client.execute(
        "CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL
        )",
        &[],
    ).await?;

    // Insert user
    let name = "John Doe";
    let age = 30;
    let email = "john@example.com";

    let row = client.query_one(
        "INSERT INTO users (name, age, email) VALUES ($1, $2, $3) RETURNING id",
        &[&name, &age, &email],
    ).await?;

    let id: i32 = row.get(0);
    println!("Inserted user with ID: {}", id);

    // Query users
    for row in client.query("SELECT id, name, age, email FROM users WHERE age > $1", &[&25]).await? {
        let user = User {
            id: row.get(0),
            name: row.get(1),
            age: row.get(2),
            email: row.get(3),
        };
        println!("User: {:?}", user);
    }

    Ok(())
}
```

## MongoDB with mongodb crate

### Installation
```toml
[dependencies]
mongodb = "2.8"
tokio = { version = "1", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
```

### Basic Usage
```rust
use mongodb::{bson::doc, Client, Collection};
use serde::{Deserialize, Serialize};
use std::error::Error;

#[derive(Debug, Serialize, Deserialize)]
struct User {
    #[serde(rename = "_id", skip_serializing_if = "Option::is_none")]
    id: Option<bson::oid::ObjectId>,
    name: String,
    age: i32,
    email: String,
    #[serde(with = "bson::serde_helpers::chrono_datetime_as_bson_datetime")]
    created_at: chrono::DateTime<chrono::Utc>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Create client
    let client = Client::with_uri_str("mongodb://localhost:27017").await?;
    let db = client.database("mydb");
    let collection: Collection<User> = db.collection("users");

    // Insert document
    let user = User {
        id: None,
        name: "John Doe".to_string(),
        age: 30,
        email: "john@example.com".to_string(),
        created_at: chrono::Utc::now(),
    };

    let insert_result = collection.insert_one(user, None).await?;
    println!("Inserted user with ID: {:?}", insert_result.inserted_id);

    // Find documents
    let filter = doc! { "age": { "$gt": 25 } };
    let mut cursor = collection.find(filter, None).await?;

    while let Some(result) = cursor.try_next().await? {
        println!("User: {:?}", result);
    }

    // Update document
    let update_filter = doc! { "name": "John Doe" };
    let update = doc! { "$set": { "age": 31 } };
    collection.update_one(update_filter, update, None).await?;

    // Delete document
    collection.delete_one(update_filter, None).await?;

    Ok(())
}
```

## Redis with redis crate

### Installation
```toml
[dependencies]
redis = { version = "0.23", features = ["tokio-comp"] }
tokio = { version = "1", features = ["full"] }
```

### Basic Usage
```rust
use redis::{AsyncCommands, Client};
use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Create client
    let client = Client::open("redis://127.0.0.1/")?;
    let mut con = client.get_async_connection().await?;

    // Strings
    let _: () = con.set("key", "value").await?;
    let value: String = con.get("key").await?;
    println!("Value: {}", value);

    // Hashes
    let _: () = con.hset("user:1", "name", "John").await?;
    let _: () = con.hset("user:1", "age", "30").await?;

    let user: std::collections::HashMap<String, String> = con.hgetall("user:1").await?;
    println!("User: {:?}", user);

    // Lists
    let _: () = con.rpush("mylist", &["item1", "item2", "item3"]).await?;
    let items: Vec<String> = con.lrange("mylist", 0, -1).await?;
    println!("List items: {:?}", items);

    // Sets
    let _: () = con.sadd("myset", &["member1", "member2", "member3"]).await?;
    let members: Vec<String> = con.smembers("myset").await?;
    println!("Set members: {:?}", members);

    // Sorted Sets
    let _: () = con.zadd("myzset", "member1", 1).await?;
    let _: () = con.zadd("myzset", "member2", 2).await?;
    let _: () = con.zadd("myzset", "member3", 3).await?;

    let scores: Vec<(String, f64)> = con.zrange_withscores("myzset", 0, -1).await?;
    println!("Sorted set: {:?}", scores);

    Ok(())
}
```

## SQLx

### Installation
```toml
[dependencies]
sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "sqlite"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
```

### Basic Usage
```rust
use sqlx::sqlite::SqlitePool;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
struct User {
    id: i64,
    name: String,
    age: i32,
    email: String,
}

#[tokio::main]
async fn main() -> Result<(), sqlx::Error> {
    // Create connection pool
    let pool = SqlitePool::connect("sqlite:mydb.db").await?;

    // Create table
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL
        )"
    )
    .execute(&pool)
    .await?;

    // Insert user
    let user_id = sqlx::query(
        "INSERT INTO users (name, age, email) VALUES (?, ?, ?) RETURNING id"
    )
    .bind("John Doe")
    .bind(30)
    .bind("john@example.com")
    .fetch_one(&pool)
    .await?
    .get::<i64, _>(0);

    println!("Inserted user with ID: {}", user_id);

    // Query users
    let users = sqlx::query_as::<_, User>(
        "SELECT id, name, age, email FROM users WHERE age > ?"
    )
    .bind(25)
    .fetch_all(&pool)
    .await?;

    for user in users {
        println!("User: {:?}", user);
    }

    // Named parameters
    let user: User = sqlx::query_as(
        "SELECT * FROM users WHERE email = ?"
    )
    .bind("john@example.com")
    .fetch_one(&pool)
    .await?;

    println!("Found user: {:?}", user);

    pool.close().await;
    Ok(())
}
```

## SeaORM

### Installation
```toml
[dependencies]
sea-orm = { version = "0.12", features = ["sqlx-sqlite", "runtime-tokio-rustls", "macros"] }
```

### Entity Definition
```rust
// src/entities/user.rs
use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Serialize, Deserialize)]
#[sea_orm(table_name = "users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub name: String,
    pub age: i32,
    pub email: String,
    pub created_at: DateTime,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {}

impl ActiveModelBehavior for ActiveModel {}
```

### Migration
```rust
// src/migration/m20230101_000001_create_users.rs
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager
            .create_table(
                Table::create()
                    .table(User::Table)
                    .if_not_exists()
                    .col(ColumnDef::new(User::Id).integer().not_null().auto_increment().primary_key())
                    .col(ColumnDef::new(User::Name).string().not_null())
                    .col(ColumnDef::new(User::Age).integer().not_null())
                    .col(ColumnDef::new(User::Email).string().unique_key().not_null())
                    .col(ColumnDef::new(User::CreatedAt).timestamp().default(Expr::current_timestamp()).not_null())
                    .to_owned(),
            )
            .await
    }

    async fn down(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager
            .drop_table(Table::drop().table(User::Table).to_owned())
            .await
    }
}
```

### CRUD Operations
```rust
use sea_orm::{Database, DatabaseConnection, EntityTrait, QueryFilter, ActiveValue, ActiveModelTrait};
use entities::user::{Entity as User, Model, ActiveModel};

pub struct UserService {
    db: DatabaseConnection,
}

impl UserService {
    pub fn new(db: DatabaseConnection) -> Self {
        Self { db }
    }

    pub async fn create_user(&self, name: String, age: i32, email: String) -> Result<Model, sea_orm::DbErr> {
        let user = ActiveModel {
            name: ActiveValue::Set(name),
            age: ActiveValue::Set(age),
            email: ActiveValue::Set(email),
            ..Default::default()
        };

        user.insert(&self.db).await
    }

    pub async fn get_user(&self, id: i32) -> Result<Option<Model>, sea_orm::DbErr> {
        User::find_by_id(id).one(&self.db).await
    }

    pub async fn get_all_users(&self) -> Result<Vec<Model>, sea_orm::DbErr> {
        User::find().all(&self.db).await
    }

    pub async fn update_user(&self, id: i32, name: Option<String>, age: Option<i32>) -> Result<Model, sea_orm::DbErr> {
        let mut user: ActiveModel = User::find_by_id(id)
            .one(&self.db)
            .await?
            .ok_or_else(|| sea_orm::DbErr::RecordNotFound("User not found".to_string()))?
            .into();

        if let Some(name) = name {
            user.name = ActiveValue::Set(name);
        }
        if let Some(age) = age {
            user.age = ActiveValue::Set(age);
        }

        user.update(&self.db).await
    }

    pub async fn delete_user(&self, id: i32) -> Result<(), sea_orm::DbErr> {
        User::delete_by_id(id).exec(&self.db).await?;
        Ok(())
    }

    pub async fn get_adult_users(&self) -> Result<Vec<Model>, sea_orm::DbErr> {
        User::find()
            .filter(user::Column::Age.gt(18))
            .all(&self.db)
            .await
    }
}
```

## Best Practices

1. **Error Handling**: Use `Result` types and proper error propagation
2. **Connection Pooling**: Use connection pools for better performance
3. **Prepared Statements**: Use parameterized queries to prevent SQL injection
4. **Async/Await**: Use async operations for better concurrency
5. **Migrations**: Use migration tools for schema changes
6. **Type Safety**: Leverage Rust's type system for database operations
7. **Resource Management**: Use RAII for proper resource cleanup
8. **Testing**: Write comprehensive tests for database operations
9. **Logging**: Implement proper logging for database operations
10. **Security**: Validate inputs and use secure connection practices</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\rust\rust-databases.md