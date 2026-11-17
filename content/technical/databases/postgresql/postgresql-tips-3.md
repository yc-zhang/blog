### 什么是执行计划

对于每个收到的查询请求，PostgreSQL 都会为其上设置执行计划（查询计划），能够正确的通过查询语句结构与数据结构进行查询计划的设定会显著提升系统性能，对于我们来说，经常会通过查询计划来找出慢查询的原因，可以说是最重要的性能工具了。当然，执行计划的分析与优化是很难的，所以本篇尝试覆盖一些基础的点。

一般来说，使用 `EXPLAIN` 可以显示查询计划了，当然你也可以使用一些 option 对其进行改变，例如常见的 `ANALYZE` `COSTS` 等等。**最常用的可能是 `ANALYZE` 了，因为其实通过实际执行的 SQL 并且获取真正的执行计划，所以你可以看到具体的时间花费以及返回行数**，如果 INSERT 或者 DELETE 了数据，那就会修改数据库。所以你可以使用 `BEGIN` 将 `EXPLAIN ANALYZE` 包入一个事务，执行完后回滚。如果你不使用 `ANALYZE` PostgreSQL 会根据一些随机的样本，已有的性能数据，或者估计等手段去推测 cost，所以是不精确的，但是足够分析性能，特别是慢查询可能会等待很久，使用 `ANALYZE` 会很没有效率。

