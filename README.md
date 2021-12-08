---
title: "SMART DESKTOP"
tags: 
status: draft
categories: 
- "建站"
- "markdown"
---


# SMART-DESKTOP

Use markdown to write blog.

Use github action to publish articles to your website automatically.

This repo will keep all my blog in [website](https://blog.eluvk.cn).

> most of the github action && python scripts is reference from this repo[zhaoolee/WordPressXMLRPCTools](https://github.com/zhaoolee/WordPressXMLRPCTools).

Feel free to copy && modified this repo's code. 

### Directories Struct
``` TEXT
/articles : posted articles.
/draft: draft articles.
/auto-publish : python scripts that post articles
```


### todo list:
- [ ] could use github action to add url link in this README.md
- [ ] for now it's only `push` articles to website. lack of `pull` action.

### some shortcut

#### snippets:
edit `markdown.json` in vscode:
``` JSON
"markdown_meta":{
    "prefix": "meta",
    "body": [
        "---",
        "title: \"$1\"",
        "tags: $2",
        "status: ${3|publish,draft|}", 
        "categories: ",
        "- \"${4|读书笔记,ProtocolBuffer,C++,模板,Rust,Trait,网络,摘抄,建站,Code,PAT,数据结构,二叉树|}\"",
        "---",
    ],
    "description": "auto impl markdown meta data header"
},
"img herf":{
    "prefix": "!img",
    "body":[
        "![$1/$2](https://github.com/EluvK/Image_server/raw/master/$1/$2)"
    ],
    "description": "auto impl img herf  month folder && name"
},
"code block for cpp":{
    "prefix": "cbc",
    "body":[
        "``` CPP",
        "$1",
        "```"
    ],
    "description": "auto impl code block for language cpp"
},
// ... more 
```

