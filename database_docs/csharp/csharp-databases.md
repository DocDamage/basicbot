# C# Database Programming

## Overview
C# has excellent database support through ADO.NET, Entity Framework, and various database-specific drivers. This document covers the most popular database solutions for .NET applications.

## ADO.NET Fundamentals

### Basic ADO.NET Usage
```csharp
using System;
using System.Data.SqlClient;
using System.Data;

class AdoNetExample
{
    static void Main()
    {
        string connectionString = @"Server=localhost;Database=mydb;Trusted_Connection=True;";

        using (SqlConnection connection = new SqlConnection(connectionString))
        {
            connection.Open();
            Console.WriteLine("Connected to database");

            // Create command
            using (SqlCommand command = new SqlCommand("SELECT * FROM Users WHERE Age > @age", connection))
            {
                command.Parameters.AddWithValue("@age", 18);

                using (SqlDataReader reader = command.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        int id = reader.GetInt32(0);
                        string name = reader.GetString(1);
                        int age = reader.GetInt32(2);
                        Console.WriteLine($"User: {id}, {name}, {age}");
                    }
                }
            }
        }
    }
}
```

### DataSet and DataAdapter
```csharp
using System;
using System.Data;
using System.Data.SqlClient;

class DataSetExample
{
    static void Main()
    {
        string connectionString = @"Server=localhost;Database=mydb;Trusted_Connection=True;";

        using (SqlConnection connection = new SqlConnection(connectionString))
        {
            // Create DataAdapter
            SqlDataAdapter adapter = new SqlDataAdapter("SELECT * FROM Users", connection);

            // Create DataSet
            DataSet dataSet = new DataSet();

            // Fill DataSet
            adapter.Fill(dataSet, "Users");

            // Work with data
            DataTable table = dataSet.Tables["Users"];
            foreach (DataRow row in table.Rows)
            {
                Console.WriteLine($"User: {row["Id"]}, {row["Name"]}, {row["Age"]}");
            }

            // Update data
            DataRow newRow = table.NewRow();
            newRow["Name"] = "John Doe";
            newRow["Age"] = 30;
            table.Rows.Add(newRow);

            // Save changes
            SqlCommandBuilder builder = new SqlCommandBuilder(adapter);
            adapter.Update(dataSet, "Users");
        }
    }
}
```

## SQL Server with ADO.NET

### NuGet Package
```
Install-Package System.Data.SqlClient
```

### Connection and CRUD Operations
```csharp
using System;
using System.Data.SqlClient;

class SqlServerExample
{
    private const string ConnectionString = @"Server=localhost;Database=mydb;Trusted_Connection=True;";

    static void Main()
    {
        // Insert
        InsertUser("John Doe", 30, "john@example.com");

        // Read
        ReadUsers();

        // Update
        UpdateUser(1, 31);

        // Delete
        DeleteUser(1);
    }

    static void InsertUser(string name, int age, string email)
    {
        using (SqlConnection conn = new SqlConnection(ConnectionString))
        {
            string query = "INSERT INTO Users (Name, Age, Email) VALUES (@name, @age, @email)";
            using (SqlCommand cmd = new SqlCommand(query, conn))
            {
                cmd.Parameters.AddWithValue("@name", name);
                cmd.Parameters.AddWithValue("@age", age);
                cmd.Parameters.AddWithValue("@email", email);

                conn.Open();
                cmd.ExecuteNonQuery();
                Console.WriteLine("User inserted");
            }
        }
    }

    static void ReadUsers()
    {
        using (SqlConnection conn = new SqlConnection(ConnectionString))
        {
            string query = "SELECT Id, Name, Age, Email FROM Users";
            using (SqlCommand cmd = new SqlCommand(query, conn))
            {
                conn.Open();
                using (SqlDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        Console.WriteLine($"User: {reader["Id"]}, {reader["Name"]}, {reader["Age"]}, {reader["Email"]}");
                    }
                }
            }
        }
    }

    static void UpdateUser(int id, int newAge)
    {
        using (SqlConnection conn = new SqlConnection(ConnectionString))
        {
            string query = "UPDATE Users SET Age = @age WHERE Id = @id";
            using (SqlCommand cmd = new SqlCommand(query, conn))
            {
                cmd.Parameters.AddWithValue("@age", newAge);
                cmd.Parameters.AddWithValue("@id", id);

                conn.Open();
                int rowsAffected = cmd.ExecuteNonQuery();
                Console.WriteLine($"{rowsAffected} user(s) updated");
            }
        }
    }

    static void DeleteUser(int id)
    {
        using (SqlConnection conn = new SqlConnection(ConnectionString))
        {
            string query = "DELETE FROM Users WHERE Id = @id";
            using (SqlCommand cmd = new SqlCommand(query, conn))
            {
                cmd.Parameters.AddWithValue("@id", id);

                conn.Open();
                int rowsAffected = cmd.ExecuteNonQuery();
                Console.WriteLine($"{rowsAffected} user(s) deleted");
            }
        }
    }
}
```

