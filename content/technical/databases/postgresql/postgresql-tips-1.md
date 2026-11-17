### Why

回顾了下自己所在项目中的数据存储技术，在关系数据库方面使用了 MySQL、PostgreSQL 这两种流行的产品，以及其他提供 SQL 接口的大数据存储服务例如 Google Big Query 与 AWS Redshift，在 NoSQL 领域自然使用了 DynamoDB，同时缓存、与部分队列使用了 Redis，以及文件存储 S3 与传统的 SFTP。由于项目早在三年前就践行微服务实践，强调 Cloud Native，强调 as-code 式管理资源，强调 on-provisioning 资源，所以大约在产品线内运行着大约 12 个关系型数据库的实例，这里面大多数是 PostgreSQL 而不是国内流行的 MySQL。好消息是，大量的实例运行在 AWS RDS 之上，所以运维并不困难，也比较适合我们这种底层能力欠缺的团队——也就是大多数普普通通的团队。

当然，在这里我们不讨论分库分表或者拆分服务，我们也不讨论运维这些东西的故事，这里我也不讨论技术选型等，自然这些很火热的话题。笔者写这篇文章的原因在于，前几天有同事提出了一个问题，为什么我们的关系型数据库使用 PostgreSQL 而不是 MySQL 或者其他？我觉得简单的回复并不合格，于是回顾和总结了一些 PostgreSQL 的知识，也是复习和巩固自己。

我首先想到的是 PostgreSQL 的功能比较齐全，多表联查支持的很好 （nest loop, hash join 与 sort merge join 都支持），SQL 语法支持的比较多，函数全面，类型上常用的数据、JSON、XML（以及各种 JSON 函数）都是比较好用的，此外还有很多常用类型的特殊值，例如时间日期上的 now today 等。社区中基于 PSQL 进行的开发也比较多，但是由于我们的实例是被托管的，所以不存在能够扩展 PSQL 的机会。PSQL 的性能优化也比较好做一些，除了常见的 explain 的支持，度量信息也很多，IO 方面我们不仅参考 RDS 提供的 IOPS，也会参考 PSQL 自己的统计。简单来说，功能上强大，性能上也足够优秀，主要相对于 MySQL 折腾比较少，或者不需要在应用层进行额外的工作。

如果要是选择一个自己最喜欢的功能的话，就是在线建立索引的功能，也就是建立索引时不锁表。这一点为我们节省了很多运维的成本，如果你参与的系统有很强的 0 downtime 的需求，那么这个功能几乎是杀手级的，同样的如果在 MySQL 的环境下实现这一点，除了停机之外还可以使用 master-slave 的方式，从复杂度上来说自然是 PSQL 更简单一些。当然进行其他 DDL 例如加一列，也是不锁表的。

**简单来说，对于一个小型的团队，或者没有专职的 DBA 的情况下，使用 PSQL 能在存储层上解决掉很多比较棘手的问题，在功能上基本上是 OOB 的。当然最重要的是在合适的地方选择合适的技术，特别是微服务化后，我们并不需要将所有的东西存放在一个巨大的关系型数据库中了，毕竟很多简单的业务 NoSQL 更适合。**

### 数据类型

#### DateTime

就像其他的关系型数据库一样，PostgreSQL 也支持大量数据类型，这里主要分享几个比较特殊的，我们先从时间和日期开始。首先 PostgreSQL 的时间类型是可以精确到秒一下的，对于 timestamp 类型来说，PostgreSQL 使用了双精度浮点的方式存储，默认情况下精确到毫秒是没问题的。

此外，PSQL 还支持 date、timestamp、time 与 inteval 之间的加减乘除例如这样的操作：

```sql
SELECT tstz,
       (tstz + interval '7 hours') AS hours_later,
       (tstz + interval '24 hours') AS expires_at,
       (date '2019-03-12' + 8) AS days_later
FROM timestamp_test;

-[ RECORD 1 ]------------------------------
tstz        | 2019-05-03 15:05:43.152825+00
hours_later | 2019-05-03 22:05:43.152825+00
expires_at  | 2019-05-04 15:05:43.152825+00
days_later  | 2019-03-20
```

当然也有支持很多时间函数，例如 now(), CURRENT_DATE 这些，同时还支持使用 extract 函数获取特定的时间子领，比如你可以得知某个 timestamp 是本年的第几周，或者第几月或者星期几，例如：

```sql
SELECT tstz,
       extract(MONTH FROM tstz) AS MONTH,
       extract(dow FROM tstz) AS dayofweek,
       extract(doy FROM tstz) AS dayofyear
FROM timestamp_test;

-[ RECORD 1 ]----------------------------
tstz      | 2019-05-03 15:05:43.152825+00
month     | 5
dayofweek | 5
dayofyear | 123
```

