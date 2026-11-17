ECMA-262 把对象定义为：“无序属性的集合，其属性可以包含基本值、对象或者函数。” 相当于对象是一组没有特定顺序的值。

我们可以将 ECMAScript 的对象想象成散列表，无非就是一组 key-value，v 可以是数据或者函数。**所以需要注意的是，JavaScript 并没有类的概念，不论是使用闭包或者原型，我们只是在模拟类的一个基本功能：模板**。

对象是一个引用类型创建的，该类型可以是 Object 也可以是其他自定义类型。

ECMAScript 有两种属性：数据与访问器

数据属性：
 - Configurable - 可 delete 从而重新定义属性
 - Enumerable - 能否 for-in 
 - Writable - 能否修改？
 - Value - 表示属性的数据值，默认为 undefined

要修改属性默认的特性，必须使用 ECMAScript 5 的 Object.defineProperty()方法。

```javascript
var people = {
    name: 'yuchen',
    age: 19,
    say: function () {
        console.log(this.name)
    }
};

people.say();

Object.defineProperty(people, 'name', {
    writable: false,
    value: 'yuchen'
});

people.name = 'lele';
people.say();

for (var t in people) {
    console.log(t);
    console.log(people[t]);
}
```

这个例子演示了一个对象中的属性，这个属性可以是一个 permitive value 也可以是 reference，那么当然也可以是一个函数。

访问器，为 getter setter 的提供者，只有 configurable、enumeration、get、set 四个属性。注意下面的 magic，如果

```javascript
var boy = {};

Object.defineProperty(boy, 'name', {
    get: function () {
        return this._name; // this &  _name?
    },
    set: function (newVal) {
        this._name = newVal;
    }
});
```
上个例子中，我们使用了 this 与 _name。当你在思考 this 时，只需要抓住一点，谁调用了这个函数，谁就是 this。这一点在 Ruby 中有更好的描述，即 this 永远表示方法的 receiver。

所以在上面这个例子中，boy 这个对象，其实他有两个属性，`name` 与 `_name`，对于 boy 对象来说，他们没有任何分别，都是属性，并有自己的值，我们使用 `_name` 的目的是为了更好的描述 getter 与 setter。

我经常在面试中问候选人一个很有意思的概念问题，function（函数） 与 method（方法） 的区别是什么？往往我们认为 method 是 function 概念上的子集，如果使用 OO 术语来说，method 是一个对象上的函数，对于 Ruby 大神来说，经常会用 receiver 这个词来描述，即 method 是一个有确定 receiver 的 function。

经常，在 OOP 中，我们倾向使用方法来定义这个类的行为，但是在 MVC 的一些范式中，是将数据与可以被操作的行为分割开的。**定义行为**的最佳实践并没有唯一解。

> 必先正名乎。

术语的正确使用可以帮你养成正确的交流习惯。

那么如何创建对象，最简单的方式也许就是工厂模式了，如果你对 Java 很熟悉，这一种方式对你就极为简单：

```javascript
function createPerson(name, age) {
  return {
    name: name,
    age: age
  };
}

var yuchen = createPerson('yuchen', 19);

console.log(yuchen.name); // yuchen
console.log(typeof yuchen); // object
```

我们定义了一个返回新对象的函数，仅此而已，但是这样的一个对象非常简单，某些时候是满足我们的需求的。但是，typeof 关键字只能给我们 object 的值，我们没有解决这个 yuchen 是什么的问题。

```javascript
function People(name, age) {
    this.name = name;
    this.age = age;
    this.getName = function () {
        return this.name;
    }
}

var yuchen = new People("yuchen", 29);
var lele = new People("lele", 28);
console.log(yuchen.getName()); // yuchen
console.log(yuchen.getName === lele.getName); // false
console.log(typeof yuchen); // People

var o = {};
People.call(o, "another yuchen", 25); // this = o
console.log(o.getName()); // another yuchen
```
这个例子引入了一个新的概念，叫做**构造函数**。我们经常使用大写字母开始来表示这个函数是构造函数，并且使用 new 的关键字来创造一个对象。这样，我们能解决对象识别问题，typeof 关键字给了我们构造函数的名称，我们很开心。

