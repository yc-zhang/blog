请参看 https://12factor.net/ ，记录我的一些解读和实践故事。

### 我的前言
在微服务如此流行的今日，我们大量的使用独立责任的微服务来完成我们的业务逻辑以及基础设施，组织架构由大组向两个披萨饼团队转换，由单一的 monolithic 应用转向由微服务组成的网，使用更多的工具帮助我们完成 CI/CD 来确保时时发布，使用 Docker 等来帮助我们整理维护开发与部署环境等等。这一切都是为了适应产品的快速变动以及释放工程师的生产能力。

这篇 The Twelve-Factor App 很好的描述了在构建 microservice 日常中的情景，在更高的层级上描述了我们该如何建设 microservice。请一定不要进行以下的断言：微服务等于 docker 化，或是就是拆分成小服务罢了。

Docker 不论是在日常开发中为我们提供了便利，也使得部署十分简单。image 为我们提供了标准化的部属单位，同时多个 image 所产生的容器可以完成复杂的任务。在我们的项目中，一个 instance 中可能有多个 containers 协作完成，但是往往只有一个 container 运行业务相关的应用，其他的可以提供 reverse proxy，log forwarder 以及 APM 性能监控等。

Docker 同时还为基础设施建设提供了便利，想象一下我们的城市，有医院、学校、工厂等等设施，里面的人们所做的工作就是我们的业务层的表述，医院只负责治疗病人就如同一个库存服务只负责管理库存，而不在乎商品入库是因为进货还是退货。而这些设施实体之间的关键却像网一样，而不是直线的数据流动。再可以联想一下，我们的城市污水系统、电力系统、公共交通等都是统一的，而所有的城市设施都是基于统一的基础设施之上的。

### I. Codebase
总体来说 12-Factory App 严格要求一个 app 一个 repo （对于 SVN 管理可能有些困难），但是会有多个用于 deploy 的 repo。但是在 dockerized app 的今日，我们的应用对于的一个 repo 并且产生一个相应的 docker image，而 deploy 的 repo 也是唯一的，只是在 CI 上的参数配置不同来区分不同的运行环境。对于本地运行环境可以在 code repo 中定义 docker-compose，特别是当 app 对其他系统有依赖的情况下，可以直接使用其他系统的 image 支持本地环境。

当然，deploy repo 尽量包含所有的参数，我们不想让 CI 上的命令、脚本（过于复杂的 CI Task 或者 pipeline 是十分危险的）等失去版本控制。也可以将 deploy repo 与 code repo 结合在一起（当你认为该 repo 没有开源必要的时候），特别是你使用了代码即是 CI 的集成工具后。但是中心是：分离部署环境，尽量让 CI 中的配置可被代码管理。

### II. Dependency
12-Factor App 希望我们显示的处理应用中的依赖，目前有大量的依赖管理工具可以帮助我们，bundle gradle sbt 等等。当然，这些工具可以帮助我们建立一个可运行的本地开发环境，你可以很方便的使用各种 IDE 去集成，并且在 IDE 中启动服务等。但是问题是，我们的服务也有其他依赖，并且我们希望本地能提供一种运行环境与线上环境相差无几，这时候就可以使用 docker-compose 这种工具。我们可以使用 volumn 挂载代码、缓存 packages，并且将单元测试运行、代码质量检测等全部放到 compose 容器中，同时，通过 compose 我们可以方便的进行 database，redis 等等依赖服务的集成。

在日常中，复杂的开发工作你可以使用 IDE 启动应用或者 debug，当然你有 database 依赖的时候，只需要使用 docker-compose 启动 database 即可。

12-Factory App 不希望我们依赖于底层的系统应用，比如 curl，wget 等，这一点是非常重要的。我们的解决办法是生产一个特别的 image 用于运行部署 task，这样 CI agent 只需要 docker 环境就可以了。

### III. Config
将所有的配置放在环境变量中！这一点非常重要，因为在不同环境下（local，stage，production），我们的代码都是一致的，而环境变量是最方便去修改并且不需要我们更新 app 代码。你也可以通过标记 `dev` `test` 或者 `prod` 来区分配置。

