### 几个系统字段的介绍

在面试中，我们经常会遇到这样一个问题：
> 如果你的表中有十万条数据，当你做了一次查询后，开始依次读取数据，当你读取到第 1000 行时，这时候，有人使用 UPDATE 语句修改了 1001 行数据，请问如果继续读到 1001 行数据时，你会读取到最新的数据吗？为什么？

这个问题粗看起来和我们之前提到的隔离级别有点关系，仔细一想好像不是，因为这次修改是发生在读取中，这个场景在日常开发中很常见，在 JDBC 中你遍历 ResultSet 或者 ADO 与 ODBC 中你移动 cursor，总之，在你读取数据的时候，数据发生了改变，这在并发环境下是很常见的。当然了，大多数人的答案是不会读取到的，**但是这是 MVCC （Multiversion Concurrency Control，多版本并发控制）的策略与实现后所产生的结果，简单来说，每个事务读到的数据项都是一个历史快照（snapshot）**，但是要解释为什么，就需要继续学习了（我们将讨论控制在 PostgreSQL 中，其他 RDBMS 的行为在此就不分析与讨论了）。

在 PostgreSQL 中每个表都存在一些隐藏的系统字段，因此你是不能使用这些隐藏字段的名字作为列名的，在 psql 中，我们使用 \d 命令也不会打印出这些字段，但是这并不表示他们不存在，对于我们这些普通的数据库使用者来说，我们只需要知道他们存在就足够了，但是如果你想了解 PostgreSQL 更深一些，你还是需要稍微学习一下。这里，我们只介绍四个字段，这四个字段可以帮助我们理解 PostgreSQL 的 MVCC 是如何工作的，让我们能够更好的回答刚开始提到的那个问题：

- xmin: 插入此当前行版本（row version）的事务 Id，**注意，row version 与 row 是不同的两个东西，而且 UPDATE 会创建一个新行并带着新的版本号，所以 xmin 实际上是 INSERT 和 UPDATE 此行的事务 Id**。
- xmax: 删除这行的事务 Id，对于没有删除的行版本（row version）这个值为 0，如果在事务中查询到这个值不为 0 就表示删除的事务还没提交，或者尝试删除的操作被回滚了。
- cmin: 事务内部插入、更新操作的命令 ID。
- cmax: 事务中删除操作的命令 ID，或者 0。

查看这四个字段也很简单，直接查询就可以了，可以看到创建这条记录的事务 ID。

```sql
select xmin,xmax,cmin,cmax, name from users where id = 10;
 xmin | xmax | cmin | cmax |    name    
------+------+------+------+------------
  627 |    0 |    0 |    0 | d3d9446802
(1 row)
```

