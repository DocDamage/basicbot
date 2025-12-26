# Java Database Programming

## Overview
Java has robust database support through JDBC (Java Database Connectivity) and various ORM frameworks. This document covers the most popular database solutions for Java applications.

## JDBC Fundamentals

### Basic JDBC Usage
```java
import java.sql.*;

public class JdbcExample {
    public static void main(String[] args) {
        String url = "jdbc:postgresql://localhost:5432/mydb";
        String user = "myuser";
        String password = "mypassword";

        try (Connection conn = DriverManager.getConnection(url, user, password)) {
            System.out.println("Connected to database");

            // Create statement
            Statement stmt = conn.createStatement();

            // Execute query
            ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE age > 18");

            // Process results
            while (rs.next()) {
                int id = rs.getInt("id");
                String name = rs.getString("name");
                int age = rs.getInt("age");
                System.out.println("User: " + id + ", " + name + ", " + age);
            }

            rs.close();
            stmt.close();

        } catch (SQLException e) {
            System.err.println("Database error: " + e.getMessage());
        }
    }
}
```

### Prepared Statements
```java
import java.sql.*;

public class PreparedStatementExample {
    public static void main(String[] args) {
        String url = "jdbc:postgresql://localhost:5432/mydb";
        String user = "myuser";
        String password = "mypassword";

        String sql = "INSERT INTO users (name, age, email) VALUES (?, ?, ?)";

        try (Connection conn = DriverManager.getConnection(url, user, password);
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            // Set parameters
            pstmt.setString(1, "John Doe");
            pstmt.setInt(2, 30);
            pstmt.setString(3, "john@example.com");

            // Execute
            int rowsAffected = pstmt.executeUpdate();
            System.out.println("Rows inserted: " + rowsAffected);

        } catch (SQLException e) {
            System.err.println("Database error: " + e.getMessage());
        }
    }
}
```

## PostgreSQL with JDBC

### Maven Dependency
```xml
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <version>42.7.3</version>
</dependency>
```

### Connection Example
```java
import java.sql.*;

public class PostgresExample {
    public static void main(String[] args) {
        String url = "jdbc:postgresql://localhost:5432/mydb";
        String user = "myuser";
        String password = "mypassword";

        try (Connection conn = DriverManager.getConnection(url, user, password)) {
            // PostgreSQL-specific features
            conn.setAutoCommit(false); // Start transaction

            try (PreparedStatement pstmt = conn.prepareStatement(
                    "INSERT INTO users (name, age) VALUES (?, ?) RETURNING id")) {

                pstmt.setString(1, "Jane Doe");
                pstmt.setInt(2, 25);

                ResultSet rs = pstmt.executeQuery();
                if (rs.next()) {
                    int generatedId = rs.getInt(1);
                    System.out.println("Generated ID: " + generatedId);
                }

                conn.commit(); // Commit transaction

            } catch (SQLException e) {
                conn.rollback(); // Rollback on error
                throw e;
            }

        } catch (SQLException e) {
            System.err.println("Database error: " + e.getMessage());
        }
    }
}
```

## MySQL with JDBC

### Maven Dependency
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
</dependency>
```

### Connection Example
```java
import java.sql.*;

public class MySQLExample {
    public static void main(String[] args) {
        String url = "jdbc:mysql://localhost:3306/mydb?useSSL=false&serverTimezone=UTC";
        String user = "myuser";
        String password = "mypassword";

        try (Connection conn = DriverManager.getConnection(url, user, password)) {
            System.out.println("Connected to MySQL");

            // MySQL-specific query
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SHOW TABLES")) {

                System.out.println("Tables:");
                while (rs.next()) {
                    System.out.println("- " + rs.getString(1));
                }
            }

        } catch (SQLException e) {
            System.err.println("Database error: " + e.getMessage());
        }
    }
}
```

## MongoDB with MongoDB Java Driver

### Maven Dependency
```xml
<dependency>
    <groupId>org.mongodb</groupId>
    <artifactId>mongodb-driver-sync</artifactId>
    <version>5.1.1</version>
</dependency>
```

### Basic Usage
```java
import com.mongodb.client.*;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Updates;
import org.bson.Document;
import org.bson.types.ObjectId;

public class MongoDBExample {
    public static void main(String[] args) {
        // Connect to MongoDB
        try (MongoClient mongoClient = MongoClients.create("mongodb://localhost:27017")) {
            MongoDatabase database = mongoClient.getDatabase("mydb");
            MongoCollection<Document> collection = database.getCollection("users");

            // Insert document
            Document user = new Document("_id", new ObjectId())
                    .append("name", "John Doe")
                    .append("age", 30)
                    .append("email", "john@example.com");

            collection.insertOne(user);
            System.out.println("User inserted with ID: " + user.getObjectId("_id"));

            // Find documents
            FindIterable<Document> users = collection.find(Filters.gt("age", 25));
            for (Document doc : users) {
                System.out.println("User: " + doc.getString("name") + ", Age: " + doc.getInteger("age"));
            }

            // Update document
            collection.updateOne(
                Filters.eq("name", "John Doe"),
                Updates.set("age", 31)
            );

            // Delete document
            collection.deleteOne(Filters.eq("name", "John Doe"));

        } catch (Exception e) {
            System.err.println("MongoDB error: " + e.getMessage());
        }
    }
}
```

## Redis with Jedis

### Maven Dependency
```xml
<dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
    <version>5.1.0</version>
