# PHP Database Programming

## Overview
PHP has extensive database support through PDO (PHP Data Objects), MySQLi, and various database-specific extensions. This document covers the most popular database solutions for PHP applications.

## PDO (PHP Data Objects)

### Basic PDO Usage
```php
<?php
// Database configuration
$host = 'localhost';
$dbname = 'mydb';
$username = 'root';
$password = '';

try {
    // Create PDO instance
    $pdo = new PDO("mysql:host=$host;dbname=$dbname", $username, $password);

    // Set error mode to exception
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    echo "Connected to database successfully\n";

    // Prepare and execute a query
    $stmt = $pdo->prepare("SELECT * FROM users WHERE age > :age");
    $stmt->execute(['age' => 18]);

    // Fetch results
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        echo "User: " . $row['id'] . ", " . $row['name'] . ", " . $row['age'] . "\n";
    }

} catch (PDOException $e) {
    echo "Connection failed: " . $e->getMessage() . "\n";
}
?>
```

### CRUD Operations with PDO
```php
<?php
class UserManager {
    private $pdo;

    public function __construct($pdo) {
        $this->pdo = $pdo;
    }

    // Create
    public function createUser($name, $age, $email) {
        $stmt = $this->pdo->prepare("INSERT INTO users (name, age, email) VALUES (?, ?, ?)");
        return $stmt->execute([$name, $age, $email]);
    }

    // Read
    public function getUser($id) {
        $stmt = $this->pdo->prepare("SELECT * FROM users WHERE id = ?");
        $stmt->execute([$id]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    // Read All
    public function getAllUsers() {
        $stmt = $this->pdo->query("SELECT * FROM users");
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    // Update
    public function updateUser($id, $name, $age, $email) {
        $stmt = $this->pdo->prepare("UPDATE users SET name = ?, age = ?, email = ? WHERE id = ?");
        return $stmt->execute([$name, $age, $email, $id]);
    }

    // Delete
    public function deleteUser($id) {
        $stmt = $this->pdo->prepare("DELETE FROM users WHERE id = ?");
        return $stmt->execute([$id]);
    }
}

// Usage
try {
    $pdo = new PDO("mysql:host=localhost;dbname=mydb", "root", "");
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $userManager = new UserManager($pdo);

    // Create user
    $userManager->createUser("John Doe", 30, "john@example.com");

    // Get all users
    $users = $userManager->getAllUsers();
    foreach ($users as $user) {
        echo "User: {$user['name']}, Age: {$user['age']}\n";
    }

} catch (PDOException $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## MySQLi Extension

### Procedural MySQLi
```php
<?php
// Database configuration
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "mydb";

// Create connection
$conn = mysqli_connect($servername, $username, $password, $dbname);

// Check connection
if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}
echo "Connected successfully\n";

// Create table
$sql = "CREATE TABLE IF NOT EXISTS users (
    id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    age INT(3) NOT NULL,
    email VARCHAR(50) UNIQUE
)";

if (mysqli_query($conn, $sql)) {
    echo "Table created successfully\n";
} else {
    echo "Error creating table: " . mysqli_error($conn) . "\n";
}

// Insert data
$sql = "INSERT INTO users (name, age, email) VALUES ('John Doe', 30, 'john@example.com')";

if (mysqli_query($conn, $sql)) {
    echo "New record created successfully\n";
} else {
    echo "Error: " . $sql . "\n" . mysqli_error($conn) . "\n";
}

// Select data
$sql = "SELECT id, name, age, email FROM users";
$result = mysqli_query($conn, $sql);

if (mysqli_num_rows($result) > 0) {
    while($row = mysqli_fetch_assoc($result)) {
        echo "User: " . $row["id"] . ", " . $row["name"] . ", " . $row["age"] . ", " . $row["email"] . "\n";
    }
} else {
    echo "0 results\n";
}

// Close connection
mysqli_close($conn);
?>
```

### Object-Oriented MySQLi
```php
<?php
class Database {
    private $conn;

