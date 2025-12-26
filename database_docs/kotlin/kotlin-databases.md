# Kotlin Database Programming

## Overview
Kotlin has excellent database support through JDBC, Exposed (Kotlin ORM), Ktorm, and various database-specific drivers. This document covers the most popular database solutions for Kotlin applications.

## JDBC with Kotlin

### Basic JDBC Usage
```kotlin
import java.sql.Connection
import java.sql.DriverManager
import java.sql.PreparedStatement
import java.sql.ResultSet

data class User(
    val id: Int,
    val name: String,
    val age: Int,
    val email: String
)

class UserDao(private val connection: Connection) {

    fun createTable() {
        val sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            )
        """.trimIndent()

        connection.createStatement().use { stmt ->
            stmt.execute(sql)
        }
    }

    fun insertUser(name: String, age: Int, email: String): Int {
        val sql = "INSERT INTO users (name, age, email) VALUES (?, ?, ?)"
        connection.prepareStatement(sql, PreparedStatement.RETURN_GENERATED_KEYS).use { stmt ->
            stmt.setString(1, name)
            stmt.setInt(2, age)
            stmt.setString(3, email)

            stmt.executeUpdate()

            val generatedKeys = stmt.generatedKeys
            return if (generatedKeys.next()) {
                generatedKeys.getInt(1)
            } else {
                throw SQLException("Creating user failed, no ID obtained.")
            }
        }
    }

    fun getUser(id: Int): User? {
        val sql = "SELECT id, name, age, email FROM users WHERE id = ?"
        connection.prepareStatement(sql).use { stmt ->
            stmt.setInt(1, id)

            val resultSet = stmt.executeQuery()
            return if (resultSet.next()) {
                User(
                    id = resultSet.getInt("id"),
                    name = resultSet.getString("name"),
                    age = resultSet.getInt("age"),
                    email = resultSet.getString("email")
                )
            } else {
                null
            }
        }
    }

    fun getAllUsers(): List<User> {
        val sql = "SELECT id, name, age, email FROM users"
        val users = mutableListOf<User>()

        connection.createStatement().use { stmt ->
            val resultSet = stmt.executeQuery(sql)
            while (resultSet.next()) {
                users.add(User(
                    id = resultSet.getInt("id"),
                    name = resultSet.getString("name"),
                    age = resultSet.getInt("age"),
                    email = resultSet.getString("email")
                ))
            }
        }

        return users
    }

    fun updateUser(id: Int, name: String? = null, age: Int? = null, email: String? = null) {
        val sql = "UPDATE users SET name = ?, age = ?, email = ? WHERE id = ?"
        connection.prepareStatement(sql).use { stmt ->
            stmt.setString(1, name)
            stmt.setInt(2, age ?: 0)
            stmt.setString(3, email)
            stmt.setInt(4, id)

            stmt.executeUpdate()
        }
    }

    fun deleteUser(id: Int) {
        val sql = "DELETE FROM users WHERE id = ?"
        connection.prepareStatement(sql).use { stmt ->
            stmt.setInt(1, id)
            stmt.executeUpdate()
        }
    }

    fun getUsersByAge(minAge: Int): List<User> {
        val sql = "SELECT id, name, age, email FROM users WHERE age >= ?"
        val users = mutableListOf<User>()

        connection.prepareStatement(sql).use { stmt ->
            stmt.setInt(1, minAge)

            val resultSet = stmt.executeQuery()
            while (resultSet.next()) {
                users.add(User(
                    id = resultSet.getInt("id"),
                    name = resultSet.getString("name"),
                    age = resultSet.getInt("age"),
                    email = resultSet.getString("email")
                ))
            }
        }

        return users
    }
}

fun main() {
    val url = "jdbc:mysql://localhost:3306/mydb"
    val user = "root"
    val password = ""

    DriverManager.getConnection(url, user, password).use { connection ->
        val userDao = UserDao(connection)

        // Create table
        userDao.createTable()

        // Insert user
        val userId = userDao.insertUser("John Doe", 30, "john@example.com")
        println("Inserted user with ID: $userId")

        // Get user
        val user = userDao.getUser(userId)
        println("Retrieved user: $user")

        // Get all users
        val allUsers = userDao.getAllUsers()
        println("All users: $allUsers")

        // Update user
        userDao.updateUser(userId, age = 31)

        // Get adult users
        val adults = userDao.getUsersByAge(18)
        println("Adult users: $adults")

        // Delete user
        userDao.deleteUser(userId)
    }
}
```

## Exposed (Kotlin ORM)

