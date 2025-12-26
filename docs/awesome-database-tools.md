# Awesome Database Tools [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> Community driven list of database tools

Here we will collect information about awesome useful and awesome experimental tools that simplify working with databases for DBA, DevOps, Developers and mere mortals.

Feel free to add information about your own db-tools or your favorite third-party db-tools.

For updates on `awesome-db-tools` and thoughts/news about databases/tools/SQL follow me at [@GraminMaksim](https://twitter.com/GraminMaksim)

## Contents
- [IDE](#ide)
- [GUI](#gui)
- [CLI](#cli)
- [Schema](#schema)
  - [Changes](#changes)
  - [Code generation](#code-generation)
  - [Diagrams](#diagrams)
  - [Documentations](#documentations)
  - [Design](#design)
  - [Samples](#samples)
- [API](#api)
- [Application platforms](#application-platforms)
- [Backup](#backup)
- [Cloning](#cloning)
- [Monitoring/Statistics/Perfomance](#monitoringstatisticsperfomance)
  - [Prometheus](#prometheus)
  - [Zabbix](#zabbix)
- [Testing](#testing)
- [HA/Failover/Sharding](#hafailoversharding)
- [Kubernetes](#kubernetes)
- [Configuration Tuning](#configuration-tuning)
- [DevOps](#devops)
- [Reporting](#reporting)
- [Distributions](#distributions)
- [Security](#security)
- [SQL](#sql)
  - [Analyzers](#analyzers)
  - [Extensions](#extensions)
  - [Frameworks](#frameworks)
  - [Formatters](#formatters)
  - [Games](#games)
  - [Parsers](#parsers)
  - [Über SQL](#über-sql)
  - [Language Server Protocol](#language-server-protocol)
  - [Learning](#learning)
  - [Plan](#plan)
  - [Scripts](#scripts)
- [Data](#data)
  - [Catalog](#catalog)
  - [Lineage](#lineage) 
  - [Generation/Masking/Subsetting](#generationmaskingsubsetting)
  - [Data Profilers](#data-profilers)
  - [Replication](#replication) 
  - [Compare](#compare) 
- [Papers](#papers)
- [Machine Learning](#machine-learning)

## IDE
- [AnySQL Maestro](https://www.sqlmaestro.com/products/anysql/maestro) - Premier multi-purpose admin tool for database management, control and development.
- [Aqua Data Studio](https://www.aquafold.com/aquadatastudio) - Productivity software for Database Developers, DBAs, and Analysts.
- [Coginiti Pro](https://www.coginiti.co/products/coginiti-pro/) - Modern IDE for analyst and analytics engineers with proweful script and grid functionality.
- [Database .net](http://fishcodelib.com/Database.htm) - Multiple database management tool with support for 20+ databases.
- [DataGrip](https://www.jetbrains.com/datagrip) - Cross-Platform IDE for Databases & SQL by JetBrains.
- [DataStation](https://github.com/multiprocessio/datastation) - Easily query, script, and visualize data from every database, file, and API.
- [DBeaver](https://github.com/dbeaver/dbeaver) - Free universal database manager and SQL client.
- [dbForge Edge](https://www.devart.com/dbforge/edge/) - Multidatabase solution for DB development, design, management, and administration of MySQL, MariaDB, SQL Server, Oracle, PostgreSQL databases, and various cloud services.
- [dbForge Studio for MySQL](https://www.devart.com/dbforge/mysql/studio) - Universal IDE for MySQL and MariaDB database development, management, and administration.
- [dbForge Studio for Oracle](https://www.devart.com/dbforge/oracle/studio) - Powerful IDE for Oracle management, administration, and development.
- [dbForge Studio for PostgreSQL](https://www.devart.com/dbforge/postgresql/studio) - GUI tool for managing and developing databases and objects.
- [dbForge Studio for SQL Server](https://www.devart.com/dbforge/sql/studio) - Powerful integrated development environment for SQL Server development, management, administration, data analysis, and reporting.
- [DBHawk](https://www.datasparc.com/) - Datasparc offers database security, database management, database governance and data analytics - all in one solution.
- [dbKoda](https://github.com/SouthbankSoftware/dbkoda) - Modern (JavaScript/Electron framework), open source IDE for MongoDB. It has features to support development, administration and performance tuning on MongoDB databases.
- [IBExpert](http://www.ibexpert.net/ibe) - Comprehensive GUI tool for Firebird and InterBase.
- [HeidiSQL](https://github.com/HeidiSQL/HeidiSQL) - A lightweight client for managing MySQL, MSSQL and PostgreSQL, written in Delphi.
- [Kangaroo](https://github.com/dbkangaroo/kangaroo) - A AI-powered SQL client and admin tool for popular databases(SQLite / MySQL / PostgreSQL / etc) on Windows / macOS / Linux, support table design, query, model, sync, export/import etc, focus on comfortable, fun and developer friendly.
- [KeepTool](https://keeptool.com) - A professional suite of tools for Oracle Database developers, administrators and advanced application users.
- [MySQL Workbench](https://www.mysql.com/products/workbench) - Unified visual tool for database architects, developers, and DBAs.
- [Navicat](https://www.navicat.com/en/products#navicat) - A database development tool that allows you to simultaneously connect to MySQL, MariaDB, SQL Server, Oracle, PostgreSQL, and SQLite databases from a single application.
- [Oracle SQL Developer](http://www.oracle.com/technetwork/developer-tools/sql-developer) - Free, integrated development environment that simplifies the development and management of Oracle Database in both traditional and Cloud deployments.
- [pgAdmin](https://www.pgadmin.org) - The most popular and feature rich Open Source administration and development platform for PostgreSQL, the most advanced Open Source database in the world.
- [pgAdmin3](https://www.bigsql.org/pgadmin3) - Long Term Support for pgAdmin3.
- [PL/SQL Developer](https://www.allroundautomations.com/products/pl-sql-developer) - IDE that is specifically targeted at the development of stored program units for Oracle Databases.
- [PostgreSQL Maestro](https://www.sqlmaestro.com/products/postgresql/maestro) - Complete and powerful database management, admin and development tool for PostgreSQL.
- [Querybook](https://github.com/pinterest/querybook) - Pinterest open-source Big Data Querying UI, combining collocated table metadata and a simple notebook IDE interface.
- [Slashbase](https://github.com/slashbaseide/slashbase) - The open-source collaborative IDE for your databases. Connect to your database, browse data, run a bunch of SQL commands or share SQL queries with your team, right from your browser.
- [Sql Server Management Studio](https://docs.microsoft.com/en-us/sql/ssms/sql-server-management-studio-ssms) - Integrated environment for managing any SQL infrastructure, for SQL Server and Azure SQL Databases.
- [Toad](https://www.quest.com/toad/) - Premier database solution for developers, admins and data analysts. Manage complex database changes with a single database management tool.
- [Toad Edge](https://www.toadworld.com/products/toad-edge) - Simplified database development tool for MySQL and PostgreSQL.
- [TOra](https://github.com/tora-tool/tora) - Open source SQL IDE for Oracle, MySQL and PostgreSQL dbs.
- [Valentina Studio](https://www.valentina-db.com/en/valentina-studio-overview) - Create, administer, query and explore Valentina DB, MySQL, MariaDB, PostgreSQL and SQLite databases for FREE.
- [WebDB](https://webdb.app) - Free Efficient Database IDE. Featuring Server Discovery, ERD, Data Generator, AI, NoSQL Structure Manager, Database Versioning and many more.


## GUI
- [Adminer](https://github.com/vrana/adminer) - Database management in a single PHP file.
- [Another Redis Desktop Manager](https://github.com/qishibo/AnotherRedisDesktopManager) - Free Open Source Redis Manager. Available on Mac, Linux, Windows, Homebrew, Snap, winget, and more.
- [Antares SQL](https://github.com/antares-sql/antares) - A modern, fast and productivity driven SQL client with a focus in UX. Available for Mac, Linux and Windows.
- [Azure Data Studio](https://github.com/microsoft/azuredatastudio) - A data management tool that enables working with SQL Server, PostgreSQL, Azure SQL DB and SQL DW from Windows, macOS and Linux.
- [Beekeeper Studio](https://github.com/beekeeper-studio/beekeeper-studio) - Open Source SQL Editor and Database Manager with a privacy commitment in their mission statement.
- [Clidey WhoDB](https://github.com/clidey/whodb) - A lightweight database explorer with next-gen UX for all SQL, NoSQL, Caches, and Queues.
- [DbGate](https://github.com/dbgate/dbgate) - Database manager for MySQL, PostgreSQL, SQL Server, MongoDB, SQLite and others. Runs under Windows, Linux, Mac or as web application.
- [DB Lens](https://github.com/dblens/app) - Open Source PostgreSQL GUI - Automatic ER diagrams, Internal DB Insights, Disk Utilisation, Performance Metrics, Index Usage, Sequential scan counts and more.
- [DbVisualizer](https://www.dbvis.com) - Universal database tool for developers, DBAs and analysts.
- [JackDB](https://www.jackdb.com) - Direct SQL access to all your data, no matter where it lives.
- [Jailer](https://github.com/Wisser/Jailer) - Database Subsetting and Relational Data Browsing Tool/Client.
- [Malewicz](https://github.com/mgramin/malewicz) - Yet Another WEB client for DB schema exploring and performance analysis, but originally created specifically for hacking and extending.
- [MissionKontrol](https://www.missionkontrol.io) - Modern drag & drop admin panel/client with full user permissions for non-technical users.
- [ocelotgui](https://github.com/ocelot-inc/ocelotgui) - For MySQL, MariaDB, and Tarantool. Developed for Linux but can run on Windows.
- [OmniDB](https://github.com/OmniDB/OmniDB) - Web tool for database management.
- [Pgweb](https://github.com/sosedoff/pgweb) - Web-based database browser for PostgreSQL, written in Go and works on macOS, Linux and Windows machines.
- [phpLiteAdmin](https://www.phpliteadmin.org) - Web-based SQLite database admin tool written in PHP with support for SQLite3 and SQLite2.
- [phpMyAdmin](https://github.com/phpmyadmin/phpmyadmin) - A web interface for MySQL and MariaDB.
- [psequel](http://www.psequel.com) - Provides a clean and simple interface for you to perform common PostgreSQL tasks quickly.
- [PopSQL](https://popsql.com) - Modern, collaborative SQL editor for your team.
- [Postico](https://eggerapps.at/postico) - A Modern PostgreSQL Client for the Mac.
- [Robo 3T](https://github.com/Studio3T/robomongo) - Shell-centric cross-platform MongoDB management tool.
- [Sequel Ace](https://github.com/Sequel-Ace/Sequel-Ace) - MySQL/MariaDB database management for macOS.
- [Sequel Pro](https://github.com/sequelpro/sequelpro) - Fast, easy-to-use Mac database management application for working with MySQL & MariaDB databases.
- [SQLite Expert](http://www.sqliteexpert.com/index.html) - Graphical interface supports all SQLite features.
- [sqlite-tui](https://github.com/mathaou/sqlite-tui) - A TUI for viewing SQLite databases, written in Go.
- [sqlpad](https://github.com/rickbergfalk/sqlpad) - Web-based SQL editor run in your own private cloud.
- [SQLPro](https://www.macpostgresclient.com) - A simple, powerful PostgreSQL manager for macOS.
- [SQuirreL](https://sourceforge.net/projects/squirrel-sql) - Graphical SQL client written in Java that will allow you to view the structure of a JDBC compliant database, browse the data in tables, issue SQL commands etc.
- [SQLTools](https://github.com/mtxr/vscode-sqltools) - Database management for VSCode.
- [SQLyog](https://www.webyog.com/product/sqlyog) - The most complete and easy to use MySQL GUI.
- [Tabix](https://github.com/tabixio/tabix) - SQL Editor & Open source simple business intelligence for Clickhouse.
- [TablePlus](https://github.com/TablePlus/TablePlus) - Modern, native, and friendly GUI tool for relational databases: MySQL, PostgreSQL, SQLite & more.
- [TeamPostgreSQL](http://www.teampostgresql.com) - PostgreSQL Web Administration GUI - use your PostgreSQL databases from anywhere, with rich, lightning-fast AJAX web interface.
- [Query.me](https://query.me) - Collaborative SQL editor in Notebook format. Let's you reference query results using JINJA, visualize data, and schedule runs and exports.


## CLI
- [ipython-sql](https://github.com/catherinedevlin/ipython-sql) - Connect to a database for issue SQL commands within IPython or IPython Notebook.
- [iredis](https://github.com/laixintao/iredis) - A Cli for Redis with AutoCompletion and Syntax Highlighting.
- [pgcenter](https://github.com/lesovsky/pgcenter) - Top-like admin tool for PostgreSQL.
- [pg_activity](https://github.com/julmon/pg_activity) - Top-like application for PostgreSQL server activity monitoring.
- [pg_top](https://github.com/markwkm/pg_top) - Top for PostgreSQL.
- [pspg](https://github.com/okbob/pspg) - PostgreSQL Pager.
- [SQLcl](http://www.oracle.com/technetwork/developer-tools/sqlcl/overview/index.html) - Oracle SQL Developer Command Line (SQLcl) is a free command line interface for Oracle Database.
- [sqlite-utils](https://github.com/simonw/sqlite-utils) - CLI tools for manipulating SQLite database files - inserting data, running queries, creating indexes, configuring full-text search and more.
- [SQLLine](https://github.com/julianhyde/sqlline) - Command-line shell for issuing SQL to relational databases via JDBC.
- [usql](https://github.com/xo/usql) - A universal command-line interface for PostgreSQL, MySQL, Oracle Database, SQLite3, Microsoft SQL Server, and many other databases including NoSQL and non-relational databases!

### dbcli
- [athenacli](https://github.com/dbcli/athenacli) - CLI tool for AWS Athena service that can do auto-completion and syntax highlighting.
- [litecli](https://github.com/dbcli/litecli) - CLI for SQLite Databases with auto-completion and syntax highlighting.
- [mssql-cli](https://github.com/dbcli/mssql-cli) - A command-line client for SQL Server with auto-completion and syntax highlighting.
- [mycli](https://github.com/dbcli/mycli) - A Terminal Client for MySQL with AutoCompletion and Syntax Highlighting.
- [pgcli](https://github.com/dbcli/pgcli) - PostgreSQL CLI with autocompletion and syntax highlighting.
- [vcli](https://github.com/dbcli/vcli) - Vertica CLI with auto-completion and syntax highlighting.


## Schema

### Changes
- [2bass](https://github.com/CourseOrchestra/2bass) - Database configuration-as-code tool that utilizes concept of idempotent DDL scripts.
- [Atlas](https://github.com/ariga/atlas) - Inspect and Apply changes to your database schema.
- [Bytebase](https://github.com/bytebase/bytebase) - Web-based, zero-config, dependency-free database schema change and version control tool for teams.
- [flyway](https://github.com/flyway/flyway) - Database migration tool.
- [gh-ost](https://github.com/github/gh-ost) - Online schema migration for MySQL.
- [liquibase](https://github.com/liquibase/liquibase) - Database-independent library for tracking, managing and applying database schema changes.
- [migra](https://github.com/djrobstep/migra) - Like diff but for PostgreSQL schemas.
- [node-pg-migrate](https://github.com/salsita/node-pg-migrate) - Node.js database migration management built exclusively for PostgreSQL. (But can also be used for other DBs conforming to SQL standard - e.g. CockroachDB.)
- [pg-osc](https://github.com/shayonj/pg-osc) - Easy CLI tool for making zero downtime schema changes and backfills in PostgreSQL.
- [Prisma Migrate](https://github.com/prisma/migrate) - Declarative database schema migration tool that uses a declarative data modeling syntax to describe your database schema.
- [Pyrseas](https://github.com/perseas/Pyrseas) - Provides utilities to describe a PostgreSQL database schema as YAML.
- [Reshape](https://github.com/fabianlindfors/reshape) - An easy-to-use, zero-downtime schema migration tool for Postgres.
- [SchemaHero](https://github.com/schemahero/schemahero) - A Kubernetes operator for declarative database schema management (gitops for database schemas).
- [Skeema](https://github.com/skeema/skeema) - Declarative pure-SQL schema management system for MySQL and MariaDB, with support for sharding and external online schema change tools.
- [Sqitch](https://github.com/sqitchers/sqitch) - Sensible database-native change management for framework-free development and dependable deployment.
- [sqldef](https://github.com/k0kubun/sqldef) - Idempotent schema management for MySQL, PostgreSQL, and more.
- [yuniql](https://github.com/rdagumampan/yuniql) - Yet another schema versioning and migration tool just made with native .NET Core 3.0+ and hopefully better.

### Code generation
- [ddl-generator](https://github.com/catherinedevlin/ddl-generator) - Infers SQL DDL (Data Definition Language) from table data.
- [scheme2ddl](https://github.com/qwazer/scheme2ddl) - Command line util for export Oracle schema to set of ddl init scripts with ability to filter undesirable information, separate DDL in different files, pretty format output.

### Diagrams
- [Azimutt](https://github.com/azimuttapp/azimutt) - An Entity Relationship diagram (ERD) visualization tool, with various filters and inputs to help understand your database schema.
- [ChartDB](https://github.com/chartdb/chartdb) - Free and Open-source database diagrams editor, visualize and design your DB with a single query.
- [DrawDB](https://github.com/drawdb-io/drawdb) - Free, simple, and intuitive online database design tool and SQL generator. 
- [ERAlchemy](https://github.com/Alexis-benoist/eralchemy) - Entity Relation Diagrams generation tool.
- [ERD Lab](https://www.erdlab.io/) - Free cloud based entity relationship diagram (ERD) tool made for developers.
- [Liam ERD](https://github.com/liam-hq/liam) - Open-source tool that generates beautiful and easy-to-read Entity Relationship Diagrams from your database and ORMs.
- [QuickDBD](https://www.quickdatabasediagrams.com/) - Simple online tool to quickly draw database diagrams.

### Documentations
- [dbdocs](https://dbdocs.io/) - Create web-based database documentation using DSL code.
- [DBML](https://github.com/holistics/dbml) - Database Markup Language, designed to define and document database structures.
- [SchemaCrawler](https://github.com/schemacrawler/SchemaCrawler) - A free database schema discovery and comprehension tool.
- [Schema Spy](https://github.com/schemaspy/schemaspy) - Generating your database to HTML documentation, including Entity Relationship diagrams.
- [tbls](https://github.com/k1LoW/tbls) - CI-Friendly tool for document a database, written in Go.

### Design
- [Database Design](https://github.com/alextanhongpin/database-design) - Useful tips for designing robust database schema.
- [DBDiagram](https://dbdiagram.io) - A free, simple tool to draw ER diagrams by just writing code.
- [DbSchema](https://dbschema.com/) - Universal database designer for out-of-the-box schema management, schema documentation, design in a team, and deployment on multiple databases. DbSchema features tools for writing and writing and executing queries, exploring the data, generating data, and building reports.
- [ERBuilder Data Modeler](https://soft-builder.com/erbuilder-data-modeler) - Easy-to-use database modeling software for high-quality data models. It's a complete data modeling solution for data modelers and data architects.
- [Moon Modeler](https://www.datensen.com) - Data modeling tool for both noSQL and relational databases. Available for Windows, Linux and macOS.
- [Navicat Data Modeler](https://www.navicat.com/en/products/navicat-data-modeler) - A powerful and cost-effective database design tool which helps you build high-quality conceptual, logical and physical data models.
- [Oracle SQL Developer Data Modeler](http://www.oracle.com/technetwork/developer-tools/datamodeler/overview/index.html) - Free graphical tool that enhances productivity and simplifies data modeling tasks.
- [pgmodeler](https://github.com/pgmodeler/pgmodeler) - Data modeling tool designed for PostgreSQL.
- [WWW SQL Designer](https://github.com/ondras/wwwsqldesigner) - Online SQL diagramming tool.

### Samples
- [Oracle Database Sample Schemas](https://github.com/oracle/db-sample-schemas) - Sample schemas for Oracle Database.


## API
Building API for your Data
- [Datasette](https://github.com/simonw/datasette) - A tool for exploring and publishing data.
- [DreamFactory](https://github.com/dreamfactorysoftware/dreamfactory) - A open source REST API backend for mobile, web, and IoT applications.
- [Graphweaver](https://github.com/exogee-technology/graphweaver) - Turn multiple data sources into a single GraphQL API.
- [Hasura GraphQL Engine](https://github.com/hasura/graphql-engine) - Blazing fast, instant realtime GraphQL APIs on PostgreSQL with fine grained access control, also trigger webhooks on database events.
- [Oracle REST Data Services](http://www.oracle.com/technetwork/developer-tools/rest-data-services) - A mid-tier Java application, ORDS maps HTTP(S) verbs (GET, POST, PUT, DELETE, etc.) to database transactions and returns any results formatted using JSON.
- [Prisma](https://github.com/prismagraphql/prisma) - Turns your database into a realtime GraphQL API.
- [PostGraphile](https://github.com/graphile/postgraphile) - Instantly spin-up a GraphQL API server by pointing PostGraphile at your existing PostgreSQL database.
- [PostgREST](https://github.com/PostgREST/postgrest) - REST API for any PostgreSQL database.
- [prest](https://github.com/prest/prest) - Is a way to serve a RESTful API from any databases written in Go.
- [Remult](https://github.com/remult/remult) - End-to-end type-safe CRUD via REST API for your database, with fine-grained access control.
- [restSQL](https://github.com/restsql/restsql) - SQL generator with Java and HTTP APIs, uses a simple RESTful HTTP API with XML or JSON serialization.
- [resquel](https://github.com/formio/resquel) - Easily convert your SQL database into a REST API.
- [sandman2](https://github.com/jeffknupp/sandman2) - Automatically generate a RESTful API service for your legacy database.
- [soul](https://github.com/thevahidal/soul) - Automatic SQLite RESTful and realtime API server.
- [VulcanSQL](https://github.com/Canner/vulcan-sql) - Write templated SQL to automatically exposing RESTful APIs from your database/data warehouse/data lake.

## Application platforms
Low-code and no-code platforms for application building
- [Appsmith](https://github.com/appsmithorg/appsmith) - Powerful open source low code framework to build internal applications really quickly.
- [Budibase](https://github.com/Budibase/budibase) - Low-code platform for creating internal apps in minutes.
- [ILLA Cloud](https://github.com/illacloud/illa-builder) - Low-code internal tool building platform.
- [Nhost](https://github.com/nhost/nhost) - The Open Source Firebase Alternative with GraphQL.
- [Saltcorn](https://github.com/saltcorn/saltcorn) - Open source no-code builder for web datatabase applications. Server and drag-and-drop UI builder, data stored in PostgreSQL or SQLite.
- [SQLPage](https://github.com/sqlpage/SQLPage) - Fast SQL-only data application builder. Automatically build a UI on top of SQL queries.
- [Tooljet](https://github.com/ToolJet/ToolJet) - Open-source low-code platform to build internal tools.


## Backup
- [BaRMan](https://github.com/2ndquadrant-it/barman) - Backup and Recovery Manager for PostgreSQL.
- [pgbackrest](https://github.com/pgbackrest/pgbackrest) - Reliable PostgreSQL Backup & Restore.
- [pgcopydb](https://github.com/dimitri/pgcopydb) - Copy a PostgreSQL database to a target PostgreSQL server (pg_dump | pg_restore on steroids).

## Cloning
- [Database Lab Engine](https://gitlab.com/postgres-ai/database-lab) - Instant thin cloning for PostgreSQL to scale the development process.
- [clone_schema](https://github.com/denishpatel/pg-clone-schema) - PostgreSQL clone schema utility without need of going outside of database.
- [Spawn](https://spawn.cc/) - Cloud service for creating instant database copies for development and CI. No more local db installs, instant recovery to arbitrary save points, isolated copies for each feature branch or test. Instant provisioning regardless of database size.


## Monitoring/Statistics/Perfomance
- [ASH Viewer](https://github.com/akardapolov/ASH-Viewer) - Provides a graphical view of active session history data within the Oracle and PostgreSQL DB.
- [Metis](https://www.metisdata.io/product/troubleshooting) - Provides observability and performance tuning for SQL databases.
- [Monyog](https://www.webyog.com/product/monyog) - Agentless & Cost-effective MySQL Monitoring Tool.
- [mssql-monitoring](https://github.com/microsoft/mssql-monitoring) - Monitor your SQL Server on Linux performance using collectd, InfluxDB and Grafana.
- [Navicat Monitor](https://www.navicat.com/en/products/navicat-monitor) - A safe, simple and agentless remote server monitoring tool that is packed with powerful features to make your monitoring effective as possible.
- [Percona Monitoring and Management](https://github.com/percona/pmm) - Open source platform for managing and monitoring MySQL and MongoDB performance.
- [pganalyze collector](https://github.com/pganalyze/collector) - Pganalyze statistics collector for gathering PostgreSQL metrics and log data.
- [pgbadger](https://github.com/dalibo/pgbadger) - A fast PostgreSQL Log Analyzer.
- [pgDash](https://pgdash.io) - Measure and track every aspect of your PostgreSQL databases.
- [PgHero](https://github.com/ankane/pghero) - A performance dashboard for PostgreSQL - health checks, suggested indexes, and more.
- [pgmetrics](https://github.com/rapidloop/pgmetrics) - Collect and display information and stats from a running PostgreSQL server.
- [pgMonitor](https://github.com/CrunchyData/pgmonitor) - All-in-one tool to easily create an environment to visualize the health and performance of your PostgreSQL cluster.
- [pgMustard](https://www.pgmustard.com) - A user interface for PostgreSQL explain plans, plus tips to improve performance.
- [pgstats](https://github.com/gleu/pgstats) - Collects PostgreSQL statistics, and either saves them in CSV files or print them on the stdout.
- [pgwatch2](https://github.com/cybertec-postgresql/pgwatch2) - Flexible self-contained PostgreSQL metrics monitoring/dashboarding solution.
- [PostgreSQL Metrics](https://github.com/spotify/postgresql-metrics) - Service to extract and provide metrics on your PostgreSQL database.
- [PostgreSQL Monitor](https://postgresmonitor.com) - An easy-to-use monitoring service for PostgreSQL providing alerts, dashboards, query stats and dynamic recommendations.
- [postgres-checkup](https://gitlab.com/postgres-ai/postgres-checkup) - New-generation diagnostics tool that allows users to do a deep analysis of the health of PostgreSQL databases.
- [Promscale](https://github.com/timescale/promscale) - The open-source observability backend for metrics and traces powered by SQL.
- [Releem](https://releem.com) - Performance monitoring and optimization tool for MySQL & MariaDB that delivers actionable insights and safe automation for misconfigurations, slow queries, schema issues, and deadlocks, reducing manual work at scale.
- [Telegraf PostgreSQL plugin](https://github.com/influxdata/telegraf/tree/master/plugins/inputs/postgresql) - Provides metrics for your PostgreSQL database.

### Prometheus
- [pgSCV](https://github.com/weaponry/pgscv) - Metrics exporter for PostgreSQL and PostgreSQL-related services.
- [postgres_exporter](https://github.com/wrouesnel/postgres_exporter) - Prometheus exporter for PostgreSQL server metrics.
- [pg_exporter](https://github.com/Vonng/pg_exporter) - Fully customizable Prometheus exporter for PostgreSQL & Pgbouncer with fine-grained execution control.

### Zabbix
- [Mamonsu](https://github.com/postgrespro/mamonsu) - Monitoring agent for PostgreSQL.
- [Orabbix](http://www.smartmarmot.com/wiki/index.php?title=Orabbix) - Plugin designed to work with Zabbix Enterprise Monitor to provide multi-tiered monitoring, performance and availability reporting and measurement for Oracle Databases, along with server performance metrics.
- [pg_monz](https://github.com/pg-monz/pg_monz) - This is the Zabbix monitoring template for PostgreSQL Database.
- [Pyora](https://github.com/bicofino/Pyora) - Python script to monitor Oracle Databases.
- [ZabbixDBA](https://github.com/anetrusov/ZabbixDBA) - Fast, flexible, and continuously developing plugin to monitor your RDBMS.


## Testing
- [DbFit](https://github.com/dbfit/dbfit) - A database testing framework that supports easy test-driven development of your database code.
- [pgTAP](https://github.com/theory/pgtap) - Unit Testing for PostgreSQL.
- [RegreSQL](https://github.com/dimitri/regresql) - Regression Testing your SQL queries.
- [SQLancer](https://github.com/sqlancer/sqlancer) - Automatically test DBMS in order to find logic bugs in their implementation.


## HA/Failover/Sharding
- [Citus](https://github.com/citusdata/citus) - PostgreSQL extension that distributes your data and your queries across multiple nodes.
- [patroni](https://github.com/zalando/patroni) - A template for PostgreSQL High Availability with ZooKeeper, etcd, or Consul.
- [Percona XtraDB Cluster](https://github.com/percona/percona-xtradb-cluster) - A High Scalability Solution for MySQL Clustering and High Availability.
- [ShardingSphere](https://github.com/apache/shardingsphere) - Distributed SQL transaction & query engine for data sharding, scaling, encryption, and more - on any database.
- [stolon](https://github.com/sorintlab/stolon) - Cloud native PostgreSQL manager for PostgreSQL high availability.
- [pg_auto_failover](https://github.com/citusdata/pg_auto_failover) - PostgreSQL extension and service for automated failover and high-availability.
- [pglookout](https://github.com/aiven/pglookout) - PostgreSQL replication monitoring and failover daemon.
- [pgslice](https://github.com/ankane/pgslice) - PostgreSQL partitioning as easy as pie.
- [PostgreSQL Automatic Failover](https://github.com/ClusterLabs/PAF) - High-Availibility for PostgreSQL, based on industry references Pacemaker and Corosync.
- [autobase](https://github.com/vitabaks/autobase) - Open-source DBaaS that automates the deployment and management of highly available PostgreSQL clusters.
- [Vitess](https://github.com/vitessio/vitess) - Database clustering system for horizontal scaling of MySQL through generalized sharding.


## Kubernetes
- [KubeDB](https://kubedb.com) - Making running production-grade databases easy on Kubernetes.
- [PostgreSQL operator](https://github.com/zalando/postgres-operator) - The PostgreSQL Operator enables highly-available PostgreSQL clusters on Kubernetes (Kubernetes) powered by Patroni.
- [Spilo](https://github.com/zalando/spilo) - HA PostgreSQL Clusters with Docker.
- [StackGres](https://gitlab.com/ongresinc/stackgres) - Enterprise-grade, Full Stack PostgreSQL on Kubernetes.


## Configuration Tuning
- [MySQLTuner-perl](https://github.com/major/MySQLTuner-perl) - Script written in Perl that allows you to review a MySQL installation quickly and make adjustments to increase performance and stability.
- [PGConfigurator](https://pgconfigurator.cybertec-postgresql.com) - Free online tool to generate an optimized `postgresql.conf`.
- [pgtune](https://github.com/gregs1104/pgtune) - PostgreSQL configuration wizard.
- [postgresqltuner.pl](https://github.com/jfcoz/postgresqltuner) - Simple script to analyse your PostgreSQL database configuration, and give tuning advice.


## DevOps
- [DBmaestro](https://www.dbmaestro.com) - Accelerates release cycles & supports agility across the entire IT ecosystem.
- [Toad DevOps Toolkit](https://www.quest.com/products/toad-devops-toolkit/) - Executes key database development functions within your DevOps workflow —without compromising quality, performance or reliability.


## Reporting
- [Chartbrew](https://chartbrew.com) - Create live dashboards, charts, and client reports from multiple databases and services.
- [Poli](https://github.com/shzlw/poli) - An easy-to-use SQL reporting application built for SQL lovers.


## Distributions
- [DBdeployer](https://github.com/datacharmer/dbdeployer) - Tool that deploys MySQL database servers easily.
- [dbatools](https://github.com/sqlcollaborative/dbatools) - PowerShell module that you may think of like a command-line SQL Server Management Studio.
- [Postgres.app](https://github.com/PostgresApp/PostgresApp) - Full-featured PostgreSQL installation packaged as a standard Mac app.
- [BigSQL](https://www.bigsql.org) - A developer-friendly distribution of PostgreSQL.
- [Elephant Shed](https://github.com/credativ/elephant-shed) - Web-based PostgreSQL management front-end that bundles several utilities and applications for use with PostgreSQL.
- [Pigsty](https://github.com/Vonng/pigsty) - Battery-Included Open-Source Distribution for PostgreSQL with ultimate observability & Database-as-Code toolbox for developers.


## Security
- [Acra](https://github.com/cossacklabs/acra) - Database security suite. Database proxy with field-level encryption, search through encrypted data, SQL injections prevention, intrusion detection, honeypots. Supports client-side and proxy-side ("transparent") encryption. SQL, NoSQL.
- [Databunker](https://github.com/securitybunker/databunker) - Special GDPR compliant secure vault for customer records built on top of regular DB.
- [Inspektor](https://github.com/poonai/inspektor) - Access control layer for databases. Inspektor leverages open policy agent to make policy decisions.


## SQL

### Analyzers
- [Holistic.dev](https://holistic.dev) - Automatic detection service for database performance, security, and architecture issues.
- [SQLCheck](https://github.com/jarulraj/sqlcheck) - Automatically detects common SQL anti-patterns.
- [SQLFluff](https://github.com/sqlfluff/sqlfluff) - Dialect-flexible and configurable SQL linter.
- [SQLLineage](https://github.com/reata/sqllineage) - SQL Lineage Analysis Tool powered by Python.
- [TSQLLint](https://github.com/tsqllint/tsqllint) - A tool for describing, identifying, and reporting the presence of anti-patterns in TSQL scripts.

### Extensions
- [PartiQL](https://partiql.org) - SQL-compatible access to relational, semi-structured, and nested data.

### Frameworks
- [Apache Calcite](https://calcite.apache.org) - Dynamic data management framework with advanced SQL features.
- [ZetaSQL](https://github.com/google/zetasql) - Analyzer Framework for SQL.

### Formatters
- [CodeBuff](https://github.com/antlr/codebuff) - Language-agnostic pretty-printing through machine learning.
- [JSQLFormatter](https://github.com/manticore-projects/jsqlformatter) - Open Source Java SQL Formatter for many RDBMS based on JSqlParser.
- [SQL Online](https://sqlonline.in) - A Free Tool to format your SQL Queries followed by content for Analysts.
- [pgFormatter](https://github.com/darold/pgFormatter) - A PostgreSQL SQL syntax beautifier.
- [Poor SQL](https://poorsql.com) - Instant free and open-source T-SQL formatting. 
- [SQL Formatter](https://github.com/zeroturnaround/sql-formatter) - JavaScript library for pretty-printing SQL queries.

### Games
- [Lost at SQL](https://lost-at-sql.therobinlord.com) - A SQL learning game to help you pick up basic SQL skills - so that you can use queries to get information.
- [Querymon](https://codepip.com/games/querymon/) - Learn to use SQL queries on the Querydex, a database of monsters from common to legendary.
- [Schemaverse](https://datalemur.com/blog/games-to-learn-sql#schemaverse) - A Space-based strategy game implemented entirely within a PostgreSQL database.
- [SQL Island](https://sql-island.informatik.uni-kl.de) - After the survived plane crash, you will be stuck on SQL Island for the time being. By making progress in the game, you will find a way to escape from this island.
- [SQL Murder Mystery](https://mystery.knightlab.com) - Designed to be both a self-directed lesson to learn SQL concepts and commands and a fun game for experienced SQL users to solve an intriguing crime.
- [SQL Police Department](https://sqlpd.com) - In SQLPD, you get to solve crimes while learning SQL at the same time.

### Parsers
- [General SQL Parser](https://www.sqlparser.com) - Parsing, formatting, modification and analysis for SQL.
- [jOOQ](https://github.com/jOOQ/jOOQ) - Parses SQL, translates it to other dialects, and allows for expression tree transformations.
- [JSqlParser](https://github.com/JSQLParser/JSqlParser) - Parses an SQL statement and translate it into a hierarchy of Java classes.
- [libpg_query](https://github.com/pganalyze/libpg_query) - C library for accessing the PostgreSQL parser outside of the server environment.
- [More SQL Parsing!](https://github.com/klahnakoski/mo-sql-parsing) - Parse SQL into JSON.
- [sqlparse](https://github.com/andialbrecht/sqlparse) - Non-validating SQL parser for Python.
- [SQLGlot](https://github.com/tobymao/sqlglot) - Pure Python SQL parser, transpiler, and builder.

### Über SQL
Run SQL queries against anything
- [CloudQuery](https://github.com/cloudquery/cloudquery) - Extracts, transforms, and loads your cloud assets into normalized PostgreSQL tables.
- [csvq](https://github.com/mithrandie/csvq) - SQL-like query language for CSV.
- [dsq](https://github.com/multiprocessio/dsq) - Commandline tool for running SQL queries against JSON, CSV, Excel, Parquet, and more.
- [MAT Calcite plugin](https://github.com/vlsi/mat-calcite-plugin) - This plugin for Eclipse Memory Analyzer allows to query heap dump via SQL.
- [OctoSQL](https://github.com/cube2222/octosql) - Query tool that allows you to join, analyse and transform data from multiple databases and file formats using SQL.
- [osquery](https://github.com/osquery/osquery) - SQL powered operating system instrumentation, monitoring, and analytics.
- [Resmo](https://www.resmo.com) - Audit and evaluate resources using SQL.
- [Steampipe](https://github.com/turbot/steampipe) - Use SQL to instantly query your cloud services (AWS, Azure, GCP and more).
- [TextQL](https://github.com/dinedal/textql) - Execute SQL against structured text like CSV or TSV.
- [trdsql](https://github.com/noborus/trdsql) - CLI tool that can execute SQL queries on CSV, LTSV, JSON and TBLN.
- [Trino](https://github.com/trinodb/trino) - Distributed SQL query engine designed to query large data sets distributed over one or more heterogeneous data sources.

### Language Server Protocol
- [SQLLanguageServer](https://github.com/joe-re/sql-language-server) - SQL Language Server.
- [sqls](https://github.com/lighttiger2505/sqls) - SQL Language Server written in Go.

### Learning
Learning and puzzles for SQL
- [Advanced SQL Puzzles](https://github.com/smpetersgithub/AdvancedSQLPuzzles) - Difficult set-based SQL puzzles.
- [Hackerrank](https://www.hackerrank.com/domains/sql) - Practice coding, prepare for interviews, and get hired.
- [Learn SQL in a Month of Lunches](https://www.manning.com/books/learn-sql-in-a-month-of-lunches) - A book about how to use SQL to retrieve, filter, and analyze data.
- [LeetCode](https://leetcode.com/problemset/database) - Enhance your skills, expand your knowledge and prepare for technical interviews.
- [Select Star SQL](https://selectstarsql.com) - Free interactive book which aims to be the best place on the internet for learning SQL.
- [StrataScratch](https://www.stratascratch.com/blog/categories/sql) - Data science educational resources.
- [SQL Murder Mystery](https://github.com/NUKnightLab/sql-mysteries) - Self-directed lesson to learn SQL concepts and commands and a fun game for experienced SQL users to solve an intriguing crime.

### Plan
- [Explain.depesz.com](https://explain.depesz.com) - Online tool for PostgreSQL execution plan analysis.
- [Explain Extended](https://explainextended.com) - How to create fast database queries.
- [PEV2](https://github.com/dalibo/pev2) - PostgreSQL Execution Plan Visualizer.
- [pgMustard](https://www.pgmustard.com) - A user interface for PostgreSQL explain plans, plus tips to improve performance.

### Scripts
- [Adminer](https://github.com/vrana/adminer) - Database management in a single PHP file.
- [pgbedrock](https://github.com/rdadolf/pgbedrock) - Manage PostgreSQL roles and privileges in a declarative way.
- [pgsync](https://github.com/ankane/pgsync) - Sync data from one Postgres database to another.
- [pgxnclient](https://github.com/dvarrazzo/pgxnclient) - Command line client for the PostgreSQL Extension Network.
- [PostGIS](https://github.com/postgis/postgis) - Spatial database extender for PostgreSQL object-relational database.
- [Postgres.app](https://github.com/PostgresApp/PostgresApp) - Full-featured PostgreSQL installation packaged as a standard Mac app.
- [psql2csv](https://github.com/fphilipe/psql2csv) - Run a query in psql and output the result as CSV.
- [sql-scripts](https://github.com/nilportugues/sql-scripts) - SQL scripts for PostgreSQL, MySQL, OracleSQL, SQLServer and SQLite.
- [sqldump](https://github.com/aklomp/sqldump) - Lightweight, fast SQL dump reader.
- [sqlfiddle](https://sqlfiddle.com) - Online SQL playground.
- [sqlpad](https://github.com/rickbergfalk/sqlpad) - Web-based SQL editor run in your own private cloud.
- [sqlpkg](https://github.com/nalgeon/sqlpkg) - SQLite package manager.
- [sqlx](https://github.com/launchbadge/sqlx) - The Rust SQL Toolkit. An async, pure Rust SQL crate featuring compile-time checked queries without a DSL. Supports PostgreSQL, MySQL, and SQLite.
- [usql](https://github.com/xo/usql) - A universal command-line interface for PostgreSQL, MySQL, Oracle Database, SQLite3, Microsoft SQL Server, and many other databases including NoSQL and non-relational databases!


## Data

### Catalog
- [Amundsen](https://github.com/amundsen-io/amundsen) - Metadata search & discovery tool for improved data discoverability.
- [DataHub](https://github.com/datahub-project/datahub) - The Metadata Platform for the Modern Data Stack.
- [Metacat](https://github.com/Netflix/metacat) - Unified metadata exploration API service for Hive, RDS, Teradata, Redshift, S3 and Cassandra.
- [OpenMetadata](https://github.com/open-metadata/OpenMetadata) - Open standard for metadata. A single place to discover, collaborate and get your data right.

### Lineage 
- [Apache Atlas](https://atlas.apache.org) - Data governance and metadata framework for Hadoop.
- [Collibra](https://www.collibra.com) - Data governance platform.
- [Egeria](https://github.com/odpi/egeria) - Open metadata and governance for data and software landscapes.
- [Marquez](https://github.com/MarquezProject/marquez) - Collect, aggregate, and visualize a data ecosystem's metadata.

### Generation/Masking/Subsetting
- [Databuddy](https://github.com/databuddy-hq/databuddy) - Magical data generation tool for developers.
- [Datafaker](https://github.com/datafaker-net/datafaker) - Generate fake data for a variety of purposes.
- [dbForge Data Generator for MySQL](https://www.devart.com/dbforge/mysql/data-generator) - Powerful GUI tool for creating massive volumes of realistic test data.
- [dbForge Data Generator for Oracle](https://www.devart.com/dbforge/oracle/data-generator) - GUI tool for populating Oracle schemas with tons of realistic test data.
- [dbForge Data Generator for SQL Server](https://www.devart.com/dbforge/sql/data-generator) - GUI tool for a fast generation of large volumes of SQL Server test table data.
- [Fake2db](https://github.com/emirozer/fake2db) - Fake database generator.
- [Mockaroo](https://mockaroo.com) - Generate realistic data for testing.
- [pg_anonymize](https://github.com/rjuju/pg_anonymize) - Anonymize data in PostgreSQL using SQL.
- [pgcopydb](https://github.com/dimitri/pgcopydb) - Copy a PostgreSQL database to a target PostgreSQL server (pg_dump | pg_restore on steroids).
- [pglogical](https://github.com/2ndQuadrant/pglogical) - PostgreSQL Logical Replication.
- [synthetic-data-generator](https://github.com/fako/synthetic-data-generator) - Generate synthetic data using Markov chains.

### Data Profilers
- [Datafold](https://www.datafold.com) - Data quality monitoring & testing for analytics and data pipelines.
- [Dataprofiler](https://github.com/capitalone/dataprofiler) - What's in your data? Extract schema, statistics and entities from datasets.
- [Great Expectations](https://github.com/greatexpectations/great_expectations) - Always know what to expect from your data.
- [Monte Carlo](https://www.montecarlodata.com) - Data observability platform.
- [Soda](https://github.com/sodadata/soda-core) - Data quality testing for the modern data stack.

### Replication 
- [Bucardo](https://github.com/bucardo/bucardo) - Asynchronous PostgreSQL replication system, allowing for both multi-master and multi-slave operations.
- [pglogical](https://github.com/2ndQuadrant/pglogical) - PostgreSQL Logical Replication.
- [Slony-I](https://github.com/postgrespro/slony) - "Master to multiple slaves" replication system for PostgreSQL.

### Compare
- [apgdiff](https://github.com/credativ/apgdiff) - Another PostgreSQL diff tool that is useful for schema upgrades.
- [pgdiff](https://github.com/eventuate-foundation/pgdiff) - Compares the PostgreSQL schema between two databases and generates SQL statements that can be run manually against the second database to make their schemas match.
- [pgquarrel](https://github.com/eulerto/pgquarrel) - Compares PostgreSQL database schemas (DDL).
- [Schema Compare for Oracle](https://www.devart.com/dbforge/oracle/schema-compare) - Tool for easy and effective comparison and synchronization of Oracle database schemas.
- [Schema Compare for SQL Server](https://www.devart.com/dbforge/sql/schema-compare) - Tool for easy and effective comparison and synchronization of SQL Server database schemas.
- [SQL Server Data Compare](https://www.devart.com/dbforge/sql/data-compare) - Tool for easy and effective comparison and synchronization of SQL Server data.

## Papers
- [Architecture of a Database System](http://db.cs.berkeley.edu/papers/fntdb07-architecture.pdf) - Anatomy of a database management system.
- [Database System Concepts](https://www.db-book.com) - The standard textbook on database systems.
- [Readings in Database Systems](http://www.redbook.io) - Online collection of influential papers in database systems.
- [The Database Relational Model: A Retrospective Review and Analysis](https://www.cidrdb.org/cidr2015/Papers/CIDR15_Paper16.pdf) - A look back at the relational model.

## Machine Learning
- [MADlib](https://github.com/apache/madlib) - Open-source library for scalable in-database analytics.
- [MLDB](https://github.com/mldbai/mldb) - The Machine Learning Database.
- [ModelDB](https://github.com/mitdbg/modeldb) - End-to-end ML model management system.
- [pgml](https://github.com/postgresml/postgresml) - PostgreSQL extension that enables ML workloads.
- [Predibase](https://predibase.com) - No-code platform for machine learning on databases.
- [SQLFlow](https://github.com/sql-machine-learning/sqlflow) - Extends SQL to support AI/ML workloads.