特别是在本地开发的环境中，灵活的修改环境变量可以方便的在不同环境中切换，例如集成测试时也许需要 stage 环境，只需要修改变量就行。

在 java 开发中，我经常使用 -D 的方式来加入 properties 用来本地测试，并且连接 docker-compose 启动的数据库。

当然你可以将 config 放在其他服务中，在此章节中核心点是使用环境变量在程序运行时 apply config。可以参考 [External Configuration Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/external-configuration-store) 来实现 external configuration。

### IV. Backing Services
我们的 app 经常依赖于上游与下游中各类的服务，database, queue, service 与 caching。在 12-Factory App 中，我们都需要将其视为同类的资源。在我们的 code repo 中我们不应该区别对待本地资源与三方服务，例如在 sidekid 中， 用于调度任务的 redis 也是通过存储在 config 中的 url 来访问的。

Docker 可以很方便的为我们做到这些，数据库、缓存等有丰富的 image 可供选择，对于三方服务，如果其为 dockerized 服务，只需要配置 image 即可。但是对于一些非 dockerized 服务，可以使用替代品用于本地测试，或者直接配置在 config 中。

### V. Build, Release, Run
我们经常混淆 build，release 以及 run 。在 12-Factor App 中，这三项是截然不同的，传统的做法是 build code，例如在 java 中，往往是将代码、依赖、资源生成 jar 包则认为是 build，而 release 则是将 config 加入其中，使其能够快速的投入使用。运行时则是选择版本，并且在运行环境中使用。

在开发 dockerized app 时，build 往往是指生成无配置的 image，并且使用版本号作为 tag，然后发布在 docker repository 中。而 release 则会制定不同的 config 作为环境变量输入其中，最后在运行前，由 CI 工具来确定在什么环境中应用哪些 config。

我们十分同意文中对于 build 和 run 的区别对待，build 中往往会做很多工作，例如 unit test，integration test，style check，coverage check 等等，让开发人员能尽早的发现问题。一旦 image 创建，只需要组织 config 并且这一部分并不需要人工干预。微服务的魅力就在于此，不是某周、某日发布新的应用，对于一个系统，任何时候内部的微服务都有可能在 release。当然，正因为如此，清晰的 contract 以及集成测试才是万分重要的。

 ### VI. Processes
