---
title: "Sizedness in Rust"
tags: 
status: publish
categories: 
- "Rust"
- "读书笔记"
---

[toc]

原blog: https://github.com/pretzelhammer/rust-blog/blob/master/posts/sizedness-in-rust.md

【更新中】

### Intro
`Sizedness` 的概念可能是 `Rust` 里最重要也最不起眼的一个，冷不防就会碰到类似于 `x doesn't have size known at compile time` (编译期无法确定x的大小)的错误。

术语解释：
|phrase|shorthand for|翻译|
|-|-|-|
| sizedness | property of being `sized` or `unsized` | 确定大小或不确定大小的这种特性 |
| `sized` type | type with a known size at compile time | 编译期可确定大小的类型 |
| 1) `unsized` type _or_<br>2) `DST` | dynamically-sized type, i.e. size not known at compile time | 编译器无法确定大小的类型 <br> 或者称之为动态大小类型
| `?sized` type | type that **may or may not be sized** | 可能是确定大小，也可能是不确定大小的类型 |
| unsized coercion | coercing a `sized` type into an `unsized` type | 强制把确定大小类型转为不确定大小类型 |
| `ZST` | zero-sized type, i.e. instances of the type are 0 bytes in size | 零大小类型 |
| `width` | single unit of measurement of pointer `width` | 指针宽度的测量单位 |
| 1) thin pointer _or_<br>2) `single-width` pointer | pointer that is _1 width_ | 窄指针<br>1个宽度的指针 |
| 1) fat pointer _or_<br>2) `double-width` pointer | pointer that is _2 widths_ | 宽指针<br>2个宽度的指针 |
| 1) pointer _or_<br>2) reference | some pointer of some `width`, `width` will be clarified by context | 宽度由上下文确定的指针 |
| slice | `double-width` pointer to a dynamically sized view into some array | 切片，用一个宽指针指向一个动态大小类型的视图 |

### Sizedness
* 在 `Rust` 中，如果一个类型的大小可以在编译期间确定，那么就说这个类型是 `sized` ，能够确定大小才能在栈( `stack` )上分配内存。确定大小的类型可以通过值传递、通过引用传递
* 如果一个类型的大小，在编译期间无法确定，那就是 `unsized` ，或者 `DST`。 `unsized` 类型只能通过引用传递。

#### Sized example:

##### 基础类型：

基本类型、以及由基本类型通过 结构体(`struct`)、元组(`tuple`)、枚举(`enum`)、定长数组(`arrays`)等方式(递归得)组成的类型，在考虑了填充、对齐(padding and alignment)后，可以比较直观的把字节数加起来得到确定的结果。

``` RUST
use std::mem::size_of;

fn main() {
    // primitives
    assert_eq!(4, size_of::<f32>());
    assert_eq!(8, size_of::<i64>());

    // tuple
    assert_eq!(16, size_of::<(i32, f32, i64)>());
    // tuple with padding
    assert_eq!(16, size_of::<(i32, i64)>());

    // fixed-size arrays
    assert_eq!(0, size_of::<[i32; 0]>());
    assert_eq!(16, size_of::<[i32; 4]>());

    #[allow(dead_code)]
    struct Point {
        x: i32,
        y: i32,
    }
    // struct
    assert_eq!(8, size_of::<Point>());

    // emums
    assert_eq!(8, size_of::<Option<i32>>());
}

```

