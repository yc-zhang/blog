最近做了一些前端方面的工作，修修改改，走走停停，bug 、magic 到处都是，实在是让人百爪挠心，而且发现自己在 cookie 与 user-agent 上面犯了一些经验主义的错误，于是整理下这部分的知识便于加深印象。

### 什么是 cookie?

我们这里所说的 cookie 全称为 `HTTP cookie`，词义为饼干，来自于 Unix 程序员的术语 `magic cookie`，常常指代一个程序所收到的一些数据集合，然后返回其未改变的值。简单来说，当 HTTP Client 发送请求时，会在 HTTP Header 上附带一个名为 cookie 的 header 发送给服务器，而有时服务器会在 response 中返回一个 set-cookie 的 header 提示客户端将其保留以便将来使用。听起来很麻烦，但是这样设计是有道理的，首先我们知道 HTTP 是一个无状态的协议，协议并不关心我们业务中的上下文，每次的请求都是完全独立的，但是 real world 中状态无处不在，就像人类的对话中总是有隐式的上下文一般，例如：朋友问你好吃吗？你就会根据之前提到的食物是否好吃回答他，而不是说什么好吃。所以就需要在 HTTP 中保留状态去处理我们的事务，每个网站都需要管理该用户是否登录成功，这就是一个状态。在有 cookie 的情况下，好吃吗这个问题大约会变成这样：

> A（Client）：你昨天吃的什么？
> B（Server）：火锅（set-cookie：食物=火锅）
> A（Client）：好吃吗（cookie：食物=火锅）？
> B（Server）：好吃的很~

你可以很方便的使用浏览器中的 DevTools 去观察每个 HTTP 请求与其附带的 cookie，也可以看到服务端返回的 set cookie。如果你使用其他的 HttpClient （例如说 curl 或者 Java HttpClient），有时候你需要自己处理 cookie，例如说使用数据结构保存在代码中。对于研究 cookie 来说，浏览器是一个黑盒，可以简单的理解为是一个 HttpClient 伴随着很多其他的功能。

### Cookie Header & Set Cookie

