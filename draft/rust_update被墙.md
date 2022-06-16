---
title: "解决`rust update`更新失败"
tags: 
- "shortcuts"
status: publish
categories: 
- "rust"
---



更改`rustup update`的目标地址的环境变量：`RUSTUP_DIST_SERVER`（默认指向 https://static.rust-lang.org）和 `RUSTUP_UPDATE_ROOT` （默认指向https://static.rust-lang.org/rustup）
``` TEXT
# 换成中科大的源
RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static 
RUSTUP_UPDATE_ROOT=https://mirrors.ustc.edu.cn/rust-static/rustup
```

命令如下： 
`RUSTUP_DIST_SERVER=https://mirrors.ustc.edu.cn/rust-static RUSTUP_UPDATE_ROOT=https://mirrors.ustc.edu.cn/rust-static/rustup rustup update`

💊