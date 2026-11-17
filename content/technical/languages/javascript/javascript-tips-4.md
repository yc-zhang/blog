这篇文章压力很大，为什么在 OOP 中要有继承这个词？很多时候，我们希望使用 is-a 的方式来解决问题，我们需要让对象变成一个能做某事的对象，is-a 和 has-a 都能解决，都可以解决代码复用的问题，但是继承这个术语在某些时候更贴近我们的场景，例如汽车可以开，那么宝马车也可以开。OO 最大的好处是贴近生活，在描述实体时，OO 有很好的表达能力，帮助我们阅读但 OO 也不是万能的，并且每个语言的支持都不尽相同，也无法与我们的现实世界相同，所以当理想的 OO 落实在代码中时，总会有一些不太合理的地方，最常见的例子就是发明不在现实中的对象了，并且在描述过程时又十分混乱。

回到今天的话题，JavaScript 没有 class 的概念，为了模拟 class，我们可以使用 prototype，但是 prototype 只是一个函数的属性，而对于函数，是不存在严格意义的构造函数之说。我们只是使用 JavaScript 的基本特性，来创造出一种类似于模板的东西，而这个东西，很多人称作 class。虽然在 ES6 后已经引入了 class 关键字，但是在本质中，你要清晰的知道，这个 class 只是帮你去理解 JavaScript（很多时候也会造成混乱）。

一般来说，有两种继承方式：接口继承与实现继承，如果你对 Java 很了解这两种方式你都应该非常熟悉。接口继承只继承方法签名，你无法重用代码，只是着重表达 is-a 的意义，在 Java 中也无法解决多继承的问题。如果你想使用两个类中的实现，那你只能考虑 has-a 的方式，即创造依赖，遗憾的是 JavaScript 没有函数签名，所以无法实现接口继承。所以，我们只能使用实现继承。

首先我们知道
- 每个函数（构造函数）都有一个原型对象
- 每个原型对象都包含有一个指向构造函数的指针
- 每个实例都包含一个指向原型对象的内部指针

那么，在进行属性查找时，我们会找当前对象的属性，如果没有，就去通过指针去找其原型对象，我们可以利用这种思路实现原型链的继承。

#### 原型链

如果我们让原型对象等于另一个类型的实列，在属性查找时，我们就可以使用链条的方式一层一层的找了。这种方式很简单，很好实现，大约如同下面：

```
function SuperType() {
    this.property = true;
}

SuperType.prototype.getSuperValue = function () {
    console.log("Super Value: " + this.property);
};

function SubType() {
    this.subProperty = true;
}

SubType.prototype = new SuperType();

SubType.prototype.getSubValue = function () {
    console.log("Sub Value: " + this.subProperty);
};

var instance = new SubType();
instance.getSubValue();
instance.getSuperValue();

console.log(SubType.prototype.constructor); // SuperType
```

本质性，原型链只是扩展了原型搜索机制。当读取一个属性时，首先会在实例中搜索，如果没有，则会继续搜索实例的原型。如果没有，则沿着原型链继续往上查找。别忘记，所有的引用类型都继承了 Object，而且这个继承也是由原型链所继承的。

使用字面量添加新方法时，会产生这样的问题：
```
SubType.prototype = new SuperType();

SubType.prototype = {
    getSubValue: function () {
        console.log(this.subProperty);
    }
};

var instance = new SubType();
instance.getSubValue();
```

所以继承就没有了，原型链被断开了。当然，原型链还有下面的问题：

1. 属性也会被继承为原型属性了，如果该属性是引用，则可能会出问题。

```
function Car() {
    this.types = ['normal', 'SUV'];
}

Car.prototype.run = function () {
    console.log("I'm running!");
};

function BMW() {
    this.name = 'BMW';
}

BMW.prototype = new Car();

var m3 = new BMW();
var m5 = new BMW();

m3.run(); // I'm running!
m5.run(); // I'm running!

m3.types.push('sport');

console.log(m3.types); // [ 'normal', 'SUV', 'sport' ]
console.log(m5.types); // [ 'normal', 'SUV', 'sport' ] ???
```

2. 参数无法传递，你见过哪个构造函数没参数的？那我还继承做什么？

#### 借用构造函数

我们可以使用 call 这个方法来进行属性借用，借用构造函数的方式只能处理属性，优点是解决了参数问题与引用，刚才那个 types 的引用问题就不存在了，而且我们可以将 name 往下面传递。但是这个方式有很大的问题：无法处理函数复用的问题。因为我们并没有在 Child 中对原型进行任何方式的操作，所以 sayName 这个函数就无法被使用了，因为这是对子类是不可见的。