##### 枚举
以下为尝试后能够成功编译运行的代码：
``` RUST
#![allow(dead_code)]
use std::mem::size_of;

fn main() {
    //enums of options
    assert_eq!(8, size_of::<Option<i32>>());
    assert_eq!(16, size_of::<Option<i64>>());

    //enums of result
    assert_eq!(8, size_of::<Result<i32, i32>>());
    assert_eq!(16, size_of::<Result<i32, i64>>());

    enum Color {
        Blue(i32),
        Red(i32),
        Green(i32),
    }
    assert_eq!(8, size_of::<Color>());

    enum Color2 {
        Blue(i32),
        Red(i32),
        Green(i64),
    }
    assert_eq!(16, size_of::<Color2>());
}

```
`Rust` 的枚举的size大小就有点复杂了，是一个[tagged union](https://en.wikipedia.org/wiki/Tagged_union)，详细的可以看看[Rustonomicon: Data Layout](https://doc.rust-lang.org/nomicon/repr-rust.html)。

简单来说就是除了用来保存枚举数据的空间，额外还需要一个表示是哪个枚举的 `tag` 的空间。
但是当枚举里是一个 `None` 和一个 `&T` 引用时，这个枚举的空间就显得没必要了。可以看以下这个例子：

``` RUST
#![allow(dead_code)]
use std::mem::size_of;

fn main() {
    enum MustOption<T> {
        Value(T),
    }

    enum MyOption<T> {
        Value(T),
        None,
    }

    #[repr(C)]
    enum MyOptionInC<T> {
        Value(T),
        None,
    }

    assert_eq!(4, size_of::<i32>());
    assert_eq!(8, size_of::<&i32>());
    assert_eq!(8, size_of::<MustOption<&i32>>());
    assert_eq!(8, size_of::<MyOption<&i32>>());
    assert_eq!(16, size_of::<MyOptionInC<&i32>>());
}

```

其中`#[repc(C)]`表示按照C的内存布局来操作，也就没有了 `Rust` 优化这种case下不必要的 `tag` （为了表示 `None` ）而节省的空间。这种标志在 `FFI` 场景下是很关键的的细节。其它表示方法参考[Rustonomicon: Data Layout - others reprs](https://doc.rust-lang.org/nomicon/other-reprs.html)


##### 指针大小
有点远了收回来，看一下指针的size。指针有窄指针和宽指针，分别用1个和2个 `width` 表示，一个 `width` 是8个字节，

* 对于**固定大小的对象**的指针，都是窄指针，一个 `width` 大小，只需要存储地址

``` RUST
use std::mem::size_of;

const WIDTH: usize = size_of::<&()>();

fn main() {
    assert_eq!(WIDTH, size_of::<&i32>());
    assert_eq!(WIDTH, size_of::<&&i32>());
    assert_eq!(WIDTH, size_of::<&mut i32>());
    assert_eq!(WIDTH, size_of::<Box<i32>>());
    assert_eq!(WIDTH, size_of::<&[i64; 10]>());
    assert_eq!(WIDTH, size_of::<fn(i32) -> i32>());
}

```

* 对于**不固定大小的对象**的指针，都是宽指针，两个 `width` 大小，因为需要存储地址+大小

``` RUST
use std::mem::size_of;

const WIDTH: usize = size_of::<&()>();
const DOUBLE_WIDTH: usize = 2 * WIDTH;

fn main() {
    struct UnsizedStruct {
        _unsized_slice: [i32],
    }

    assert_eq!(DOUBLE_WIDTH, size_of::<&str>()); // string slice
    assert_eq!(DOUBLE_WIDTH, size_of::<&[i32]>()); // i32 slice
    assert_eq!(DOUBLE_WIDTH, size_of::<&dyn ToString>()); // trait object
    assert_eq!(DOUBLE_WIDTH, size_of::<Box<dyn ToString>>()); // trait object
    assert_eq!(DOUBLE_WIDTH, size_of::<&UnsizedStruct>()) // unsized-type-ptr
}

```

#### 总结
Rust智能操作能够确定大小的对象，也就是 `Sized` 的对象，对于动态大小的对象，只能通过引用来操作，指针类型指向的对象可以是动态大小的，但是指针对象本身肯定也是 `Sized` 的。


### Sized Trait
`Sized` 这个Trait是自动实现的标记Trait (both `auto trait` && `marked trait`)，`auto trait` 也一定是 `marked trait` 但是反之不成立（比如之前的 `Eq` Trait就是一个 `marked trait`，需要程序员手动注明，告知编译器该类型具有自反性。
也就是说类型是否有 `Sized` 的Trait完全由编译器(根据其成员类型)判断并添加上默认空实现，而且也无法手动去掉这个Trait:

``` RUST
#![feature(negative_impls)]

// this type is Sized, Send, and Sync
// auto marked trait
struct Struct;

// opt-out of Send trait
impl !Send for Struct {} // ✅

// opt-out of Sync trait
impl !Sync for Struct {} // ✅

// can't opt-out of Sized
impl !Sized for Struct {} // ❌
```

#### 总结
`Sized` 是无法手动消除的`auto marked trait`。语言特性下的规则。


### 在泛型里的 `Sized` 

#### 泛型语法糖：
1. 实际上使用泛型时，编译器会默认加上 `Sized` 的泛型限制：
2. 当然我们也可以手动限制成 `?Sized` 的泛型类型
``` RUST
// normally we do:
fn func<T>(t: T) {}  // ✅

// de-sugar version:
fn func<T: Sized>(t: T) {} // ✅

// try mark `?Sized` ?
fn func<T: ?Sized>(t: T) {} // ❌ the size for values of type `T` 
                            // cannot be known at compilation time

// we can use ?Sized to mark a ref params:
fn func<T: ?Sized>(t: &T) {} // ✅
fn func<T: ?Sized>(t: Box<T>) {} // ✅
```

#### Example:
刚开始接触泛型时很可能会出现的问题：

``` RUST
use std::fmt::Debug;

fn debug<T: Debug>(t: T) { // T: Debug + Sized
    println!("{:?}", t);
}

fn main() {
    debug("my str"); // T = &str, &str: Debug + Sized ✅
}

```

一切正常，但是发现 `debug` 函数拿走了 `t` 的所有权，自然想到改成 `&T`：
``` RUST
use std::fmt::Debug;

fn debug<T: Debug>(t: &T) {
    // T: Debug + Sized
    println!("{:?}", t);
}

fn main() {
    debug("my str"); // now &T = &str,
                     // so   T =  str,
                     // str: Debug + ?Sized ❌
}

```
Boom! 编译器告诉你：**the trait `Sized` is not implemented for `str`**，强大的rustc甚至直接提示：考虑加上`?Sized`
``` TEXT
 --> src/main.rs:3:10
  |
3 | fn debug<T: Debug>(t: &T) {
  |          ^ required by this bound in `debug`
help: consider relaxing the implicit `Sized` restriction
  |
3 | fn debug<T: Debug + ?Sized>(t: &T) {
  |                   ++++++++

```
把 `debug` 函数的泛型限制加上 `?Sized` 后，此时传入的参数虽然是 `Unsized` 的，但是也在编译器的预期( `?Sized` )内，是引用就ok，执行成功。
``` RUST
use std::fmt::Debug;

fn debug<T: Debug + ?Sized>(t: &T) {
    // T: Debug + ?Sized
    println!("{:?}", t);
}

fn main() {
    debug("my str"); // &T = &str, T = str, str: Debug + !Sized ✅
}

```

#### 总结
1. 泛型类型会自动加上 `T: Sized` 的类型限制
2. 如果我们传入的是泛型 `T` 的引用类型，大多是时候不妨想清楚并写明此时 `T` 本身是否可以是动态大小类型，如果可以，加上 `T: ?Sized` 


### Unsized Type
`todo!()`

### Zero-Sized Types
`todo!()`
