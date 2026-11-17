### 事务

#### 介绍

[事务 transaction](https://en.wikipedia.org/wiki/Database_transaction) 可能是关系型数据库最重要的功能之一，往往我们通过事务可以组织一系列的操作，并且不必担心一致性，这为我们编写业务代码提供了很大的便利，此外，当数据库被并发访问时，事务的存在为我们提供了隔离变化的机制，让开发人员不必考虑过于复杂的并发问题。

对于一个关系型数据库来说，事务必须具有 ACID 特性，以下引用自 Wikipedia：

*   **原子性（Atomicity）**：事务作为一个整体被执行，包含在其中的对数据库的操作要么全部被执行，要么都不执行。
*   **一致性（Consistency）**：事务应确保数据库的状态从一个一致状态转变为另一个一致状态。*一致状态*的含义是数据库中的数据应满足完整性约束。
*   **隔离性（Isolation）**：多个事务并发执行时，一个事务的执行不应影响其他事务的执行。
*   **持久性（Durability）**：已被提交的事务对数据库的修改应该永久保存在数据库中。

对于 PostgreSQL 来说，事务的使用和其他数据库没什么特别的区别，都是使用 BEGIN 来启动一个事务，并且在合适的时机使用 COMMIT 或者 ROLLBACK 进行提交或者回滚。当然，PostgreSQL 还支持 SAVEPOINT 存档功能，对于一个较长的事务，你可以自己设置回滚点，例如下面的操作：

```sql
for_test=# BEGIN;
BEGIN
for_test=# INSERT INTO consumers(id, consumer_id) VALUES (1, 'jerry');
INSERT 0 1
for_test=# 
for_test=# INSERT INTO consumers(id, consumer_id) VALUES (2, 'Tom');
INSERT 0 1
for_test=# SELECT * FROM consumers;
-[ RECORD 1 ]------
id          | 1
consumer_id | jerry
-[ RECORD 2 ]------
id          | 2
consumer_id | Tom

for_test=# SAVEPOINT save_point_1;
SAVEPOINT
for_test=# INSERT INTO consumers(id, consumer_id) VALUES (3, 'Bob');
INSERT 0 1
for_test=# INSERT INTO consumers(id, consumer_id) VALUES (1, 'Harry');
ERROR:  duplicate key value violates unique constraint "consumers_pk"
DETAIL:  Key (id)=(1) already exists.
for_test=# SELECT * FROM consumers;
ERROR:  current transaction is aborted, commands ignored until end of transaction block
for_test=# ROLLBACK TO SAVEPOINT save_point_1;
ROLLBACK
for_test=# SELECT * FROM consumers;
-[ RECORD 1 ]------
id          | 1
consumer_id | jerry
-[ RECORD 2 ]------
id          | 2
consumer_id | Tom

for_test=# COMMIT;
COMMIT
```

可以注意的是，因为 `INSERT INTO consumers(id, consumer_id) VALUES (1, 'Harry');` 的失败，导致事务无法继续，此时我们进行查询会获得 `ERROR:  current transaction is aborted, commands ignored until end of transaction block`，这时候你可以回滚到你的存档点就可以继续其他操作了，可以看到我们在 `ROLLBACK TO SAVEPOINT save_point_1;` 后，依旧可以进行 `COMMIT` 去提交事务的。

此外，PostgreSQL 的 MVCC 实现可以允许你将很多 DDL 语句放入事务中，**也就是说对表的结构进行修改、增加索引等都可以事务化**，例如下面的例子：

```sql
for_test=# BEGIN;
BEGIN
for_test=# ALTER TABLE consumers ADD created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE
for_test=# \d consumers
                    Table "public.consumers"
   Column    |           Type           |       Modifiers        
-------------+--------------------------+------------------------
 id          | bigint                   | not null
 consumer_id | text                     | 
 created_at  | timestamp with time zone | not null default now()
Indexes:
    "consumers_pk" PRIMARY KEY, btree (id)

for_test=# ROLLBACK;
ROLLBACK
for_test=# \d consumers
     Table "public.consumers"
   Column    |  Type  | Modifiers 
-------------+--------+-----------
 id          | bigint | not null
 consumer_id | text   | 
Indexes:
    "consumers_pk" PRIMARY KEY, btree (id)
```

可以清楚的看到，ROLLBACK 后，**我们新增的列就不存在了**。这个功能可以说是与其他数据库最大的区别了。

#### 隔离级别

讲事务就不能不说隔离级别，基本上在后端服务开发的领域，使用事务最多的场景就是支持并发处理，事务提供的不同隔离级别能够满足我们的业务场景，此外，还需要理解下一部分锁才算是完全清楚关系型数据库的并发处理机制。我们这里先说事务的隔离级别：Transaction Isolation。

对于 SQL 标准，默认是存在四种事务的隔离级别的，对于最严格的 `Serializable` 一般可以理解为，对于并发执行一组 `Serializable` 的事务，保证他们执行完的效果是与按照一定顺序执行的效果完全一致的，所以我们一般认为是串行的。而另外三种隔离级别是根据**并发事务不一致**的情况所描述的，而这些情况在 `Serializable` 级别下都是不可能发生的，在其它级别下，是**可能发生**的（可能发生的意思是说，如果跑了一次一组事务后，一致性没有问题，这种情况下无法判断事务之间的影响会造成一致性的问题，**但实际上这些异常现象是可能发生的**）。所以，在说隔离级别之前，需要提一下我们希望避免的不一致性的**情况**：

*   **脏读（dirty read）**：一个事务读取了另一个**正在执行的，没有提交的事务**的写入数据。
*   **不可重复读（non-repeatable read）**：一个事务重新读取前面读取过的数据时，发现该数据已经被另一个事务所修改了，**往往另一个事务的修改提交在第一次读取之后**，理解不可重复读可以直接从字面上理解，就是*重复读会出事儿！！！*。
*   **幻读（phantom read）**：一个事务重新执行了一个查询语句，返回的满足查询条件的一组数据，这时发现，这一组数据已经被另一个事务所修改（往往出现于当前事务读取一组记录，这组记录中包含了另一个事务增加或者删除的记录）。
*   **序列化异常（serialization anomaly）**：成功提交一组事务的结果与按照所有可能的顺序运行这些事务的结果，存在不一致性。

按照 SQL 标准，PostgreSQL 也实现了这些隔离级别，如下表：

| 事务隔离级别              | 脏读     | 不可重复读 | 幻读     | 序列化异常 |
|---------------------------|----------|------------|----------|------------|
| 读未提交 Read Uncommitted | 可能出现 NPG | 可能出现   | 可能出现 | 可能出现   |
| 读提交 Read Committed     | 不可能   | 可能出现   | 可能出现 | 可能出现   |
| 可重读 Repeatable Read    | 不可能   | 不可能     | 可能出现 NPG | 可能出现   |
| 序列化 Serializable    | 不可能   | 不可能     | 不可能 | 可能出现   |

这些标准的隔离级别是 PostgreSQL 支持的，你都可以在 transaction 开始时指定这些标准的隔离级别，但是，实际上 PostgreSQL 只实现了三种隔离级别，对于 `读未提交 Read Uncommitted` 来说，其行为是与 `读提交 Read Committed` 完全一致的，使用它只是为了适配 SQL 隔离级别的标准。

**注意，在上表中，带 NPG 的 cell （例如 可能出现 NPG）有极其重要的特殊含义，即：在 SQL 标准中，这些不一致的现象是可能会出现的，但是在 PostgreSQL 中不会出现。所以 PostgreSQL 中没有读未提交，并且 Repeatable Read  不会出现幻读的现象。**

#### 怎么去练习隔离级别？

很多同学对于隔离级别的理解不准确，或者不深是缺乏相应的练习，导致对这些不一致的现象并不敏感，从而在项目中忽略了可能会造成不一致问题的点从而遭受挫折，下面我们就可以试试这些隔离级别到底是怎么一回事。当然写本文的时候，我发觉我的电脑上并没有安装 PostgreSQL，刚好我们可以使用 docker，练习隔离级别时，我们需要两个不同的 session 模拟并发的情况，所以我们需要做如下的准备：

```bash
# 启动数据库服务
docker run --name some-postgres -d postgres:9.5 # 版本 11，10，9 都可以

# 连接数据库
docker exec -it some-postgres psql -U postgres

# 创建数据库
postgres=# create database for_test;
CREATE DATABASE
postgres=# \c for_test
You are now connected to database "for_test" as user "postgres".
```

为了描述方便，我们将这个 session 其称为 T1，下来我们在 TI 中创建测试数据，并对当前 session 关闭 auto commit：
```sql
CREATE SEQUENCE user_id_seq;

CREATE TABLE users (
    id BIGINT NOT NULL DEFAULT nextval('user_id_seq'),
    type VARCHAR(10) NOT NULL,
    name VARCHAR(128) NOT NULL,
    address TEXT,
    married BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id)
);

-- 搞点测试数据，这次来 20 个
INSERT INTO users (type, name, address)
SELECT 'testing', left(md5(i::text), 10), left(md5(random()::text), 50)
FROM generate_series(1, 20) s(i);

-- 在 psql client 中关闭 auto commit
\set AUTOCOMMIT off
```

##### 练习1 `读未提交 Read Uncommitted` 与 `读未提交 Read Committed`：

我们需要开启另一个 terminal，就叫它 T2 好了，然后连接 PostgreSQL 服务，并关闭 AUTOCOMMIT:
```bash
docker exec -it some-postgres psql -U postgres -d for_test
for_test=# \set AUTOCOMMIT off
```

这时候，在 T1 中开启 transaction，并使用 `Read Uncommitted` 隔离级别：
```sql
BEGIN TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
```

然后我们在 T2 中进行数据修改，注意，**这里是不进行 COMMIT 提交修改的**：
```sql
BEGIN;
UPDATE users SET name = 'from t2' WHERE id = 11;
```

这时候，T1 去进行查询操作，你会发现，数据并没有被改变，**那是因为 PostgreSQL 并没读未提交的隔离级别，也就是说，你只能读取到已经提交的数据**。

```sql
SELECT * FROM users WHERE id = 11;
 id |  type   |    name    |             address              | married |          created_at           |          updat
ed_at           
----+---------+------------+----------------------------------+---------+-------------------------------+---------------
----------------
 11 | testing | 6512bd43d9 | 29c8eaa9ceb56fda9f6838d2bbcd744a | f       | 2019-05-25 16:22:10.503297+00 | 2019-05-25 16:
22:10.503297+00
(1 row)
```

然后，你如果你在 T2 中进行提交:

```sql
COMMIT;
```

再在 T1 中重读:
```sql
SELECT * FROM users WHERE id = 11;
 id |  type   |  name   |             address              | married |          created_at           |          updated_
at           
----+---------+---------+----------------------------------+---------+-------------------------------+------------------
-------------
 11 | testing | from t2 | 29c8eaa9ceb56fda9f6838d2bbcd744a | f       | 2019-05-25 16:22:10.503297+00 | 2019-05-25 16:22:
10.503297+00
(1 row)
```

数据已经被修改了，T1 读取到了 T2 提交后的数据。这里我们稍微总结一下：

1. PostgreSQL 的读未提交与读提交等价，如果 transaction 的隔离级别设置成了这两种，都表示，只能读取到被提交的数据。
2. 可以看到 T1 中我们读取了两次数据，但是两次的结果不一致，所以对于 `SELECT * FROM users WHERE id = 11; ` 存在不可重读的情况。
3. PostgreSQL 默认的隔离级别是 `读提交 Read Committed`，不是比较严格的 `Repeatable Read`。

所以为了加深印象，我们可以进行这种额外的练习：
1. 幻读：T1 中使用 `Read Committed` 开启事务，T2 中开启另一个事务，并执行 INSERT，然后 T1 进行 `SELECT * FROM users; `全表搜索，观察是否有 T2 插入的数据，然后 T2 COMMIT，T1 重复执行，观察是否有 T2 插入的数据。
2. 真正的 `读未提交`：既然有了 docker，使用 MySQL 镜像重复之前的练习，可以使用 innoDB 作为数据库引擎，观察在 MySQL 在读未提交的情况下的结果。例如这样启动 MySQL: 

```bash
docker run --name some-mysql -p 3306:3306  -e MYSQL_ROOT_PASSWORD=99887766 -d mysql
```

##### 练习2 `可重读 Repeatable Read`：

在 T1 中开启 transaction，并使用 `Repeatable Read` 隔离级别：
```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

然后我们在 T2 中进行数据修改，注意，**这里是不进行 COMMIT 提交修改的**：
```sql
BEGIN;
UPDATE users SET name = 'from t2 RR' WHERE id = 11;
```

这时候，T1 去进行查询操作，数据并没有被改变（依旧 name 值是上次 `from t2`），**那是因为 `可重读 Repeatable Read` 不会发生脏读**。

```sql
SELECT * FROM users WHERE id = 11;
 id |  type   |  name   |             address              | married |          created_at           |          updated_
at           
----+---------+---------+----------------------------------+---------+-------------------------------+------------------
-------------
 11 | testing | from t2 | 29c8eaa9ceb56fda9f6838d2bbcd744a | f       | 2019-05-25 16:22:10.503297+00 | 2019-05-25 16:22:
10.503297+00
(1 row)
```

然后 T2 提交:

```sql
COMMIT;
```

T1 再进行查询：
```sql
SELECT * FROM users WHERE id = 11;
 id |  type   |  name   |             address              | married |          created_at           |          updated_
at           
----+---------+---------+----------------------------------+---------+-------------------------------+------------------
-------------
 11 | testing | from t2 | 29c8eaa9ceb56fda9f6838d2bbcd744a | f       | 2019-05-25 16:22:10.503297+00 | 2019-05-25 16:22:
10.503297+00
(1 row)
```

可以发现本质性的区别，**name 的值依旧是 from t2**，因为`可重读 Repeatable Read` 确保了两次读取的值的一致性。同时，我们知道，**PostgreSQL 中 `可重读 Repeatable Read` 其实并不会出现幻读现象**，如果你在 T2 中进行 INSERT 并 COMMIT，T1 中还是之前的结果（21 条数据，但是 T2 中已经有 22 条了）。

照例，我们可以额外练习下：
1. 幻读：完成之前提到的幻读的实验，理解在 PostgreSQL 的 `Repeatable Read` 中不会出现幻读的现象。
2. 重复幻读：在 MySQL 中使用 `Repeatable Read` 重复幻读实验，对照结果。
3. 思考：不可重复读、幻读这两种不一致的现象会对我们的应用产生什么影响？我们应该怎么合理的使用隔离级别有什么意义？

#### 万事大吉？

假设我们有这样一段业务逻辑，当用户在网站上进行购买时，我们需要对用户的账户进行扣款，因为我们是不允许用户白吃白喝的。所以，我们的业务逻辑大约是，先读取用户有多少钱，然后再扣去用户购买产品的价格，如果用户账户的钱不够的话，就返回错误不进行任何修改，我们写的代码大约这个样子的：

1. 打开一个 transaction，准备进行结算操作。
2. 读取目标用户的账户中有多少钱，并且存放在代码的变量中。
3. 检查总共的钱数与购买产品的价格，如果合理进行扣款，并进行提交，事务结束。
4. 如果购买的钱数大约账户数，就不进行扣款，直接报错给用户，事务结束。

从我们之前学习到的知识来说，我们肯定希望读取的钱数是已经提交成功的，所以应该使用 `Read Committed` 隔离级别，这样，如果同时用户对账户进行了两次扣款，我们只能读取到已经提交后的账户余额，感觉上是没错的。**但是很遗憾的是，不论是 `Read Committed` 或者 `Repeatable Read` 都无法解决另一个问题，也就是当我们的 transaction 完成第二歩并读取到了最新的余额例如 50￥，这时候，另一个 transaction 对余额进行了修改，将其改为了 30￥，这时候我们的 transcation 进行第三步扣款 40￥的操作就会出现问题，导致余额变成了 -10￥。**这时候我们就知道，单单使用事务与其隔离级别是完全不够的，**我们需要一种机制在第二歩和第三步之间锁定记录，只允许我们进行修改，**那么这就是下面我们要讲的 PostgreSQL 中的锁。

### 锁

#### 表锁与行锁

如同其他关系型数据库一样，PostgreSQL 也有行锁和表锁之分，顾名思义，他们面向的操作对象是不同的。但是这些锁并不是按照我们的想法是“锁定某些对象”，而更贴近描述对数据库进行 CRUD 时状态的记录，并根据这些状态来决定操作。简单来说，当需要增删改查时，我们先要获得表上的锁，然后再获得行锁，然后才能进行操作。

以下是 PostgreSQL 的表级锁：
 - ACCESS SHARE
只与 ACCESS EXCLUSIVE 冲突
SELECT 命令将会在引用的表上加上该锁，通常任何读取并不修改的查询都会要求这种表锁，**所以 SELECT 并发是没有冲突的，因为 ACCESS SHARE 和 ACCESS SHARE 并不冲突**。

- ROW SHARE
与 `EXCLUSIVE` 与 `ACCESS EXCLUSIVE` 这两种锁冲突
只有 `SELECT FOR UPDATE` 与 `SELECT FOR SHARE` 这两个命令会要求这样的表锁，**我们常常用来锁定一些需要被修改的数据。**

- ROW EXCLUSIVE
与 `SHARE` `SHARE ROW EXCLUSIVE` `EXCLUSIVE` `ACCESS EXCLUSIVE` 锁冲突。
`UPDATE` `DELETE` `INSERT` 这些命令会请求这样的表锁，如果这些命令 `SELECT` 了其他表的资源，同样还会产生 `ACCESS SHARE` 的锁。**简单来说，任何修改数据的请求都会申请这个表锁**。

- SHARE UPDATE EXCLUSIVE
与 `SHARE UPDATE EXCLUSIVE`, `SHARE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE` 和 `ACCESS EXCLUSIVE` 这些表锁冲突，这个锁防止了并发的表结构更改与 VACUUM 运行。
命令 `VACUUM (without FULL)`, `ANALYZE`, `CREATE INDEX CONCURRENTLY` `ALTER TABLE VALIDATE` 或者其他 `ALTER TABLES` 会申请这个锁。

- SHARE
与 `ROW EXCLUSIVE`, `SHARE UPDATE EXCLUSIVE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE`, `ACCESS EXCLUSIVE` 锁模式冲突，这个锁防止并发的数据改动。
只有非并发式创建索引会请求这个表（也就是 `CREATE INDEX`），**所以有了这个锁修改数据是不行的，但是可以访问数据，`ACCESS SHARE` 是不冲突的。**

- SHARE ROW EXCLUSIVE
与 `ROW EXCLUSIVE`, `SHARE UPDATE EXCLUSIVE`, `SHARE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE`, `ACCESS EXCLUSIVE` 冲突，这个锁保护表不会受到数据修改，并且这个锁与自己排他，表示只有一个 session 能够持有这个锁。
`CREATE TRIGGER` 与 `ALTER TABLE` 会请求这个锁，**全世界只有一个这个锁**。

- EXCLUSIVE
与 `ROW SHARE`, `ROW EXCLUSIVE`, `SHARE UPDATE EXCLUSIVE`, `SHARE`, `SHARE ROW EXCLUSIVE`, `EXCLUSIVE`, 以及 `ACCESS EXCLUSIVE` 锁模式冲突。
只有 `REFRESH MATERIALIZED VIEW CONCURRENTLY` 会请求这个锁，不是很重要。

- ACCESS EXCLUSIVE
与所有锁模式冲突，这个锁模式保证只有一个 transaction 可以访问被锁的数据表。
`DROP TABLE`, `TRUNCATE`, `REINDEX`, `CLUSTER`, `VACUUM FULL`, `REFRESH MATERIALIZED VIEW (without CONCURRENTLY)` 都会请求这个锁，**所以 `VACUUM FULL` 是非常危险的，就像 major GC 一样，会 block 到所有的操作**。某些 `ALTER TABLE` 也会请求这个锁， 这也是 `LOCK TABLE` 语句的默认锁级别。

PostgreSQL 和其他关系型数据库一样，都花了一个表格来描述锁之间的冲突，但是有这么多锁难以记下来并且理解，首先需要明确的是，这些锁都是**表锁**，一开始只有 SHARE 和 EXCLUSIVE 锁，SHARE 锁表示不能修改数据，则与所有的 EXCLUSIVE 锁冲突，而 EXCLUSIVE 锁则具有排他性，与所有的 SHARE 锁冲突，但是如果只有这两个锁性能也太差了，特别是并发的情况下，我们经常对数据表又读又写，使用这两个锁是没有效率的。于是我们就引入了 ACCESS SHARE 锁，表示可以在查询时允许对表内的数据修改，这就是说你在一个 SESSION 中 SELECT 并不影响另一个 SESSION 对其进行 INSERT 或者 UPDATE。ACCESS SHARE 的描述范围太大了，有时候我们只需要操作几行数据进行更新，**所以我们引入了 ROW SHARE 和 ROW EXCLUSIVE 这两种锁，他们都是表级锁，但他们并不互相冲突**，他们只是表示会进一步的使用行锁来控制并发，可以说这两个锁是最重要的锁。

ROW EXCLUSIVE 通过 UPDATE、INSERT、DELETE 命令生成，所以必须是排他的，但是在表中我们并不知道 UPDATE 的数据范围，因为同时 UPDATE 两行不同的数据是被允许的，所以 ROW EXCLUSIVE 一定不能和自己冲突。ROW SHARE 也是一样的，我们通过其“锁定”某一些数据，而并不是全表，所以它与它自己也是不冲突的。**既然这两个锁都无法互相冲突，那么我们还需要另外一种机制来控制并发，也就是行锁。**对于 PostgreSQL 来说，也存在行级的读锁与写锁，因为读锁没有排他性，所以控制并发的责任实际上是行锁决定的。

对于一个 UPDATE 语句，它先会要求在表上的 ROW EXCLUSIVE 锁，如果获取到了，它就会继续要求所修改数据的行锁，这时候行锁如果被另一个语句所获取，那它就必须等待，直到锁被释放。我们可以根据下面的实验重现这个场景：

打开第一个 ternimal，称为 T1：
```sql
\set AUTOCOMMIT off

BEGIN;

-- 获得进程号
SELECT pg_backend_pid();
 pg_backend_pid 
----------------
            920
(1 row)

-- 进行修改不提交
UPDATE users SET name = 'from t1 updating' WHERE id = 11;

-- 查看表锁
SELECT locktype,
       relation::regclass as relation,
       transactionid,
       MODE,
       GRANTED
FROM pg_locks
WHERE pid = 920;

   locktype    |  relation  | transactionid |       mode       | granted 
---------------+------------+---------------+------------------+---------
 relation      | pg_locks   |               | AccessShareLock  | t
 relation      | users_pkey |               | RowExclusiveLock | t
 relation      | users      |               | RowExclusiveLock | t
 virtualxid    |            |               | ExclusiveLock    | t
 transactionid |            |           636 | ExclusiveLock    | t
(5 rows)
```

可以看到在第三行， "relation      | users      |               | RowExclusiveLock | t" 表示，我们已经在表上获取了 RowExclusiveLock。

这时候我们打开 T2：
```sql
BEGIN;

SELECT pg_backend_pid();
 pg_backend_pid 
----------------
            276
(1 row)

-- 进行更新
UPDATE users SET name = 'from t2 updating' WHERE id = 11;
-- 注意，此时这句话会被卡主，因为我们在尝试更新同一条数据
```

然后我们回到 T1，再查看下 T2 的锁：
```sql
SELECT locktype,
       relation::regclass as relation,
       transactionid,
       MODE,
       GRANTED
FROM pg_locks
WHERE pid = 276;
   locktype    |  relation  | transactionid |       mode       | granted 
---------------+------------+---------------+------------------+---------
 relation      | users_pkey |               | RowExclusiveLock | t
 relation      | users      |               | RowExclusiveLock | t
 virtualxid    |            |               | ExclusiveLock    | t
 transactionid |            |           636 | ShareLock        | f
 transactionid |            |           637 | ExclusiveLock    | t
 tuple         | users      |               | ExclusiveLock    | t
(6 rows)
```

第二条数据 " relation      | users      |               | RowExclusiveLock | t" 表示，进程 276 也就是 T2 同样获得了 RowExclusiveLock，因为我们之前说过，RowExclusiveLock 这个表锁是不会相互冲突的，所以是被 granted 的，但是为什么 T2 还被卡主了呢？**这就是之前提到过的行级的写锁所产生的排他效果，T2 必须等待 T1 完成并释放，然后才能完成结果。如果你这时候再 T1 进行 COMMIT，你就可以看到 T2 的 UPDATE 返回结果 UPDATE 1 了。**

PostgreSQL 不会在内存中记录行锁，因为行锁的开销实在是太大了，如果每一条记录的行锁都被记录，我们的共享内存是不够的。这时候你可以观察上表中的 `transactionid` 发现，637 也就是 T2 的事务是被 T1 中的 636 所互斥的，通过这一点我们就可以 debug 死锁的问题了。

#### 悲观锁与乐观锁

对于 PostgreSQL 的锁模式我们已经学习过了，但是遗憾的是这对于我们在之前提到过的扣款付费的业务场景是无效的，因为我们实际上是需要两个操作的配合才能完成业务，**根本的需求便是在获取存款后，我们不希望任何人改变存款，只能由我们进行扣款。**经过修改，我们的业务大约是这个样子：

1. 打开一个 transaction，准备进行结算操作。
2. 读取目标用户的账户中有多少钱，并锁定，并且存放在代码的变量中。
3. 检查总共的钱数与购买产品的价格，如果合理进行扣款，解除锁定，事务结束。
4. 如果购买的钱数大约账户数，就不进行扣款，解除锁定，事务结束。

一般来说，这种 OCC 问题在冲突可能性不大的情况下，我们会使用乐观锁，往往乐观锁并不是一个真正的锁，它并不记录互斥关系，所以乐观锁的实现往往是在应用程序中实现的，我们在这里就不赘述了，可以[参考 JPA 的实践](https://www.baeldung.com/jpa-optimistic-locking)来进行理解，这方面的文章也特别多，就不写了。

但是对于悲观锁，往往是在数据库层面实现的，在 PostgreSQL 中我们就可以使用 ROW SHARE 这个表锁以及行锁来达到目的，例如：

```sql
SELECT name FROM users WHERE id = 11 FOR UPDATE;
-[ RECORD 1 ]----------
name | from t2 updating

SELECT locktype,                             
       relation,
       transactionid,
       MODE,
       GRANTED
FROM pg_locks
WHERE pid = 992;
-[ RECORD 3 ]-+----------------
locktype      | relation
relation      | 16387
transactionid | 
mode          | RowShareLock
granted       | t
```

这时候，RowShareLock 和行锁已经被加到 id = 11 的行中了，任何人都无法修改（你可以开启另一个 session 尝试修改，并查看下锁的情况），然后我们就可以进行余额计算等更新事务了。所以在我们第一节提到的“万事大吉？”的问题上，我们已经解决了这个并发问题。悲观锁认为修改发生冲突的可能性很大，所以真是在加互斥的锁来解决这个问题，显而易见的是这样效率会比较低，因为如果请求过多那么大家可能都在等待锁。因为这一部分网上已经有很多文章在描述与分析了，我们就不啰嗦了，可以参考下面：
- [https://stackoverflow.com/questions/129329/optimistic-vs-pessimistic-locking](https://stackoverflow.com/questions/129329/optimistic-vs-pessimistic-locking)
- [https://www.obsidianscheduler.com/blog/when-to-use-pessimistic-locking/](https://www.obsidianscheduler.com/blog/when-to-use-pessimistic-locking/)
- [https://www.hollischuang.com/archives/934](https://www.hollischuang.com/archives/934)

所以总结一下，不论是悲观锁还是乐观锁，都可以帮助我们解决一致性的问题，但是具体使用哪一种以及如何实现，还需要按照自己的数据库、应用、事务控制等综合考虑。**数据库优化是一项复杂的事情，性能、一致性、查询方式等都是需要深思熟虑的，在这一层面请不要迷信任何简单的解决方案，熟悉自己的应用程序所做的事情，再进行调整优化才是有意义的，三张表的 JOIN 未必会慢，乐观锁的性能未必会好，base on fact and know your application first。**


