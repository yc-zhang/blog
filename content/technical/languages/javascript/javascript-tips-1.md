### 开头

我重新鼓起勇气学习 JavaScript 的原因不仅是因为项目需要，而且还有下面这句很可怕的话
> Any application that can be written in JavaScript, will eventually be written in JavaScript.  - Jeff Atwood
> https://blog.codinghorror.com/the-principle-of-least-power/

简单来说，不论是前端、后端、写嵌入式、写解析器、挖矿、hacking、给某航天飞机写算法还是创造自己的 AlphaGo，你都可以使用 JavaScript。这些年来，与其相关的技术、框架已经塞满脑海，说话中不谈 Vue 与 React 就是落伍，而且也有更好的基于 JS 的语言被发明，例如 TypeScript、Flow 等等，而且我们还看到 ES6 的落地，甚至还有同学固执的认为 NodeJS 是一门语言等等，也有同学曾经在面试时告诉我，他们的 React 单页应用是跑在 node 上的……

这也是我们在学习语言的过程中一些有意思的错误，问题是，我们总认为工具大于语言，我们认为学会了 React 可以获取一份前端的工作，至于 JavaScript 是什么，不就是一堆关键字长的像 Java 的东西一样，任何不是很笨的人，看了就会写。实际上这是本末倒置的，就如同 Java 领域火热的 SSH 或者 SSM 这种可笑的关键字是一样的，很多想找一份 Java 开发工作时，如果简历中有这样的关键字，并且在面试中解释不清楚依赖这种术语时，我就会挂掉他们（真的）。

所以语言特性才是整个问题的核心，理解语言特性，框架工具什么的都不是太大的问题。因为大多数框架与工具的设计方式与思路都是互通的，只是为了适配不同的语言。对于 JavaScript，在看了《JavaScript高级程序设计》一书后，我们可以将重点放在这几个章节：

- 变量、作用域与内存
- 引用类型
- 面向对象程序设计
- 函数

### 变量、作用域与内存

ECMA-262 JavaScript 的变量按照松散类型的本质，决定了它只是在特定的时间用于保存特定值的一个名字罢了。

ECMAScript 的变量可能包含两种不同的数据类型：基本类型值与引用类型值。

基本类型值是指简单的数据段：Undefined、Null、Boolean、Number、String —— Primitive Values。

引用类型值指那些可能由多个值构成的对象 —— Reference。

字符串在很多语言中由对象的形式表示，而 ECMAScript 中使用基本类型来表示。

JavaScript 不允许直接访问内存中的位置，也就是说不能直接操作对象的内存空间。

```
var person = {};
person.name = "Yuchen";
console.log(person.name);

var anotherOne = "hi";
anotherOne.name = "Yuchen";
console.log(anotherOne.name); // undefined
```

我们只能给引用类型值动态的添加属性。

复制基本类型则会创建新值；复制引用类型值则会创建另一个引用，而引用是处于堆内存中的。关于 stack & heap 是 runtime 所决定的，例如 Google V8。

ECMAScript 中所有函数的参数都是按值传递，也就是说，把函数外部的值复制给函数内部的参数，就和把值从一个变量复制到另一个变量一样。

```
function setName(people) {
    people.name = "Someone";
    people = {};
    people.name = "AnotherOne";
}

var friend = {};
setName(friend);
console.log(friend.name); // Someone
```

实际上，当在函数内部重写 obj 时，这 个变量引用的就是一个局部对象了。而这个局部对象会在函数执行完毕后立即被销毁。

执行环境 **execution context** 定义了变量或函数有权访问的其他数据，决定了他们的行为。每个执行环境都有一个与之关联的变量对象 **variable object**，环境中定义的所有变量和函数都保存在这个对象中。我们无法访问，只有解析器处理数据时在后台会使用。

这个对象实际上被称为 activation object，可以理解为是一个不能被直接访问的**对象**。

全局执行环境是最外围的一个执行环境，根据宿主的不同，标识执行环境的对象也不同。在浏览器中，通常被认为是 window 对象。

