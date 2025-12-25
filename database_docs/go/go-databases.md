# Go Database Programming

## Overview
Go has excellent database support through the standard `database/sql` package and various database-specific drivers. Popular ORMs include GORM and sqlx. This document covers the most popular database solutions for Go applications.

## database/sql Package

### Basic Usage with MySQL
```go
package main

import (
    "database/sql"
    "fmt"
    "log"

    _ "github.com/go-sql-driver/mysql"
)

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Age   int    `json:"age"`
    Email string `json:"email"`
}

func main() {
    // Open database connection
    db, err := sql.Open("mysql", "user:password@tcp(localhost:3306)/mydb")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Test connection
    if err := db.Ping(); err != nil {
        log.Fatal(err)
    }
    fmt.Println("Connected to database")

    // Create table
    createTableSQL := `CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
    )`

    if _, err := db.Exec(createTableSQL); err != nil {
        log.Fatal(err)
    }

    // Insert user
    insertSQL := "INSERT INTO users (name, age, email) VALUES (?, ?, ?)"
    result, err := db.Exec(insertSQL, "John Doe", 30, "john@example.com")
    if err != nil {
        log.Fatal(err)
    }

    id, err := result.LastInsertId()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Inserted user with ID: %d\n", id)

    // Query users
    rows, err := db.Query("SELECT id, name, age, email FROM users WHERE age > ?", 25)
    if err != nil {
        log.Fatal(err)
    }
    defer rows.Close()

    var users []User
    for rows.Next() {
        var user User
        if err := rows.Scan(&user.ID, &user.Name, &user.Age, &user.Email); err != nil {
            log.Fatal(err)
        }
        users = append(users, user)
    }

    if err := rows.Err(); err != nil {
        log.Fatal(err)
    }

    for _, user := range users {
        fmt.Printf("User: %d, %s, %d, %s\n", user.ID, user.Name, user.Age, user.Email)
    }
}
```

### Prepared Statements
```go
package main

import (
    "database/sql"
    "fmt"
    "log"

    _ "github.com/go-sql-driver/mysql"
)

func main() {
    db, err := sql.Open("mysql", "user:password@tcp(localhost:3306)/mydb")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Prepare statement
    stmt, err := db.Prepare("INSERT INTO users (name, age, email) VALUES (?, ?, ?)")
    if err != nil {
        log.Fatal(err)
    }
    defer stmt.Close()

    // Execute prepared statement multiple times
    users := []struct {
        name  string
        age   int
        email string
    }{
        {"John Doe", 30, "john@example.com"},
        {"Jane Smith", 25, "jane@example.com"},
        {"Bob Johnson", 35, "bob@example.com"},
    }

    for _, user := range users {
        _, err := stmt.Exec(user.name, user.age, user.email)
        if err != nil {
            log.Printf("Error inserting user %s: %v", user.name, err)
        }
    }

    fmt.Println("All users inserted successfully")
}
```

## PostgreSQL with pq driver

### Installation
```bash
go get github.com/lib/pq
```

### Basic Usage
```go
package main

import (
    "database/sql"
    "fmt"
    "log"

    _ "github.com/lib/pq"
)

func main() {
    // Connection string
    connStr := "host=localhost port=5432 user=myuser password=mypassword dbname=mydb sslmode=disable"

    db, err := sql.Open("postgres", connStr)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    if err := db.Ping(); err != nil {
        log.Fatal(err)
    }
    fmt.Println("Connected to PostgreSQL")

    // Create table
    createTableSQL := `CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INTEGER NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
    )`

    if _, err := db.Exec(createTableSQL); err != nil {
        log.Fatal(err)
    }

    // Insert with returning
    var userID int
    insertSQL := "INSERT INTO users (name, age, email) VALUES ($1, $2, $3) RETURNING id"
    err = db.QueryRow(insertSQL, "John Doe", 30, "john@example.com").Scan(&userID)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Inserted user with ID: %d\n", userID)

    // Query with parameters
    rows, err := db.Query("SELECT id, name, age, email FROM users WHERE age > $1", 25)
    if err != nil {
        log.Fatal(err)
    }
    defer rows.Close()

    for rows.Next() {
        var id int
        var name string
        var age int
        var email string

        if err := rows.Scan(&id, &name, &age, &email); err != nil {
            log.Fatal(err)
        }
        fmt.Printf("User: %d, %s, %d, %s\n", id, name, age, email)
    }
}
```