## PostgreSQL with Npgsql

### NuGet Package
```
Install-Package Npgsql
```

### Basic Usage
```csharp
using System;
using Npgsql;

class PostgresExample
{
    private const string ConnectionString = "Host=localhost;Database=mydb;Username=myuser;Password=mypassword";

    static void Main()
    {
        using (var conn = new NpgsqlConnection(ConnectionString))
        {
            conn.Open();
            Console.WriteLine("Connected to PostgreSQL");

            // Create table
            using (var cmd = new NpgsqlCommand("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT, age INTEGER)", conn))
            {
                cmd.ExecuteNonQuery();
            }

            // Insert data
            using (var cmd = new NpgsqlCommand("INSERT INTO users (name, age) VALUES (@name, @age) RETURNING id", conn))
            {
                cmd.Parameters.AddWithValue("name", "Jane Doe");
                cmd.Parameters.AddWithValue("age", 25);

                int newId = (int)cmd.ExecuteScalar();
                Console.WriteLine($"Inserted user with ID: {newId}");
            }

            // Query data
            using (var cmd = new NpgsqlCommand("SELECT id, name, age FROM users WHERE age > @age", conn))
            {
                cmd.Parameters.AddWithValue("age", 20);

                using (var reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        Console.WriteLine($"User: {reader.GetInt32(0)}, {reader.GetString(1)}, {reader.GetInt32(2)}");
                    }
                }
            }
        }
    }
}
```

## MongoDB with MongoDB.Driver

### NuGet Package
```
Install-Package MongoDB.Driver
```

### Basic Usage
```csharp
using System;
using MongoDB.Bson;
using MongoDB.Driver;

class MongoDbExample
{
    static void Main()
    {
        var client = new MongoClient("mongodb://localhost:27017");
        var database = client.GetDatabase("mydb");
        var collection = database.GetCollection<BsonDocument>("users");

        // Insert document
        var user = new BsonDocument
        {
            { "name", "John Doe" },
            { "age", 30 },
            { "email", "john@example.com" },
            { "createdAt", DateTime.Now }
        };

        collection.InsertOne(user);
        Console.WriteLine($"Inserted user with ID: {user["_id"]}");

        // Find documents
        var filter = Builders<BsonDocument>.Filter.Gt("age", 25);
        var users = collection.Find(filter).ToList();

        foreach (var doc in users)
        {
            Console.WriteLine($"User: {doc["name"]}, Age: {doc["age"]}");
        }

        // Update document
        var updateFilter = Builders<BsonDocument>.Filter.Eq("name", "John Doe");
        var update = Builders<BsonDocument>.Update.Set("age", 31);
        collection.UpdateOne(updateFilter, update);

        // Delete document
        collection.DeleteOne(updateFilter);
    }
}

// Strongly typed approach
public class User
{
    public ObjectId Id { get; set; }
    public string Name { get; set; }
    public int Age { get; set; }
    public string Email { get; set; }
    public DateTime CreatedAt { get; set; }
}

class TypedMongoDbExample
{
    static void Main()
    {
        var client = new MongoClient("mongodb://localhost:27017");
        var database = client.GetDatabase("mydb");
        var collection = database.GetCollection<User>("users");

        // Insert
        var user = new User
        {
            Name = "Jane Doe",
            Age = 25,
            Email = "jane@example.com",
            CreatedAt = DateTime.Now
        };

        collection.InsertOne(user);

        // Query
        var users = collection.Find(u => u.Age > 20).ToList();
        foreach (var u in users)
        {
            Console.WriteLine($"User: {u.Name}, Age: {u.Age}");
        }
    }
}
```

## Redis with StackExchange.Redis

### NuGet Package
```
Install-Package StackExchange.Redis
```

### Basic Usage
```csharp
using System;
using StackExchange.Redis;

class RedisExample
{
    static void Main()
    {
        ConnectionMultiplexer redis = ConnectionMultiplexer.Connect("localhost:6379");
        IDatabase db = redis.GetDatabase();

        // Strings
        db.StringSet("key", "value");
        string value = db.StringGet("key");
        Console.WriteLine($"Value: {value}");

        // Hashes
        db.HashSet("user:1", new HashEntry[] {
            new HashEntry("name", "John"),
            new HashEntry("age", "30")
        });

        var user = db.HashGetAll("user:1");
        foreach (var entry in user)
        {
            Console.WriteLine($"{entry.Name}: {entry.Value}");
        }

        // Lists
        db.ListRightPush("mylist", new RedisValue[] { "item1", "item2", "item3" });
        var items = db.ListRange("mylist", 0, -1);
        Console.WriteLine("List items: " + string.Join(", ", items));

        // Sets
        db.SetAdd("myset", new RedisValue[] { "member1", "member2", "member3" });
        var members = db.SetMembers("myset");
        Console.WriteLine("Set members: " + string.Join(", ", members));

        // Sorted Sets
        db.SortedSetAdd("myzset", new SortedSetEntry[] {
            new SortedSetEntry("member1", 1),
            new SortedSetEntry("member2", 2),
            new SortedSetEntry("member3", 3)
        });

        var scores = db.SortedSetRangeByRankWithScores("myzset", 0, -1);
        foreach (var entry in scores)
        {
            Console.WriteLine($"{entry.Element}: {entry.Score}");
        }

        redis.Close();
    }
}
```