每个函数都有自己的执行环境，当执行流进入一个函数时，函数的环境就会被推入一个**环境栈**中，函数执行后，栈将其环境弹出，将控制权返回给之前的执行环境。

当代码执行时，会创建变量对象的 scope chain，其作用是保证对执行环境有权访问的所有变量和函数的有序访问。如果这个环境是函数，则将其活动对象(activation object)作为变量对象。活动对象在最开始时只包含一个变量，即 arguments 对象(这个对象在全局环境中是不存在的)。作用域链中的下一个变量对象来自包含(外部)环境，而再下一个变量对象则来自下一个包含环境。这样，一直延续到全局执行环境;全局执行环境的变量对象始终都是作用域链中的最后一个对象。

作用域链会在 try-catch 的 catch block 中加长，会在 with 语句中加长。

```
function buildUrl() {
    var qs = "?debug=true";
    with (location) {
        var url = href + qs; // get href from location scope
    }
    return url;
}
```

JavaScript 没有块级作用域。
```
if (true) {
    var color = "magic"
}
console.log(color); // magic
```

使用 var 声明的变量会自动被添加到最接近的环境中。在函数内部，最接近的环境就是函数的局部环境，在 with 语句中，最接近的是函数环境。

我们这里不讨论 ES6 的东西，先把 ES5 的东西搞清楚，关于 ES6 可以参考阮一峰的博客。

```
function add(num1, num2) {
    var sum = num1 + num2;
    return sum;
}

var result = add(10, 20);
console.log(result);  //30
console.log(sum); // undefined
```

思考上面的例子，如果去掉 var。如果没有 var，sum 将会在作用域链中寻找 sum，如果没有，则会在全局环境中创建。 **strcit mode** 将会避免这个问题。关于 Strict Mode，相信你已经在很多代码中见到了，可以 Google 一下就明白这东西了，这里我们就不说了。

当在某个环境中为了读取或写入而引用一个变量标识符时，必须通过搜索来确定该标识符实际代表什么。搜索过程从作用域链的前端开始，向上逐级查询与给定名字匹配的标识符。如果在局部环境中找到了该标识符，搜索过程停止，code is ready.

```
var color = "blue";

function getColor() {
    return color;
}

console.log(getColor());  //"blue"

var color = "blue";

function getNewColor() {
    var color = "red";
    return color;
}

console.log(getNewColor());  //"red"
```

JavaScript 你不需要关心内存使用问题，因为分配与回收都是自动管理的。

局部变量只在函数执行的过程中存在，在这个过程中，**会为局部变量在栈或堆内存上分配相应的空间**，以便存储，当执行完毕后，很容易判断该变量是否有存在的必要，然后清除。

常见的清除（GC）有两种，mark-and-sweep 非常常见的一种方式，执行策略也如同名字。垃圾收集器在运行的时候会给存储在内存中的所有变量都加上标记(当然，可以使用任何标记方式)。然后，它会去掉环境中的变量以及被环境中的变量引用的变量的标记。而在此之后再被加上标记 的变量将被视为准备删除的变量，原因是环境中的变量已经无法访问到这些变量了。引用计数(reference counting) 会引发循环引用的 bug，在采用引用计数策略的实现中，当函数执行完毕后，objectA 和 objectB 还将继续存在，因为它们的引用次数永远不会是 0。假如这个函数被重复多次调用，就会导致大量内存得不到回收。

```
function problem(){
    var objectA = new Object();
    var objectB = new Object();
    objectA.someOtherObject = objectB;
    objectB.anotherObject = objectA;
}
```

具体来说，GC 的实现应该是解释器的事情，我们不需要关心，设一个值为 null 只能解除引用，但是并不意味着回收。解除引用的真正作用是让值脱离执行环境，以便垃圾收集器下次运行时将其回收。

```
var a = {} // someobj
a = null; // it won't start GC!
```

关于内存，参考：https://developer.mozilla.org/en-US/docs/Web/JavaScript/Memory_Management
