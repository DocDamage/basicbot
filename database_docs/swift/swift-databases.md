# Swift Database Programming

## Overview
Swift has excellent database support through SQLite.swift, Core Data, GRDB, and various database-specific libraries. This document covers the most popular database solutions for Swift applications.

## SQLite.swift

### Installation
```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/stephencelis/SQLite.swift.git", from: "0.14.1")
]
```

### Basic Usage
```swift
import SQLite

struct User {
    let id: Int64
    let name: String
    let age: Int
    let email: String
}

do {
    // Open database
    let db = try Connection("mydb.db")

    // Create table
    let users = Table("users")
    let id = Expression<Int64>("id")
    let name = Expression<String>("name")
    let age = Expression<Int>("age")
    let email = Expression<String>("email")

    try db.run(users.create(ifNotExists: true) { t in
        t.column(id, primaryKey: true)
        t.column(name)
        t.column(age)
        t.column(email, unique: true)
    })

    // Insert user
    let insert = users.insert(name <- "John Doe", age <- 30, email <- "john@example.com")
    let rowid = try db.run(insert)
    print("Inserted user with rowid: \(rowid)")

    // Query users
    let query = users.filter(age > 25)
    for user in try db.prepare(query) {
        let user = User(
            id: user[id],
            name: user[name],
            age: user[age],
            email: user[email]
        )
        print("User: \(user.name), Age: \(user.age)")
    }

} catch {
    print("Error: \(error)")
}
```

### Advanced Queries
```swift
import SQLite

do {
    let db = try Connection("mydb.db")
    let users = Table("users")
    let name = Expression<String>("name")
    let age = Expression<Int>("age")
    let email = Expression<String>("email")

    // Insert multiple users
    let usersToInsert = [
        ["name": "John Doe", "age": 30, "email": "john@example.com"],
        ["name": "Jane Smith", "age": 25, "email": "jane@example.com"],
        ["name": "Bob Johnson", "age": 35, "email": "bob@example.com"]
    ]

    for userData in usersToInsert {
        let insert = users.insert(
            name <- userData["name"]!,
            age <- Int(userData["age"]!)!,
            email <- userData["email"]!
        )
        try db.run(insert)
    }

    // Complex queries
    let adults = users.filter(age >= 18)
    let count = try db.scalar(adults.count)
    print("Number of adults: \(count)")

    // Join example (if we had a posts table)
    // let posts = Table("posts")
    // let userPosts = users.join(posts, on: users[id] == posts[Expression<Int64>("user_id")])

    // Update
    let userToUpdate = users.filter(email == "john@example.com")
    try db.run(userToUpdate.update(age <- 31))

    // Delete
    let userToDelete = users.filter(email == "john@example.com")
    try db.run(userToDelete.delete())

} catch {
    print("Error: \(error)")
}
```

## Core Data

### Model Definition
```swift
// User+CoreDataClass.swift
import Foundation
import CoreData

@objc(User)
public class User: NSManagedObject {
    @NSManaged public var id: UUID
    @NSManaged public var name: String
    @NSManaged public var age: Int16
    @NSManaged public var email: String
    @NSManaged public var createdAt: Date
}
```

```swift
// User+CoreDataProperties.swift
import Foundation
import CoreData

extension User {
    @nonobjc public class func fetchRequest() -> NSFetchRequest<User> {
        return NSFetchRequest<User>(entityName: "User")
    }

    @NSManaged public var id: UUID
    @NSManaged public var name: String
    @NSManaged public var age: Int16
    @NSManaged public var email: String
    @NSManaged public var createdAt: Date
}
```