## SQLite with go-sqlite3

### Installation
```bash
go get github.com/mattn/go-sqlite3
```

### Basic Usage
```go
package main

import (
    "database/sql"
    "fmt"
    "log"

    _ "github.com/mattn/go-sqlite3"
)

func main() {
    // Open SQLite database (creates file if it doesn't exist)
    db, err := sql.Open("sqlite3", "./mydb.db")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    if err := db.Ping(); err != nil {
        log.Fatal(err)
    }
    fmt.Println("Connected to SQLite")

    // Create table
    createTableSQL := `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        email TEXT UNIQUE NOT NULL
    )`

    if _, err := db.Exec(createTableSQL); err != nil {
        log.Fatal(err)
    }

    // Insert user
    result, err := db.Exec("INSERT INTO users (name, age, email) VALUES (?, ?, ?)",
        "John Doe", 30, "john@example.com")
    if err != nil {
        log.Fatal(err)
    }

    id, err := result.LastInsertId()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Inserted user with ID: %d\n", id)

    // Query users
    rows, err := db.Query("SELECT id, name, age, email FROM users WHERE age > ?", 25)
    if err != nil {
        log.Fatal(err)
    }
    defer rows.Close()

    for rows.Next() {
        var id int
        var name string
        var age int
        var email string

        if err := rows.Scan(&id, &name, &age, &email); err != nil {
            log.Fatal(err)
        }
        fmt.Printf("User: %d, %s, %d, %s\n", id, name, age, email)
    }
}
```

## MongoDB with mongo-go-driver

### Installation
```bash
go get go.mongodb.org/mongo-driver/mongo
```

### Basic Usage
```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "go.mongodb.org/mongo-driver/bson"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
)

type User struct {
    ID        interface{} `bson:"_id,omitempty"`
    Name      string      `bson:"name"`
    Age       int         `bson:"age"`
    Email     string      `bson:"email"`
    CreatedAt time.Time   `bson:"created_at"`
}

func main() {
    // Create client
    client, err := mongo.NewClient(options.Client().ApplyURI("mongodb://localhost:27017"))
    if err != nil {
        log.Fatal(err)
    }

    // Connect to MongoDB
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    err = client.Connect(ctx)
    if err != nil {
        log.Fatal(err)
    }
    defer client.Disconnect(ctx)

    // Ping database
    err = client.Ping(ctx, nil)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("Connected to MongoDB")

    // Get collection
    collection := client.Database("mydb").Collection("users")

    // Insert document
    user := User{
        Name:      "John Doe",
        Age:       30,
        Email:     "john@example.com",
        CreatedAt: time.Now(),
    }

    insertResult, err := collection.InsertOne(ctx, user)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Inserted user with ID: %v\n", insertResult.InsertedID)

    // Find documents
    filter := bson.M{"age": bson.M{"$gt": 25}}
    cursor, err := collection.Find(ctx, filter)
    if err != nil {
        log.Fatal(err)
    }
    defer cursor.Close(ctx)

    var users []User
    if err = cursor.All(ctx, &users); err != nil {
        log.Fatal(err)
    }

    for _, user := range users {
        fmt.Printf("User: %s, Age: %d\n", user.Name, user.Age)
    }

    // Update document
    updateFilter := bson.M{"name": "John Doe"}
    update := bson.M{"$set": bson.M{"age": 31}}
    _, err = collection.UpdateOne(ctx, updateFilter, update)
    if err != nil {
        log.Fatal(err)
    }

    // Delete document
    _, err = collection.DeleteOne(ctx, updateFilter)
    if err != nil {
        log.Fatal(err)
    }
}
```

