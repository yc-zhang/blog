### Database

我们已经想不起来为什么需要在项目中使用数据库了，基本上做后端开发是无法离开的数据库的，从 RDBMS 到 NoSQL 再到最近火热的 NewSQL，我们一直在寻找更好更快的数据存储方案，不论硬盘是从磁盘变成了 SSD，但是依旧在用来自 1970 年代的 SQL。的确，使用现代的 web 框架配合 MySQL 能够很快的完成一个 RESTful 或者 MVC 式的应用，但是这是有限的，对于 RDBMS 来说，最大的问题是按照行列的方式进行数据存储，而我们的业务逻辑算法（可能只是一个简单的 flatmap 之类的东西），往往是有多种数据结构需求的。

现代数据库系统都提供了企业级的功能，比如自动备份、落盘加密、分布式与性能保证，对于架构师来说，这些写在白皮书上的功能很有诱惑力，很多时候我们必须要通过这些功能点进行技术选型，但是这是 low-level details，对于架构的设计来说，我们不应该限定某种数据库，或者并不希望数据库束缚住我们。**其实这在项目中还是比较常见的，经常会有人使用 h2 做 memory database 支持开发，线上则用 MySQL 或者 MariaDB，换 JDBC Driver 就可以做到这一点，但是本文是想讨论在 JDBC 之外的代码。**

我不止一次的听过有人说，使用 MongoDB 是因为其提供的性能，但实际上优化与重构代码所带来的性能提升远远大于使用某种数据库，或者说起性能的要求并没有极端到必须要使用某种存储技术。这并不是说性能不重要，**而是说我们的系统应该有足够的灵活性**。往往在新项目开始时，我们所面对的性能压力并不是很大，可能第一个版本只是需要一个恰好能够表达业务就行，这时候将存储技术与实际业务进行解耦就非常关键了，因为在不久的将来可能你会使用 MySQL Proxy 进行分库分表，或者直接使用 DynamoDB 这种 NoSQL。

有前辈曾向我展示过某银行使用 MySQL Binlog 来进行某种数据同步，并围绕该实现进行了一系列的定制化开发，随着人员的更迭与技术的革新，这部分的系统已经没有人能进行修改与升级了，诚然他们也想换掉这种不是很专业的实现，使用专业的中间件实现数据迁移同步并不是很难，但是已有的代码与细节绑定的太深，以至于没人敢停掉现在的实现，**虽然这些代码依旧在工作，但是从架构的角度上来说是失败的。**

我们在学习算法与数据结构时，使用过很多例如列表、树、链表、队列、堆栈、Map 等等很多数据架构，而 RDBMS 只能提供行列，你有没有将一个树存放在数据库中的经验？不管使用哪种方式实现，你都会觉得比较别扭，比如下面的例子：

Option 1:  使用 Parent Id 存储树
```
id | parent_id | data
---+-----------+----------
 1 |      NULL | root
 2 |         1 | Child 1
 3 |         2 | Child 1.1
 4 |         2 | Child 1.2
 5 |         1 | Child 2
 6 |         5 | Child 2.1
 7 |         5 | Child 2.2
```
Option 2: 存储左右子树的关系
```
id | parent_id | lft | rgt | data
---+-----------+-----+-----+----------
 1 |         0 |   1 |  14 | root
 2 |         1 |   2 |   7 | Child 1
 3 |         2 |   3 |   4 | Child 1.1
 4 |         2 |   5 |   6 | Child 1.2
 5 |         1 |   8 |  13 | Child 2
 6 |         5 |   9 |  10 | Child 2.1
 7 |         5 |  11 |  12 | Child 2.2
```
我个人曾经实践过使用 Option 2 的方式，比如使用类似的 SQL 进行获取节点计算：
```sql
SELECT * FROM nodes WHERE lft >= 2 AND rgt < 7 AND id != 2
```
这种模式很好的表达了树的结构，但是在我进行节点的新建与更新时，需要更新的数据行要远远多于 Option 1 了，这种 case 只适用于读远远大于写的场景。