### Core Data Stack
```swift
import CoreData

class CoreDataManager {
    static let shared = CoreDataManager()

    let persistentContainer: NSPersistentContainer

    private init() {
        persistentContainer = NSPersistentContainer(name: "MyAppModel")
        persistentContainer.loadPersistentStores { (description, error) in
            if let error = error {
                fatalError("Unable to load persistent stores: \(error.localizedDescription)")
            }
        }
    }

    var context: NSManagedObjectContext {
        return persistentContainer.viewContext
    }

    func saveContext() {
        let context = persistentContainer.viewContext
        if context.hasChanges {
            do {
                try context.save()
            } catch {
                let nserror = error as NSError
                fatalError("Unresolved error \(nserror), \(nserror.userInfo)")
            }
        }
    }
}
```

### CRUD Operations
```swift
import CoreData

class UserManager {
    private let context = CoreDataManager.shared.context

    // Create
    func createUser(name: String, age: Int16, email: String) -> User? {
        let user = User(context: context)
        user.id = UUID()
        user.name = name
        user.age = age
        user.email = email
        user.createdAt = Date()

        do {
            try context.save()
            return user
        } catch {
            print("Error saving user: \(error)")
            return nil
        }
    }

    // Read
    func getUser(withId id: UUID) -> User? {
        let fetchRequest: NSFetchRequest<User> = User.fetchRequest()
        fetchRequest.predicate = NSPredicate(format: "id == %@", id as CVarArg)

        do {
            let users = try context.fetch(fetchRequest)
            return users.first
        } catch {
            print("Error fetching user: \(error)")
            return nil
        }
    }

    // Read All
    func getAllUsers() -> [User] {
        let fetchRequest: NSFetchRequest<User> = User.fetchRequest()
        fetchRequest.sortDescriptors = [NSSortDescriptor(key: "name", ascending: true)]

        do {
            return try context.fetch(fetchRequest)
        } catch {
            print("Error fetching users: \(error)")
            return []
        }
    }

    // Update
    func updateUser(_ user: User, name: String? = nil, age: Int16? = nil, email: String? = nil) {
        if let name = name {
            user.name = name
        }
        if let age = age {
            user.age = age
        }
        if let email = email {
            user.email = email
        }

        CoreDataManager.shared.saveContext()
    }

    // Delete
    func deleteUser(_ user: User) {
        context.delete(user)
        CoreDataManager.shared.saveContext()
    }

    // Query with predicates
    func getAdultUsers() -> [User] {
        let fetchRequest: NSFetchRequest<User> = User.fetchRequest()
        fetchRequest.predicate = NSPredicate(format: "age >= %d", 18)

        do {
            return try context.fetch(fetchRequest)
        } catch {
            print("Error fetching adult users: \(error)")
            return []
        }
    }
}
```

### Usage
```swift
let userManager = UserManager()

// Create user
if let user = userManager.createUser(name: "John Doe", age: 30, email: "john@example.com") {
    print("Created user: \(user.name)")
}

// Get all users
let users = userManager.getAllUsers()
for user in users {
    print("User: \(user.name), Age: \(user.age)")
}

// Update user
if let user = users.first {
    userManager.updateUser(user, age: 31)
}

// Get adult users
let adults = userManager.getAdultUsers()
print("Number of adult users: \(adults.count)")
```

## GRDB

### Installation
```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/groue/GRDB.swift.git", from: "6.0.0")
]
```

### Model Definition
```swift
import GRDB

struct User: Codable, FetchableRecord, PersistableRecord {
    var id: Int64?
    var name: String
    var age: Int
    var email: String
    var createdAt: Date

    // Table name
    static let databaseTableName = "users"

    // Column names
    enum Columns: String, ColumnExpression {
        case id, name, age, email, createdAt
    }

    // Initialize from database row
    init(row: Row) throws {
        id = row[Columns.id]
        name = row[Columns.name]
        age = row[Columns.age]
        email = row[Columns.email]
        createdAt = row[Columns.createdAt]
    }

    // Encode to database
    func encode(to container: inout PersistenceContainer) throws {
        container[Columns.id] = id
        container[Columns.name] = name
        container[Columns.age] = age
        container[Columns.email] = email
        container[Columns.createdAt] = createdAt
    }
}
```