诚然数据库的特性可以帮助我们节省很多操作，例如计算星期几用 Java 语言写会稍微麻烦一点，在数据库层面解决了就太好了。但是这些方言的过多使用的确会使应用程序与存储层过多耦合而丧失迁移的能力，常见的例子是，我们在生产环境下我们使用 MySQL 的某个版本，但是在测试环境下可能是另一个不一致的版本，在本地又会使用 H2 或者 SQLite，这种不一致性会就会造成麻烦，很多可以使用的特性不得不放弃。目前，我们会需要考虑存储层的移植性，例如 MySQL 到 MariaDB 或者 Amazon Aurora ，这也是 JDBC 的意义之一。所以针对这种情况，我们应该慎重考虑：

**1. 对数据库的特性使用应该保持克制，特别是 SQL 命令层级的特性**
**2. 在技术选型时考虑存储层的可迁移性**
**3. 尽量统一自己的存储层技术，例如使用 docker 获取更一致的本地环境**
**4. 对于 Migration，直接使用 DDL 优于使用 ROM 提供 DSL**

对于时间和日期最后一点就是时区，时区是一个头疼的，并且容易会被忽视然后酿成大祸的东西。在 PSQL 下，往往处理这种事情有两种不同的方式，不过我们先说说 timestamp 与 timestamptz，我们都知道，对于 timestamp 是允许你存放时间和日期的一种类型，当然没有时区，所以当你修改了你的数据库的时区，存放的值并没有任何改变，因为并没有时区信息。而 timestamptz 是有时区的，PostgreSQL 使用 UTC 落盘，当你 INSERT 一个时间时，PSQL 将其转换为 UTC 并且存放在表中。所以，当你查询一个 timestamptz 的值时，PSQL 将其转换为当前的时区返回给你，也就是与数据库建立 session 时所指定的时区。这也就是为什么下面的例子中，ts 没有改变的原因。

```SQL
SET timezone = 'Asia/Chongqing';

CREATE TABLE tz_test (ts TIMESTAMP, tstz TIMESTAMPTZ);

INSERT INTO tz_test VALUES (now(), now());

SELECT * FROM tz_test;

-[ RECORD 1 ]-----------------------
ts   | 2019-05-03 23:34:18.793234
tstz | 2019-05-03 23:34:18.793234+08

SET timezone = 'America/Los_Angeles';

SELECT * FROM tz_test;

-[ RECORD 1 ]-----------------------
ts   | 2019-05-03 23:34:18.793234
tstz | 2019-05-03 08:34:18.793234-07
```

所以显而易见的我们有两种处理 timestamp 时区的方式：

1. 全部使用 timestamp 类型存放时间，并且规定所有的时间都是 UTC 格式的，在客户端由调用者进行转换
2. 使用 timestamptz 格式存放时间，保存时区，根据 session timezone 返回时间

显而易见的是，第一种方式比较简单，我们不需要考虑那么多，只需要每个人都记住然后在使用时自己转换即可。但问题往往出在每个人都记住这一点上，我们发明了一个额外的并且是隐式的知识，这就会随着时间的流逝而淡薄，最危险的是，一旦将来我们犹豫了时区问题，从源头上已经无法获取正确的值了，因为时区信息永久的丢失了。

**第二种方法我们有时候也会获取 UTC 时区的时间作为返回值，然后再按需转换，但是问题是，在数据库中，我们的 timestamp 是确定的，不会根据任何时区的改变而改变，所以通常意义上的 best practice 是使用 timestamptz 存放你的时间日期，并且明确你的 session timezone。**

#### Enum

与 MySQL 等数据库不同的是，PostgreSQL 的枚举类型往往需要你自己去使用 CREATE TYPE 创建一个枚举，比如像这个样子：

```sql
CREATE TYPE cat_color AS enum('red', 'black', 'white');
CREATE TABLE cat_coffee(name text, color cat_color);

INSERT INTO cat_coffee VALUES ('Alice', 'red');
INSERT INTO cat_coffee VALUES ('Bob', 'black');
INSERT INTO cat_coffee VALUES ('Bad Guy', 'green');
# ERROR:  invalid input value for enum cat_color: "green"
```

对于 PostgreSQL，每个枚举值在磁盘上只有 4 个字节，一定程度上可以减少我们的空间占用，但是问题是，这样做值吗？就如同在 MySQL 上大家对枚举值的争论一样，以下的问题依旧是你需要考虑的：

