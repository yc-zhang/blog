### 架构与架构师

对于软件产品来说，往往是用两方面的价值体现，行为与结构，行为方面的价值表现为业务上的实现，也就是你可以使用软件来定制、完成业务，获取收益，而结构上的体现则反映在架构上，良好的架构设计能让系统易于理解、易于开发、易于部署、易于维护，能够让我们快速响应需求变化。**结构上的价值对于软件更为重要，因为它体现出了软件的“软”。这也是软件架构与建筑架构所不同的地方，建筑架构更多是追求稳定，而软件架构则是面向演进和变化。**

作为架构设计的终极目标是，降低在软件产品的生命周期中的花费，并且最大限度的提高工程师的生产力。架构设计的目的不是为了让系统工作正常，回想一下每个人都在公司中遇见过所谓的“老系统”，这些系统复杂笨重，难以运维、部署，但是往往这些系统都工作正常，最少在是满足最开始的设计的。所以，架构设计时要尽可能的考虑到系统的生命周期，在这个周期中，让我们的系统能够有能力接受新的 option，这与框架、语言、数据库、中间件等细节是没有关系的。

**作为架构师或者设计架构的人，首先必须是一位足够优秀的程序员**，他们必须持续的写代码才能明白自己的设计是否正确与高效，如果只是画格子（box drawer）他们就无法真正的体验到实践架构时的问题与痛苦，也无法回答其他工程师所面对的具体实现问题，比如：我们是使用 Pageable 分页还是自己写？我们应该采用哪种中间件？或者使用 NoSQL 时，应该如何保证复杂查询的效率？或者仅仅是搞定一个诡异的 bug。

### 独立性

关于解耦（Decpouling），在我的学习过程中，设计架构和写代码是有很强的共通性的，我们都是在考虑抽象，考虑更好的表达与组合，只是写代码时组合的是方法或者类，这里有很成熟的设计模式可供参考，而架构设计更多的是系统与组件之间的组合。设计模式或者 SOLID 这些准则都指导我们去做解耦，我们不希望拆东墙补西墙，也不希望按了葫芦起了瓢。比如下面这段代码，将输入的解析与业务的处理放在一起是非常不明智的，实际上这是两个不同的功能。

```java
public String translate(String input) {
    String currentLine;
    try {
        BufferedReader br = new BufferedReader(new FileReader(input));
        while ((currentLine = br.readLine()) != null) {
            boolean foundTranslator = false;
            for (Translator translator : translators) {
                if (translator.isMatched(currentLine)) {
                    translator.translate(currentLine);
                    foundTranslator = true;
                    break;
                }
            }
            if (!foundTranslator) {
                outputCollector.addError();
            }
        }
    } catch (FileNotFoundException e) {
        System.out.println(e.getMessage());
    } catch (IOException e) {
        System.out.println(e.getMessage());
    }
    String outputs = outputCollector.getOutputs();
    return outputs;
}
```
*这份代码有很多 bad smell 与反模式上的问题，显然出自初学者之手，我在读书时也常常写这种代码，如果没特殊指明，你都不会猜到 `translator.translate(currentLine)` 实际上是在进行业务逻辑处理。*

Don't repeat yourself (DRP 准则) 指导我们需要尽可能的消除重复，但是也需要判断这个重复是否为**真正的重复**，我有一个现实中的例子刚好可以说明 Uncle Bob 提出的真正的重复。当时我们在做一个新的服务叫做 Spotlight，它的职责是返回一些热销的产品信息，由于我们的业务网关（BFF，聚合后端服务的专为前端应用服务的服务）的良好设计，实现 Spotlight 的功能只用了两个星期不到，大家都很开心。当时的产品经理一再强调，**其返回的数据格式与其他返回产品信息的服务的格式一致**，所以虽然 SpotlightService 类中有与其他 Service 类中一样的代码，我们还是保留下来了（即使 IDE 提出需要抽出），因为当时的 Tech Lead 一再强调，这两段重复的代码负责两个截然不同的业务，用 Uncle Bob 的话说就是，他们的 actor 或者 stakeholder 不同。不出所料的是，Spotlight 有了新的需求，所以我们的改动没有影响其他的服务，我们也避免了在共享的代码中加入 if-else 来判断调用者。这种情况下共享代码十分危险，因为一旦做错，就会影响一大片的功能，而很多功能你不一定清楚是怎么一回事。

