### HTTP2 解决了部分浪费问题

> 本文只做科普，真正的学习请参考标准 [RFC 7520 HTTP/2](https://tools.ietf.org/html/rfc7540)。

在我刚开始工作时，经常使用 SOAP 调用 WebService，理论上 SOAP 可以使用任何协议作为载体：HTTP、FTP、SMTP、甚至你自己写的某种协议，但是大家都是使用 HTTP，这便是我第一个问题：why？答案当然可以写出很多，但是有一个词启发了我，那就是**穿墙**。**穿墙**保证你可以很方便的通过防火墙去调用远端的服务，那么为什么防火墙支持 80 或者 443 端口呢（in default most times）？因为 HTTP 协议很流行。那么为什么 HTTP 协议很流行呢？因为 web，没有 web 你现在也没办法在简书上看文章了。所以 HTTP 是最重要的应用层协议。但是 HTTP 是非常不美好的一个实现，最让人诟病的是资源的浪费。

- 我们知道这是一个先进先出的协议 FIFO，也就是说在一个 connection 中，第一个 request 发出后你必须要等待 response，直到收到 response 再进行下一次的请求，所以现代浏览器会同时启动多个 connection 进行资源下载（RFC-2616-8.1.4 Practical Considerations) 来提高性能。但是，在底层 socket 中，我们知道这是一个 duplex 的连接，那为什么我们还要等前一个请求完成呢？
- 当你在淘宝进行一次搜索时，如果 dump 出一个完整的 HTTP 请求，可以看到除了内容以外还有大量的 header 进行传输，特别是一些用于记录行为的 cookie。我们知道 HTTP 一个无状态的协议（这是一个优点大于缺点的选择），所以我们不得不带上这些 header 以及其中的 cookie，而 body 则是可以选择压缩来节约带宽的。
- HTTP 是底层是建立在 TCP 之上的，我们知道如果传输数据的成本小与建立连接的成本（特别是 TLS）那是及不划算的，也无法利用到现在网络终端的高带宽。之前我们的解决方案多是降低延迟，而不是增加带宽使用效率，因为 HTTP 无法做到在一个连接上增加传输，无法多路复用（Multiplexing）。
- 当你打开某大型网站时，HTML 下载完成后（现代浏览器不是这样，但是效率也不会太高），你才能够获取内嵌的 js、css、图片等等这些资源。但是几乎每个网站的每个页面都有共享的资源（例如 header、通用样式等），或者我们希望在连接建立时就能获取这些通用的资源。
- 对于 Mobile HTTP 是天生不友好的，WebService 开发相对于 RPC 是简单的，但是对于性能有一定要求的 APP，使用 WebService 则有很大的风险，连接过多、效率很低。所以也有部分同学在自己的 APP 中使用自订的协议（各种 PRC），而这些协议难以开发，难以调试。
- Server 不能发起主动通告，我们有时候希望服务器在做完某些事情后通知我们，但是 HTTP 是不支持的，所以我们有了很多折中的方案：while poll、websocket 等，但是我们知道，这是效率很低的做法。

### HTTP2 怎么做到的？
HTTP2  最大的优势就是提升了 web 性能，并且兼容了 HTTP1.1 的语义，实现了向后兼容。Akamai 的朋友曾经告诉我，Akamai 在 CDN 中已经默认打开了 HTTP2，大约性能提升在 10%~20%（这个数字是非常粗略的并且没有足够的上下文，很多情况需要具体分析，所以才会有最后的例子），而这对于很多开发人员来说，只是一个开关的事情。

所以 HTTP2 需要重新发明与 TCP 的集成方式，而不是简单粗暴的将 ASCII 格式的消息丢下去，同时还必须要兼容 HTTP1.1，所以应对这种问题，经典的解决方案就是：加一层。

> Any problem in computer science can be solved by another layer of indirection.

### Binary Framing —— 二进制封帧

HTTP2 引入了 frame 作为数据层的封装表示，归根结底HTTP2 的目标是提高资源利用——尽量的在一个 connection 中做更多的事情——也就意味着原始的 raw ASCII 传递是需要被替代的，而这个替代就是 frame 与 stream。Binary Frame 是 HTTP2 数据交换的单位或是最小实体，我们使用二进制的格式去构造这些 frame。操作 frame 要简单于一个巨大的二进制流，这意味着我们可以做很多高级的操作：并发、流量控制、错误处理与优先排序，同时还有更好的扩展性。

### Multiplexing —— 多路复用