**1. 枚举字段只是保存了数据的特征信息，也不是全量的数据，有时候你真的需要节省那么点空间吗？**
**2. 不论是 MySQL 还是 PSQL，更改枚举的成本很高**
**3. 很难获取枚举全部的值，虽然你可以从 pg_enum 里面拿到，但是并不是原生的 SQL**
**4. 几乎很难在其他数据库复用，基本上数据库的枚举功能都是特性，特别是你在迁移 enum 时，基本上是个灾难**

所以我们还是建议你慎重考虑使用 enum，如果我们要存储的是准确的、不变的的值时，我们可以考虑使用 enum，但是上文中的例子就是反例，因为猫的颜色还有很多，某日你可能需要修改这个 cat_color 让他支持黄色或者绿色。

#### JSON

诚实的说，我们一开始选用 PostgreSQL 的很大原因是对 JSON 的支持很好，特别是 JSONB 这种类型还支持在 JSON 上建立索引，以及很多好用的 JSON 函数可以帮助 BA 直接获取数据。对于 PostgreSQL 来说，目前是有两种用于处理 JSON 的类型：JSON 与 JSONB，对于 JSON 类型来说，只是把数据原封不动的放入到数据库中，进行语法检查但不做任何处理，所以现在已经很少使用了。而 JSONB 则是在存放时将其解析为二进制格式的 JSON，有点类似于 MongoDB 的 BSON，所以在使用时我们就不需要再 parse 了，这自然带来了更好的性能以及灵活性，比如建立索引。

当然，我们也可以使用 text 或者 varchar 来存放 JSON，如果不需要处理 JSON 内容，你也可以直接使用这些方式去存储，只是没有存储前的检查罢了。

JSON 类型支持很多特殊的操作符，你可以简单的做一些 path extract 或者判等，例如:

```sql
jsonb '[1,2]' = jsonb '[1,2]' => t
jsonb '[2,1]' = jsonb '[1,2]' => f
jsonb '{"a":"name", "b":99}' = jsonb '{"b": 99, "a":"name"}' => t
SELECT '{"a":"name", "b":99}'::jsonb ->> 'a'; => name
SELECT '[2, 3, 5]'::jsonb -> 2;  => 5
```

此外，你也可以很轻松的将其他你能想到的东西转换为 JSON，例如：

```sql
to_json(array[1, 2, 3])
to_json(ROW(9, 8, 7))
json_object('{a, 1, b, 2, c, 4}')
```

或者使用 build object 进行特定的输出，这样会有更好的灵活性，例如：

```sql
SELECT json_build_object(
    'name', name,
    'time', tstz
) FROM timestamp_test;

#  {"name" : "now", "time" : "2019-05-03T15:05:43.152825+00:00"}
```

在这里我们就不列举 PSQL 所支持的 JSON 函数与操作符了，更多的请参考这里 https://www.postgresql.org/docs/9.5/functions-json.html。当然，对于 XML PSQL 依旧也有类似的支持。**我们的意见是：如果你真的需要在存储层进行 JSON 与 XML 的复杂操作，PSQL 的确能帮到你很多，而且功能好用性能稳定，但是在没必要的情况下，对于数据库的特殊功能还是需要慎重，以免为将来挖坑。**

#### Others

PSQL 还有很多有趣的数据类型，但是这也不是本文的重点，这里就不一一介绍了，也请大家参阅：https://www.postgresql.org/docs/9.5/datatype.html。下面回顾了一些有特点的类型：

Array 是专门对数据类型进行的封装，而且根据之前 JSON 的介绍，你可以很容易的和 JSON 进行转换，当然我们使用 Array 很多情况下是为了避免自己发明 Array —— 我是指实际上使用字符串进行存储，然后自定义分隔符的方式，这在其他 RDBMS 中很常见，也自然会存在问题。不过好消息是，在 PSQL 如果你真的需要使用 Array 来描述某项数据时，这个类型还是蛮好用的。

Range 也是 PSQL 独有的数据类型，常用来表示范围，比如一个时间范围或者一个整数范围，那么这个东西有什么用呢？简单来说可以通过这个类型极大的提升范围查询的执行效率，例如 start >= value1 and end <= value2。往往我们会给 start 与 end 做两个索引，这样的查询会先做两个 index scan 然后在 bitmap scan 将数据求和，再使用 condition 过滤，这样的效率自然不高。但是使用 Range 作为类型的话，并且创建索引的话，可以直接进行 index seq 进行查询，那性能提高就不是一个数量级的事情了。流行的例子是使用 Range 来创建 IP 的子类型（inet），这样就可以支持常用的一些网络方面的操作，比如判断某个 range 内是否有这个 IP 作为查询条件，例如：

```sql
SELECT * FROM some_table WHERE my_ip_range @> '192.168.0.12'::inet;
```
