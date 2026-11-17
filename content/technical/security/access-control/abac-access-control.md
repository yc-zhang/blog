## 引言

### 引言

在一个典型的软件开发场景中，你作为一名开发人员加入到某个项目后，假设是“超人组”，你往往需要访问这个项目的代码库然后才能开始工作。当你的 Team Lead 将你加入 Git Organization 后，你自然可以访问到“超人组”的代码仓库，然后就可以愉快的进行开发工作了。但是，当你的任务完成后，可能你需要参与另一个项目，你自然就没有权利去访问“超人组”的代码库，所以你的 TL 会将你移出。这是一个典型的访问控制场景，我们所控制的**对象是工程师，资源则是代码仓库**。

对于软件工程师来说，类似的场景十分常见，可以说任何一个系统都存在访问控制机制，从操作系统到复杂的云上应用，我们也发明了很多名词、技术来实现类似的功能，但是核心都是为了控制人或者其他对象，能否访问资源。

> Access Control Mechanism (ACM): The logical component that serves to receive the access request from the subject, to decide, and to enforce the access decision.

### RBAC 的缺憾

对于访问控制模型，大家最熟悉、或者实现最多的就是 RBAC Role Based Access Control，我们通过赋予不同 role 的不同权限来进行访问控制。对于一个主体（往往是组织内的人员或者某个客户端），他可以拥有多个 role 以应对多种不同的操作权限。**RBAC 的流行很重要很大程度上是贴近现实生活，方便大家理解与使用**，例如老王是销售经理，同时也是技术委员会的成员，我们很自然就给他两个 role：Sales Manager 与 Technology Group Member，而这两个 role 对应的权限也很清晰明确，Sales Manager 可以查看所有的销售数据，并进行修改等，而 Technology Group Member 只能查看技术上的文献，不论是在系统设计还是在运营时，这些名词都与我们的 title 相对应，**对于管理人员来说，只是修改不同的 role 对应的权限而已。** 当老王专心去做技术研究之后，我们就移除他的 Sales Manager Role，这样他就无法访问销售上的数据了。

