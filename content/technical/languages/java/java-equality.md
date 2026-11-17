Java 的 == 与 equals 是一个很常见的**面试**问题，有时候我考察候选人时，也会问这样的问题，多用于考察你的语言熟练度。有一个诀窍就是一旦遇见语言标准，官方文档是第一位，其次是自己的 practice 与验证，最后才是其他人的 blog。

首先，== 是运算符而 equals 是在 Object 类上的方法。对于 == 简单的解释是比较的是 value，对于基本类型，比如说两个 int 在内存中存储的是 value 就是数字的大小，所以以下成立：
```
int a = 10;
int b = 10;
System.out.println(a == b); // true
```
但是对于 object 来说，其 value 为内存中的地址，所以 == 比较的结果为：
```
Object objectA = new Object();
Object objectB = new Object();
System.out.println(objectA == objectB); // false
objectB = objectA;
System.out.println(objectA == objectB); // true
```
所以按照我们的“常识”来说，== 运算符并不能解决工作中**判等**的职责，或许是因为这个原因 Java 使用了 equals 针对于对象的**判等**。根据官方文档
> public boolean equals([Object](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html "class in java.lang") obj)
Indicates whether some other object is "equal to" this one.
The equals method implements an equivalence relation on non-null object references:
>*   It is reflexive: for any non-null reference value x, x.equals(x) should return true.
>*   It is symmetric: for any non-null reference values x and y, x.equals(y) should return true if and only if y.equals(x) returns true.
>*   It is transitive: for any non-null reference values x, y, and z, if x.equals(y) returns true and y.equals(z) returns true, then x.equals(z) should return true.
>*   It is consistent: for any non-null reference values x and y, multiple invocations of x.equals(y) consistently return true or consistently return false, provided no information used in equals comparisons on the objects is modified.
>*   For any non-null reference value x, x.equals(null) should return false.
> 
> The equals method for class Object implements the most discriminating possible equivalence relation on objects; that is, for any non-null reference values x and y, this method returns true if and only if x and y refer to the same object (x == y has the value true).
Note that it is generally necessary to override the hashCode method whenever this method is overridden, so as to maintain the general contract for the hashCode method, which states that equal objects must have equal hash codes.

也就是说，如果你想让你的对象有 "**equal to**" 的属性的话，也就是你需要满足上面的五点条件，并且 hash codes 必须是相等的，所以在标准的 String 类中，equals 方法是这样实现的：
```
public boolean equals(Object var1) {
    if (this == var1) {
        return true;
    } else {
        if (var1 instanceof String) {
            String var2 = (String)var1;
            int var3 = this.value.length;
            if (var3 == var2.value.length) {
                char[] var4 = this.value;
                char[] var5 = var2.value;
                for(int var6 = 0; var3-- != 0; ++var6) {
                    if (var4[var6] != var5[var6]) {
                        return false;
                    }
                }
                return true;
            }
        }
        return false;
    }
}
```
于是，我们进行了以下的测试：
```
String stringA = new String("hi");
String stringB = new String("hi");
System.out.println(stringA == stringB); // false
System.out.println(stringA.equals(stringB)); // true
```
看起来没什么问题，因为 AB 的 value 不一样的所以肯定 == 是 false，**但是 String 类 override 了 equals**，所以肯定是 true，但是问题来了……
```
String stringC = "hi";
String stringD = "hi";
System.out.println(stringC == stringD); // ?
System.out.println(stringC.equals(stringD)); // ?

String stringE = "hi";
String stringF = new String("hi");
System.out.println(stringE == stringF); // ?
System.out.println(stringE == stringF.intern()); // ?
System.out.println(stringE.equals(stringF)); // ?
```
这是一个非常有意思的思考题，我们知道 String 类是一个比较“特殊”的类，往往我们可以直接将字符串常量赋值给它而其他类不具备这样的特征。但是这个所谓的赋值常量为什么会对我们刚才梳理的 == 有影响呢？所以需要继续学习关于 String Constant Pool 的部分知识（你可以继续 Google 这个知识点，是个非常有意思的技术）。

此外，Java 还有一些非常有意思的类 Wrapper Class 例如：Integer, Short, Boolean 等等，我们知道这些类是用来取代 Primitive types 的，但是这些类型的 equals 与 == 是怎么一回事呢？
```
Integer integer1 = new Integer(1000);
Integer integer2 = new Integer(1000);
System.out.println(integer1 == integer2); // false
System.out.println(integer1.equals(integer2)); // true

Integer integer3 = 1000;
Integer integer4 = 1000;
System.out.println(integer3 == integer4); // ?
System.out.println(integer4.equals(integer4)); // true
```
比较有意思的是，System.out.println(integer3 == integer4); 的结果是 false，这与 String 类是不同的，但是以下的情况又不一样：
```
Integer integer5 = 100;
Integer integer6 = 100;
System.out.println(integer5 == integer6); // true
System.out.println(integer5.equals(integer6)); // true
```
如果你学习了部分 String Constant Pool 的知识，大约可以猜想到 Integer 类中，是不是也有点 magic ？这就需要你自己去研究了。**但是有一点是非常重要的，为什么我们要有这样的 magic 在 JDK 中？看起来给我们造成了麻烦，但是又给我们带来了什么好处？我可以从这样的设计学到什么？**

下来我们来说说 hashCode, 我们知道，如果你 override 了 equals 方法，必须 override hashCode 方法，我们这样做是为了维持 contract：如果两个类相等，其 hashCode 的返回值必然相等。大约是下面这个例子：
```
import java.util.Objects;
public class Sample {
    private String name;
    private Integer age;
    public Sample(String name, Integer age) {
        this.name = name;
        this.age = age;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Sample sample = (Sample) o;
        return Objects.equals(name, sample.name) &&
                Objects.equals(age, sample.age);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, age);
    }
}
```
关于这个 hashCode，我们需要重视两点：1\. 它可以对 HashMap 等集合有非常大的帮助；2\. 大多数默认的实现是内部地址的转换，但这并不是一定的。我在这里并不想展开的说明 hashCode 的作用，如果你感兴趣，可以参考官方文档，或者复习 hash 算法的部分知识。

虽然我们讲了一个很简单的知识点，但是留下了很多问题需要自己学习思考：

1.  String Constant Pool
2.  Integer Cache
3.  什么时候我需要 override equals 方法？
4.  Wrapper Class 与 Autoboxing and Unboxing
5.  什么是 hashCode？有什么用？
