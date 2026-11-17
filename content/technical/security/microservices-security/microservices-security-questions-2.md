### Question

If an attacker got hold of one service’s messaging credentials, how much data could they get access to? 

### Answer

If the guy gets the middleware credentials, we assume he could pass your network boundary and steal data from middleware.  So this question becomes how to prevent data losing, first we don't recommend using a super big middleware in Microservice implementation, many enterprises they are shocked by a new streams like Apache Kafka or AWS Kinesis, then they are using them as the new ESB, so if the hacker could access it, everything will be taken.

In our practice, separate the middleware resources is very important and with strict access control, a mail sender will use the SQS just from email content transfer and that sender should only have permission to receive the message.  We use things like AWS IAM to control which instance could get data from this queue, and reject the other clients.  We could also block the SSH to the instance to make sure no one could log in to the machine.  So, if you have the credential, the other places to run the command or SDK to fetch data will be blocked.  On the other hand, please consider the data in middleware, do you need to put everything in middleware? Maybe persist some in the database and only events in middleware.

### Reference

- [Principle of least privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege)
- [Access Control in RabbitMQ](https://www.rabbitmq.com/access-control.html)
- [Actions, Resources, and Condition Keys for Amazon SQS](https://docs.aws.amazon.com/IAM/latest/UserGuide/list_amazonsqs.html)

### Question

What information can I get out of the unauthenticated APIs of your gateway services? (Enumeration)

### Answer

Design the API is most interesting and important thing during the service development, actually, we are defining the contract about the service which will be exposed to wild.  We want the API clear, easy to understand, maybe RESTful and any clients could access it easily.  Most microservice implementations have API gateway (BTW there are a lot of products), and some companies they are running their own BFF services, and the clients like web browser or mobile, will invoke these edge services via some access token, maybe from SSO identity provider.  That architecture is good, decouples the token issuer and validator, and if the token is invalid, return code 401.

But this question gives us another view about the 401 problems, sometimes we want the service return more information to make the frontend developer’s work easier and we ignore the security risk.  The [OWSAP document here](https://www.owasp.org/index.php/Testing_for_User_Enumeration_and_Guessable_User_Account_(OWASP-AT-002)) describes what is the vulnerability the attacker could use to enumeration users and start a brute force attack.  In my experience, we prefer to give frontend message to just describe the action result, like `unauthorized` or `invalid token`, the message to the user depends on the client scenarios, for mobile client always tells people you need to login or sign up and this message should be defined in client side.  If the message from your service reveals the credentials, you should be careful.

### Reference
- [Username Enumeration Vulnerabilities](https://www.gnucitizen.org/blog/username-enumeration-vulnerabilities/)
- [OWSAP Testing for User Enumeration](https://www.owasp.org/index.php/Testing_for_User_Enumeration_and_Guessable_User_Account_(OWASP-AT-002))
- [What is Enumeration](https://resources.infosecinstitute.com/what-is-enumeration/)
