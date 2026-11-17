### CSRF 的传统修复方式

几天前，在阅读一篇极为专业的渗透测试报告时，发现了安全人员汇报了一个严重又常见的问题：CSRF 跨站请求伪造，诚然由于开发者的疏忽，产生 CSRF 的问题的确比较严重，好在发现的早我们可以尽早修复。安全人员是这样建议的：

> The application should implement anti-CSRF tokens into all requests that perform actions which change the application state or which add/modify/delete content. An anti-CSRF token should be a long randomly generated value unique to each user so that attackers cannot easily brute-force it. It is important that anti-CSRF tokens are validated when user requests are handled by the application. The application should both verify that the token exists in the request, and also check that it matches the user's current token. If either of these checks fails, the application should reject the request.

使用 anti-CSRF token 是防御 CSRF 的有效手段之一，安全人员的建议也很照本宣科的，很多 web 框架与编程语言都类似的实现方式，例如：

```html
<form method="POST" action="/profile">
    <input type="hidden" name="${_csrf.parameterName}" value="${_csrf.token}"/>
    ...
</form>
```
或者使用 cookie / meta 与 ajax 全局设置，例如：

```javascript
// 在 HTML 里面塞入这个 meta
<meta name="csrf-token" content="{{ csrf_token() }}">

$.ajaxSetup({
    headers: {
        'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content')
    }
});
```