## Entity Framework Core

### NuGet Packages
```
Install-Package Microsoft.EntityFrameworkCore.SqlServer
Install-Package Microsoft.EntityFrameworkCore.Tools
```

### Model Classes
```csharp
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

public class User
{
    [Key]
    [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public int Id { get; set; }

    [Required]
    [MaxLength(100)]
    public string Name { get; set; }

    [Required]
    public int Age { get; set; }

    [Required]
    [EmailAddress]
    public string Email { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.Now;
}
```

### DbContext
```csharp
using Microsoft.EntityFrameworkCore;

public class AppDbContext : DbContext
{
    public DbSet<User> Users { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        optionsBuilder.UseSqlServer(@"Server=localhost;Database=mydb;Trusted_Connection=True;");
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Additional configuration
        modelBuilder.Entity<User>()
            .HasIndex(u => u.Email)
            .IsUnique();
    }
}
```

### Usage Example
```csharp
using System;
using System.Linq;

class EfCoreExample
{
    static void Main()
    {
        using (var context = new AppDbContext())
        {
            // Ensure database is created
            context.Database.EnsureCreated();

            // Create user
            var user = new User
            {
                Name = "John Doe",
                Age = 30,
                Email = "john@example.com"
            };

            context.Users.Add(user);
            context.SaveChanges();
            Console.WriteLine($"User created with ID: {user.Id}");

            // Query users
            var users = context.Users.Where(u => u.Age > 25).ToList();
            foreach (var u in users)
            {
                Console.WriteLine($"User: {u.Name}, Age: {u.Age}, Email: {u.Email}");
            }

            // Update user
            user.Age = 31;
            context.SaveChanges();

            // Delete user
            context.Users.Remove(user);
            context.SaveChanges();
        }
    }
}
```

## Dapper (Micro ORM)

### NuGet Package
```
Install-Package Dapper
```

### Basic Usage
```csharp
using System;
using System.Data.SqlClient;
using Dapper;

class DapperExample
{
    private const string ConnectionString = @"Server=localhost;Database=mydb;Trusted_Connection=True;";

    static void Main()
    {
        using (var connection = new SqlConnection(ConnectionString))
        {
            // Create table
            connection.Execute(@"
                CREATE TABLE IF NOT EXISTS Users (
                    Id INT PRIMARY KEY IDENTITY(1,1),
                    Name NVARCHAR(100) NOT NULL,
                    Age INT NOT NULL,
                    Email NVARCHAR(100) UNIQUE NOT NULL
                )");

            // Insert
            var user = new { Name = "John Doe", Age = 30, Email = "john@example.com" };
            int id = connection.QuerySingle<int>(@"
                INSERT INTO Users (Name, Age, Email)
                OUTPUT INSERTED.Id
                VALUES (@Name, @Age, @Email)", user);
            Console.WriteLine($"Inserted user with ID: {id}");

            // Query
            var users = connection.Query<User>("SELECT * FROM Users WHERE Age > @age", new { age = 25 });
            foreach (var u in users)
            {
                Console.WriteLine($"User: {u.Id}, {u.Name}, {u.Age}, {u.Email}");
            }

            // Update
            connection.Execute("UPDATE Users SET Age = @age WHERE Id = @id", new { age = 31, id = 1 });

            // Delete
            connection.Execute("DELETE FROM Users WHERE Id = @id", new { id = 1 });
        }
    }
}

public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int Age { get; set; }
    public string Email { get; set; }
}
```

## Best Practices

1. **Connection Management**: Use `using` statements for proper resource cleanup
2. **Parameterized Queries**: Always use parameters to prevent SQL injection
3. **Async Operations**: Use async methods for better scalability
4. **Connection Pooling**: ADO.NET handles connection pooling automatically
5. **Transaction Management**: Use transactions for data consistency
6. **Error Handling**: Implement comprehensive exception handling
7. **Configuration**: Store connection strings securely
8. **Migrations**: Use EF Core migrations for schema changes
9. **Performance**: Use appropriate fetching strategies (lazy vs eager loading)</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\csharp\csharp-databases.md