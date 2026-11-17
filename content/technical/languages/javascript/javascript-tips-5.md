闭包在 JS 领域中，是指有权访问另一个函数作用域中的变量的函数，常见的方式就是在一个函数中创建另一个函数。例如

```
function createComparisonFunction(property) {
    return function (object1, object2) {
        var value1 = object1[property];
        var value2 = object2[property];

        if (value1 < value2) {
            return -1;
        } else if (value1 > value2) {
            return 1;
        } else {
            return 0;
        }
    }
}

var compare = createComparisonFunction('name');
console.log(compare({name: 'yuchen'}, {name: 'lele'}));
```

当某函数被调用时，会创建一个 execution context 与 scope chain，然后使用 arguments 与其他的命名参数来初始化 activation object。在 scope chain 中，外部函数的 activation object 永远处于第二位，外部函数的外部函数的 activation object 永远处于第三位，直至 scope chain 结束。

如果是一个简单的 compare 函数，是这样搞的：
	1. 创建预先包含全局变量环境的作用域链
	2. 将这个作用域链保存在内部的 scope 属性中
	3. 调用 compare 函数时
	4. 活动对象被推入了执行环境作用域链的前端
	5. 所以 compare 函数的作用域链有两个变量：本地与全局

当一个匿名函数从 createComparisonFunction 中被返回后：
	1. 它的作用域链包含：createComparisonFunction 中的活动对象与全局变量
	2. createComparisonFunction 在调用后，活动对象不会被销毁，直到返回的匿名函数被销毁

当代码在一个环境中被执行时，会创建变量对象的作用域链，作用域链存储了变量对象，如果是在函数中，也就是活动对象。

执行环境 => 包含 => 作用域链 => 包含 => 活动对象

createComparisonFunction 运行时，执行环境中的 scope chain 为 global 与自己的 activation object

匿名函数运行时，执行环境的 scope chain 中包含自己的 activation object，与createComparisonFunction 的 activation objects，所以

活动对象不会被销毁
活动对象不会被销毁
活动对象不会被销毁

所以，参考下面的例子：

```
function createFunction() {
    var results = [];

    for (var i = 0; i < 10; i++) {
        results.push(function () {
            return i;
        });
    }

    return results;
}

var functions = createFunction();
console.log(functions[0]());
console.log(functions[1]());
```

functions[0] 与 function[1] 引用了同样的 activation object，所以都是 10。

```
function createFunction() {
    var results = [];

    for (var i = 0; i < 10; i++) {
        results.push(function(num) {
            return function() {
                console.log(i);
                return num;
            }
        }(i));
    }

    return results;
}

var functions = createFunction();
console.log(functions[0]());
console.log(functions[1]());
```

因为创建了 function(num) 时，创建了新的活动对象哦~

```
var name = "The Window";
var object = {
    name: "My Object",
    getNameFunc: function () {
        return function () {
            return this.name;
        };
    }
};

console.log(object.getNameFunc()());

var name = "The Window";
var object = {
    name: "My Object",
    getNameFunc: function () {
        var that = this;
        return function () {
            return that.name;
        };
    }
};

console.log(object.getNameFunc()());
```

函数表达式：

```
(function() {
   console.log("here")
})();


(function() {
    console.log("here")
}());

function() {
    console.log("here")
}();
```

1.(function(){})(),(function(){})是一个表达式，会强制其理解成函数直接量方式，也就是表达式方式创建函数，(function(){})它会返回函数对象的引用，最后使用小括号()调用此函数。
2.(function(){}())，如果不用外面包裹的小括号，{}就会理解为复合语句，那么function(){}就被理解为函数声明，但是没有标识符，所以会报错，使用小括号以后，就会变成表达式，也会被理解为直接量方式。

所以我们要使用函数来进行块级作用域的实现，例如：

```
function yuchen() {
    for (var i = 0; i < 10; i++) {
        console.log(i);
    }
    console.log("I'm going to touch: ");
    console.log(i);
}

yuchen();

function lele() {
    (function () {
        for (var i = 0; i < 10; i++) {
            console.log(i);
        }
    })();
    console.log("I'm going to touch: ");
    console.log(i);
}

lele();
```

当 lele 执行完后，匿名函数会被回收掉，所以不会有残留，我们也实现了 i 的块级作用域的作用。

```
var park = function () {
   var carPark = [];

   carPark.push("VW");

   return {
       howMany: function () {
           return carPark.length;
       },

       parkCar: function (car) {
           carPark.push(car);
       }
   }
}();

console.log(park.howMany());
park.parkCar("BMW");
console.log(park.howMany());
// park.carPark ???
```