关于更多的系统字段，可以参阅 [DDL System Columns](https://www.postgresql.org/docs/9.5/ddl-system-columns.html)。

### 怎么用这四个字段？

在我们开始 MVCC 之前，先学习一下这四个字段的用法，对于 PostgreSQL 来说存在一个行版本 （row version）的说法，这个行版本的叫法不准确，这个词表示这样的情况：对于一行记录 row，存在多个版本 version，而这几个字段自然是会随着版本的不同而被改变的，他们的改变规则如下：

- 当新增一条数据时，新的行中的 xmin 就是当前事务的 ID，xmax 是 0。
- 当更新一条数据时，实际上是新增了一条新的记录，旧行上 xmin 不变，但是 xmax 是当前事务 ID （因为标记被删除了），然后新的行中的 xmin 就是当前事务的 ID，xmax 是 0（这时候当前行就有两个版本了）。
- 删除一行时，被删除的行 xmax 是当前事务 ID。

所以总结一下，不论你是什么 SQL 命令引起的行变化，如果是创建了新行，xmin 是当前事务 ID，如果是删除了旧行，xmax 就是删除的事务的 ID，这里特别要注意的是，UPDATE 命令会更新数据，但是实际上是新增了数据。而行的版本，就有点像 git，你是可以看到旧的历史记录，但是一般来说我们关心最新的（只有旧的事务，才关心旧的）。

为了验证之前我们提到的规则，我们还是开启两个 terminal，在 T1 中，我们进行如下操作：

```sql
for_test=# BEGIN;
BEGIN
for_test=# select txid_current();
 txid_current 
--------------
          640
(1 row)

for_test=# update users set name = 'updated' where id = 10;
UPDATE 1
for_test=# select xmin,xmax,cmin,cmax, name from users where id = 10;
 xmin | xmax | cmin | cmax |  name   
------+------+------+------+---------
  640 |    0 |    0 |    0 | updated
(1 row)
```
可以看到，T1 在没有 commit 前，新列的 xmin 已经是 T1 的 ID 640 了，这时候，如果你在 T2 进行查询，你应该会看到:

```sql
for_test=# select xmin,xmax,cmin,cmax, name from users where id = 10;
 xmin | xmax | cmin | cmax |  name   
------+------+------+------+---------
  627 |  640 |    0 |    0 | d3d9446802
(1 row)
```

**xmax 不为 0 时表示这一行已经被删除了，但是还没有提交**，这时候，如果 T1 进行 COMMIT，T2 再进行查询，结果便是：

```sql
for_test=# select xmin,xmax,cmin,cmax, name from users where id = 10;
 xmin | xmax | cmin | cmax |  name   
------+------+------+------+---------
  640 |    0 |    0 |    0 | updated
```

可以看到 xmin 是 T1 的事务 ID 640，xmax 已经是 0 了。**这里留一个思考，如果 T2 中执行的这两句命令在一个事务中，结果会是一样的吗？为什么？**

对于 cmin 和 cmax 是为了解决一个事务中命令的顺序问题的，作用没有 xmax 与 xmin 大。在一个事务中，命令的 ID 是会自增的，请允许我借用这个例子：

```sql
pgsql=# begin;
BEGIN
pgsql=# select * from tab01;
 id | cd
----+----
(0 rows)

pgsql=# select xmin,xmax,cmin,cmax,* from tab01;
 xmin | xmax | cmin | cmax | id | cd
------+------+------+------+----+----
(0 rows)

pgsql=# insert into tab01 values(1,'1'),(2,'2'),(3,'3');
INSERT 0 3
pgsql=# insert into tab01 values(4,'4'),(5,'5'),(6,'6');
INSERT 0 3
pgsql=# select xmin,xmax,cmin,cmax,* from tab01;
 xmin | xmax | cmin | cmax | id | cd
------+------+------+------+----+----
 1897 |    0 |    0 |    0 |  1 | 1
 1897 |    0 |    0 |    0 |  2 | 2
 1897 |    0 |    0 |    0 |  3 | 3
 1897 |    0 |    1 |    1 |  4 | 4
 1897 |    0 |    1 |    1 |  5 | 5
 1897 |    0 |    1 |    1 |  6 | 6
(6 rows)
```

`insert into tab01 values(1,'1'),(2,'2'),(3,'3');` 的 command ID 是 0，`insert into tab01 values(4,'4'),(5,'5'),(6,'6');` 是 1，这时候，如果第一条 command 是一个 select 并且返回了一个 cursor，然后我们又执行了 command 2 加入了三条数据，这是在一个事务中的，这时候，cursor 继续读取或者修改数据，但是后面三条数据的 cmin 是 1 比自己的 0 大，所以这三条数据是不可见的，也就是不能读到的，这就是 cmin 和 cmax 的意义。但是 cmax 实际上和 cmin 是一个值，请参考 [cmin 与 cmax 的社区讨论](https://www.postgresql.org/message-id/CAL454F1o56ZkfmsMasjxJHcOw%3DmwgowBu33JSkKWh2d31ARAUg%40mail.gmail.com)。

### MVCC & VACUUM

了解了上面的四个系统字段，我们就可以简略的说一下 PostgreSQL 的 MVCC 是怎么实现的了。之前我们的问题中提到，不论是读的时候发生了写，还是写的时候我正在读取，都会产生数据不一致的问题，实际上我们希望的是在读取的瞬间，数据是不变的，这样的好处是大于一半新数据，一半老数据的情况的，那最简单的办法就是加锁，不论是读还是写都给表上加锁，就像是 synchronized 关键字一样，但是任何环境、编程语言下都会降低性能，所以有人提出了快照的概念，实际上在读取的时候，依旧读取的是旧数据，而写数据时并不删除，这就解决了这个问题。

对于 PostgreSQL，实现的方式就是我们刚才讲到的 row version，写入或更新新数据时并不修改原数据，只创建新行就行。这种方式实现起来相对比较简单，因为不需要移动与删除旧数据，所以我们需要有 xmin xmax cmin cmax 的标记来帮助事务判断版本，显而易见的缺点是当数据被删除后，也是存留在磁盘中，我们的空间依旧是被占用的。

还有一点值得注意的是，对于事务所产生的修改数据，会有 xmin 与 xmax 的标记，但是如果事务回滚，PostgreSQL 也不会删除这些创建的数据，这也是为了性能而采取的措施，当我们需要去回收存储空间时，就可以通过 xmin 与 xmax 去找事务是否成功来进行回收了，而事务的成功与否存在于 commit log 中。

下来，就需要非常重要的 VACUUM 命令了，VACUUM 命令是一个垃圾回收器，会清除我们之前提到的无效的、废弃的数据，所以周期性的使用 vacuum 进行回收是非常重要的。直接使用 VACUUM 会处理当前数据库中的每一张表，你当然也可以指定某一张表。对于 VACUUM 的参数，有两个参数值得我们注意：

- FULL: 有点类似于 stop the world 的 full GC，FULL 参数会给我们腾出更多的空间，但是会锁表，也需要很多的空间，因为实际上 VACUUM FULL 是把当前表进行了一次拷贝！**所以，使用 VACUUM FULL 需要非常留心，除非你必须要腾出很多空间，或者能接受停机，否则尽量别用它。**
- ANALYZE: 更新查询分析器的统计数据，帮助我们的查询计划能够更精确，**很多人在业务不繁忙时手动进行 VACUUM 的情况下会加入 ANALYZE 参数**，这样能显著的提高查询性能。

当然 VACUUM 是 PostgreSQL 独有的命令，并不是 SQL 标准。而且默认下 PostgreSQL 的 autovacuum 是打开的，PostgreSQL 很智能的在更新达到一定情况下会使用 VACUUM，这就是为什么很多使用 PostgreSQL 的同学没有用过 VACUUM 的原因之一了。这里查看 [autovacuum](https://www.postgresql.org/docs/9.5/runtime-config-autovacuum.html) 文档介绍。

所以，PostgreSQL 的 MVCC 使我们考虑事务就比较简单了，笔者曾经在一个事务中进行了百万次的插入，并不需要特别担心什么，即使出错 ROLLBACK 也是一瞬间的事情，因为并不做物理删除，所以在插入、修改的时候，性能还是比较稳定的，但是我们不得不消耗系统资源去进行垃圾回收，这就如同 Java GC 一样，VACUUM 进程的回收也是要消耗资源的。