其实[官方文档](https://www.postgresql.org/docs/9.4/using-explain.html)是最好的解释，对其他 options 或者想深入学习的，还是请参考。

### 输出结果的解释

我们先来实际试试 `EXPLAIN`：

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

# 准备十万条测试数据

INSERT INTO users (type, name, address)
SELECT 'testing', left(md5(i::text), 10), left(md5(random()::text), 50)
FROM generate_series(1, 100000) s(i);
```

所以我们进行 `EXPLAIN` 的结果如下：

```sql
EXPLAIN select * from users;
                          QUERY PLAN                          
--------------------------------------------------------------
 Seq Scan on users  (cost=0.00..1600.80 rows=26680 width=369)
(1 row)
```

- `Seq Scan` 表示我们常说的全表扫描，从头到尾的顺序扫描。
- `cost=0.00..1600.80` 表示花费，`0.00` 表示获取第一行需要多少 cost, `1600.80` 则表示全部返回需要多少 cost。
- `rows` 表示返回多少行
- `width` 表示平均每行多少字节（*你可以用 rows 和 width 来估算数据大小*）

在讲 cost 之前，我们发现 rows 的数据并不正确，这张表里有 100,000 条数据，怎么查询计划里面只有 26,680 条？还记得我们之前提到的 `EXPLAIN` 会根据很多性能数据**推测**，因为这张表刚刚建立，数据不充分所导致结果偏差很大。你可以做一个 `SELECT COUNT(*)` 后再试试刚才的 `EXPLAIN` 语句，结果会有很大的不同。

**`cost` 并不与我们的实际执行时间挂钩，只是 PostgreSQL 用来描述执行成本的单位，这个东西不能和任何时间单位进行换算**，PSQL 是这样定义的，例如 `seq_page_cost 顺序的扫描一页` 的代价就是 1.0, 处理一行数据的代价是 0.01，当然这些常量你也可以自己修改，其他的表示可以参考[官方文档](https://www.postgresql.org/docs/9.4/runtime-config-query.html#RUNTIME-CONFIG-QUERY-CONSTANTS)，一般情况下，你不需要特别了解 cost 到底是什么，它只要使你能进行性能分析就足够了。

下来我们看看使用了 `ANALYZE` 后的效果：
```sql
EXPLAIN ANALYZE select * from users;
                                                  QUERY PLAN
-----------------------------------------------------------------
 Seq Scan on users  (cost=0.00..2334.00 rows=100000 width=77) (actual time=0.013..631.094 rows=100000
 loops=1)
 Planning time: 0.068 ms
 Execution time: 1249.210 ms
(3 rows)
```

结果中有了具体的查询时间以及返回数据的总时间，你也可以使用 `buffers` 去查看缓存命中的情况：

```sql
EXPLAIN (ANALYZE true, BUFFERS true) select * from users;
                                                  QUERY PLAN                                         
-----------------------------------------------------------------
 Seq Scan on users  (cost=0.00..2334.00 rows=100000 width=77) (actual time=0.020..634.054 rows=100000
 loops=1)
   Buffers: shared hit=1334
 Planning time: 0.223 ms
 Execution time: 1254.985 ms
(4 rows)
```

可以看到命中 1334 个 block，特别是你做了数据表的 prewarm 后，查看缓存的命中也是很有必要的，以此可以来来评估 `pg_prewarm` 的效果。

### 扫描

PostgreSQL 的扫描有三种，顺序扫描 `seq scan`，索引扫描 `index scan` 与位图扫描 `bitmap scan`，顺序扫描也称为全表扫描，是把表的所有数据块从头到尾扫一遍，然后获取符合条件的数据，而索引扫描是在索引中找出需要的数据的位置，然后再去将数据取出的过程，以下有两个例子：

```sql
EXPLAIN select * from users;
                          QUERY PLAN                          
--------------------------------------------------------------
 Seq Scan on users  (cost=0.00..2334.00 rows=100000 width=77)
(1 row)

EXPLAIN select * from users where id = 9999;
                               QUERY PLAN                                
-------------------------------------------------------------------------
 Index Scan using users_pkey on users  (cost=0.29..8.31 rows=1 width=77)
   Index Cond: (id = 9999)
(2 rows)
```

第一个查询将会扫描表中的 100,000 条数据，由于我们没有 where 子句，所以这个查询计划只有 seq scan，而第二个查询直接在索引中进行搜索（**还记得第二篇中的 B-Tree Index 吗？对它进行搜索的过程就是 Index Scan**）。

而位图扫描 `bitmap scan` 也是一种走索引扫描的方式，原理是进行索引扫描，把满足条件的行的指针 `tuple-pointer` 立刻取出，存放在内存中的位图里，当扫描结束后，再对位图中的 `tuple-pointer` 去读取实际数据块中的数据。这种查询方式常常用于非等值查询的情况下，而且如果走了两个索引，可以将两个索引的位图进行 `and` 与 `or` 的计算，合并成新的位图，再根据其位置取出实际数据，**这个过程中每个数据块只在扫描中被读取了一次**。比如说，我们对某个索引进行一个条件查询：

```sql
# 手动关闭这两个 scan，强制使用 bitmap scan
SET enable_indexscan = off;
SET enable_seqscan = off;

# 建立索引

CREATE INDEX users_name ON users (name);

# 进行查询
EXPLAIN SELECT * FROM users WHERE name IN ('a', 'b', 'c');

                                QUERY PLAN                                
--------------------------------------------------------------------------
 Bitmap Heap Scan on users  (cost=13.28..24.89 rows=3 width=77)
   Recheck Cond: ((name)::text = ANY ('{a,b,c}'::text[]))
   ->  Bitmap Index Scan on users_name  (cost=0.00..13.28 rows=3 width=0)
         Index Cond: ((name)::text = ANY ('{a,b,c}'::text[]))
(4 rows)
```

Recheck 的原因是由于 MVCC，我们还需要将数据读出后，再检查一下条件。

```sql
EXPLAIN SELECT * FROM users WHERE name IN ('a', 'b', 'c') OR name IN ('p', 'b', 'k');
                                
                                QUERY PLAN          
--------------------------------------------------------------------------
 Bitmap Heap Scan on users  (cost=26.56..49.45 rows=6 width=77)
   Recheck Cond: (((name)::text = ANY ('{a,b,c}'::text[])) OR ((name)::text = ANY ('{p,b,k}'::text[])
))
   ->  BitmapOr  (cost=26.56..26.56 rows=6 width=0)
         ->  Bitmap Index Scan on users_name  (cost=0.00..13.28 rows=3 width=0)
               Index Cond: ((name)::text = ANY ('{a,b,c}'::text[]))
         ->  Bitmap Index Scan on users_name  (cost=0.00..13.28 rows=3 width=0)
               Index Cond: ((name)::text = ANY ('{p,b,k}'::text[]))
(7 rows)
```

这是一个 bitmap scan OR 的例子，我们使用 OR 将两个 bitmap 合并，再最后进行数据读取。

### 条件、排序等

对于条件，排序，limit 等操作，也有相应的查询计划，比起 scan 来容易理解，比如下面这个查询计划：

```sql
EXPLAIN SELECT * FROM users WHERE id > 100 ORDER BY created_at DESC LIMIT 10;

                               QUERY PLAN                                
-------------------------------------------------------------------------
 Limit  (cost=4742.89..4742.91 rows=10 width=77)
   ->  Sort  (cost=4742.89..4992.65 rows=99904 width=77)
         Sort Key: created_at
         ->  Seq Scan on users  (cost=0.00..2584.00 rows=99904 width=77)
               Filter: (id > 100)
(5 rows)
```

`limit` `sort` `filter` 都在计划中，可以看到排序是非常贵的操作（cost=4742.89..4992.65），合理的使用排序可以显著提高性能。

### Join

PostgreSQL 有三种 JOIN 的方式 `nestloop join` `hash join` `merge join`，PostgreSQL 会根据数据量的大小与性能的统计数据等选择合适的方式。

`nestloop join` 也叫嵌套循环，顾名思义，就是使用嵌套循环的方式，先在外表获取数据，再去内表寻找进行匹配。所以这种方式并不适合数据量比较大的情况，例如行数上万的情况。显而易见复杂度是 O(M*N)，M 和 N 是需要 join 的数据量，但是即使看起来 `nestloop join` 不是很高效，但是这种方式是可以计算任何的多表联查情况的，你可以认为这是一个最基本的功能。

但是如果 inner 表中用于 join 的字段存在索引，那么 `nestloop join` 的效率就会稍微好一点，我们知道 B-Tree 的查询复杂度是 log(N)，所以在 index scan 中 `O(M*log(N))` 是优于 `nestloop join` 的 `O(M*N)` 的。

以下是一个 nestloop JOIN 的实例，并且带有 Index Scan，可以看到在对 `users` 进行全表扫描后，对每一条数据进行 JOIN 去查询 users_2 表是否存在满足条件的数据，即使用 `Index Cond`。

```sql
# 强制走 nestloop 
SET enable_nestloop = ON;
SET enable_hashjoin = OFF;
SET enable_mergejoin = OFF;

EXPLAIN SELECT * FROM users JOIN users_2 ON users.id = users_2.id;

                                    QUERY PLAN                                     
-----------------------------------------------------------------------------------
 Nested Loop  (cost=0.42..79748.00 rows=100000 width=154)
   ->  Seq Scan on users  (cost=0.00..2334.00 rows=100000 width=77)
   ->  Index Scan using users_2_pkey on users_2  (cost=0.42..0.76 rows=1 width=77)
         Index Cond: (id = users.id)
```

`hash join` 比 `nestloop` 先进了一些，**一般来说 PostgreSQL 查询优化器会使用两个表中较小的表**，将其放入内存建立一个散列表，然后再扫描大表并查询内存中的散列表，然后找出数据。这种情况很适合 JOIN 时小的表完全放入内存之中，但是如果小的数据表无法全部放入内存中，PostgreSQL 会将其分区并将无法放入内存的部分写入临时段，那就自然需要消耗大量的 I/O 成本。

```sql
# 走 hash join
SET enable_nestloop = OFF;
SET enable_hashjoin = ON;
SET enable_mergejoin = OFF;

EXPLAIN SELECT * FROM users JOIN users_2 ON users.id = users_2.id;

                                QUERY PLAN                                
--------------------------------------------------------------------------
 Hash Join  (cost=4854.00..36487.00 rows=100000 width=154)
   Hash Cond: (users_2.id = users.id)
   ->  Seq Scan on users_2  (cost=0.00..11667.00 rows=500000 width=77)
   ->  Hash  (cost=2334.00..2334.00 rows=100000 width=77)
         ->  Seq Scan on users  (cost=0.00..2334.00 rows=100000 width=77)
```
这个查询计划就非常清楚了，先对表 users 进行了 seq scan 然后将其结果放入内存中的 hash，因为表 users 只有100,000 条数据，是一个小表，再对 users_2 表进行 seq scan，然后去 hash 中进去 hash join，**所以它的结果的总 cost 是小于 nestloop 的，即：36487.00 < 79748.00，但是启动时间（第一条数据返回的时间）却大于 nestloop 即 4854.00 > 0.42，因为需要建立 hash table**。

一般来说 `hash join` 的效果是好于 `merge join` 的，但是如果需要 JOIN 的字段上有索引，或者已经被进行过排序（例如说 JOIN 一个结果表），那么久不需要为其建立 hash 了，这时候 `merge join` 的性能会好于 `hash join`。所以在我们上面的例子中，如果打开全部的 JOIN 选项，PostgreSQL 会默认的去走更高效的 `merge join`。

```sql
# 打开所有的 JOIN 开关
SET enable_nestloop = ON;
SET enable_hashjoin = ON;
SET enable_mergejoin = ON;
EXPLAIN SELECT * FROM users JOIN users_2 ON users.id = users_2.id;

                                         QUERY PLAN                                         
--------------------------------------------------------------------------------------------
 Merge Join  (cost=1.60..9351.82 rows=100000 width=154)
   Merge Cond: (users.id = users_2.id)
   ->  Index Scan using users_pkey on users  (cost=0.29..3941.29 rows=100000 width=77)
   ->  Index Scan using users_2_pkey on users_2  (cost=0.42..19666.42 rows=500000 width=77)
```
因为索引已经是排好序的，所以两个 Index Scan 直接扫描了索引，可以看到预计的 cost 是三种情况中最好的。

### 关于性能优化

我们在之前的例子中，使用了类似 `enable_mergejoin` 的参数来控制 PostgreSQL 强制执行不同的查询计划，那是因为如果不这样做，PostgreSQL 的优化器会选择最优的情况进行执行，例如 JOIN 的例子中往往会走 merge join。

在通常情况下，PostgreSQL 都不会走错查询计划，有时候走错往往发生在刚刚启动数据库服务或者使用一张新表的时候，因为那时候还没有足够多的统计信息来帮助优化器进行决策。所以，**在项目中，如果没有特殊情况，不需要手动的使用这种 `enable_mergejoin` 参数来强制执行计划。**

另外，PostgreSQL 可以使用 `analyze` 命令来收集统计表的信息，这些统计信息会帮助优化器选择合适的执行计划。但是一般来说，PostgreSQL 默认会运行一个 `autovacuum` 的进程进行 vacuum 操作，并自动的分析所有表，有时候我们也会关闭这个进程，周期性的、手动的进行 vacuum 与 analyze （比如在半夜）。**但是，如果没有特殊的情况，我倾向于使用 `autovacuum` 避免手动 analyze 时容易犯的人为错误。**如果你想进一步学习，可以参考[官方文档](https://www.postgresql.org/docs/9.5/sql-vacuum.html)，我们也会在下来的更新中具体说说 VACUUM。

我们面对慢查询第一件事就是分析执行计划，例如常常做的套路就是将 Seq Scan 变为 Index Scan，或者取消掉 Nestloop 这种。一般情况下，如果查询语句已经无法改变，通过执行计划获取到具体的执行路径与成本，再进行针对性的优化。