> **Twelve-factor processes are stateless and [share-nothing](http://en.wikipedia.org/wiki/Shared_nothing_architecture).**

十分重要的观点，stateless 与 share nothing 是保证 app 可以被 scale up 的根本。所有需要被 persist 的数据都应该保存在数据库或者其他服务中。

避免使用 session，或者将 session 存放在 Memcached 与 Redis 中，我们需要避免在 processes 中传递 session 数据，或者依赖等待 session 数据。

怎么确定自己的服务是由 stateless 和 share nothing 的呢？很简单， 1 个 instance 可以解决问题，100 个 instances 也是可以达到同样的效果的，只是时间消耗的差异。

### VII. Port binding
对于 web app 或者 SAAS，一个端口一个地址就是我们需要的全部。在日常中，我们的 service 逻辑往往会运行在 tomcat、unicron 等等容器中，暴露出一个端口，而所有依赖的服务都可以通过机器名与端口找到该服务。

需要注意的是，所有在互联网上的服务都可以使用端口来指明 service，例如支持 MySQL Protocol 的 sphinx，调用者无需知道 sphinx 的实现细节，只需要知道该服务的协议与端口，在开发中，我甚至可以用一个 MySQL 的 image 替代它。这样做还有一个好处，当我们的服务依赖于其他时，我们可以很方便的将 endpoint 作为配置。

同理，我们在本地开发中，测试的本地 MySQL 与 RDS 中的 MySQL 略有不同，但是对于 app，是不需要感知到不同的。

### VIII. Concurrency
按照负载动态扩展是我们的追求，最重要的目的是为了避免浪费！12-Facto App 认为进程是一等公民，并且进程之间是相互隔离的。当然在 build 一个 docker image 时你的 container，只能有一个进程在运行（对于 docker 来说这是十分重要 [one process per container](https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#each-container-should-have-only-one-concern))。

运气好的是，docker 为我们提供了天然的隔离进程的方式，并且由于部署简单，在 scale up 时，只需要达到了设定的 threshold 就可以开启多个 instances，并且 pull 下 image 运行。当然，现在有更强悍的 container 管理服务，我们可以告别 instances 而直接使用 container 进行扩展，从而使得应用的 scale up 更快，参看 [AWS ESC](https://aws.amazon.com/ecs/details/)。

得益于微服务的业务分割，每个服务的职责是简单的、有边界的，所以考虑单个服务的 concurrency 是相对简单的。我所在的小组（5人）维护了十多个应用，提供 webservice 的应用有 7 个，每个服务都是能够轻松的动态扩展的，并且 concurrency 问题得到了较好的处理。这么来讲，只有三个 repositories 访问一张数据表的 concurrency 情况是非常简单的，而不是满世界的 join 你那张可怜的数据表。

### IX. Disposability
我们的应用很好的达到了优雅的启动，部分系统达到了优雅的终止。我们都希望自己的应用在关闭时也保持优雅，在关闭完端口后，不接收任何请求，并且完成线程池内的任务，然后再关闭自己。因为在负载变化较大的情况下，关闭一个 instanes 是常常发生的，我们并不希望在处理中的任务失败，丢失用户信息或是产生脏数据。

### X. Dev/prod parity
在日常的工作中，service bug 将是每个人的噩梦，很多分配到 fix 的同事第一个问题是：我该怎么重现 bug 呢？12-Factor App 推荐我们等价开发环境与生产环境，这是非常重要的，在业务上很多 bug 是可以依靠等价的环境在本地重现的，从而方便修复。

我所在的小组只有 5 名开发人员，却维护这十多个独立的，相互耦合的应用（感谢微服务！），严格的控制开发环境与线上环境的等价是我们的基础之一，按照文中的维度，我可以描述我们做到了什么：

- 缩小时间差异：尽快部署，修改后的代码可以在几分钟内上线
- 缩小人员差异：Dev 人员不仅需要开发，还需要参与 QA，监控部署以及服务状态
- 缩小工具差异：几乎本地环境可以完全视为线上环境

这里可以多说说 integration first，当一个新的项目启动后，第一件事情就是部署，我们需要一套本地的 docker-compose 环境来表示项目的环境，同时也需要构建 CI task 将其部署在产品环境。从此以后，任何的修改，都必须通过 CI。在开发中，我们会慢慢的加入 dummy response、unit test、integration test 等，并且会更新 CI pipeline。永远维护一个可用的线上环境，这样可以确保以后的更改不会破坏任何东西。当然在开发过程中我们有可能需要调整环境，这些事情往往是第一优先级的。

### XI. Log
大约两年前，有人告诉我说在进行大数据开发中，你都不知道 log 在哪里看，或者你都不知道是哪台机器出了问题！我承认当时我被吓到了，直到我摆脱了传统 log pattern 之后。重点是：永远永远永远不要将 log 存放在本地。引申为你的 app process 是无状态，它并不染指本地的存储资源。

我们可以使用 `stdout` 流优雅的解决这个问题，12-Factor App 将 log 放入输出流，谁关心谁去使用，不论是存档或是发送到日志中心这是与 app 无关的。得益于强大的日志分析工具，我们可以轻松的查看异常、统计 request time 或者分析流量。

Docker 又一个好处是天生的支持我们需要的 12-Factor App Log，参看 [Docker Log](https://docs.docker.com/engine/admin/logging/view_container_logs)。是时候结束那种 ssh 到环境上，tail -f logfile 的悲惨日子了。

### XII. Admin processes
我们需要那种只运行一次的管理任务，日常中可能最重要的是做数据库 migration，我们希望这种任务只运行一次，并且只在一个实例中运行。举个例子，在一个 ruby 的项目中，发布的 image 是包含有能够运行 migration 的任务的，这时，CI 只需要开启一个实例并且运行该任务即可，在完成后，由于程序正常退出，该任务所在的实例也会被正常关闭掉。