（[Closure Table Pattern](http://technobytz.com/closure_table_store_hierarchical_data.html) 应该是最流行的解决方案了，常见在各种 ORM 中会有实现，这里就不展开讲了。）

这种别扭还会表达在其他地方，在代码中，**插入数据我们希望是一个 LinkedList，存储 K-V 我们希望有一个 map，计算多级关系我们希望用树，计算路径我们需要 graph，做 workflow 我们更想要一个 DAG，这些方便的数据结构往往在存储时会造成麻烦，**这是我们不得不面对的。

关系型数据库的优势是 relation，使用 relation 你可以很方便的表达类似于我有几台电脑这种关系，使用 JOIN 类似的查询也很简单，但这个功能不一定是必要的。一旦没有使用好 JOIN 或者其他的多表查询会造成性能上的问题，而且多表查询的语句也很难写、难以理解与改动。在你使用 DynamoDB 或者 MongoDB 这种没有 relation 的数据库时，很多时候你不得不自己编写程序来应对 JOIN 的需求，对于 NoSQL 类型的数据库，你必须要根据查询需求进行性能优化，加上分页与排序就更糟糕了。

这里面必须提到微服务的一些特性，在微服务世界中，我们提倡每个服务管理自己的数据，某种程度上降低了多表联查的出现（我已经很少看到三个表 JOIN 在一起的语句了，也有规范认为三表 JOIN 就是反模式），但是并不代表这种 JOIN 的逻辑消失了，当你的 BFF 组织后端几个服务的返回时，那其实就是做 JOIN。

所以，不论你的数据库是否支持 JOIN 或者类似的功能，你都要将查询的方法与过程远远的放到业务逻辑之外，就是上文中我们画过的边界。你的 service 希望 repository 提供什么样的数据，这在接口上一定要定义清楚，有时候你甚至需要再引入 converter 将格式化的数据结构转为适合计算的数据结构。看起来是麻烦了一些，但是边界清晰，即使存储层有巨大的改动需求，也不需要破坏与改动 service。

```java
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface BookRepository extends JpaRepository<Book, UUID> {
    Page<Book> findByBookIdOrderByUpdatedSeqDesc(String userId, Pageable pageable);

    Optional<Book> findByIdAndUserId(UUID bookId, String userId);

    Optional<Book> findByNameAndUserId(String bookName, String userId);
}
```

**ORM 也是现代框架中提供的杀手级功能，的确能够满足大多数人的开发需求，但是我们也要警惕 ORM 过多侵入代码的问题。**Uncle Bob 不提倡我们将 ORM 的 Model 与业务的 Entity 混在一起，但是对于 Spring 开发的程序员来说很难做到，因为 Annotation Entity 几乎随处可见，特别是 relation 的注解可以让我们不需要直面 JOIN 语句了，还有其他的注解例如 org.hibernate.annotations.Type 这种直接帮我们使用数据库的功能的。但是其实也没那么糟糕，对于 Java Annotation 来说，你不使用它就可以忽略它，只是不太好看，但是其他的编程语言与框架就不一定了。

```java
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.Type;
import org.hibernate.annotations.UpdateTimestamp;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.UniqueConstraint;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(uniqueConstraints = {@UniqueConstraint(columnNames = {"type", "value"})})
public class FakeProductExample {
    @Id
    @Type(type = "pg-uuid")
    private UUID id;

    @Column
    private String type;

    @Column
    private String value;
    @CreationTimestamp
    @Column(updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    private Instant updatedAt;

...
```

所以我的感受是，在 ORM 层与数据库细节决裂是还是可以实现的，从 Service 层来看，是不需要知道 Entity 的 Annotation，把 Entity 做 POJO 来使用就可以了，同时再直接使用 Repository 获取 Entity，因为 Repository 是接口，对于 Service 来说就无须考虑存储细节了。在其他语言或者框架下，这也是可以做到的，比如下面这个 scala 的例子：

```scala
trait ProfilesDAO extends BasicDAO {
  def createProfile(profileUid: String, ...): Profile
  def updateProfileEmail(uid: String, ...): Int
  def profileEmailExists(email: String): Boolean
...
}


object ProfileDAOImpl extends ProfilesDAO with DBPreferenceSupport with PrimitiveTypeMode {
  def trans[A](action: => A): A = transaction(action)

  override createProfile(profileUid: String, ...): Profile = {
    ...
    inTransaction {
      DB.profile.insert(profile)
      ...
    }
    profile
  }
...
}

import SquerylImplicits._
object DB extends Schema {
  case class Profile(
                      @Column("profile_uid") id: String,
                      ...
                      @Column("profile_name") name: Option[String],
                      ...
                      @Column("updated_at") updatedAt: Timestamp = new Timestamp(System.currentTimeMillis())
                      ) extends KeyedEntity[String] {
    def uid: String = id
  }
...
}
```

trait ProfilesDAO 是外部代码使用的边界，就相当于我们常说的接口，ProfileDAOImpl 负责实现，调用了 DB 的成员（ object DB 很轻量，写了一些映射就足够了）并混入了其他功能，我个人还是比较喜欢这种做法的，没有引入过重的依赖，边界也很清晰，ProfileDAOImpl 的实现也比较符合语言特性。

### Web

在我刚开始工作的时候，我接触了 jQuery 并很开心的使用 $.ajax 去调用一些 endpoint，**几年后我很惊讶的发现我自己竟然都没意识到我是在进行 web service 调用，因为 web service 并不只是笨重的 WSDL 与 SOAP 啊！**随着时代的发展，MVC 式的应用已经逐渐没落，大家已经不喜欢做一个大而笨重的后端应用了，也不喜欢既有后端渲染页面，也有异步的 ajax 去实现的复杂前端。HTML5 的发展伴随着单页应用的崛起，而我们的后端从有状态、有 session 的巨大单体应用也逐渐解体，被微服务替代，我觉得挺好，很高兴我们不是在浏览器里跑 Java Applet 或者 Microsoft Silverlight 了。

### Framework

按照 Uncle Bob 的说法 Framework 也是一种 detail，我们要避免自己的应用被框架绑架的情况。在现代软件开发的过程中，我们无法不依赖前人进行开发，往往的节奏是，选定一个框架，搞清楚基本功能，然后在上实现我们想要的功能。我们会跟进应用程序的需求来选择框架，比如说在 web 领域，如果是一个 MVC 式的应用可能会使用 Spring MVC 或者 Ruby on Rails，如果我们要写 Restful Service，可能会用 Ruby grape、Spring Boot、Scala Unfiltered 等等。因为框架的确帮助我们提供了通用的功能，帮助我们可以专注于业务逻辑。但是往往的问题是，我们对框架的依赖过重了，导致我们的代码与框架没有清晰的边界，从而失去扩展的机会。

```
import unfiltered.netty.future.Plan._
import unfiltered.request._

class AppRoutes(myController: MyController) {

  val routes: Intent = {
    case req@GET(Path(Seg("schema" :: Nil)))     => myController.schema()
    case req@GET(Path(Seg("search" :: Nil)))     => myController.search(req)
...
    case req@OPTIONS(Path(Seg("search" :: Nil))) => myController.options(req)
  }

}
```

**上面的例子描述了，在路由中我们调用了 myController 来处理业务，而 myController 是注入进来的，我们没有在路由中直接编写业务逻辑。但是，myController.search(req) 方法中的 req 是框架所定义的 HttpRequest，所以 MyController 的必须要依赖 unfiltered.request.HttpRequest，那么你就无法轻松的换掉 unfiltered 了。**

这种被绑架的情况被称为“不对称的婚姻”，对于 framework 的发明者来说，这样的方式的确易于控制，但是对你来说，你必须适应框架的规则，并且持续更新，你必须要做出很大的改动才能适应和使用框架。我们在使用 play framework 时就遇见了类似的问题，该项目是接手一个无人管理的代码仓库，为了升级 framework 我们必须做出上千行的代码改动，危险的是，因为没有足够的上下文，没人能确定改动的正确性，更悲观的是，因为使用了很多特性（日志、路由、注入等），我们几乎无法选择新的框架来替代。

另一个例子是，某公司的新一代交易引擎是跑在 Flink 这种流式处理框架之上的，几个运算模块按照拓扑被依次调用，对于这个场景他们使用 Flink 只是为了先验证计算方式的正确性，而未来到底使用哪种技术去调用引擎还不是很确定（可以理解为这是一个从消息中间件中获取事件，再调用引擎计算，再将计算结果放回中间件，这种模式非常常见）。所以在架构的角度上来说，Flink 与计算引擎之间的边界很清晰，所以在尝试使用其他消息消费者获取事件、驱动计算的过程中，计算引擎的部分一行代码都没有修改，整个改动也非常小，在实际的工作中，其他忙于引擎开发的同事并没有感受到任何变化。

上面那个项目最后使用了 Spring Boot 来进行依赖注入、组装 bean，那么不需要 Spring Boot 可以做这件事吗？答案是可行的，Spring Boot 使用 autowire 的方式来管理组件的依赖，我们自然也可以使用手动管理。将业务需要的 bean 一个个 new 出来，再组装在一起，看起来复杂，但是实际上只花了一个多小时就做到了，你可以把这些逻辑放在 main 函数中，而这些逻辑是与框架无关的，所以你可以像 helloworld 一样，点一个按钮就可以跑起来了。