```
function People(name) {
    this.name = name;
}

// this won't work
People.prototype.sayName = function () {
    console.log("Hi, I'm : " + this.name);
};

function Child(name, age) {
    People.call(this, name);
    this.age = age;
}

var c1 = new Child("maomao", 12);
var c2 = new Child("duoduo", 11);

console.log(c1.name); // maomao
console.log(c2.name); // duoduo

c1.sayName(); // error!
```

顾名思义，这个方式只是在构造函数里调用构造函数，来达到 属性绑定在 this 上的一种实现，意义也不是很大，因为没有做到方法的继承。

#### 组合式
组合继承则是前两种方式的组合，融合了优点，让 instanceof 与 isPropertyOf 得到了解决，当然也是最流行的方式了。

```
function Car(name) {
    this.name = name;
    this.colors = ['red'];
}

Car.prototype.sayName = function () {
    console.log(this.name);
};

Car.prototype.sayColors = function () {
    console.log(this.colors)
};

function BMW(brand) {
    this.brand = brand;
    Car.call(this, "BMW")
}

BMW.prototype = new Car();
BMW.prototype.constructor = Car;
BMW.prototype.sayBrand = function () {
    console.log(this.name + ": " + this.brand)
};

var x3 = new BMW("X3");
x3.colors.push("black");
x3.sayColors(); // [ 'red', 'black' ]

var m3 = new BMW("M3");
m3.sayBrand(); // BMW: M3
m3.sayColors(); // [ 'red' ]
```

这种方式看起来十分完美，但是也有一点瑕疵，注意这句话

```
BMW.prototype = new Car(); 
```

虽然我们继承了前两种方式的做法，真正做到了 属性即属性，方法即方法的继承，但是上面那句话依旧会调用构造函数，为 BMW 的 property 上创建了一些无意义的属性，即 name 与 colors，由于 JavaScript 的特性，你依旧可以使用这两个属性，造成了部分浪费。

#### 原型式继承
使用 Object.create() 进行扩充，问题是还是需要一个模板对象，同时，如果属性是引用，可能会造成问题。

```
var person = {
    name: "Yuchen",
    friends: ["Momo", "Wenting", "Chenyu"]
};

var yuchen1 = Object.create(person);
console.log(yuchen1.friends);
yuchen1.friends.push("Huihui");
var yuchen2 = Object.create(person);
console.log(yuchen2.friends); // this problem happens again!!!
```

简单情况可以考虑。

#### 寄生式继承

```
function maybe(obj) {
    function F() {}
    F.prototype = obj;
    return new F();
}

function parasitic(obj) {
    var clone = maybe(obj); // any function will return Object
    clone.name = 'yuchen';
    return clone;
}

var person = {
    age: 30
};
var yuchen3 = parasitic(person);
console.log(yuchen3.name);
console.log(yuchen3.age);
```

寄生式继承的思路与寄生构造函数和工厂模式类似，即创建一个仅用于封装继承过程的函数，该函数在内部以某种方式来增强对象，最后再像真地是它做了所有工作一样返回对象。函数复用问题依旧没法解决。另外，任何一个可以返回对象的函数，都可以作为 maybe 函数的替代。

#### 寄生组合式继承

寄生组合式继承，即通过构造借用函数来继承属性，通过原型链来继承方法。避免了原型链继承时，属性直接继承的缺点；避免了借用构造函数，无法优化方法复用的情况。

```
function obj(o) {
    function F() {}
    F.prototype = o;
    return new F();
}

function inheritPrototype(sub, sup) {
    var p = obj(sup.prototype);
    p.constructor = sub;
    sub.prototype = p;
}

function People(name) {
    this.name = name;
    this.friends = ['none'];
}

People.prototype.sayName = function () {
    console.log(this.name);
};

function Developer(skill) {
    People.call(this, 'developer');
    this.skill = skill
}

inheritPrototype(Developer, People); // what if move it after property define
// Developer.prototype = new People("developer"); // old inherit way, problem is invoke constructor twice and redundant properties on prototype

Developer.prototype.saySkill = function () {
    console.log(this.skill);
};

var developer = new Developer('java');
developer.saySkill();
developer.sayName();
developer.friends.push('yuchen');
var developer2 = new Developer('ruby');

developer2.saySkill();
developer2.sayName();

console.log(developer.friends); // none, yuchen
console.log(developer2.friends); // none
```

最完美的方案，但是也是最复杂的方案。这个例子的高效率体现在它只调用了一次 People 构造函数，并且因此避免了在 SubType. prototype 上面创建多余的属性。与此同时，原型链还能保持不变。开发人员普遍认为寄生组合式继承是引用类型最理想的继承范式，但是实现它还是有点复杂了，所以可以使用其他库提供的继承，比如 jQuery 或者 YUI。