HTTP2 最重要的改进就是多路复用，为了实现多路复用，引入了 stream 这个抽象的概念。如果 frame 是车厢的话，stream 就是火车，调度这些 stream 来达到多路复用（老实说，要按照标准实现 stream 来达到多路复用真是一个很有挑战的事情，特别是我看完了 stream state 后……或许应该用 Go 写一个作为练习）。按照 RFC，stream 应该有一下的特性：

- Stream 是独立的、双向的用于 frame 传输的序列
- 一个 HTTP2 connection 包含大量的、并发的 stream
- 通信双方可以从 stream 中获取 frame 
- Stream 在被建立后可以单独的使用，也可以被共享
- Stream 可以被通信双方关闭
- Stream 中的 frame 的顺序是非常重要的，应答 frame 的顺序与收到时相同
- Stream 使用 Integer 值标识，并由端点指定

所以我们可以访问一个网站，就使用一个 connection，也不会担心 FIFO 造成性能上的损失（head-of-line blocking problem），如果一个 response 比较慢，其他的 frames 会带来另一些快速的 response，而系统不会被 block 住。

### Header Compression —— 头部压缩

很多人喜欢用 TCP [Slow Start](http://en.wikipedia.org/wiki/Slow-start) 来说明 Header Compression 的作用，我感觉貌似搞错了点。虽然是有一部分的相关性，但是重点是为了节约传输的 bits。即时轻度的头部压缩，只要能在一次 round trip 完成任务就是非常高效的了。很多网站都有很多图片、样式表、JS等等资源，如果每个资源有 800 bytes 的 headers（cookies、refer 等等），我们可以计算下只为这些 header 传输，我们可以节约多少资源。

### Server Push —— 服务端推送

当浏览器请求一个页面时，服务器会在响应中发送 HTML 返回给浏览器，然后需要等待浏览器解析 HTML 并在开始发送JavaScript，图像和 CSS 之前发出对所有嵌入资源的请求。Server Push 可能允许服务器通过将它认为客户端需要的响应 push 到其缓存中来避免这种延迟，简直太智能、太美好了！所以在 2018 年我们终于有点未来世界的影子了？

然而并不是，仔细想想 Server Push 的描述，有几个词是很难做到的：“需要的”、“缓存”。有缓存，就需要有过期策略，就需要有相应的刷新策略，没有哪个前端工程师喜欢缓存，当然大多数人必须承认缓存是能提高部分用户体验的。

但是我一直比较关心的是，Server Push 可以替代一些只为了推送而开的 WebSocket 与 loop AJAX 吗？当然如果是富交互应用，我不觉得 HTTP2 的目标是取代 WebSocket。

### 练习

粗略的读完了 HTTP2 的 RFC，也做了一些简单的练习，主要用户观察多路复用的具体表现与 Server Push，思路是使用 docker-compose 在本地开启一些 NGINX 容器。使用 docker 去验证、学习是一个很好的载体，某种情况下，docker 是一个秒级的、轻量的、全功能的虚拟机。而 compose 可以避免你记录一堆命令或者配置。

[Example: Http2 Practice](https://github.com/yc-zhang/http2-practice) 

在 `docker-compose.yml` 文件中我们定义了三个容器用来验证，`web-server-http1` 用于对照。 

```yaml
version: '2'

services:
  base:
    image: nginx:1.13.12
    volumes:
      - ./site:/usr/share/nginx/html
      - ./cert:/etc/nginx/ssl

  web-server-http1:
    extends:
      service: base
    volumes:
      - ./config/base-ssl.conf:/etc/nginx/nginx.conf
    ports:
      - "443:443"

  web-server-http2:
    extends:
      service: base
    volumes:
      - ./config/base-ssl-http2.conf:/etc/nginx/nginx.conf
    ports:
      - "444:443"

  web-server-http2-server-push:
    extends:
      service: base
    volumes:
      - ./config/base-ssl-http2-server-push.conf:/etc/nginx/nginx.conf
    ports:
      - "445:443"
```
以下是多路复用的观察结果：
![效果拔群](https://upload-images.jianshu.io/upload_images/3819274-8991db1f142bb3a7.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

关于 NGINX 的 HTTP2 Features 可以参考:
- [theory-and-practice-1](https://www.nginx.com/blog/http2-theory-and-practice-in-nginx-stable-13/)
- [theory-and-practice-2](https://www.nginx.com/blog/http2-theory-and-practice-in-nginx-stable-part-2/)
- [theory-and-practice-3](https://www.nginx.com/blog/http2-theory-and-practice-in-nginx-part-3/)
- [nginx-server-push](https://www.nginx.com/blog/nginx-1-13-9-http2-server-push/#configuring)