## Redis with go-redis

### Installation
```bash
go get github.com/go-redis/redis/v8
```

### Basic Usage
```go
package main

import (
    "context"
    "fmt"
    "log"

    "github.com/go-redis/redis/v8"
)

func main() {
    // Create client
    rdb := redis.NewClient(&redis.Options{
        Addr: "localhost:6379",
    })
    defer rdb.Close()

    // Ping Redis
    pong, err := rdb.Ping(context.Background()).Result()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("Connected to Redis:", pong)

    ctx := context.Background()

    // Strings
    err = rdb.Set(ctx, "key", "value", 0).Err()
    if err != nil {
        log.Fatal(err)
    }

    value, err := rdb.Get(ctx, "key").Result()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("Value:", value)

    // Hashes
    err = rdb.HSet(ctx, "user:1", "name", "John", "age", "30").Err()
    if err != nil {
        log.Fatal(err)
    }

    user, err := rdb.HGetAll(ctx, "user:1").Result()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("User:", user)

    // Lists
    err = rdb.RPush(ctx, "mylist", "item1", "item2", "item3").Err()
    if err != nil {
        log.Fatal(err)
    }

    items, err := rdb.LRange(ctx, "mylist", 0, -1).Result()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("List items:", items)

    // Sets
    err = rdb.SAdd(ctx, "myset", "member1", "member2", "member3").Err()
    if err != nil {
        log.Fatal(err)
    }

    members, err := rdb.SMembers(ctx, "myset").Result()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("Set members:", members)

    // Sorted Sets
    members := []redis.Z{
        {Score: 1, Member: "member1"},
        {Score: 2, Member: "member2"},
        {Score: 3, Member: "member3"},
    }

    err = rdb.ZAdd(ctx, "myzset", &redis.ZAddArgs{Members: members}).Err()
    if err != nil {
        log.Fatal(err)
    }

    scores, err := rdb.ZRangeWithScores(ctx, "myzset", 0, -1).Result()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("Sorted set:", scores)
}
```

## GORM ORM

### Installation
```bash
go get gorm.io/gorm
go get gorm.io/driver/mysql  # or driver/postgres, driver/sqlite
```

### Basic Usage
```go
package main

import (
    "fmt"
    "log"

    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

type User struct {
    ID        uint   `gorm:"primaryKey"`
    Name      string `gorm:"not null"`
    Age       int    `gorm:"not null"`
    Email     string `gorm:"uniqueIndex;not null"`
    CreatedAt time.Time
    UpdatedAt time.Time
}

func main() {
    // Connect to database
    dsn := "user:password@tcp(localhost:3306)/mydb?charset=utf8mb4&parseTime=True&loc=Local"
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    if err != nil {
        log.Fatal(err)
    }

    // Auto migrate
    db.AutoMigrate(&User{})

    // Create user
    user := User{Name: "John Doe", Age: 30, Email: "john@example.com"}
    result := db.Create(&user)
    if result.Error != nil {
        log.Fatal(result.Error)
    }
    fmt.Printf("Created user with ID: %d\n", user.ID)

    // Read user
    var foundUser User
    db.First(&foundUser, user.ID)
    fmt.Printf("Found user: %s, Age: %d\n", foundUser.Name, foundUser.Age)

    // Update user
    db.Model(&user).Update("Age", 31)

    // Delete user
    db.Delete(&user)

    // Query with conditions
    var users []User
    db.Where("age > ?", 25).Find(&users)

    for _, u := range users {
        fmt.Printf("User: %s, Age: %d\n", u.Name, u.Age)
    }
}
```

