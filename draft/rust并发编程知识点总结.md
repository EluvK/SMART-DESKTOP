---
title: "rust 并发编程知识点总结"
tags: 
status: draft
categories: 
- "Rust"
- "Concurrent"
---


[toc]

## todo list:
- [x] 使用多线程 
- [x] 线程同步：channel
- [ ] 线程同步：锁、条件变量

## 使用多线程
### 创建线程
``` RUST
use std::thread;
use std::time::Duration;

fn main() {
    thread::spawn(|| {
        for i in 1..10 {
            println!("spawn thread: {}", i);
            thread::sleep(Duration::from_millis(1));
        }
    });

    for i in 1..5 {
        println!("main thread : {}", i);
        thread::sleep(Duration::from_millis(2));
    }
}

```

> 线程执行顺序不定，不可依赖于线程在代码中的顺序

### 等待线程结束 `join`
``` RUST
use std::thread;
use std::time::Duration;

fn main() {
    let handle = thread::spawn(|| {
        for i in 1..10 {
            println!("spawn thread: {}", i);
            thread::sleep(Duration::from_millis(1));
        }
    });

    // handle.join().unwrap(); // spawn 线程执行完毕后继续

    for i in 1..5 {
        println!("main thread : {}", i);
        thread::sleep(Duration::from_millis(2));
    }

    handle.join().unwrap();
}

```

### 线程获取所有权 `move`
``` RUST
use std::thread;

fn main() {
    let v = vec![1, 2, 3];

    let handle = thread::spawn(move || {
        println!("Got a vector: {:?}", v);
    });

    handle.join().unwrap();

    // borrow of moved value: `v` value borrowed here after move
    // println!("{:?}", v);
}

```

### 线程屏障 `Barrier`
``` RUST
use std::sync::{Arc, Barrier};
use std::thread;

fn main() {
    let mut handles = Vec::with_capacity(6);
    let barrier = Arc::new(Barrier::new(3));

    for _ in 0..6 {
        let b = barrier.clone();
        handles.push(thread::spawn(move || {
            println!("before wait");
            b.wait();
            println!(" after wait");
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }
}

```

### 线程局部变量 `thread_local!`
``` RUST
use std::cell::RefCell;
use std::thread;

fn main() {
    thread_local!(static FOO:RefCell<u32> = RefCell::new(1));

    FOO.with(|f| {
        assert_eq!(*f.borrow(), 1);
        *f.borrow_mut() = 2;
    });

    let t = thread::spawn(move || {
        FOO.with(|f| {
            assert_eq!(*f.borrow(), 1);
            *f.borrow_mut() = 3;
        });
    });

    t.join().unwrap();
    FOO.with(|f| {
        assert_eq!(*f.borrow(), 2);
    });
}

```

> 每个新线程访问时都会以初始值作为开始。且各个线程的局部变量互不干扰。


### 条件变量 `Condvar`

``` RUST
use std::sync::{Arc, Condvar, Mutex};
use std::thread;
use std::time::Duration;

fn main() {
    let pair = Arc::new((Mutex::new(false), Condvar::new()));
    let pair2 = pair.clone();

    thread::spawn(move || {
        thread::sleep(Duration::from_secs(1));
        let &(ref lock, ref cvar) = &*pair2;
        let mut started = lock.lock().unwrap();
        println!("set started = true");
        *started = true;
        cvar.notify_one();
    });

    let &(ref lock, ref cvar) = &*pair;
    let mut started = lock.lock().unwrap();
    while !*started {
        started = cvar.wait(started).unwrap();
    }
    println!("started is true");
}

```

### 唯一初始化 `Once`
``` RUST
use std::sync::Once;
use std::thread;

static mut VAL: usize = 0;
static INIT: Once = Once::new();

fn main() {
    let handle1 = thread::spawn(move || {
        INIT.call_once(|| unsafe {
            VAL = 1;
        });
    });
    let handle2 = thread::spawn(move || {
        INIT.call_once(|| unsafe {
            VAL = 2;
        });
    });

    handle1.join().unwrap();
    handle2.join().unwrap();

    println!("{}", unsafe { VAL });
}

```

## 线程同步：消息传递
### 消息通道 `channel`

#### 阻塞的 `recv()`
``` RUST
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        thread::sleep(Duration::from_secs(1)); // take some time.
        tx.send(1).unwrap();
    });
    println!("receive {}", rx.recv().unwrap());
}

```