</dependency>
```

### Basic Usage
```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import java.util.Map;
import java.util.Set;

public class RedisExample {
    public static void main(String[] args) {
        try (JedisPool pool = new JedisPool("localhost", 6379)) {
            try (Jedis jedis = pool.getResource()) {
                // Strings
                jedis.set("key", "value");
                String value = jedis.get("key");
                System.out.println("Value: " + value);

                // Lists
                jedis.rpush("mylist", "item1", "item2", "item3");
                java.util.List<String> items = jedis.lrange("mylist", 0, -1);
                System.out.println("List items: " + items);

                // Hashes
                jedis.hset("user:1", "name", "John");
                jedis.hset("user:1", "age", "30");
                Map<String, String> user = jedis.hgetAll("user:1");
                System.out.println("User: " + user);

                // Sets
                jedis.sadd("myset", "member1", "member2", "member3");
                Set<String> members = jedis.smembers("myset");
                System.out.println("Set members: " + members);
            }
        } catch (Exception e) {
            System.err.println("Redis error: " + e.getMessage());
        }
    }
}
```

## Hibernate (ORM)

### Maven Dependencies
```xml
<dependency>
    <groupId>org.hibernate</groupId>
    <artifactId>hibernate-core</artifactId>
    <version>6.4.4.Final</version>
</dependency>
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <version>42.7.3</version>
</dependency>
```

### Entity Class
```java
import jakarta.persistence.*;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private Integer age;

    @Column(unique = true)
    private String email;

    // Constructors, getters, setters
    public User() {}

    public User(String name, Integer age, String email) {
        this.name = name;
        this.age = age;
        this.email = email;
    }

    // Getters and setters...
}
```

### Hibernate Configuration
```java
import org.hibernate.SessionFactory;
import org.hibernate.cfg.Configuration;

public class HibernateUtil {
    private static final SessionFactory sessionFactory = buildSessionFactory();

    private static SessionFactory buildSessionFactory() {
        try {
            return new Configuration()
                    .configure("hibernate.cfg.xml")
                    .addAnnotatedClass(User.class)
                    .buildSessionFactory();
        } catch (Throwable ex) {
            System.err.println("Initial SessionFactory creation failed." + ex);
            throw new ExceptionInInitializerError(ex);
        }
    }

    public static SessionFactory getSessionFactory() {
        return sessionFactory;
    }

    public static void shutdown() {
        getSessionFactory().close();
    }
}
```

### Usage Example
```java
import org.hibernate.Session;
import org.hibernate.Transaction;
import java.util.List;

public class HibernateExample {
    public static void main(String[] args) {
        Session session = HibernateUtil.getSessionFactory().openSession();
        Transaction transaction = null;

        try {
            transaction = session.beginTransaction();

            // Create user
            User user = new User("John Doe", 30, "john@example.com");
            session.save(user);
            System.out.println("User saved with ID: " + user.getId());

            // Query users
            List<User> users = session.createQuery("FROM User WHERE age > 25", User.class).list();
            for (User u : users) {
                System.out.println("User: " + u.getName() + ", Age: " + u.getAge());
            }

            // Update user
            user.setAge(31);
            session.update(user);

            // Delete user
            session.delete(user);

            transaction.commit();

        } catch (Exception e) {
            if (transaction != null) {
                transaction.rollback();
            }
            System.err.println("Hibernate error: " + e.getMessage());
        } finally {
            session.close();
            HibernateUtil.shutdown();
        }
    }
}
```

## Spring Data JPA

### Maven Dependencies
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>
```

### Entity Class
```java
import jakarta.persistence.*;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private Integer age;

    @Column(unique = true)
    private String email;

    // Constructors, getters, setters...
}
```

### Repository Interface
```java
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    List<User> findByAgeGreaterThan(Integer age);
    User findByEmail(String email);
    void deleteByName(String name);
}
```

### Service Class
```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Transactional
    public User createUser(String name, Integer age, String email) {
        User user = new User(name, age, email);
        return userRepository.save(user);
    }

    public List<User> findUsersOlderThan(Integer age) {
        return userRepository.findByAgeGreaterThan(age);
    }

    public User findUserByEmail(String email) {
        return userRepository.findByEmail(email);
    }

    @Transactional
    public void deleteUserByName(String name) {
        userRepository.deleteByName(name);
    }
}
```

## Best Practices

1. **Connection Pooling**: Use connection pools (HikariCP, C3P0)
2. **Prepared Statements**: Always use PreparedStatement to prevent SQL injection
3. **Transaction Management**: Use transactions for data consistency
4. **Resource Management**: Use try-with-resources for automatic resource cleanup
5. **Error Handling**: Implement comprehensive exception handling
6. **Connection Configuration**: Configure connection timeouts and limits
7. **ORM Best Practices**: Use lazy loading appropriately, avoid N+1 queries
8. **Migration Tools**: Use Flyway or Liquibase for schema migrations</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\java\java-databases.md