### Advanced GORM Features
```go
package main

import (
    "gorm.io/gorm"
    "time"
)

type Post struct {
    ID          uint      `gorm:"primaryKey"`
    Title       string    `gorm:"not null"`
    Content     string    `gorm:"type:text"`
    UserID      uint      `gorm:"not null"`
    User        User      `gorm:"foreignKey:UserID"`
    Tags        []Tag     `gorm:"many2many:post_tags"`
    PublishedAt *time.Time
    CreatedAt   time.Time
    UpdatedAt   time.Time
}

type Tag struct {
    ID        uint      `gorm:"primaryKey"`
    Name      string    `gorm:"uniqueIndex;not null"`
    Posts     []Post    `gorm:"many2many:post_tags"`
    CreatedAt time.Time
    UpdatedAt time.Time
}

// Preloading associations
func getUsersWithPosts(db *gorm.DB) {
    var users []User
    db.Preload("Posts").Find(&users)

    for _, user := range users {
        fmt.Printf("User: %s\n", user.Name)
        for _, post := range user.Posts {
            fmt.Printf("  Post: %s\n", post.Title)
        }
    }
}

// Transactions
func createUserWithPosts(db *gorm.DB, user User, posts []Post) error {
    return db.Transaction(func(tx *gorm.DB) error {
        if err := tx.Create(&user).Error; err != nil {
            return err
        }

        for i := range posts {
            posts[i].UserID = user.ID
        }

        if err := tx.Create(&posts).Error; err != nil {
            return err
        }

        return nil
    })
}
```

## sqlx Library

### Installation
```bash
go get github.com/jmoiron/sqlx
```

### Basic Usage
```go
package main

import (
    "fmt"
    "log"

    "github.com/jmoiron/sqlx"
    _ "github.com/go-sql-driver/mysql"
)

type User struct {
    ID    int    `db:"id"`
    Name  string `db:"name"`
    Age   int    `db:"age"`
    Email string `db:"email"`
}

func main() {
    // Connect to database
    db, err := sqlx.Connect("mysql", "user:password@tcp(localhost:3306)/mydb")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Create table
    schema := `CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
    )`

    db.MustExec(schema)

    // Insert user
    insertQuery := `INSERT INTO users (name, age, email) VALUES (?, ?, ?)`
    result, err := db.Exec(insertQuery, "John Doe", 30, "john@example.com")
    if err != nil {
        log.Fatal(err)
    }

    id, err := result.LastInsertId()
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Inserted user with ID: %d\n", id)

    // Query single user
    var user User
    err = db.Get(&user, "SELECT * FROM users WHERE id = ?", id)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("User: %+v\n", user)

    // Query multiple users
    var users []User
    err = db.Select(&users, "SELECT * FROM users WHERE age > ?", 25)
    if err != nil {
        log.Fatal(err)
    }

    for _, u := range users {
        fmt.Printf("User: %s, Age: %d\n", u.Name, u.Age)
    }

    // Named queries
    userNamed := User{Name: "Jane Doe", Age: 25, Email: "jane@example.com"}
    insertNamed := `INSERT INTO users (name, age, email) VALUES (:name, :age, :email)`
    _, err = db.NamedExec(insertNamed, userNamed)
    if err != nil {
        log.Fatal(err)
    }
}
```

## Best Practices

1. **Connection Pooling**: Use `sql.DB` connection pooling for better performance
2. **Prepared Statements**: Use prepared statements for repeated queries
3. **Error Handling**: Always check for errors and handle them appropriately
4. **Context Usage**: Use context for timeout and cancellation
5. **Resource Management**: Close connections, statements, and result sets properly
6. **Transactions**: Use transactions for data consistency
7. **Migrations**: Use migration tools for schema changes
8. **Security**: Use parameterized queries to prevent SQL injection
9. **Logging**: Implement proper logging for database operations
10. **Testing**: Write unit tests for database operations using test databases</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\go\go-databases.md