Uncle Bob 提到，好的架构设计应该允许系统从单块应用（Monolithic）开始，逐渐演变为多组件式、多服务式的应用（SOA），诚然服务之间的调用相对于代码级是很慢的，但是却提供了最好的独立性，每个服务是可以按需扩容，独立部署而不影响到其他。好的架构是允许 options open 的，能拆分服务也能重新聚合，我们早期的 ruby 编写的一些服务自然可以用 Spring Boot 重写，而这种重写不会影响其他的服务。所以我一直不喜欢 Spring Cloud 的重要原因是其侵入性太强，导致 Java 作为唯一的选型，当我们需要使用平台级的能力时（比如 k8s 上的各种 mesh，其他的容器编排平台，或者公有云的能力），就会难以实施。

### 边界

边界这几章着重强调的是画线的位置，是用来强调解耦的一种手段（写这篇文章时，渐渐的感觉到整本书就是两个字，解耦），我们的前端页面不应该关系后台的服务的业务逻辑，所以其中有一条边界分割，业务逻辑也不需要知道具体是哪种数据库完成了他们对存储的需求，所以也存在一种边界。**表现在代码中，就是业务逻辑使用数据库的接口进行存储层的操作，而由存储层的实现来最终完成这些操作，最少当你考虑业务的时候，你只应该考虑业务。**

```scala
trait ProfileDAO extends BasicDAO {

  def createProfile(profileUid: String, email: String, ...): Profile

  def updateProfileEmail(uid: String, email: String): Int

  def updateProfilePassword(uid: String, passwordHash: String): Int

  ...
}

object ProfileDBDAO extends ProfileDAO with SomeDBPreferenceSupport ...

abstract class SomeBusiness(dao: ProfileDAO, generator: SomeGenerator...

object SomeBusiness extends SomeBusiness(ProfileDBDAO, SomeGenerator, OtherComponent, ...
```

这段不太规整的 scala 代码描述了业务与数据库之间的关系，SomeBusiness 的业务逻辑是写在 abstract class 中的，其注入的 dao 变量并没有说明实现细节，对于 SomeBusiness 来说，只知道使用 dao 的某些方法，至于细节的实现则是在 object ProfileDBDAO 中完成的。那组合这些功能的地方，则在 object SomeBusiness 中，这里采用了伴生对象的方法，在 scala 中算是比较常见的做法，在测试中，我们只要面对 abstract class SomeBusiness 就可以了，object SomeBusiness 只是起到了注入依赖的作用。按照书中的意思，我们也画一个边界意思一下：