但是，很可惜的，在 JavaScript 的世界中，并没有**构造函数**这个严谨的定义。构造函数是什么，构造函数就是一个函数，你当然可以用任何合法的字符定义一个函数。只是我们约定俗成的将**可以用作对象创建，并且首字母大写的函数**成为构造函数。那么构造函数的秘密是什么呢？就是 this 与 new。

```javascript
function someOne(name) {
  this.name = name;
}

someOne('yuchen'); // this.someOne('yuchen') or window.someOne('yuchen')

console.log(window.name); // yuchen
console.log(this); // window
```

这个例子说明了 this 与构造函数的关系，在浏览器的运行环境中，someOne function 是绑定在 window 对象中的，当调用 someOne 时，this 表示调用者，即 window，我们可以看到 name yuchen 被赋值给了 window 对象中的 name 属性中。

那么，new 关键字的意义是什么呢？可以简单的理解为 new 创建了一个空对象，并且将其作为 this 调用某个函数，再将其返回，大约如同下面的代码。

```javascript
var o = {};
People.call(o, "another yuchen", 25); // this = o
console.log(o.getName()); // another yuchen
```

事实上的实现更复杂一些，我鼓励你去自己找到答案，因为我知道我的描述是不正确的或者不严谨的 :)

无论什么时候，只要你创建了一个函数，就会为其创建 prototype 属性，其指向函数的原型对象。原型对象的属性最初只包含 constructor，指原先对象的函数。例如 Person.prototype.constructor -> Person。当构造函数创建一个新实例后，该实例内部包含一个指针指向构造函数的原型。

虽然 ECMA-262 管这个指针叫做 Prototype，在 Firefox、Safari、Chrome 中每个对象都有 __proto__ 用于表示原型，但这不是标准。原型最初只包含 constructor 属性，该属性也是共享的，所以可以通过对象实例访问。

```javascript
function Person() {
}

Person.prototype.name = 'yuchen';
Person.prototype.sayName = function () {
    console.log(this.name);
};

var yuchen = new Person();

console.log(yuchen.hasOwnProperty("name")); // false

yuchen.sayName(); // yuchen

yuchen.name = 'zhang yuchen';
yuchen.sayName(); // zhang yuchen

console.log(yuchen.hasOwnProperty("name")); // true
```

这段代码描述了 JavaScript 很重要的特性：属性查找。规则很简单，现在对象上找这个属性，如果没有，就在原型上找。当我们第二次设置了 zhang yuchen 作为属性时，name 这个属性在 yuchen 这个对象上已经存在了，所以属性被找到。对于执行方法？方法是属性，定义在原型上，所以也被找到了，再加一对小括号，执行！

```javascript
function Person(name) {
  this.name = name;
}

Person.prototype = {
    // constructor: Person,
    sayName: function () {
        console.log(this.name)
    }
};

var anotherYuchen = new Person('yuchen');
console.log(typeof anotherYuchen); // object ?!
console.log(anotherYuchen instanceof Object); // true
console.log(anotherYuchen instanceof Person); // true
console.log(anotherYuchen.constructor == Person); // false
console.log(anotherYuchen.constructor == Object); // true
```

prototype 上的 constructor 属性为我们解决了 typeof 问题，上面这个例子有点意外，为什么 typeof 返回的是 object ? 

原型对象是指针，修改了就会切断最初原型的联系，一旦修改了原型，原有的指针还是指向旧的原型。参考下面这个例子：

```
function Person(name) {
  this.name = name;
}

Person.prototype.sayName = function () {
  console.log(this.name);
};

var yuchen = new Person('yuchen');
yuchen.sayName(); // yuchen

Person.prototype = {
  sayName: function() {
    console.log("I'm not: " + this.name);
  }
}
                
yuchen.sayName(); // yuchen

var cloneYuchen = new Person('yuchen');
cloneYuchen.sayName();  // I'm not: yuchen
```
当然，当你使用原型时，也要注意引用类型的情况，例如：

```
function Person() {
}

Person.prototype = {
    constructor: Person,
    name: 'yuchen',
    friends: ['lele', 'jd'],
    sayName: function () {
        console.log(this.name);
    }
};

var p1 = new Person();
var p2 = new Person();
p1.friends.push('duomi');
console.log(p2.friends); // lele jd duomi ???
```

这个就很好解释了，因为都是一个对象引用！那么如果你将 p1.friends = [] 然后再做 push 呢？
