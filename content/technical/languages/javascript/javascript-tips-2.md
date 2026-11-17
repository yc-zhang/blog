ECMAScript 中，引用类型只是一种数据结构，用于数据与功能的组装，常被称为类，但并不妥当。虽然引用类型与类看起来相似，但它们并不是相同的概念。

每个函数都是 Function 类型的实例，而且都与其他引用类型一样具有属性和方法。
```
function sum(num1, num2) {
    return num1 + num2;
}

console.log(sum(10, 10));        //20

var anotherSum = sum;
console.log(anotherSum(10, 10)); //20

sum = null;
console.log(anotherSum(10, 10)); //20
```

函数名有点类似于指针，按照变量的方式参考，就变成这样，所以 ECMAScript 并没有重载这一说法，因为被覆盖了。
```
function addSomeNumber(num, anotherNum){
    return num + 100 + anotherNum;
}
function addSomeNumber(num) {
    return num + 200;
}
console.log(addSomeNumber(100)); //300
```

而实际上，解析器在向执行环 境中加载数据时，对函数声明和函数表达式并非一视同仁。解析器会率先读取函数声明，并使其在执行 9 任何代码之前可用(可以访问);至于函数表达式，则必须等到解析器执行到它所在的代码行，才会真正被解释执行。请看下面的例子。

```
console.log(sum(10,10));
function sum(num1, num2){
    return num1 + num2;
}

// error
console.log(sum(10,10));
var sum = function(num1, num2){
    return num1 + num2;
};
```

因为解释器会在执行时，找不到 sum 对应的函数引用。

函数可以传递，并且也可以被返回（废话）。

函数 arguments 是一个挺有意思的东西，使用 arguments.callee 会避免耦合问题。
```
function factorial(num) {
    if (num <= 1) {
        return 1;
    } else {
        return num * arguments.callee(num - 1)
        // return num * factorial(num - 1)
    }
}

var trueFactorial = factorial;
factorial = function(){
    return 0;
};
console.log(trueFactorial(5));     //120
console.log(factorial(5));         //0
```
函数内部的另一个特殊对象是 this，其行为与 Java 和 C#中的 this 大致类似。换句话说，this 引用的是函数据以执行的环境对象——或者也可以说是 this 值(当在网页的全局作用域中调用函数时， this 对象引用的就是 window)。

每个函数都包含两个非继承而来的方法:apply()和 call()。这两个方法的用途都是在特定的作用域中调用函数，实际上等于设置函数体内 this 对象的值。

apply() 与 call() 真正的意义是扩充函数的作用域。参考下面这个有意思的例子：

```
window.color = "red";

var o = { color: "blue" };
function sayColor(){
    var color = "black";
    console.log(color);
}
sayColor(); // red
sayColor.call(this); // red
sayColor.call(o); // blue

o = null;
sayColor.call(o); // red
function sayColor(){
    var color = "black";
    console.log(this.color);
    // this 引用的是函数据以执行的环境对象
    // same as before
}

function sayColor(){
    var color = "black";
    console.log(color);
    // all black
}

window.color = "red";
var o = { color: "blue" };
function sayColor(){
    console.log(this.color);
}

var myColor = sayColor.bind(o);

myColor();
```
使用 `.bind()` 当你希望获得一个函数，并且可以在合适的时机调用（例如 lazy load 等场景），或者可以作为事件，当你使用 `.call()` 或 `.apply()` 当你想立刻调用该函数，并且修改其上下文。
