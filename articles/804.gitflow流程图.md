---
title: "Git Flow 版本控制流程"
tags: 
status: publish
categories: 
- "工具"
---

[toc]

#### 背景
帮公司重新整理了下现状的分支，之前使用的从`dev`分支切出`release`分支的方法，一旦出现了线上bug需要`hotfix`，hotfix代码需要同时合并到`release`分支和`dev`分支。或者合并到`release`分支后再`merge`回开发分支...容易忘记或者变得很乱...

花了半天时间重新画了下流程图，后续期望能够按照这个执行吧...

#### 正常开发
![2021-12/github-version-gitflow_normal.png](https://github.com/EluvK/Image_server/raw/master/2021-12/github-version-gitflow_normal.png)


##### 新迭代开发分支

例如： 由`branch:master`或`tag:1.2.6`切出新迭代的`dev/1.2.7`分支。

* **开发组leader**在公共仓库里，**基于最新的`branch:master`/`tag:latest`**，切出新迭代的开发分支

* 该迭代开发分支完成所有特性合入后，由**开发组leader**/anyone发起PR，CI通过、相关开发CR无误后，QA准入`master`分支，打上对应版本tag。
* 迭代结束后，暂存开发分支直到下一个版本打上tag时删除，期间出现的`hotfix`需要现在该迭代分支上做验证。

##### 迭代内特性分支
例如： 所属于迭代1.2.7内的某个特性建立单独的特性分支，方便多位开发协同。由`dev/1.2.7`切出`feat/contract_frame`。

* 特性**开发owner**在自己仓库/公共仓库，**基于所属的开发分支**，切出该特性的开发分支。
* 特性分支的准入无CI要求，由owner控制。
* 基于的开发分支发生`rebase`时，特性分支的`rebase`工作由**开发owner**负责，记得完成后通知给其他相关开发。
* 特性分支PR进迭代分支，需要CI通过、相关开发CR、QA测试准入。


##### 特性协同开发
例如: 参与某特性的开发，基于owner仓库/公共仓库在自己仓库里切出开发分支。由`feat/contract_frame`切出`frame_1`。

---

#### 多迭代并行开发
![2021-12/github-version-gitflow_multi_version.png](https://github.com/EluvK/Image_server/raw/master/2021-12/github-version-gitflow_multi_version.png)


例如：当前迭代1.2.7进行中，并行有属于1.2.8的开发任务。

* **开发组leader**在公共仓库里，基于最新的版本Tag(`tag:1.2.6`)，切出新迭代的开发分支`dev/1.2.8`。
* 前一个迭代完成后，后一个迭代分支需要由开发leader进行`rebase`操作。
* 对迭代分支进行`rebase`操作后，需要公告出来，并重点通知给当前特性分支owner。特性分支owner执行`rebase`操作。并通知给相关开发提醒他们本地分支`pull --rebase`。
---


#### Hotfix
![2021-12/github-version-gitflow_hotfix.png](https://github.com/EluvK/Image_server/raw/master/2021-12/github-version-gitflow_hotfix.png)

`master`分支出现的问题，且需要立即修改换包的情况。

当`master`分支发生`hotfix`时，**开发组leader**需评估是否影响当前正在进行中的迭代分支。如果影响需要对迭代分支执行`rebase`操作。

对迭代分支进行`rebase`操作后，需要公告出来，并重点通知给当前特性分支owner。特性分支owner自己评估当前特性开发是否依赖该hotfix，依赖的话也执行`rebase`操作。并通知给相关开发提醒他们本地分支`pull --rebase`。

---