### Database Manager
```swift
import GRDB

class DatabaseManager {
    static let shared = DatabaseManager()

    let dbQueue: DatabaseQueue

    private init() {
        do {
            let databaseURL = try FileManager.default
                .url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
                .appendingPathComponent("mydb.sqlite")

            dbQueue = try DatabaseQueue(path: databaseURL.path)

            try migrator.migrate(dbQueue)
        } catch {
            fatalError("Unable to initialize database: \(error)")
        }
    }

    private var migrator: DatabaseMigrator {
        var migrator = DatabaseMigrator()

        migrator.registerMigration("createUsers") { db in
            try db.create(table: "users") { t in
                t.autoIncrementedPrimaryKey("id")
                t.column("name", .text).notNull()
                t.column("age", .integer).notNull()
                t.column("email", .text).notNull().unique()
                t.column("createdAt", .datetime).notNull()
            }
        }

        return migrator
    }
}
```

### CRUD Operations
```swift
import GRDB

class UserManager {
    private let dbQueue = DatabaseManager.shared.dbQueue

    // Create
    func createUser(name: String, age: Int, email: String) throws -> User {
        try dbQueue.write { db in
            var user = User(id: nil, name: name, age: age, email: email, createdAt: Date())
            try user.insert(db)
            return user
        }
    }

    // Read
    func getUser(id: Int64) throws -> User? {
        try dbQueue.read { db in
            try User.fetchOne(db, key: id)
        }
    }

    // Read All
    func getAllUsers() throws -> [User] {
        try dbQueue.read { db in
            try User.fetchAll(db)
        }
    }

    // Update
    func updateUser(_ user: User, name: String? = nil, age: Int? = nil) throws {
        try dbQueue.write { db in
            var updatedUser = user
            if let name = name {
                updatedUser.name = name
            }
            if let age = age {
                updatedUser.age = age
            }
            try updatedUser.update(db)
        }
    }

    // Delete
    func deleteUser(id: Int64) throws {
        try dbQueue.write { db in
            _ = try User.deleteOne(db, key: id)
        }
    }

    // Query with filters
    func getAdultUsers() throws -> [User] {
        try dbQueue.read { db in
            try User
                .filter(Column("age") >= 18)
                .fetchAll(db)
        }
    }

    // Complex queries
    func searchUsers(namePattern: String) throws -> [User] {
        try dbQueue.read { db in
            try User
                .filter(Column("name").like("%\(namePattern)%"))
                .order(Column("name"))
                .fetchAll(db)
        }
    }
}
```

### Usage
```swift
let userManager = UserManager()

do {
    // Create user
    let user = try userManager.createUser(name: "John Doe", age: 30, email: "john@example.com")
    print("Created user: \(user.name)")

    // Get all users
    let users = try userManager.getAllUsers()
    for user in users {
        print("User: \(user.name), Age: \(user.age)")
    }

    // Update user
    if let user = users.first {
        try userManager.updateUser(user, age: 31)
    }

    // Get adult users
    let adults = try userManager.getAdultUsers()
    print("Number of adult users: \(adults.count)")

    // Search users
    let searchResults = try userManager.searchUsers(namePattern: "John")
    print("Search results: \(searchResults.count)")

} catch {
    print("Database error: \(error)")
}
```

## PostgreSQL with PostgresClientKit

### Installation
```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/codewinsdotcom/PostgresClientKit.git", from: "1.0.0")
]
```

