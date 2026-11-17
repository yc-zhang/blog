### 引子
Refer: http://www.grahamlea.com/2015/07/microservices-security-questions/

这一篇关于微服务安全的 post 给了我很大的启发，我也在去年尝试的在很多地方分享过关于微服务安全的知识和经验。至于文章的内容我就不翻译了，但是针对作者 Graham Lea 提出的 *Microservices Security: All the Questions*，我想根据我这几年的浅薄经验，尝试解答。

### Core Services
> by which I mean services that make up your system which do not interface with the Internet or other external systems

我们可以浅显的理解为内部系统，或者部署在 private subnet 中的系统，往往这些系统使用 Web Service、RFC 或者 middleware 的方式与外部集成。

- Are you just protecting your system at the Internet boundary? ([Defence in Depth](https://buildsecurityin.us-cert.gov/articles/knowledge/principles/defense-in-depth))

Internet boundary is necessary for most cases, but not enough.  First we should apply defence in depth in our infrastructure level (or four-layer network), secondary, it will be great if the cloud platform could supply abilities on granularity control, eg: AWS IAM could set any policy statement, and the subnet we always use it to protect resources could be accessed from some specified CIDR.

- What protections do you have in place if an intruder gets inside your core network? (Defence in Depth)

Endpoint protection could help us, for example Nessus is nice to have.  But if intruder gets inside, we could have another hand, for me I prefer 80 is the only open port in VM (of course you could have a lot of tools to connect your alarm systems like PagerDuty, to tell you someone break the glass).

 - How easily could someone inside your network get access to the traffic between your services? ([Secure Communications](https://en.wikipedia.org/wiki/Secure_communication))

This is a really good question, cause most company they have plain HTTP for the internal network,  if someone breaks in the boundary so everything goes wild.  HTTPS is a solution but requires a CA and more ops work and you can't avoid it, but not enough, I think in future people must face the [zero trust network](https://www.csoonline.com/article/3247848/network-security/what-is-zero-trust-a-model-for-more-effective-security.html).   To consider this question a bit further, if someone breaks in, traffic is a part the hack could steal, but what about the others?  The database snapshots, the log center, the reports and the code?

- Do your services trust each other too much? Or… Do your services trust *whoever is calling them* too much? (Are you sure only your services can call into your services?) ([Reluctance to Trust](https://buildsecurityin.us-cert.gov/articles/knowledge/principles/reluctance-to-trust))

This a another great question, service trust could be resolve in different network layer, for example we could use certificate cert below the application layer or we could implement in application like api-key or some JWT tokens, it's nice to have if the platform have more security abilities, we often use `AWS security group` to control the client services to the other services, some resources like `EC2` `Lambda` or `ECS` could only have the permissions to their resources.

- When your service is called, does it require the calling software to authenticate itself, or does it let anything connect? (Service Authentication)

If you want to have a centralized authentication and verification service, you can't apply Microservice 100%.  I'm a bit curious how to implement without OAuth & JWT.  I worked for a project they have their own authentication service and issue some tokens in different structure, finally we refactor is to use new modern SSO impl.

- Do your services let their callers access all the APIs that a service offers, or just the ones it needs to fulfil its function? (Service Authorisation)

People often confused with Authentication & Authorization, if you apply SSO with standard protocols, let the verification of authorization happens in resource side.  Service is a kind of resource.

- Does the identity of the person who originated each call at the client get passed into your internal services, or is that lost at the gateway? (Principal Propagation)

I think for identity we could get it from client side which includes in the short access token, but for user's profile like some PII data, we could have another service to handle it.  For the id token, it should only have the information safe to expose, also please consider to hide the email or fullname, maybe use * to mask.

- Can your services request any data from each other, or only the data of a user that has given their authority? (Principal Authorisation)

I don't think this question belong to Microservice Security, Micronservice is an application architecture, we decouple the monolithic app into micro parts to make them could scale\monitor\change fast, each service could be function or a module in old monolithic application, that's how we build product. I don't think for users they could know the inside of the application they are using, so they don't need to care to authorize the data inside the system or product. 

- If an attacker owned a service, could they pretty easily request anything from its downstream services? (Principal Authorisation)

This question is good, most cases is yes, the attacher could control the downstream.  It's very complicates to deal, for the web service downstream services, forward the access token to request is a good try, but for the middleware, we often ignore the protections.

- What guarantees do you have that a request received from an authenticated user hasn’t been tampered with? (Tamper-Proofing)

Signature, and always get the latest public keys.

- How do you ensure that an authorised request, delivered a second time, is detected and rejected? ([Replay Protection](https://en.wikipedia.org/wiki/Replay_attack))

Most times you don't need to worry, SSL/TLS everything.

-- 未完待续 --


