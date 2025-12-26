# MongoDB Database Documentation

## Introduction to MongoDB

MongoDB is a document database designed for ease of development and scaling. It stores data in flexible, JSON-like documents, meaning fields can vary from document to document and data structure can be changed over time.

## Key Concepts

### Documents
MongoDB stores data records as BSON documents. BSON is a binary representation of JSON documents.

### Collections
MongoDB stores documents in collections. Collections are analogous to tables in relational databases.

### Databases
MongoDB groups collections into databases. Each database has its own set of files on the file system.

## CRUD Operations

### Create
```javascript
db.collection.insertOne({name: "John", age: 30})
db.collection.insertMany([{name: "Jane"}, {name: "Bob"}])
```

### Read
```javascript
db.collection.find({age: {$gt: 25}})
db.collection.findOne({name: "John"})
```

### Update
```javascript
db.collection.updateOne({name: "John"}, {$set: {age: 31}})
db.collection.updateMany({age: {$lt: 30}}, {$inc: {age: 1}})
```

### Delete
```javascript
db.collection.deleteOne({name: "John"})
db.collection.deleteMany({age: {$lt: 25}})
```

## Indexing

Indexes support the efficient execution of queries. Without indexes, MongoDB must perform a collection scan to find matching documents.

```javascript
db.collection.createIndex({name: 1})
db.collection.createIndex({age: 1, name: 1})
```

## Aggregation

MongoDB's aggregation framework processes data records and returns computed results.

```javascript
db.collection.aggregate([
  {$match: {age: {$gte: 18}}},
  {$group: {_id: "$department", count: {$sum: 1}}}
])
```

## Replication

MongoDB provides high availability through replica sets. A replica set is a group of mongod instances that maintain the same data set.

## Sharding

Sharding is the process of storing data records across multiple machines. MongoDB uses sharding to support deployments with very large data sets and high throughput operations.</content>
<parameter name="filePath">C:\Users\dferr\Desktop\basic_chatbot\rag-chatbot\database_docs\mongodb_docs\mongodb-basics.md