### Basic Usage
```swift
import PostgresClientKit

do {
    // Create connection
    var connection = try Connection(
        host: "localhost",
        port: 5432,
        user: "myuser",
        password: "mypassword",
        database: "mydb"
    )

    // Create table
    let createTableSQL = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """

    let createStatement = try connection.prepareStatement(text: createTableSQL)
    defer { createStatement.close() }
    try createStatement.execute()

    // Insert user
    let insertSQL = "INSERT INTO users (name, age, email) VALUES ($1, $2, $3) RETURNING id"
    let insertStatement = try connection.prepareStatement(text: insertSQL)
    defer { insertStatement.close() }

    try insertStatement.execute(parameterValues: ["John Doe", 30, "john@example.com"])

    if let result = try insertStatement.result(), let row = result.rows.first {
        let id = try row.get().columns[0].int()
        print("Inserted user with ID: \(id)")
    }

    // Query users
    let selectSQL = "SELECT id, name, age, email FROM users WHERE age > $1"
    let selectStatement = try connection.prepareStatement(text: selectSQL)
    defer { selectStatement.close() }

    try selectStatement.execute(parameterValues: [25])

    if let result = try selectStatement.result() {
        for row in result.rows {
            let columns = try row.get().columns
            let id = try columns[0].int()
            let name = try columns[1].string()
            let age = try columns[2].int()
            let email = try columns[3].string()

            print("User: \(id), \(name), \(age), \(email)")
        }
    }

    connection.close()

} catch {
    print("Database error: \(error)")
}
```

## MongoDB with MongoSwift

### Installation
```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/mongodb/mongo-swift-driver.git", from: "1.0.0")
]
```

### Basic Usage
```swift
import MongoSwift
import NIO

struct User: Codable {
    let id: BSONObjectID?
    let name: String
    let age: Int
    let email: String
    let createdAt: Date
}

class MongoDBManager {
    private let client: MongoClient
    private let database: MongoDatabase
    private let collection: MongoCollection<User>

    init() throws {
        client = try MongoClient("mongodb://localhost:27017")
        database = client.db("mydb")
        collection = try database.collection("users", withType: User.self)
    }

    func createUser(name: String, age: Int, email: String) async throws -> User {
        let user = User(id: nil, name: name, age: age, email: email, createdAt: Date())
        let insertResult = try await collection.insertOne(user)
        return user
    }

    func getAllUsers() async throws -> [User] {
        let users = try await collection.find().toArray()
        return users
    }

    func getAdultUsers() async throws -> [User] {
        let filter = ["age": ["$gte": 18]] as Document
        let users = try await collection.find(filter).toArray()
        return users
    }

    func updateUser(email: String, newAge: Int) async throws {
        let filter = ["email": email] as Document
        let update = ["$set": ["age": newAge]] as Document
        try await collection.updateOne(filter: filter, update: update)
    }

    func deleteUser(email: String) async throws {
        let filter = ["email": email] as Document
        try await collection.deleteOne(filter)
    }

    func close() {
        client.close()
    }
}

// Usage
do {
    let mongoManager = try MongoDBManager()

    // Create user
    let user = try await mongoManager.createUser(name: "John Doe", age: 30, email: "john@example.com")
    print("Created user: \(user.name)")

    // Get all users
    let users = try await mongoManager.getAllUsers()
    for user in users {
        print("User: \(user.name), Age: \(user.age)")
    }

    // Get adult users
    let adults = try await mongoManager.getAdultUsers()
    print("Number of adult users: \(adults.count)")

    // Update user
    try await mongoManager.updateUser(email: "john@example.com", newAge: 31)

    // Delete user
    try await mongoManager.deleteUser(email: "john@example.com")

    mongoManager.close()

} catch {
    print("MongoDB error: \(error)")
}
```

## Best Practices

1. **Error Handling**: Use Swift's error handling with do-catch blocks
2. **Memory Management**: Use ARC and proper resource cleanup
3. **Thread Safety**: Use appropriate concurrency models for database operations
4. **Prepared Statements**: Use parameterized queries to prevent SQL injection
5. **Connection Pooling**: Use connection pools for better performance
6. **Migrations**: Implement proper database migration strategies
7. **Type Safety**: Leverage Swift's type system for database operations
8. **Testing**: Write comprehensive unit tests for database operations
9. **Performance**: Use appropriate indexing and query optimization
10. **Security**: Validate inputs and use secure connection practices</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\swift\swift-databases.md