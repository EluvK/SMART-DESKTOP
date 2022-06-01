---
title: "Use Rust lib in C/C++ project"
tags: 
- "FFI"
status: draft
categories: 
- "Rust"
- "C++"
---

[toc]

## 背景
最近把EVM虚拟机引入到公司项目里，EVM虚拟机本身的实现依赖的是第三方Rust写的[rust-blockchain/evm](https://github.com/rust-blockchain/evm)，公司的项目是C++开发的，所以需要把整个EVM作为静态库引入进来，之间的FFI交互本身需要（只能）按照C的格式传递，两端再封装一下，让使用起来舒适一些。

这个过程中搜到的资料都非常零散，在不断试错、优化的过程中也积累一些经验，如果读者也有需求要把第三方的**rust库引入到C/C++项目**里，可以参考一下~

如果你也是接触rust的跨语言FFI不久，可以先阅读[官方book的FFI介绍](https://doc.rust-lang.org/nomicon/ffi.html)


## 解决跨语言的调用和编译依赖问题
这一节举例说明解决跨语言的编译问题，用统一的CMake工具来管理编译跨语言的不同模块

### `C call Rust` && `Rust call C` 说明
如果第三方的lib功能比较简单纯粹，一般只需要单向的使用。然而我实际上需要先提供给EVM一些C这边的功能，再把EVM封装起来提供给C，所以两种都涉及到了。

这里需要先提一下工具链，主项目是通过`CMake`来管理模块关系的，我需要把一个capi的模块提供给rustlib使用，再把rustlib作为一个模块提供给其它模块使用：

**依赖关系：capi.a(C/C++) -> rust_evm.a(Rust) -> xxx.a(C/C++)**

后面的以这三个模块名举例说明

每个模块下都有各自的`CMakeLists.txt`，包括rustlib模块：此时的目录结构大致是这样的：
``` BASH
$ tree .
.
├── capi
│   ├── capi.cpp
│   └── CMakeLists.txt
├── rust_evm
│   ├── Cargo.toml
│   ├── CMakeLists.txt
│   └── src
│       └── main.rs
└── xxx
    ├── CMakeLists.txt
    └── xxx.cpp

```

### `rust_evm` 依赖 `capi` : `Rust call C`

#### `Rust Call C`
使用`extern "C" {}`来把需要c提供的接口包起来，另外还可以用`mod`来增强代码可读性：
比如：
``` RUST
pub(crate) mod exports {
    #[link(name = "capi")]
    extern "C" {
        pub(crate) fn evm_read_register(register_id: u64, ptr: u64);
        pub(crate) fn evm_register_len(register_id: u64) -> u64;
    }
}
```
在其他地方就可以通过：
``` RUST
unsafe {
    //...
    exports::evm_read_register(...);
    //...
}
```
的方式来使用`capi.a`里提供的方法了。

上面第二行的 `#[link(name = "capi")]` 用于告诉链接器链接指定的库，但是我在实操的时候发现，在后面`build.rs`里写上链接lib后，不写这个link宏其实也没问题(写于2022-05，rust 1.60版本)，读者可以自行尝试。

#### 让 `CMake` 来管理编译 `rust_evm`
上面的方式，手动编译出 `capi.a` 后执行 `cargo build` 可以使用，通过 `CMake` 来管理的话，需要完成：
1. 在 `build.rs` 里完成复制 `capi.a` 的操作，不然后面编译`rust_evm`时找不到链接的依赖。
2. 让 `CMake` 执行 `cargo build` 的编译命令

##### 写一下 `build.rs`
``` RUST
#![allow(unused)]
use std::env;

use std::process::Command;

#[cfg(feature = "build_with_cmake")]
fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();

    Command::new("cp")
        .arg("-f")
        .arg(&format!(
            "{}/../../../../../../../lib/Linux/libcapi.a",
            out_dir
        ))
        .arg(&format!("{}", out_dir))
        .status()
        .unwrap();

    println!("cargo:rustc-link-search=native={}", out_dir);
    println!("cargo:rustc-link-lib=static=capi");
}

#[cfg(not(feature = "build_with_cmake"))]
fn main() {}

```

注意几点：
1. 使用`cp`命令复制`libcapi.a`，需要弄清楚当前CMake项目，保管目标lib的目录，一般会通过根CMake文件设置到`LIBRARY_OUTPUT_PATH`（更新的 `cmake` 版本里也可能用 `LIBRARY_OUTPUT_DIRECTORY` ?）。需要从当前的目录相对路径到此处复制（到 `cargo` 的 `out_dir` ）。
2. 可以使用 `feature` 来控制不同场景的编译，后面会提到，用 `cmake` 编译的时候可以附带 `feature` 参数，所以可以默认情况下没有编译前参数，用于单独管理这个rust子项目的情况；在 `cmake` 编译时自动带上 `feature` 参数，启用这个复制命令。

##### `rust_evm` 的 `CMakeLists.txt`
放一下参考配置： `rust_evm/CMakeLists.txt`
``` CMake
# find cargo
execute_process (
    COMMAND bash -c "which cargo | grep 'cargo' | tr -d '\n'"
    OUTPUT_VARIABLE CARGO_DIR
)

execute_process (
    COMMAND ${CARGO_DIR} --version
)

# set build command:
message(STATUS "Cargo dir: " ${CARGO_DIR})
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
set(CARGO_CMD ${CARGO_DIR} build --features=build_with_cmake)
set(TARGET_DIR "debug")
else ()
set(CARGO_CMD ${CARGO_DIR} build --features=build_with_cmake --release)
set(TARGET_DIR "release")
endif ()

message(STATUS "Cargo cmd: " ${CARGO_CMD})
set(EVM_A "${CMAKE_CURRENT_BINARY_DIR}/${TARGET_DIR}/librust_evm.a")
message(STATUS "EVM_A: " ${EVM_A} )
message(STATUS "CMAKE_CURRENT_BINARY_DIR: " ${CMAKE_CURRENT_BINARY_DIR})
message(STATUS "CMAKE_CURRENT_SOURCE_DIR: " ${CMAKE_CURRENT_SOURCE_DIR})
message(STATUS "LIBRARY_OUTPUT_PATH: " ${LIBRARY_OUTPUT_PATH})

# custom_compile && cp
add_custom_target(rust_evm ALL
    COMMAND CARGO_TARGET_DIR=${CMAKE_CURRENT_BINARY_DIR} ${CARGO_CMD} 
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND cp -f ${EVM_A} ${LIBRARY_OUTPUT_PATH})

set_target_properties(rust_evm PROPERTIES LOCATION ${LIBRARY_OUTPUT_PATH})

add_dependencies(rust_evm capi)
```

这个配置需要根据项目实际情况做调整，需要理解其含义。忽略中间的编译调试信息，核心步骤就是三步：
1. find cargo:
2. set build command:
3. custom_compile && cp to library output path:

补充说明：
* `EVM_A` 表示使用 `cargo` 工具链编译出来的 `rust_evm` 静态库的位置
* `LIBRARY_OUTPUT_PATH` 就是整个项目的位置，需要复制过去供后面其他模块链接使用。
* `add_custom_target` 来调用 `cargo` 编译这个模块
* 最后的`add_dependencies` 来确定编译的拓扑关系，确保编译到这一步时，前面的`build.rs`一定能找到编译好的 `libcapi.a`


至此我们已经完成了`Rust call C`的依赖关系，并且把 `rust_evm` 也编译成了 `librust_evm.a` 放到了目标lib目录下。

### `xxx` 依赖 `rust_evm` : `C call Rust`
#### `xxx` 模块的 cmake:
在`xxx/CMakeLists.txt`下加上依赖关系：
``` CMake
add_dependencies(xxx rust_evm)
get_target_property(RUST_EVM_DIR rust_evm LOCATION)
target_link_libraries(xxx PRIVATE ${RUST_EVM_DIR}/librust_evm.a)
```
其中第二行：get_target_property获取的就是 `librust_evm.a` ，是在编译`rust_evm`时通过`set_target_properties` 设置进去的

#### `C call Rust`
模块 `xxx` 这边找个地方声明一下外部实现：就可以直接调用了。
``` CPP
extern "C" bool call_contract();
```
噢，在 `rust_evm` 提供的接口这样写：
``` RUST
mod interface{
    #[no_mangle]
    pub extern "C" fn call_contract() -> bool {
        todo!()
    }
}
```


## 优化使用体验：（TODO）
### 待更新
todo list:
- [ ] 传参 or 统一管道管理
- [ ] 使用 protobuf 来传递跨语言参数。

## 注意点：（TODO）
### 待更新
todo list:
- [ ] 考虑好内存对象的生命周期，由谁创建、管理、释放。