    public function __construct($host, $user, $pass, $db) {
        $this->conn = new mysqli($host, $user, $pass, $db);

        if ($this->conn->connect_error) {
            die("Connection failed: " . $this->conn->connect_error);
        }
    }

    public function query($sql) {
        return $this->conn->query($sql);
    }

    public function prepare($sql) {
        return $this->conn->prepare($sql);
    }

    public function close() {
        $this->conn->close();
    }
}

// Usage
$db = new Database("localhost", "root", "", "mydb");

// Insert with prepared statement
$stmt = $db->prepare("INSERT INTO users (name, age, email) VALUES (?, ?, ?)");
$stmt->bind_param("sis", $name, $age, $email);

$name = "Jane Doe";
$age = 25;
$email = "jane@example.com";

$stmt->execute();
echo "New record created successfully\n";
$stmt->close();

// Select
$result = $db->query("SELECT id, name, age, email FROM users");

if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        echo "User: " . $row["id"] . ", " . $row["name"] . ", " . $row["age"] . ", " . $row["email"] . "\n";
    }
}

$db->close();
?>
```

## PostgreSQL with PDO

### Basic PostgreSQL Usage
```php
<?php
try {
    // PostgreSQL connection
    $pdo = new PDO("pgsql:host=localhost;port=5432;dbname=mydb;user=myuser;password=mypassword");

    // Set error mode
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    echo "Connected to PostgreSQL successfully\n";

    // Create table
    $pdo->exec("CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INTEGER NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
    )");

    // Insert data
    $stmt = $pdo->prepare("INSERT INTO users (name, age, email) VALUES (?, ?, ?)");
    $stmt->execute(["John Doe", 30, "john@example.com"]);

    // Query with parameters
    $stmt = $pdo->prepare("SELECT * FROM users WHERE age > ?");
    $stmt->execute([25]);

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        echo "User: {$row['id']}, {$row['name']}, {$row['age']}, {$row['email']}\n";
    }

} catch (PDOException $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## MongoDB with MongoDB PHP Driver

### Installation
```bash
composer require mongodb/mongodb
```

### Basic MongoDB Usage
```php
<?php
require 'vendor/autoload.php';

try {
    // Create MongoDB client
    $client = new MongoDB\Client("mongodb://localhost:27017");

    // Select database
    $db = $client->mydb;

    // Select collection
    $collection = $db->users;

    // Insert document
    $user = [
        'name' => 'John Doe',
        'age' => 30,
        'email' => 'john@example.com',
        'created_at' => new MongoDB\BSON\UTCDateTime()
    ];

    $result = $collection->insertOne($user);
    echo "Inserted user with ID: " . $result->getInsertedId() . "\n";

    // Find documents
    $users = $collection->find(['age' => ['$gt' => 25]]);

    foreach ($users as $user) {
        echo "User: {$user['name']}, Age: {$user['age']}\n";
    }

    // Update document
    $collection->updateOne(
        ['name' => 'John Doe'],
        ['$set' => ['age' => 31]]
    );

    // Delete document
    $collection->deleteOne(['name' => 'John Doe']);

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## Redis with Predis

### Installation
```bash
composer require predis/predis
```

### Basic Redis Usage
```php
<?php
require 'vendor/autoload.php';

try {
    // Create Redis client
    $redis = new Predis\Client([
        'scheme' => 'tcp',
        'host'   => '127.0.0.1',
        'port'   => 6379,
    ]);

    // Strings
    $redis->set('key', 'value');
    $value = $redis->get('key');
    echo "Value: $value\n";

    // Hashes
    $redis->hset('user:1', 'name', 'John');
    $redis->hset('user:1', 'age', '30');

    $user = $redis->hgetall('user:1');
    print_r($user);

    // Lists
    $redis->rpush('mylist', 'item1', 'item2', 'item3');
    $items = $redis->lrange('mylist', 0, -1);
    print_r($items);

    // Sets
    $redis->sadd('myset', 'member1', 'member2', 'member3');
    $members = $redis->smembers('myset');
    print_r($members);

    // Sorted Sets
    $redis->zadd('myzset', 1, 'member1', 2, 'member2', 3, 'member3');
    $scores = $redis->zrange('myzset', 0, -1, 'WITHSCORES');
    print_r($scores);

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## Laravel Eloquent ORM

### Model Definition
```php
<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class User extends Model
{
    protected $fillable = [
        'name',
        'email',
        'age'
    ];

    protected $casts = [
        'age' => 'integer',
        'created_at' => 'datetime',
        'updated_at' => 'datetime'
    ];

    // Relationships
    public function posts()
    {
        return $this->hasMany(Post::class);
    }
}
```

### Basic CRUD Operations
```php
<?php
use App\Models\User;

// Create
$user = User::create([
    'name' => 'John Doe',
    'email' => 'john@example.com',
    'age' => 30
]);

// Read
$user = User::find(1);
$users = User::where('age', '>', 25)->get();

// Update
$user = User::find(1);
$user->update(['age' => 31]);

// Delete
$user = User::find(1);
$user->delete();

// Query Builder
$users = User::select('name', 'email')
    ->where('age', '>', 20)
    ->orderBy('name')
    ->limit(10)
    ->get();
```

### Relationships
```php
<?php
// One to Many
class Post extends Model
{
    public function user()
    {
        return $this->belongsTo(User::class);
    }
}

// Many to Many
class Role extends Model
{
    public function users()
    {
        return $this->belongsToMany(User::class);
    }
}

// Eager Loading
$users = User::with('posts')->get();
```

## Symfony Doctrine ORM

### Entity Definition
```php
<?php
namespace App\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * @ORM\Entity
 * @ORM\Table(name="users")
 */
class User
{
    /**
     * @ORM\Id
     * @ORM\GeneratedValue
     * @ORM\Column(type="integer")
     */
    private $id;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $name;

    /**
     * @ORM\Column(type="integer")
     */
    private $age;

    /**
     * @ORM\Column(type="string", length=100, unique=true)
     */
    private $email;

    // Getters and setters...
}
```

### Repository Usage
```php
<?php
namespace App\Repository;

use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Doctrine\Persistence\ManagerRegistry;

class UserRepository extends ServiceEntityRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, User::class);
    }

    public function findUsersOlderThan($age)
    {
        return $this->createQueryBuilder('u')
            ->andWhere('u.age > :age')
            ->setParameter('age', $age)
            ->orderBy('u.name', 'ASC')
            ->getQuery()
            ->getResult();
    }
}
```

### Controller Usage
```php
<?php
namespace App\Controller;

use App\Entity\User;
use App\Repository\UserRepository;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Component\HttpFoundation\Response;

class UserController
{
    private $entityManager;
    private $userRepository;

    public function __construct(EntityManagerInterface $entityManager, UserRepository $userRepository)
    {
        $this->entityManager = $entityManager;
        $this->userRepository = $userRepository;
    }

    public function createUser(): Response
    {
        $user = new User();
        $user->setName('John Doe');
        $user->setAge(30);
        $user->setEmail('john@example.com');

        $this->entityManager->persist($user);
        $this->entityManager->flush();

        return new Response('User created with ID: ' . $user->getId());
    }

    public function getUsers(): Response
    {
        $users = $this->userRepository->findUsersOlderThan(25);

        $response = '';
        foreach ($users as $user) {
            $response .= "User: {$user->getName()}, Age: {$user->getAge()}\n";
        }

        return new Response($response);
    }
}
```

## Best Practices

1. **Prepared Statements**: Always use prepared statements to prevent SQL injection
2. **Error Handling**: Implement comprehensive error handling with try-catch blocks
3. **Connection Pooling**: Use persistent connections when appropriate
4. **Transactions**: Use transactions for data consistency
5. **Input Validation**: Validate and sanitize all user inputs
6. **Connection Management**: Close connections properly to avoid resource leaks
7. **Security**: Store database credentials securely (environment variables)
8. **Performance**: Use appropriate indexes and query optimization
9. **Caching**: Implement caching strategies for frequently accessed data
10. **Migration Scripts**: Use migration scripts for schema changes</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\php\php-databases.md