### Installation
```kotlin
// build.gradle.kts
dependencies {
    implementation("org.jetbrains.exposed:exposed-core:0.41.1")
    implementation("org.jetbrains.exposed:exposed-dao:0.41.1")
    implementation("org.jetbrains.exposed:exposed-jdbc:0.41.1")
    implementation("mysql:mysql-connector-java:8.0.33")
}
```

### Model Definition
```kotlin
import org.jetbrains.exposed.dao.IntEntity
import org.jetbrains.exposed.dao.IntEntityClass
import org.jetbrains.exposed.dao.id.EntityID
import org.jetbrains.exposed.dao.id.IntIdTable
import org.jetbrains.exposed.sql.Column
import org.jetbrains.exposed.sql.Table
import org.jetbrains.exposed.sql.javatime.datetime
import java.time.LocalDateTime

// Table definition
object Users : IntIdTable() {
    val name = varchar("name", 100)
    val age = integer("age")
    val email = varchar("email", 100).uniqueIndex()
    val createdAt = datetime("created_at").default(LocalDateTime.now())
}

// Entity class
class User(id: EntityID<Int>) : IntEntity(id) {
    companion object : IntEntityClass<User>(Users)

    var name by Users.name
    var age by Users.age
    var email by Users.email
    var createdAt by Users.createdAt
}
```

### Database Connection
```kotlin
import org.jetbrains.exposed.sql.Database
import org.jetbrains.exposed.sql.SchemaUtils
import org.jetbrains.exposed.sql.transactions.transaction

object DatabaseConfig {
    fun init() {
        Database.connect(
            url = "jdbc:mysql://localhost:3306/mydb",
            driver = "com.mysql.cj.jdbc.Driver",
            user = "root",
            password = ""
        )

        // Create tables
        transaction {
            SchemaUtils.create(Users)
        }
    }
}
```

### CRUD Operations
```kotlin
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.transactions.transaction

class UserService {

    fun createUser(name: String, age: Int, email: String): User {
        return transaction {
            User.new {
                this.name = name
                this.age = age
                this.email = email
            }
        }
    }

    fun getUser(id: Int): User? {
        return transaction {
            User.findById(id)
        }
    }

    fun getAllUsers(): List<User> {
        return transaction {
            User.all().toList()
        }
    }

    fun updateUser(id: Int, name: String? = null, age: Int? = null, email: String? = null) {
        transaction {
            val user = User.findById(id) ?: throw IllegalArgumentException("User not found")
            name?.let { user.name = it }
            age?.let { user.age = it }
            email?.let { user.email = it }
        }
    }

    fun deleteUser(id: Int) {
        transaction {
            val user = User.findById(id) ?: throw IllegalArgumentException("User not found")
            user.delete()
        }
    }

    fun getAdultUsers(): List<User> {
        return transaction {
            User.find { Users.age greaterEq 18 }.toList()
        }
    }

    fun searchUsersByName(namePattern: String): List<User> {
        return transaction {
            User.find { Users.name like "%$namePattern%" }.toList()
        }
    }

    fun getUsersCount(): Long {
        return transaction {
            User.count()
        }
    }
}
```

### Usage
```kotlin
fun main() {
    DatabaseConfig.init()

    val userService = UserService()

    // Create user
    val user = userService.createUser("John Doe", 30, "john@example.com")
    println("Created user: ${user.name}")

    // Get all users
    val users = userService.getAllUsers()
    users.forEach { println("User: ${it.name}, Age: ${it.age}") }

    // Update user
    userService.updateUser(user.id.value, age = 31)

    // Get adult users
    val adults = userService.getAdultUsers()
    println("Number of adult users: ${adults.size}")

    // Search users
    val searchResults = userService.searchUsersByName("John")
    println("Search results: ${searchResults.size}")

    // Get count
    val count = userService.getUsersCount()
    println("Total users: $count")

    // Delete user
    userService.deleteUser(user.id.value)
}
```

## Ktorm (Kotlin ORM)

### Installation
```kotlin
// build.gradle.kts
dependencies {
    implementation("org.ktorm:ktorm-core:3.6.0")
    implementation("org.ktorm:ktorm-support-mysql:3.6.0")
}
```

### Model Definition
```kotlin
import org.ktorm.database.Database
import org.ktorm.entity.Entity
import org.ktorm.entity.sequenceOf
import org.ktorm.schema.*
import java.time.LocalDateTime

// Table definition
object Users : Table<Nothing>("users") {
    val id = int("id").primaryKey().autoIncrement()
    val name = varchar("name")
    val age = int("age")
    val email = varchar("email")
    val createdAt = datetime("created_at")
}

// Entity interface
interface User : Entity<User> {
    companion object : Entity.Factory<User>()

    val id: Int
    var name: String
    var age: Int
    var email: String
    var createdAt: LocalDateTime
}

// Extension for sequence
val Database.users get() = this.sequenceOf(Users)
```