> `pub fn channel<T>() -> (Sender<T>, Receiver<T>)` 上例的泛型`T`在`send(1)`时被推导出来。

#### 不阻塞的 `try_recv()`
``` RUST
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        thread::sleep(Duration::from_millis(1)); // take some time.
        tx.send(1).unwrap();
    });

    println!("receive {:?}", rx.try_recv()); // receive Err(Empty)
    thread::sleep(Duration::from_millis(10));
    println!("receive {:?}", rx.try_recv()); // receive Ok(1)
    thread::sleep(Duration::from_millis(10));
    println!("receive {:?}", rx.try_recv()); // receive Err(Disconnected)
}

```

#### 传递所有权
> 若值的类型实现了`Copy`特征，则直接复制一份该值，然后传输过去，例如之前的`i32`类型
> 若值没有实现`Copy`，则它的所有权会被转移给接收端，在发送端继续使用该值将报错

``` RUST
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        let s = String::from("string");
        tx.send(s).unwrap();

        // borrow of moved value: `s` value borrowed here after move
        // println!("try use string: {:?}",s);
    });

    println!("receive {:?}", rx.recv().unwrap());
}

```

#### 多次发送
``` RUST
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        tx.send(1u8).unwrap();
        tx.send(2u8).unwrap();
        tx.send(3u8).unwrap();
    });

    for recvd in rx.iter() {
        println!("Got : {}", recvd);
    }
}

```

> 上面的`rx : Receiver<u8>`。`Receiver`实现了Trait: `Iter`

#### 多个发生者
``` RUST
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    let tx1 = tx.clone();

    thread::spawn(move || {
        tx.send(1u8).unwrap();
    });

    thread::spawn(move || {
        tx1.send(2u8).unwrap();
    });

    for recvd in rx.iter() {
        println!("Got : {}", recvd);
    }
}

```

> 注意只有所有发送者对象都drop掉，接收者才会跳出循环，最终结束。以下代码会卡死在等不到的`recv()`里，只有手动加上一行drop原始的发生者才行。
``` RUST
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    let tx1 = tx.clone();
    let tx2 = tx.clone();

    thread::spawn(move || {
        tx1.send(1u8).unwrap();
    });

    thread::spawn(move || {
        tx2.send(2u8).unwrap();
    });

    // need to add this .
    // drop(tx);

    for recvd in rx.iter() {
        println!("Got : {}", recvd);
    }
}

```

#### 消息顺序
同一个channel里，消息会严格FIFO。

### 同步消息通道
之前的`channel`，是默认的`async`，同步的消息通道使用：`std::sync::mpsc::sync_channel`：
`pub fn sync_channel<T>(bound: usize) -> (SyncSender<T>, Receiver<T>);`

``` RUST
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::sync_channel(0);

    thread::spawn(move || {
        println!("before send 1"); // --- seq 0
        tx.send(1u8).unwrap();
        println!("after send 1"); // --- seq 2
        println!("before send 2");
        tx.send(2u8).unwrap();
        println!("after send 2");
    });

    println!("before sleep");
    thread::sleep(Duration::from_micros(1));
    println!("after sleep");
    for recvd in rx.iter() {
        println!("Got : {}", recvd); // --- seq 1
    }
}

```
> 运行以上代码，可以观察到：子线程发送完`1`以后，需要等到主线程`Got 1`，才会正在完成`send`操作，再打印处的`after send 1`
> `sync_channel`的构造函数参数实际就是通道缓存区的大小，表示在到达这个大小之前，都是异步的，大于这个大小的操作就会阻塞住。

### 传输多种类型：
`channel`里只能传递同一种类型。这个在创建channel的时候就决定了。但是可以使用Rust强大的枚举来把不同类型的消息通过同一个`channel`传递：
``` RUST
use std::sync::mpsc;
use std::thread;

enum Fruit {
    Apple(u8),
    Orange(String),
}

fn main() {
    let (tx, rx) = mpsc::channel::<Fruit>();

    thread::spawn(move || {
        tx.send(Fruit::Apple(2)).unwrap();
        tx.send(Fruit::Orange("sweet".to_string())).unwrap();
    });

    for recvd in rx.iter() {
        match recvd {
            Fruit::Apple(count) => println!("received {} apples", count),
            Fruit::Orange(flavor) => println!("received {} oranges", flavor),
        }
    }
}

```