![老王失去了 Sales Manager 的 role 后，就无法继续访问销售数据了](https://upload-images.jianshu.io/upload_images/3819274-a359836df3b0df7b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

RBAC 在很多时候是管用的，比如我们的系统是面向销售公司或者学校这种组织架构很严整的地方，但是在复杂场景下，RBAC 渐渐就不够用了，它会产生很多虚无的 role 而且在管理和控制上更难：在某个医疗机构中，我们想要控制一个科室内，护士只能访问自己所负责的病人资料时，我们就无法直接使用 nurse 这个 role，我们需要更细粒度的 role 去划分病人老张还是老王，这就会产生和现实不对应的 role，例如：老张的护士，老王的护士。在医院这种病人流动性很大的场景下，频繁的创建和销毁 role 是很容易出问题，我们的确要求很频繁，但是与现实不 match 的虚无的 role 很难管理。

另一种情况是，如果管理者考虑医疗数据的安全性与隐私性，不希望护士在离开医院后能够访问到病人资料，我们会更加难办，常见的策略要么是在底层网络层进行处理，直接禁止在院外的一切访问，但是很多企业的需求往往是，使用 VPN 我依旧可以访问内部的资源，但是我还是希望基于所在地进行精确的控制，比如看邮件是可以的，但是看财务数据是不行的。在 RBAC 下，我们也可以通过虚拟的 role 来控制，比如下班后给与其 Out of Office 的 role，然后给与这个 role 最小的权限，这自然又需要虚拟的 role 与大量的动态控制。

![给在办公室外的同事创建了与职位不对称的 role](https://upload-images.jianshu.io/upload_images/3819274-dee3d2d5c056b1ea.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

> 一般来说，在 RBAC 中滥用 role 所带来的问题被称为 “role explosion”，跟“曹操”与“曹操小时候”这个笑话很类似，但的确我们的访问控制系统中存在很多这样的 role。

## ABAC

### 介绍

所以，直觉上来说我们需要更多的“东西”来进行更精细的访问控制，用来匹配我们复杂的业务场景，同时，我们也希望这个新的模型易于理解和实现，也利于控制与运维，这就是 ABAC —— 基于属性的访问控制 (Attribute Based Access Control) —— 想要解决的问题。简单来说，对于 ABAC 我们判断一个用户是否能访问某项资源，是对其很多不同属性的计算而得到的。

**传统的 RBAC 与 ACL 等访问控制机制中，可以认为是 ABAC 的子集，对于 RBAC，只是我们的访问机制的实现只是基于属性 role 而已，ACL 则是基于属性是 identity 的 AC。**

### 术语

要理解 ABAC 首先需要从一些领域内的术语说起，按照我个人的习惯，对于专业性的术语一向是不翻译的，因为的确是受够了每次讨论授权、认证、验权、验证等区别，虽然技术讨论时彼此都理解要说的是什么，但是在场景中这是需要独一无二的、易于理解的名字的（此处插入 DDD 的通用语言），此外还有一个好处就是好写代码，正确的名字可以帮助你的代码易于理解和维护。

**Attribute**：属性，用于表示 subject、object 或者 environment conditions 的特点，attribute 使用 key-value 的形式来存储这些信息，比如我在公司的 role 是 developer，role 是 key，developer 是 value，而我的小组昵称袋熊，key 是 team，value 是 wombat。

**Subject**：常常指代使用系统的人或者其他使用者（non-person entity，NPE），比如说客户端程序，访问 API 的 client 或者移动设备等等。当然一个 subject 可以有多个的 attributes，就像用户属性这些我们曾经用过的名词一样。

**Object**：指代我们这个 ACM 需要管理的资源，比如文件，比如某项记录，比如某台机器或者某个网站，任何你需要进行访问控制的资源都可以称为 object，**同样 object 也可以有多项属性，比如袋熊组的桌子，或者洛克组的线上实例**，我们也常常使用 resource 来描述这些资源，但是在 ABAC 的环境下，我们称为 object。

**Operation**：有了 object 有了 subject，自然就有了 subject 需要做的事情，比如查看某条记录，登录某台服务器，使用某个 SaaS 服务进行报销或者查看候选人的作业。往往包括我们常说的读、写、修改、拷贝等等，**一般 operation 是会表达在 request 中的，比如 HTTP method。**

**Policy**：通过 subject、object 的 attribute 与 environment conditions 一起来判断 subject 的请求是否能够允许的关系表示，**比如说：policy 可以用人类语言这样表达，只有袋熊组的人才能访问这几台服务器，或者只有在办公室才能访问这些资源，但对于机器来说，无非就是一个判断语句罢了**。当然了，policy 可以是一堆这样 boolean 逻辑判断的组合，比如只有公司的正式员工、并且在公司的六楼区域的网络中，才能访问某个服务。你可以使用 [Specification Pattern](https://en.wikipedia.org/wiki/Specification_pattern) 来实现 policy，其实没那么复杂。

**Environment Conditions**：表示目前进行的访问请求发生时，的操作或情境的上下文。Environment conditions 常常用来描述环境特征，是独立于 subject 与 object 的，常用来描述系统的情况：比如时间，当前的安全等级，生产环境还是测试环境等等。

### 基本场景与概念

一个典型的 ABAC 场景描述如下图，当 subject 需要去读取某一条记录时，我们的访问控制机制在请求发起后遍开始运作，该机制需要计算，来自 policy 中记录的规则，subject 的 attribute，object 的 attribute 以及 environment conditions，而最后会产生一个是否允许读取的结果。

![From NIST 800-162: Basic ABAC Scenario](https://upload-images.jianshu.io/upload_images/3819274-5fd4b58622ad8a25.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

1. 尝试访问
2. ACM 进行计算：subject attributes + object attributes + environment conditions = allow or deny?
3. 进行访问

在 NIST 的描述中，我们对 ACM 内部进行进一步的抽象，可以得出这两个核心模块：Policy Decision Point (PDP) 与 Policy Enforcement Point (PEP)，如下图：

![PDP + PEP](https://upload-images.jianshu.io/upload_images/3819274-d5429723f54c5cf9.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

所以，实现 ABAC 的核心机制是在请求发起后，subject attributes、object attributes 与 environment conditions 作为输入，PDP 根据 PEP 的数据去获取 policy 与环境条件，再进行计算，最后确定是否有权进行请求。ABAC 的逻辑并不复杂，根据之前我们所画的基本场景与机制的图中，你可以很轻松的开始进行架构设计，往往最开始你需要定义出 subject、object 以及其相关的 attribute，同时你也需要思考，当去进行 object 访问时，你该如何表达 request 以及 operation。

![From NIST 800-162: An Example of ACM Functional Points](https://upload-images.jianshu.io/upload_images/3819274-036be3b114f42cb1.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

RESTful 是我们常用的设计风格，RESTful 的流行是与 HTTP 协议密不可分的，其中我们很看重 HTTP 协议中的 methods，并且赋予了这些 methods 易于理解的语义，我们会很自然的认为 GET 是获取资源，而 POST 是创建新的资源，PUT 则是修改，使用这些 methods 是与控制资源联系在一起。但是，在 HTTP 协议中，并没有规定 GET 是否可以进行资源上的修改和更新，因为这只是个传输协议罢了，是我们在这个协议之上发明了新的东西，所以也没有“官方的、标准的” RESTful。之所以在这里提到 RESTful 与 HTTP 的关系，是想让大家理解在进行 ABAC 系统设计时，operation 是可以有很多种表达的，而重要的是定义这些 operation 与 request 的关系，你可以使用 SOAP 或者其他协议，或者在 RESTful 之上自己发明一些字段，或者加入进 HTTP header，但是一定需要有清楚的 operation 描述。

### 为什么 ABAC 能解决复杂场景下的问题

在学习 ABAC 的过程中我发现，ABAC 和很多创新一样，并不是因为科技的突破性进展，而只是在 RBAC 的思维上前进了一点，理解 ABAC 的术语时，你能很快的联想到已有的技术实践，比如 AWS IAM。而且，这些术语也如同我们做面向对象编程时，是很好的描述现实的。

#### Attribute 易于管理

我们可以很容易的为不同的用户设计 attribute，往往在很多企业的实现中存在一个 consumer profile 或者 user details 的服务，这些服务中很多字段比如职位、职级、办公室、项目等就是天然的 attribute，对于需要管理的 object，如果是一台虚拟机，那么 IP 地址、归属组织、cost code 等都可以是 attribute，而且因为 attribute 是 K-V 式的，往往一张一对多的表就可以控制好 subject、object 与 attribute 的对应。

#### 细粒度授权支持

ABAC 能做到细粒度的授权管理，我们知道，在 policy 中，我们的准许访问的判断是可以写的很灵活的，我们甚至可以判断请求中的某个属性是否满足于一个正则表达式，或者字符串相等（这个很常见，特别是在使用 AWS IAM 做最小权限原则时），我们也可以使用逻辑与、逻辑或的关系自由组合很多不同的访问规则。**你可以使用之前提到的 Specification Pattern 很轻松的实现灵活的 policy，解析 JSON 或者 XML 去动态的创建规则，而这些含有规则的 JSON 或 XML，则是可以被编程实现的（可编程的 policy 是动态的授权验权的前提）**。你的 policy 甚至可以做到，只有姓张的工程师在某个项目时才能访问某个资源，在 RBAC 的时代，这是很难的。

#### 访问控制管理成本很低

ABAC 对系统管理员是友好的，在 RBAC 的时代，如果我需要实现细粒度的资源管理或者经常 subject 与 object 的对应关系经常变动，那么管理员难以操作的，也很容易出现问题，其中常常被采用的解决方案就是创建那些本不应该存在的 role。但是在 ABAC 时代，管理员的管理对象会缩减到 policy，也就是只处理访问控制。我们再回到医疗机构的那个例子中，如果某个护士负责照顾老张，系统管理员只需要新建一个 policy 并写上允许访问即可，当老张出院后，**只需要删除或者失效这个 policy 就可以了**。在 RBAC 的环境中，你可能需要为某个虚拟的 role 动态的添加 permission，而 permission 如果到了针对单个病人的情况下，是绝对多如牛毛的，特别是有两个叫做老张的病人时。

往往，我们会使用 JSON 或者 XML 定义这个 policy，那么，这一切都可以完全自动化，而不需要使用管理员点击。再现实一些的话，我们可以完全实现一个审批的流程，如果你使用过 Google Drive，你会对这个请求访问的过程绝不陌生。

![Require Access](https://upload-images.jianshu.io/upload_images/3819274-0a8fc7af2935bfde.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

#### 动态的总体控制

Environment conditions 也能够提供统一的系统级别的控制，比如威胁等级或者按照区域划分安全级别，不同的区域使用 ABAC 时，可能环境上会有变化。例如我们常用红区来表示最高安全级别，那么我们默认就需要 deny 所有请求，并且会触发警报等等，但是在绿区这种办公区域，可能默认所有的请求都是被允许的等等。**Environment conditions 可以提供“拉闸”这样的功能**，而且它也是可以动态调整的。

## ABAC 在落地上的一些经验和故事

### AWS IAM

如果谁能作为 ABAC 比较好的实现榜样的话，我第一个想起的就是 AWS IAM 的实现。如果当你的企业正在使用公有云时，对公有云的资源进行控制是非常难以管理的，你当然可以为每个小组安排好虚拟机或者 RDS 之类的，但是这太静态了，而且也不足以细粒度。比如，当我们想实现最小权限原则时就很难办到（例如你的数据库只想被你确定的几台实例所访问到），往往这种需求会实现为，在某个网段内，大家都可以访问到某个数据库或者中间件，那自然是不够理想的。

公有云的资源是租用的，你可以按照自己的需求动态的扩容或者降低你的资源，那么这种场景下，资源是动态的，而且变化很大（可能会根据流量动态的启动实例或者关闭），那在这种情况下如何做到访问控制与最小权限原则，那你就不能再基于 users 与 roles 进行操作，这时候你就需要 ABAC。好消息是，AWS 作为云计算的领导者，很早就实现了类似的功能，而使用 IAM 则是 operations 的必修课。

请参考这个视频，来自 AWS Senior Manager，[个人认为是讲的最好的 IAM 与 ABAC 介绍](https://www.youtube.com/watch?v=Iq_hDc385t4&t=2378s)。

### 一些实践经验

最开始实践 ABAC 是因为我们在进行一个内部云的资源控制项目，在设计时我们参考了 AWS 的玩法，并进行了类似的设计。实际上 ABAC 是与你要管理的资源无关的，更像是一种模式，在云资源控制中大多数 subject 不是用户或者真正的人，而是客户端、实例机器等。实现一个类似 policy 的策略管理并不是很难，主要的工作在管理端的开发以及为客户端提供 SDK 上了，此外还有集成策略。我们也考虑过 XACML & NGAC (Next Generation Access Control) 去描述 policy 或者直接使用，但 XACML 过于复杂以及并不成熟，最后还是采取了自研的策略。故事这里是很多的，但是篇幅有限不予展开。

## 总结

ABAC 在概念上的设计的确是有先进性的，对于有 RBAC 知识的人，ABAC 不难理解，也就是“基于用户属性进行访问权限判断”，但是当我去阅读 NIST 的文章或者参考 XACML 实现时，却担心 ABAC 的复杂实现，毕竟 NIST 给与的企业级实现考虑的长度占文章的一半。**对于 ABAC 的概念，这并不是复杂度的来源，而是授权这件事本身的复杂性，对于系统的设计者与管理者来说，一旦需要关注细粒度的授权管理，那么复杂是无法避免的。**

**微服务的流行与 ABAC 的配合值得写另一篇文章，特别是分布式身份验证之后，怎么做到分布式的授权与验权，怎么实现 PEP、PDP 等 ABAC 提倡的模块设计，这些东西可否做成应用程序透明的方式，可否与 security sidecar 集成等等，这些都是可以进一步完善的。**

业务人员希望有一种业务语言能够描述授权策略，但是 gap 在于技术人员无法理解与实现，对于 ABAC 这种授权模式中，我们需要的是一位能够同时说业务与技术两种语言的人，将真正的业务需要转为技术语言，从而指导落地。

## 参考文献

- [NIST (美国国家标准技术研究所) 的 ABAC 的定义与实现考虑，最重要的资料](https://nvlpubs.nist.gov/nistpubs/specialpublications/NIST.SP.800-162.pdf)
- [AWS IAM ABAC 介绍](https://www.youtube.com/watch?v=Iq_hDc385t4&t=2378s)
- [Specification Pattern](https://en.wikipedia.org/wiki/Specification_pattern)
- [ABAC 与 XACML 复杂性讨论](https://www.linkedin.com/pulse/abac-xacml-where-does-complexity-come-from-borja-roux-lorenzo/)
- [Yet Another Authorization Language](https://github.com/bolilla/yaal)
- [XACML](https://en.wikipedia.org/wiki/XACML)
- [Next Generation Access Controls NGAC](https://www.slideshare.net/TranscendentGroup/next-generation-access-controls)