我们常说的和 cookie 相关的 header 有两种：`cookie` 与 `set-cookie`，`cookie` 是 `request-header` 意为在 http request 时出现，发送给服务端的，而 `set-cookie` 是 `response-header` 只会在返回时出现。我们知道 HTTP header 分为：General Header, Request Header, Response Header 与 Entity Header，可以阅读下文帮助理解：[RFC 2616](https://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html)。

所以只有请求时才会有 `cookie` 发送给服务器，格式很简单：

>Cookie: <cookie-list>
Cookie: name=value
Cookie: name=value; name2=value2; name3=value3 

例如：

>Cookie: PHPSESSID=298zf09hf012fh2; csrftoken=u32t4o3tb3gg43; _gat=1;

但是 `set-cookie` 就比较复杂，格式为：
>Set-Cookie: <cookie-name>=<cookie-value>; Domain=<domain-value>; Secure; HttpOnly

例如：
>Set-Cookie: qwerty=219ffwef9w0f; Domain=somecompany.co.uk; Path=/; Expires=Wed, 30 Aug 2019 00:00:00 GMT

### Domain & Path

我们知道服务端在 response 告诉我们应该保存这些 cookie，但是问题是我们怎么知道在**哪个请求中需要带上哪个 cookie 呢？**如果是我们自己使用 curl 或者 postman 这种工具时，看起来我们是可以自己写任何值作为 cookie 的（有没有效果取决于服务器），那么对于浏览器这种高级的 http user agent，我们并不需要告诉浏览器你下次带上哪个 cookie，而是浏览器根据 cookie 的属性来确定是否需要。帮助浏览器等确定是否要带上 cookie 时，有两个重要的属性就是 `domain` 与 `path`。

>Domain=<domain-value> Optional
确定在做哪些请求时，可以发送该 cookie，如果 domain 被指定了，subdomain 也是被包括的。

也就是说，当我们收到这样一个 `set-cookie` 时:
>Set-Cookie: qwerty=219ffwef9w0f; Domain=somecompany.com; Path=/

访问 `www.somecompany.com` 或者 `www.auth.somecompany.com` 或者 `www.order.somecompany.com` 时，request header 中都是有 cookie `qwerty=219ffwef9w0f` 的。

>Path=<path-value> Optional
Path 是 domain 的更深一层限制，有点类似于路径匹配，例如 /doc, /login 等等。

例如收到这样一个 `set-cookie`:
>Set-Cookie: tok=219ffwef9w0f; Domain=somecompany.com; Path=/login/reissue

只有在访问 `somecompany.com/login/reissue` 时，这个 `cookie` 才有效果，因为 URL 的 path 与 `cookie` 匹配。

### Expires & Max-Age

`cookie` 也是有时间限制的，如果你的 token 是无限期的话，那是一个非常危险的事情，所以 `cookie` 有这些属性来保证 `cookie` 如果过期，就不能再使用了。

>Expires=<date> Optional
标志 cookie 的有效生命周期的字段，当该时间过期后，cookie 就不再有效了。但是，如果这个字段为空的话，这个 cookie 也被成为 session cookie，注意这和我们常说的 session 不是一个东西。当浏览器被关闭时，就应该删除 session cookie。当然现代浏览器有时候也会使用 restore session cookie 这样的机制来保证你只关闭了 tab 再打开时，可以继续使用这个 cookie。

>Max-Age=<number> Optional
也是一个用于规定 cookie 生命周期的属性，单位为秒数。如果 expires 与 max-age 都被设定了，max-age 是优先的。

### Secure & HttpOnly

这两个属性放到一起来复习，是因为和安全相关，众所周知 HTTP 是一个 plain text 协议，如果不使用 HTTPS 的话，你的 request\response 都是明文的，很容易被截获、篡改，这对于信息安全是不可接受的。目前大多数网站都是使用 HTTPS 来保证连接安全，当然这是一个很伟大的实现，首先 HTTPS 在语义层面和 HTTP 完全一致，只是在底层使用了 SSL/TLS 来确保安全。

>Secure Optional
所以有 Secure 标记的 cookie 只会在 SSL 与 HTTPS 的协议下发送，对于敏感信息比如说身份、隐私等，都必须使用 Secure 标记。有一点需要注意的是，这个标记并不表示你的信息是被加密的（在 SSL 层做了加密，所以在这里不需要）。

我们知道 JavaScript 是可以通过 `Document.cookie` 直接访问 cookie，那么，我们在做 ajax 请求时也是可以设置 header 的，那么问题来了，我们知道 cookie 也是一个 header，那么我们就可以随意的设置 cookie 来绕过浏览器对于 cookie 的限制。那这样能做什么呢？**[XSS](https://en.wikipedia.org/wiki/Cross-site_scripting)**。

>HttpOnly Optional
HTTP-only cookies 是不能通过 Document.cookie 读取的，所以这能一定程度上的防御 XSS，但是不是全部。

XSS 是一个并不复杂的攻击方式，往往利用的是 web 的实现不完善，所以每一个漏洞所利用和针对的弱点都不尽相同。这就给 XSS 漏洞防御带来了困难：不可能以单一特征来概括所有XSS攻击。所以 HttpOnly 并不是完全能解决的 XSS 的。

### Session
最后我们来聊聊 session，我在这篇文章中刻意的回避了 server session 是因为对于 HTTP 协议层面来说，并没有一个规则来管理用户的上下文（也就是状态）。我们是可以使用 cookie 来解决这个问题的，例如说保存你在购物车里的产品，但是这会让 cookie 变得十分臃肿，而且每次请求都会带上这个 cookie 效率很低，而且在安全方面也是有很多隐患的，因为客户端是可以控制 cookie 的，对于服务端要想避免客户端修改 cookie，也需要引入更多的机制。那么，我们可否将状态保存在服务端呢？答案是可行的，但是协议又是无状态，服务端如何知道哪个请求对应的是哪个 session 呢？所以一般的解决方案就是在 cookie 中放入 sessoin id，类似于 key 一样的东西。这样你在请求时，服务端就可以通过 key 读取到你的 session 了，再根据上下文给与计算。

这里还是不展开说了，喜欢刨根问底的可以参考这里 [session](https://en.wikipedia.org/wiki/Session_(computer_science)#HTTP_session_token)。