### Database Connection
```kotlin
import org.ktorm.database.Database

object DatabaseConfig {
    val database = Database.connect(
        url = "jdbc:mysql://localhost:3306/mydb",
        user = "root",
        password = "",
        driver = "com.mysql.cj.jdbc.Driver"
    )
}
```

### CRUD Operations
```kotlin
import org.ktorm.dsl.*
import org.ktorm.entity.findById
import org.ktorm.entity.removeIf
import org.ktorm.entity.update

class UserService(private val database: Database = DatabaseConfig.database) {

    fun createUser(name: String, age: Int, email: String): User {
        return database.users.add {
            set(Users.name, name)
            set(Users.age, age)
            set(Users.email, email)
            set(Users.createdAt, LocalDateTime.now())
        }.let { id ->
            database.users.findById(id) ?: throw IllegalStateException("User creation failed")
        }
    }

    fun getUser(id: Int): User? {
        return database.users.findById(id)
    }

    fun getAllUsers(): List<User> {
        return database.users.toList()
    }

    fun updateUser(id: Int, name: String? = null, age: Int? = null, email: String? = null) {
        database.users.findById(id)?.let { user ->
            name?.let { user.name = it }
            age?.let { user.age = it }
            email?.let { user.email = it }
            user.flushChanges()
        }
    }

    fun deleteUser(id: Int) {
        database.users.removeIf { it.id eq id }
    }

    fun getAdultUsers(): List<User> {
        return database
            .from(Users)
            .select()
            .where { Users.age greaterEq 18 }
            .map { Users.createEntity(it) }
    }

    fun searchUsersByName(namePattern: String): List<User> {
        return database
            .from(Users)
            .select()
            .where { Users.name like "%$namePattern%" }
            .map { Users.createEntity(it) }
    }

    fun getUsersStatistics(): Map<String, Any> {
        val count = database.users.count()
        val averageAge = database
            .from(Users)
            .select(avg(Users.age).aliased("avg_age"))
            .map { it.getInt("avg_age") ?: 0 }
            .firstOrNull() ?: 0

        return mapOf(
            "count" to count,
            "averageAge" to averageAge
        )
    }
}
```

### Usage
```kotlin
fun main() {
    val userService = UserService()

    // Create user
    val user = userService.createUser("John Doe", 30, "john@example.com")
    println("Created user: ${user.name}")

    // Get all users
    val users = userService.getAllUsers()
    users.forEach { println("User: ${it.name}, Age: ${it.age}") }

    // Update user
    userService.updateUser(user.id, age = 31)

    // Get adult users
    val adults = userService.getAdultUsers()
    println("Number of adult users: ${adults.size}")

    // Search users
    val searchResults = userService.searchUsersByName("John")
    println("Search results: ${searchResults.size}")

    // Get statistics
    val stats = userService.getUsersStatistics()
    println("Statistics: $stats")

    // Delete user
    userService.deleteUser(user.id)
}
```

## PostgreSQL with Exposed

### PostgreSQL Setup
```kotlin
import org.jetbrains.exposed.sql.Database
import org.jetbrains.exposed.sql.transactions.transaction
import org.jetbrains.exposed.sql.SchemaUtils

object PostgresConfig {
    fun init() {
        Database.connect(
            url = "jdbc:postgresql://localhost:5432/mydb",
            driver = "org.postgresql.Driver",
            user = "myuser",
            password = "mypassword"
        )

        transaction {
            SchemaUtils.create(Users)
        }
    }
}
```

## MongoDB with KMongo

### Installation
```kotlin
// build.gradle.kts
dependencies {
    implementation("org.litote.kmongo:kmongo:4.8.0")
}
```