![a boundary](https://upload-images.jianshu.io/upload_images/3819274-42479ffad5598589.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

也就是说，有朝一日你需要将使用 MySQL 的 ProfileDBDAO 换成 ProfileMongoDBDAO，你只需要关注边界下面的改动实现，在 Spring 的世界中，Autowire 会帮你直接注入新的 DB DAO。

所以画一条边界线可以帮你把系统 breakdown 成合理的 component，并且搞清楚哪里是你的业务逻辑（也就是需求方关心的地方），哪里是你可以自由发挥的地方，使用这种方式你能很快的理解依赖反转，**因为你想要做到解耦的话，就一定会用到类似接口的东西，即使使用 duck typing 语言（js、ruby 等）你也需要不断提醒自己，我们不希望把细节带到高级的业务抽象中。**

### high-level policy & low-level detail

业务才是程序的核心，是能够让程序产生价值的东西，描述业务的东西一般被称为 policy statement，这些 statement 组成了程序最核心的部分，自然这一部分也距离输入与输出的地方最远，于是就被成为 high-level policy。你是不会在业务逻辑中去判断输入的字符串是否是一个标准的 json 并且将其序列化为输入的 model 的，你也不会在业务逻辑中使用 system.out 直接输出计算结果，因为在 high-level policy 中，并不需要关心这些。

high-level 关心的是业务逻辑，也就是作者提到的 Business Rules，根据习惯，我们使用 Entity 常常来描述在业务领域的集合。按照 DDD 的一些实践建议，在我们定义 Entity 的时候，我们也会习惯性的把业务逻辑放进去，例如：

```javascript
class Job extends Entity<IJobProps> {
  // ... constructor
  // ... private factory method

  get questions (): QuestionsCollection {
    return this.props.questions;
  }

  public hasApplicants (): boolean {
    return this.props.applicants.length !== 0;
  }

  public addQuestion (question: Question) {
    if (this.hasApplicants()) {
      throw new Error("Can't add a question when there are already applicants to this job.")
    }
    
    if (this.props.questions.length === MAX_QUESTIONS_PER_JOB) {
      throw new Error("This job already has the max amount of questions.")
    }

    this.props.questions.push(question);
  }
}
```

所以 Job 也被成为领域模型，在这个模型中，虽然 Job 可能会有其他更多复杂的对象作为其成员，但是对于业务人员与开发者来说 Job 是统一语言后在领域中的模型，也是业务的操作对象。

实际上，是 use cases 来控制这些 entity，具体的业务规则最后应该在这类 entity 中展开，往 Job 中放入任务，或者判断 Job 是否被人申请，但是 use cases 并不是描述最终用户的行为，它不是 user story 或者类似的东西，**对于 entity 来说，并不需要知道 use cases 是如何控制他们的。**

很多时候在 Java 世界，我们会用 @Entity 的 annotation 标志某个 POJO model，这样 DAO 或者 Repository 就会贴心的将其映射到数据库的某张表中，请一定要在这种时候保证这个 Model 是 POJO，因为我们不希望 entity 也知道这些数据库是什么，或者是哪种 ORM 在操作他们。所以如果你想让自己的代码灵活易改，尽量保证使用纯 Java 的能力去构建，写 POJO 就是一个很好的实践（当然有时候也不好用，要不然 lombok 就不会那么火）。

```java
@Entity
public class Player {

    @Id
    @Type(type = "pg-uuid")
    private UUID id;

    private String name;
    
    ...
    
    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }
    
    ...
```

在上面的例子中，虽然 Player 带着大量的 JPA annotation，但是其依旧是 POJO，如果在将来不使用 JPA 来处理持久化，改成别的存储技术也非常的简单。

在我们编写 Controller 这种面向输入输出的功能时，我们往往会对输入建模，并进行 validate，再使用内部的 Service 去完成业务，我们不会把 HttpRequest 传递给 service，也不会把 HttpResponse 从 service 中返回。对于内部的 service（也是 higher-level），不应该知道外部的细节，今天是 HTTP 与 SOAP，明天可能是 JSON 或者从中间件中 poll 数据出来，这都是有可能的，这也都不是修改内部 service 的借口。

### Main 组件与测试边界

**Main component 是整个系统中最低级的 policy**，是程序的起点与入口，往往 Main 组件（或者 main 函数或者其他有类似功能的东西）用来做依赖注入，进行其他组件之间的组合，将他们一个个 new 出来。我们会经常让面试 Java 后端的同学考虑一下，如果没有 Spring 你该如何把注入的事情搞定，或者你应该如何实现一个 IoC 容器。很多的答案都是模糊的回答，我会使用反射或者其他动态技术，但是其实我们只想让你表达一下在没有框架帮你完成注入的时候，你应该怎么组织和处理依赖。

```java
public class SomeRequestHandler implements RequestHandler<KinesisEvent, Void> {
    ...

    @Override
    public Void handleRequest(final KinesisEvent input, final Context context) {
        ThreadContext.put(AWS_REQUEST_ID_KEY, context.getAwsRequestId());
        final SomeEventHandler handler = new SomeEventHandlerImpl(
                this.initDBConnectionProvider(),
                this.initEventConverter(),
                this.initEventProcessor(),
                this.initDeadLetterSQSClientSupplier(),
                new EventLoggerImpl());

        handler.handle(input);

        return null;
    }

    private DBConnectionProvider initDBConnectionProvider() {
        ...
        return new DBConnectionProviderImpl(credentialProvider);
    }

    private EventConverter initEventConverter() {
        final ObjectReader objectReader = new ObjectMapper().readerFor(EventModel.class);
        return new EventConverterImpl(objectReader);
    }

    private EventHandlerMapper initEventProcessor() {
        final EventTypeHandler sample1EventHandler = new CreateEventTypeHandlerImpl(new InsertOperationImpl());
        final EventTypeHandler sample2EventHandler = new UpdateEventTypeHandlerImpl(new UpdateOperationImpl());
        ...
        return new EventHandlerMapperImpl(sample1EventHandler, sample2EventHandler...);
    }

    private Supplier<SQSClient> initDeadLetterSQSClientSupplier() {
        return () -> new SQSClientImpl(AmazonSQSClientBuilder.defaultClient(), System.getenv(DEAD_QUEUE_ENDPOINT_KEY));
    }

}
```

SomeRequestHandler 就是一个 Main Component，它将我们的 Handler 创建了出来，自然在创建的过程中处理完了依赖，也完成了配置读取等。虽然是手动的处理了依赖（毕竟这些对象都是一个个 new 出来的，但是考虑到程序的规模，这个 Main Component 是可以接受的，实际上除去 import 后只有 40 行的有效代码。我们为什么不用 Spring 或者其他框架来做这件事，是因为这段代码需要跑在 AWS Lambda 上，这种轻量的，有明确输入输出的运行环境，再往里面装一个 Spring 这不是有毛病吗？

下一个问题是，如果这段代码是跑在 AWS Lambda 这种 serverless 平台上，那本地一定就很难运行起来了，即使 AWS Lambda 给了你很好的在线调试的工具，但是也无法和本地开发的效率相提并论，对于工程师来说，写完一段代码只要点击一个按钮或者一个快捷键组合后就能跑起来进行调试的诱惑是很大的，所以我们又写了一个 Test.java 用来支持本地环境，其中 initDBConnectionProvider() 方法自然返回的是一个 H2 db（你也可以用 docker 本地起一个 MySQL），initDeadLetterSQSClientSupplier() 返回的则是一个 fake SQSClient 实现，自然，在 Test.java 中，程序的入口就是经典的 java main 函数了，然后你就可以命令行输入等来进行测试。

我们之前提到，良好的架构设计需要满足的是非功能性需求，其中就包括系统的可测试性，之前这个例子的测试性是非常好的，单元测试在开发完成后立刻就可以启动，当单元测试全部通过后，功能测试可以通过 Test.java 启动，我们甚至在本地还可以使用 docker 启动一个空的数据库，再加一点 gradle task 将功能测试完全自动化，但是，我们清楚的知道，在本地环境中是无法有一个货真价实的 AWS SQS 让你使用的，那么边界就可以画在这里，因为无法等价替换掉这个东西。

作者也提倡说，不要将测试依赖在不稳定的东西上，我也是深有体会的，比如极度不稳定的基于 GUI 的自动化测试，特别是 web 前端的自动化测试。我们曾经使用过很多 headless 框架去做一些简单的测试，效果都不好，特别是有个框架叫做 nightmare，对我们来说真是无尽的 nightmare。这里就不细致吐槽了，核心点是如果是我下次遇见这种情况，我会把测试边界画在 GUI 之后。