**核心思路是，使用一个由服务器派发的 token，在前端进行状态修改时，也同时提交这个 token（往往会放在 html form 的 input 中，或者 ajax header 中），这时候服务端验证该 token 是否是之前所生成的，以此来判断这个请求是否被允许。**所以，当用户点击 hacker 所提供的三方网站时，这些恶意网站无论如何也无法获取到之前服务端生成 token，这样的话，即使请求可以发送至服务端，也不会通过验证。关于 CSRF 与 anti-CSRF Token 的具体机制本篇不再赘述，请参考[这篇文章](https://medium.com/@charithra/introduction-to-csrf-a329badfca49)，此外，**防范 CSRF 是一个稍微复杂的实践，还可以使用 referer、origin 等其他手段进行深度防御，而且一定是根据具体现状的考虑。**

按照这位安全人员的建议，我们应该在渲染 form 时，嵌入 token 作为 hidden input 并且在后端进行验证，对于成熟的 web 框架来说，Spring MVC、Ruby on Rails、Play 或者 Lavarel 几乎是两行代码的事情，那么为什么做不到呢？

### 前后端分离带来了新问题

随着前后端分离与单页应用的到来，我们往往在后端使用 RESTful 的方式暴露接口，前端使用 react、angular 或者 VUE 来控制渲染和交互，那么，也就不存在如何在 form 中放入一个 token 来进行 CSRF 的验证了。对于 RESTful 的接口，本质上是无状态的（stateless），而 anti-CSRF token 是依靠 session 中的状态来进行判断，那么也就无法再使用这种方式了。

![以前](https://upload-images.jianshu.io/upload_images/3819274-e1bddfe54f53eb7e.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

![前后端分离后](https://upload-images.jianshu.io/upload_images/3819274-1c5b0630ca8c4616.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

可以看到，在前后端进行分离后，最简单的集成方式如上图：
1）用户通过浏览器请求某个网站例如 www.google.com，然后 DNS 转移至前端站点，获取前端资源
2）返回页面，JS，CSS 等后，浏览器进行渲染页面，这时候用户就能看到页面了
3）在页面准备好后，用户的所有操作（不论是 form 提交、还是 ajax 请求），都发送给后端服务，再通过 web service 响应，修改页面，支持业务逻辑

这个流程中，对于真正存储、修改用户数据的后端服务，是无状态的，**而用户所操作的 form 是完全由前端应用控制，后端服务无法感知。所以，即使前端使用某种方式在 form 中放入了 token，但是后端也无法验证，这种 anti CSRF token 的方式是无法实现的。**

### 尝试引入状态进行修复

好消息是，自从单页应用的崛起我们已经很少直接使用 form 的方式跟后端服务打交道了（页面上也许有 form，但是提交走 ajax），通过 [OWSAP CSRF Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) 中的这一节 *JavaScript Guidance for Auto-inclusion of CSRF tokens as an AJAX Request header*，你依旧可以使用 token 的方式，具体的步骤是：

1）在某个地方存储 CSRF Token，推荐是 DOM，或者在 JS 变量中或者其他地方，不推荐 cookie 或者 localStorage。

```html
<meta name="csrf-token" content="{{ csrf_token() }}">
```
2）在 ajax 中，使用自定义的 header 发送 CSRF Token。

```html
<script type="text/javascript">
    var csrf_token = document.querySelector("meta[name='csrf-token']").getAttribute("content");
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS)$/.test(method));
    }
    var o = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(){
        var res = o.apply(this, arguments);
        var err = new Error();
        if (!csrfSafeMethod(arguments[0])) {
            this.setRequestHeader('anti-csrf-token', csrf_token);
        }
        return res;
    };
 </script>
```

3）在后端服务进行验证。

首先这种方式不能直接使用，并且也不是完全安全的，有这样几个问题：

1）存储 CSRF Token 的地方，无论是 DOM，Cookie 或者 localStorage，**只要是 JavaScript 能读取到，就会面临 XSS 风险**，很容易拆东墙补西墙。
2）很难在合适的时机放入 CSRF Token，还是单页应用的问题，获取完单页应用后，前端的渲染逻辑完全是浏览器负责，这是无法生成 CSRF Token 的。
3）就算前端代码在神奇的某处生成了 CSRF Token，后端应用也无法获取到 Token 用来验证请求是否合法，后端服务是无状态的。

解决这些问题的套路也不复杂，无非就是引入一个状态，也就是生成 token 与验证 token 的组件应该是一个，而且对于后端的服务来说，这是透明的。那么使用 API Gateway 或者自己写一个 Security Sidecar 就可以做到。大约是这样的逻辑：

![再引入一个新的模块](https://upload-images.jianshu.io/upload_images/3819274-e9a83bf1fcbd1ea1.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

看起来我们是解决了这个问题，我们引入了新的安全模块，它有可能是写在 WAF里，也有可能是 Security Sidecar 或者自定义的 API Gateway，总之，它在哪里用什么技术实现并不重要，重要的是这几个职责：

1）生成 CSRF Token 并且验证下来的请求
2）顺便可以做 token 验证，来确保用户是否有权限使用后端服务
3）常用的 HTTP Referer 与 Origin 检查
4）其他的安全拦截，比如基于 User-Agent 或者 IP 等等

### 使用 Origin/Referer Header 进行防范

不论你采用哪种方式实现了 CSRF Token，或者压根没做，**但是通过 Origin/Referer 的验证判断是必须要做的，你可以参考以下的代码实现**。听起来这种策略很完美，但是取决于浏览器的实现以及后端服务端支持的 HTTP Method（比如有程序员写的端口，通过 GET 方式去修改状态）。

```java
        /* STEP 1: Verifying Same Origin with Standard Headers */
        //Try to get the source from the "Origin" header
        String source = httpReq.getHeader("Origin");
        if (this.isBlank(source)) {
            //If empty then fallback on "Referer" header
            source = httpReq.getHeader("Referer");
            //If this one is empty too then we trace the event and we block the request 
            //(recommendation of the article)...
            if (this.isBlank(source)) {
                accessDeniedReason = "CSRFValidationFilter: ORIGIN and REFERER request" + 
                "headers are both absent/empty so we block the request !";
                LOG.warn(accessDeniedReason);
                httpResp.sendError(HttpServletResponse.SC_FORBIDDEN, accessDeniedReason);
                return;
            }
        }

        //Compare the source against the expected target origin
        URL sourceURL = new URL(source);
        if (!this.targetOrigin.getProtocol().equals(sourceURL.getProtocol()) || 
            !this.targetOrigin.getHost().equals(sourceURL.getHost())
        || this.targetOrigin.getPort() != sourceURL.getPort()) {
            //One the part do not match so we trace the event and we block the request
            accessDeniedReason = String.format("CSRFValidationFilter: Protocol/Host/Port " + 
            "do not fully matches so we block the request! (%s != %s) ",
                this.targetOrigin, sourceURL);
            LOG.warn(accessDeniedReason);
            httpResp.sendError(HttpServletResponse.SC_FORBIDDEN, accessDeniedReason);
            return;
        }
```
> 请求首部字段 Origin 指示了请求来自于哪个站点。该字段仅指示服务器名称，并不包含任何路径信息。该首部用于 CORS 请求或者 POST 请求。除了不包含路径信息，该字段与 Referer 首部字段相似。Referer 请求头包含了当前请求页面的来源页面的地址，即表示当前页面是通过此来源页面里的链接进入的。服务端一般使用 Referer 请求头识别访问来源，可能会以此进行统计分析、日志记录以及缓存优化等。

### 使用 Samesite Cookie Attribute

一般认为是 CSRF 的终极解决方式，SameSite 是最新的 cookie 属性，如同 http-only 与 secure 一般，目前在 RFC6265 中推出，这个属性顾名思义，就是限制 cookie 只能在同站中使用。我认为是很好的，因为我一直是使用 cookie 进行系统的认证与授权设计，即使用 http-only，secure 确保只有浏览器能够获取 cookie，而 JS 不能，同时，通过 domain、path 与 expires 来控制 token。这样对前后端都非常友好，此外也很安全。对于 CSRF，除了 token 与 Origin/Refer 的方式，还可以使用其他更严格的做法。

目前 Samesite 的可选值为 Lax, Strict 或 None。对于 Strict 值，用来阻止浏览器在任何跨站的情况下发送 cookie，只有当前网页的 URL 与请求目标一致，才会带上，所以用户体验可能会遭受影响，特别是你的后端服务在不同的域下，[具体请参考阮一峰的文章](http://www.ruanyifeng.com/blog/2019/09/cookie-samesite.html)。

很遗憾，如同下面引用的那句话一样，我们不得不信任浏览器的安全实现，这在网络时代是无法避免的。如同安全方法一样，能做到什么级别的安全取决于成本与投入，安全只是一种平衡，绝对的安全是不存在的。

> At the end of the day you have to "trust" the client browser to safely store user's data and protect the client-side of the session. If you don't trust the client browser, then you should stop using the web at all for anything other than static content.

### 更严格的保护

某些时候我们需要更严格的保护，特别是一些安全级别很高的后台或者服务，可以考虑以下这几种方式

- Re-Authentication (password or stronger)：在进行安全级别较高的操作时，需要用户重新认证
- One-time Token：使用类似于 HOTP / TOTP 的 token 进行认证
- CAPTCHA：验证码其实也是一种选择

### 参考资料
- [https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [https://security.stackexchange.com/questions/166724/should-i-use-csrf-protection-on-rest-api-endpoints](https://security.stackexchange.com/questions/166724/should-i-use-csrf-protection-on-rest-api-endpoints)
- [https://jemurai.com/2018/08/27/csrf-tokens-with-restful-apis/](https://jemurai.com/2018/08/27/csrf-tokens-with-restful-apis/)
- [http://www.ruanyifeng.com/blog/2019/09/cookie-samesite.html](http://www.ruanyifeng.com/blog/2019/09/cookie-samesite.html)
- [https://www.sjoerdlangkemper.nl/2019/02/27/prevent-csrf-with-the-origin-http-request-header/](https://www.sjoerdlangkemper.nl/2019/02/27/prevent-csrf-with-the-origin-http-request-header/)
- [https://my.oschina.net/meituantech/blog/2243958](https://my.oschina.net/meituantech/blog/2243958)

