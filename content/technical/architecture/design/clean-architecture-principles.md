### 《Clean Architecture》 是一本什么样的书？

废话之前先写结论，如果你有一个类似于架构师、技术负责人这种头衔，或者你是一个很优秀的工程师，想进行一些架构方面的学习，那么这本书是一定要认真看，建议看英文版，单词不难，很好理解。

![Clean Architecture](https://upload-images.jianshu.io/upload_images/3819274-df29b5214879682b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

《Clean Architecture》是《Clean Code》的姊妹篇，或者说是迟到的姊妹篇，作者 Robert.C.Martin 与其称号 Uncle Bob 想必不用介绍了，在“软件工程”领域，Uncle Bob 与 Kent Beck，Martin Flower 这些大佬一样，都是干货满满一生都在贡献的人。几年前我曾经读过《Clean Code》，至今都难以忘记这本书对我开发生涯的帮助，在不断的成长中，发现自己忍受不了所谓的垃圾代码了，我们应该追求更好的，更干净的代码。那么，除了写代码，在架构设计上有没有所谓的清晰架构呢？回首就发现了这本出了没多久的《Clean Architecture》。

```java
private static void preCondition() {
    String totalPrice = "";
    String[] products = null;
    double unitPrice = 0.0;
    int sumProducts = 0;
    String productName = "";
    Product product = null;
    for (String condition : PRODUCT_PRICE_CONDITION) {
        product = new Product();
        totalPrice = condition.split(" is ")[1].split(" ")[0].trim();
        products = condition.split(" is ")[0].split(" ");
        try {
            sumProducts = Cart.getTotalProducts(products);
        } catch (RomanException e) {
            System.err.println(e.getMessage());
        } catch (Exception e) {
            System.err.println(e.getMessage());
        }
...
        PRODUCT_UNIT_PRICE.put(productName, product);
    }
}
```

*如果你还在写上面这种不太理想的代码，非常建议认真读读《Clean Code》，以及《Effective Java》，并且进行大量的练习。*

**严格意义上来说，架构或者“Architecture”是不存在所谓的标准定义的**，我们有很多经验上的说法，比如软件架构这种词语常常描述软件的组成结构，经常有人会用建筑学的术语来类比，房屋的结构与软件架构是类似的，但是使用房屋的人会根据自己的要求是作为店铺还是住房，类似的软件的功能，往往不是架构决定的。**架构在很多时候影响的是非功能性需求。**想象一下你在大学毕业时编写的毕业设计程序，很垃圾，处处充满了不合理的设计，过度的耦合，不正确的抽象，模块之间没有清晰的边界，但是**它工作了**，它并不需要像一台家用汽车一样能开十万公里，它只需要让你毕业。

软件的特点与优势就是易于改变，易于改变也自然的成为了非功能性需求，我们希望更快的，更安全的响应需求变化，根据业务反馈调整系统，“最好今天就能上线”，这是业务人员想要的；同时我们希望软件易于理解，适合开发与测试，这是每个工程师想要的，方便测试能让你有信心进行每日部署，那么可部署性也是我们希望考虑的；我们还想能够简单方便的加入新功能，我们想降低耦合；我们想要更好的性能，我们也希望能够实现弹性以便适应横向扩展，所以也许会考虑无状态，这些都是在架构设计时，我们希望能够满足的非功能性需求。

所以《Clean Architecture》是 Uncle Bob 使用自己的经验来告诉我们在架构设计时，需要怎么思考，我们应该如何使用框架、数据库、语言特性、编程范式这些跟我们日常打交道的朋友，我们应该怎么去做架构设计。**整本书中没有任何新的知识，没有新的编程语言，没有新的应用架构模式，毕竟这里老叔不是教我们写代码的。**

那么有人肯定会说啦，羽辰你没有能跟大神比肩的知识与经验，也没写过著名的开源项目，你也谈架构有没有B数啊，我只能说，我没有！但是还是想总结与分享一下自己的学习心得，顺便联系下本人浅薄的经验与故事，那么，这篇系列博客大约是这样考虑的：
- Principles：引子，重新回顾下我们常用的代码级准则。
- Architecture：开始探讨 Uncle Bob 提出的清晰架构的知识点，业务与实现，high-level policy 与 low-level details。
- Details：我们该如何使用框架、数据库、技术选型，在架构设计时我们如何让自己避免陷入 details。
- Examples：通过具体实践故事来描述架构设计时的坑与心得，包括：keeps the options open, low-level details, main component 与 microservice。
- Know your system：我们如果描述和理解系统，如何避免画那种色块式的架构图，如何做一个合格的 box drawer。

### OO & 函数式

Uncle Bob 在书中分析了三种常见的编程范式（Programming Paradigm），结构式、面向对象与函数式，对于每种范式也给与了详细的解释，但是最出人意料的是最后的结论，比如对 OO 的描述中，Uncle Bob 并不认为封装、多态、继承（如果你用过 JS 这种“没有” class 的语言，在早期，**人们也是通过几种办法实现了继承，可以参考我写的 JS 语言特性的文章**）是 OO 的专利，但是 OO 最大的便利是多态，我们可以利用多态（Polymorphism）对系统中的每个对象进行绝对的控制，想想 Spring Boot 我们是怎么用的，完全的面向接口编程，业务逻辑的代码是不会在乎注入的对象到底是什么，这些则是 OO 带来的好处，**就像 plugin 式的组合一样，根据配置或者 @Autowire，我们可以灵活的选择具体干活的是哪个 bean。**

```java
@Autowired
public ParkingListController(ParkingService parkingService,
                             @Qualifier("parkingViewModelConverter")
                             Function<Collection, CollectionViewModel> viewModelConverter,
                             DefaultParkingService defaultParkingService) {
    this.parkingService = parkingService;
    this.converter = viewModelConverter;
    this.defaultParkingService = defaultParkingService;
}
```
*通过 @Qualifier 指定注入不同的 converter，这样的好处是在注入的时候你可以控制 bean，在 mock 的时候，你可以直接使用 lambda，因为 Controller 不需要知道 Converter 的实现。*

函数式编程近年来火热，不可变所带来的安全性，使用流式的过程描述，尾递归、纯函数、高阶函数、一等公民这些东西的确让喜欢的人爱不释手，你完全可以使用函数式与杀手级框架做出稳定、强大、现代的应用，比如 Scala 与 Akka。我自己也非常的喜欢以至于不能忍受没有类似于 λ 功能的编程语。我也会在 Java 面试中问类似的问题，最狡猾的一个问题是，**Optional.flatMap() 的返回值是什么类型？为什么一定要返回 Optional，这个方法签名的设计是遵循了什么？**

```scala
for {
  account <- dao.getAccountByEmail(email).okOrElse(EmailInvalid)
  _ <- Option(account).filter(authenticated(password, _)).okOrElse(PasswordInvalid)
  email <- account.email.okOrElse(ErrorCode.UnknownError)
  passwordHash = retrieveHashedPassword(account)
  activated = dao.isActivated(account.uid)
  _ = dao.updateLastUsedTimestamp(account.uid)
  _ = logger.info(message("login.success", account.uid))
} yield createLoginReceipt(...)
```
*这一段 Scala 代码使用 for 推导式来组织业务逻辑，就算是你不懂 scala，这些方法调用你也能搞清楚，这是先读取数据库，然后再做了某项事情。*

回到自己的经验中来，大处 OO 小处函数式也许是目前最适合我的选择，OO 天然的描述性能帮助我们进行系统设计与建模，is-a 也许是世界上最方便的描述方法了，毕竟每个人开始学习 OO 时都是对现实世界进行抽象。函数式会让每个方法变的简单安全，可以通过强大的 for 推导式或者 stream 编排稳定的业务设计，并且由于不可变与无副作用，函数式的代码非常好测试，在 mock 时写一个 λ 就搞定了。即使是使用 Java 语言开发，我也将 Service 这种类定义成 @FunctionalInterface，因为实在是太好用了。

```java
@FunctionalInterface
public interface OrderService {
    Page<Order> listAll(String clientId, Pageable pageable);
}
```
*上面这个例子中 @FunctionalInterface 能让你使用 BiFunction 来模拟这个 OrderService，对于其他使用 OrderService 的类，BiFunction<String, Pageable, Page<Order>> 是一样的。*

```java
new ParkingListController(
    (a, b) -> page, 
    c -> c == parkingLot ? viewModel : null,
    clientId -> Optional.empty())
```
*所以我们在测试中可以直接使用 λ，它会不断的提醒你，Controller 的行为是和内部的 service、converter 实现细节无关。*

```java
public static <T> void assertViolationType(Set<ConstraintViolation<T>> violations, String field, Class c) {
    assertTrue(violations.stream().filter(v -> v.getPropertyPath().iterator().next().getName().equals(field))
            .anyMatch(v -> v.getConstraintDescriptor().getAnnotation().annotationType().equals(c)));
}

public static <T> void assertNoViolation(Set<ConstraintViolation<T>> violations, String... fields) {
    List<String> fieldList = Arrays.asList(fields);
    assertTrue(violations.stream().noneMatch(v -> fieldList.contains(v.getPropertyPath()
            .iterator()
            .next().getName())));
}
```
*stream 完全可以替代循环，帮助我们专心干业务上的事，我们就可以不用思考 index、中间件变量、结果导出等等这些细节。*


### 设计准则 & 组件准则

这一部分 Uncle Bob 回顾了一下《Clean Code》中非常重要的部分——SOLID。这里笔者就不一一列举，这五个准则可以说是 OO 中最重要的设计规范了，我们在这里重申 SOLID 是为了让架构实践有更稳定的基础，毕竟我们一直希望软件易于改变，易于复用，这些准则如下：

**Single Responsiblity Principle (SRP) 单一职责准则**：每个软件模块，只能有一个原因导致变更，而不是说每个模块只负责一个事务，这是很容易误导的地方。该准则强调的是内聚，即把面向类似业务的代码放在一起，在项目中你不会把跟数据库操作相关的事务放在两个类中，我们经常会把 connect、disconnect、query 这种方法放在一个 DAO 中，比如叫做 DatabaseOperator，那么只有在我们与 DB 有新的需求时（比如加入 timeout 或者支持设置隔离级别）我们才会去改变它，而我们不会因为新加入的 SQL 语句来改变 Operator 内部的实现，因为没有必要，这就是内聚，也就是作者提到的该类只为一个 Actor 负责。

**Open-Closed Principle (OCP) 开闭准则**：相信很多人都听过，对于软件模块也好、类也好，都应该遵循面对扩展开发，对修改关闭。开闭准则是为了让系统在避免大量的修改而做好扩展，在 Java 世界中，尽量避免去 Override 已有的方法逻辑，采用不同的实现是更好的选择，比如 EmailSender 与 SMSSender 可能都继承自 Sender 这个抽象类（或者实现接口），而不是 SMSSender 去继承 EmailSender 去覆盖其中的 Sender 方法。开闭准则也可以很好的保护实现，比如使用 Sender 的类是不需要知道是如何发送消息的，这些细节被隐藏了。

**Liskov Substitution Principle (LSP) 里式替换准则**：子类应该能够替换其父类，否则就不能把其设置为子类。一言简之，如果你在使用 instanceOf 来判断某个类具体是其子类的时，**那么基本上就违背了 LSP，大多数情况下你使用 instanceOf 判断类型，然后必然跟进针对某种类型的特殊操作，这是非常危险的耦合。**

你可以这样判断是否自己违背了 LSP：
- 每当对象被继承时，询问它是否满足“可替换”的关系。
- 检查对象的类型，并根据该类型有条件地执行某些操作，这个很常见，只要有 instanceOf 就会有这样的问题，如下：

```java
public void move(Vehicle vehicle){
    
    // violates LSP
    if(vehicle instanceof ManualVehicle){
        //shift gear
    }

...
}
```
- 实现接口时抛出 NotImplementedException，也违背了 LSP。遗憾的是这样的危险代码很常见，即使是很多有名的库中。
```java
class AutomaticVehicle implements Vehicle {
    
    public void shiftGear(){
        throw new NotImplementedException();
    }
...
}
```

**Interface Segregation Principle (ISP) 接口隔离准则**：该准则鼓励我们避免依赖在不需要的接口上，鼓励我们使用小接口代替大而全的接口，特别是在 Java 语言中，一个类是可以实现多接口的，所以你可以根据需要去进行实现。

```java
public interface ApplicationContext extends EnvironmentCapable, ListableBeanFactory, HierarchicalBeanFactory,
		MessageSource, ApplicationEventPublisher, ResourcePatternResolver {
```
*Spring 的 ApplicationContext 是一个特别有意思的例子，首先它是一个接口，但是它聚合了很多小接口比如 EnvironmentCapable, MessageSource，这些小接口是互相隔离的，但是 ApplicationContext 的实现类却必须实现这些小接口，ApplicationContext 是接口的聚合。*

**Dependency Inversion Principle (DIP) 依赖翻转准则**：该准则告诉我们，灵活多变的系统应该依赖于抽象而不是实现。我认为 Uncle Bob 这一句话说的很好，像静态语言比如 Java，use、import、include 等这种语言应该 refer 到接口、抽象类这种表示抽象的东西，而不是具体的某个实现。面向接口编程，也就是面向抽象编程，你不需要知道 Sender 怎么发送邮件，也不需要知道 DAO 怎么去处理数据库的事情，业务就是负责业务，而让他们负责具体的细节（也就是 Uncle Bob 常说的 Details）。那么注入是怎么一回事呢？

假设你的文本编辑器需要某个拼写检查的功能，大约是这个样子：
```java
public class TextEditor {

    private SpellChecker checker;

    public TextEditor() {
        this.checker = new SpellChecker();
    }
}
```

这时候，SpellChecker 与 TextEditor 已经存在依赖关系了，TextEditor 直接依赖了 SpellChecker。**本来控制代码依赖是由外向内的，但是 TextEditor 却控制了 SpellChecker，这个依赖方向是反的，所以被称为 Inversion of Control，IoC**。那么，如果你需要检查的是中文或者德语，你必须要修改 TextEditor 中的 SpellChecker 为 ChineseSpellChecker 或者 GermanSpellChecker，这就是我们不想看到的。所以，我们会有大约是这样的代码解决这个问题：

```java
public class TextEditor {

    private IocSpellChecker checker;

    public TextEditor(IocSpellChecker checker) {
        this.checker = checker;
    }
}
```
这就是我们常说的注入了，通过注入 IocSpellChecker 的不同实现，实现不同的拼写检查，而不是由 TextEditor 这个类来控制需要哪种实现。

而组件准则中，作者提出的 The Reuse/Reluse Equivalence Principle、The Common Closure Principle 与 The Common Reuse Principle 与 SOLID 很类似，甚至通用闭包准确（CCP）可以认为是 SRP 的组件版，这里就不浪费口水了。如果你所开发的产品是按照组件的形式发布，那你需要认真的读一下这几章，并且认真思考你的接口是否定义正确，组件是需要进行很好的向后兼容设计。
