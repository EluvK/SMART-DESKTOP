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
### MEAT DATA
``` TEXT
---
title: "blog title"
tags: 
- "tag one"
- "tag two"
status: publish  # `draft` if is not finished.
categories: 
- "one"
- "two"
---
```
### How to use:
Keep draft file in `/draft` directory, and mv it in `/articles` when ready to publish.

``` BASH
git pull && git add . && git commit -m "update articles"
```
blog will sync your changes automatically by github action.

### todo list:
- [ ] could use github action to add url link in this README.md
- [ ] for now it's only `push` articles to website. lack of `pull` action.