### Basic Usage
```kotlin
import org.litote.kmongo.*
import com.mongodb.client.MongoClients
import java.time.LocalDateTime

data class User(
    val id: String? = null,
    val name: String,
    val age: Int,
    val email: String,
    val createdAt: LocalDateTime = LocalDateTime.now()
)

class MongoUserService {
    private val client = MongoClients.create("mongodb://localhost:27017")
    private val database = client.getDatabase("mydb")
    private val collection = database.getCollection<User>("users")

    fun createUser(name: String, age: Int, email: String): User {
        val user = User(name = name, age = age, email = email)
        collection.insertOne(user)
        return user
    }

    fun getAllUsers(): List<User> {
        return collection.find().toList()
    }

    fun getAdultUsers(): List<User> {
        return collection.find(User::age gte 18).toList()
    }

    fun updateUser(email: String, newAge: Int) {
        collection.updateOne(
            User::email eq email,
            setValue(User::age, newAge)
        )
    }

    fun deleteUser(email: String) {
        collection.deleteOne(User::email eq email)
    }

    fun searchUsersByName(namePattern: String): List<User> {
        return collection.find(User::name regex Pattern.compile(namePattern, Pattern.CASE_INSENSITIVE)).toList()
    }

    fun close() {
        client.close()
    }
}

fun main() {
    val userService = MongoUserService()

    // Create user
    val user = userService.createUser("John Doe", 30, "john@example.com")
    println("Created user: ${user.name}")

    // Get all users
    val users = userService.getAllUsers()
    users.forEach { println("User: ${it.name}, Age: ${it.age}") }

    // Get adult users
    val adults = userService.getAdultUsers()
    println("Number of adult users: ${adults.size}")

    // Update user
    userService.updateUser("john@example.com", 31)

    // Search users
    val searchResults = userService.searchUsersByName("John")
    println("Search results: ${searchResults.size}")

    // Delete user
    userService.deleteUser("john@example.com")

    userService.close()
}
```

## Redis with Jedis

### Installation
```kotlin
// build.gradle.kts
dependencies {
    implementation("redis.clients:jedis:4.3.1")
}
```

### Basic Usage
```kotlin
import redis.clients.jedis.Jedis
import redis.clients.jedis.JedisPool

class RedisService {
    private val jedisPool = JedisPool("localhost", 6379)

    private fun <T> useJedis(block: (Jedis) -> T): T {
        return jedisPool.resource.use(block)
    }

    fun set(key: String, value: String) {
        useJedis { it.set(key, value) }
    }

    fun get(key: String): String? {
        return useJedis { it.get(key) }
    }

    fun setUser(userId: String, name: String, age: Int, email: String) {
        useJedis { jedis ->
            jedis.hset("user:$userId", mapOf(
                "name" to name,
                "age" to age.toString(),
                "email" to email
            ))
        }
    }

    fun getUser(userId: String): Map<String, String> {
        return useJedis { it.hgetAll("user:$userId") }
    }

    fun addToList(key: String, values: List<String>) {
        useJedis { jedis ->
            jedis.rpush(key, *values.toTypedArray())
        }
    }

    fun getList(key: String): List<String> {
        return useJedis { it.lrange(key, 0, -1) }
    }

    fun addToSet(key: String, members: Set<String>) {
        useJedis { jedis ->
            jedis.sadd(key, *members.toTypedArray())
        }
    }

    fun getSet(key: String): Set<String> {
        return useJedis { it.smembers(key) }
    }

    fun addToSortedSet(key: String, members: Map<String, Double>) {
        useJedis { jedis ->
            jedis.zadd(key, members)
        }
    }

    fun getSortedSet(key: String): Map<String, Double> {
        return useJedis { jedis ->
            val result = jedis.zrangeWithScores(key, 0, -1)
            result.associate { it.element to it.score }
        }
    }

    fun close() {
        jedisPool.close()
    }
}

fun main() {
    val redisService = RedisService()

    // Strings
    redisService.set("key", "value")
    val value = redisService.get("key")
    println("Value: $value")

    // Hashes
    redisService.setUser("1", "John Doe", 30, "john@example.com")
    val user = redisService.getUser("1")
    println("User: $user")

    // Lists
    redisService.addToList("mylist", listOf("item1", "item2", "item3"))
    val listItems = redisService.getList("mylist")
    println("List items: $listItems")

    // Sets
    redisService.addToSet("myset", setOf("member1", "member2", "member3"))
    val setMembers = redisService.getSet("myset")
    println("Set members: $setMembers")

    // Sorted Sets
    redisService.addToSortedSet("myzset", mapOf("member1" to 1.0, "member2" to 2.0, "member3" to 3.0))
    val sortedSet = redisService.getSortedSet("myzset")
    println("Sorted set: $sortedSet")

    redisService.close()
}
```

## Best Practices

1. **Resource Management**: Use `use` function for automatic resource cleanup
2. **Prepared Statements**: Always use parameterized queries to prevent SQL injection
3. **Connection Pooling**: Use connection pools for better performance
4. **Transactions**: Use database transactions for data consistency
5. **Error Handling**: Implement comprehensive error handling with try-catch blocks
6. **Type Safety**: Leverage Kotlin's type system and null safety
7. **DSL Usage**: Use Exposed's DSL for type-safe queries
8. **Migration Scripts**: Use proper database migration strategies
9. **Testing**: Write comprehensive unit tests for database operations
10. **Security**: Validate inputs and use secure connection practices</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\kotlin\kotlin-databases.md