---
title: "Learning Awk"
tags: 
status: draft
categories: 
- "读书笔记"
- "翻译"
- "工具"
- "Awk"
---

[toc]

## 说明
主要参考 [Understanding AWK](https://earthly.dev/blog/awk-examples/) 并在其上进行一些补充拓展。

### 其它参考资料列表
* [The GNU Awk User’s Guide](https://www.gnu.org/software/gawk/manual/html_node/index.html) 官方文档永远是看花里胡哨blog迷惑时解惑的地方。


## 背景
![todo]

### What is Awk
`Awk`是一个记录处理工具，1977年由Aho、Kernighan和Weinberger编写，也正是这三位的名字缩写。`grep`可以按行搜索，`sed`可以按行做文本替换，`awk`则是可以按行做计算。
> If grep lets you search for lines, and sed lets you do replacements in lines then awk was designed to let you do calculations on lines. 

### How to pronounce 'Awk'
在一个远古论坛找到了一个年龄和我差不多大的帖子：[How to pronounce 'awk'?](http://computer-programming-forum.com/11-awk/2b3847ea18e1b35a.htm)，就按照`hawk [hɔːk]`的同音来读了。

### How to install Awk
Linux系统自带，mac如果没有，用Homebrew(`brew install gawk`)装。

``` BASH
$ awk --version
GNU Awk 4.0.2
Copyright (C) 1989, 1991-2012 Free Software Foundation.
```

## TO BEGIN WITH
### Awk Print
默认情况下，`Awk`接受标准输入，输出标准输出，使用`Awk`做的最简单的事情就是打印输入的内容：
``` BASH
$ echo "one two three" | awk '{ print }'
one two three
```
注： `{` 和 `}` 作为分隔符号，包含了一个`action`，实际上，`Awk`的语法，整体上就是一句句的`pattern { action }`，在后面的更多例子中慢慢体会。

打印的时候也可以选择打印哪一列，或者哪一个值域(**fields** is a much more precise description)：
``` BASH
$ echo "one two three" | awk '{ print $1 }'
one 
$ echo "one two three" | awk '{ print $2 }'
two 
$ echo "one two three" | awk '{ print $3 }'
three 
```
这里的序号是从1开始的，0表示一整行：
``` BASH
$ echo "one two three" | awk '{ print $0 }'
one two three
```

最开始说了，`Awk`是按行操作的，上面几个例子都是只有一行输入，如果有多行输入：
``` BASH
$ echo "
 one two three
 four five six" \
| awk '{ print $1, $2 }'

one two
four five
```

除了`$1`,`$2`,..., 还有`$NF`和`$NR`两个特殊变量，`NF`表示`number of fields`，`NR`表示`number of records`。前者表示一行里面一共有多少个`fields`，后者表示当前处理了多少行(从1开始)，这两个变量本身的值就是一个数，如果再带上$，就会得到对应的`fields`里的值了，体会一下下面两个例子：
``` BASH
$ echo "one two three
 four five six
 seven eight nine " \
 | awk '{ print NR, NF }'

1 3
2 3
3 3
```
``` BASH
$ echo "one two three
 four five six
 seven eight nine " \
 | awk '{ print $NR, $NF }'

one three
five six
nine nine 
```
基本可以理解，`{ print NR }`是有意义的，而`{ print $NR }`可能很难找到使用的场合。另外 `$NF` 还可以用来计算倒数第几个：
``` BASH
$ echo "one two three
 four five six
 seven eight nine " \
 | awk '{ print $(NF-1) }'

two
five
eight
```

## SPEED UP
### 获取一些sample数据用来练习

``` BASH
$ curl https://s3.amazonaws.com/amazon-reviews-pds/tsv/amazon_reviews_us_Digital_Video_Games_v1_00.tsv.gz \
| gunzip -c >> gamereviews.tsv
```

* 其它数据集可以从 https://s3.amazonaws.com/amazon-reviews-pds 里找找。
* 完全下载下来压缩包26.2MB，解压出来约70MB文本，`wc -l `显示一共有145432行。可以在`gunzip -c`命令后加上`| head -n 10000`获取前n行。

### 数据集格式
``` BASH
$ head -n 2 gameviews.tsv
marketplace	customer_id	review_id	product_id	product_parent	product_title	product_category	star_rating	helpful_votes	total_votes	vine	verified_purchase	review_headline	review_body	review_date
US	21269168	RSH1OZ87OYK92	B013PURRZW	603406193	Madden NFL 16 - Xbox One Digital Code	Digital_Video_Games	2	2	3	N	N	A slight improvement from last year.	I keep buying madden every year hoping they get back to football. This years version is a little better than last years -- but that's not saying much.The game looks great. The only thing wrong with the animation, is the way the players are always tripping on each other.<br /><br />The gameplay is still slowed down by the bloated pre-play controls. What used to take two buttons is now a giant PITA to get done before an opponent snaps the ball or the play clock runs out.<br /><br />The turbo button is back, but the player movement is still slow and awkward. If you liked last years version, I'm guessing you'll like this too. I haven't had a chance to play anything other than training and a few online games, so I'm crossing my fingers and hoping the rest is better.<br /><br />The one thing I can recommend is NOT TO BUY THE MADDEN BUNDLE. The game comes as a download. So if you hate it, there's no trading it in at Gamestop.	2015-08-31
```
第一行是表头，代表下面每一行中每一列的含义：
``` TEXT
DATA COLUMNS:
01  marketplace       - 2 letter country code of the marketplace where the review was written.
02  customer_id       - Random identifier that can be used to aggregate reviews written by a single author.
03  review_id         - The unique ID of the review.
04  product_id        - The unique Product ID the review pertains to. 
05  product_parent    - Random identifier that can be used to aggregate reviews for the same product.
06  product_title     - Title of the product.
07  product_category  - Broad product category that can be used to group reviews 
08  star_rating       - The 1-5 star rating of the review.
09  helpful_votes     - Number of helpful votes.
10  total_votes       - Number of total votes the review received.
11  vine              - Review was written as part of the Vine program.
12  verified_purchase - The review is on a verified purchase.
13  review_headline   - The title of the review.
14  review_body       - The review text.
15  review_date       - The date the review was written.
```

回归之前的print第几列：可以这样试一试：
``` BASH
$ awk '{print $1}' gamereviews.tsv | head 
marketplace
US
US
US
US
US
US
US
US
US

$ awk '{print $2}' gamereviews.tsv | head 
customer_id
21269168
133437
45765011
113118
22151364
22151364
38426028
6057518
20715661

$ awk '{print $3}' gamereviews.tsv | head 
review_id
RSH1OZ87OYK92
R1WFOQ3N9BO65I
R3YOOS71KM5M9
R3R14UATT3OUFU
RV2W9SGDNQA2C
R3CFKLIZ0I2KOB
R1LRYU1V0T3O38
R44QKV6FE5CJ2
R2TX1KLPXXXNYS

# ......
```
打到第6列**标题**的时候，结果开始不对劲了：
``` BASH
$ awk '{print $6}' gamereviews.tsv | head 
product_title
Madden
Xbox
Command
Playstation
Saints
Double
Sims
Playstation
Playstation
```
至少上面看过，第二行，也就是第一条review，title应该是`Madden NFL 16 - Xbox One Digital Code`，而这里只切割出来的第一个单词。

原因就是，`Awk`默认以` `，一个空格作为区分一行中不同`fileds`的分隔符`Field Separators`。

### Field Separators
使用参数` -F '{your separators}' ` 来覆盖默认的空格分隔符，这个数据集里的分隔符都是一个`tab`，所以上面的命令可以改为：
``` BASH
$ awk -F '\t' '{print $6}' gamereviews.tsv | head 
product_title
Madden NFL 16 - Xbox One Digital Code
Xbox Live Gift Card
Command & Conquer The Ultimate Collection [Instant Access]
Playstation Plus Subscription
Saints Row IV - Enter The Dominatrix [Online Game Code]
Double Dragon: Neon [Online Game Code]
Sims 4
Playstation Network Card
Playstation Network Card
```

> Noted: By default, awk does more than split the input on spaces. It splits based on one or more sequence of space or tab or newline characters. In addition, any of these three characters at the start or end of input gets trimmed and won’t be part of field contents. Newline characters come into play if the record separator results in newline within the record content.


再回顾一下之前的`NF`和`NR`，获取一下最后一行的日期(15  review_date)、第8个评分(08  star_rating)以及倒数第三个(13  review_headline)：
``` BASH
$ awk -F '\t' '{print NR,$NF,$8,$(NF-2) }' gamereviews.tsv | head -n 10
1 review_date star_rating review_headline
2 2015-08-31 2 A slight improvement from last year.
3 2015-08-31 5 Five Stars
4 2015-08-31 5 Hail to the great Yuri!
5 2015-08-31 5 Five Stars
6 2015-08-31 5 Five Stars
7 2015-08-31 5 Five Stars
8 2015-08-31 4 i like the new skills like herbalism in this
9 2015-08-31 5 Five Stars
10 2015-08-31 5 Easy & Fast
```

### Pattern Match With Regular Expressions
至此都是在对每一行进行操作，`Awk`实际包含模式匹配，之前提过，`Awk`的语法实际上是一条条的`pattern { action }`，目前我们也只用上了`{print}`这个`action`。

关于模式匹配，一个简单的例子：
``` BASH
$ echo "aa 1
bb 2
cc 3" | awk -F ' ' '/bb/ {print $2}'
2
```
可以看到，对于awk扫描的三行数据，只有匹配到了`bb`的第二行，运行了`print`的`action`。这里的`/bb/`就是`pattern`。

回到之前的数据集，比如我想匹配`Minecraft`这个游戏的reviews，看看大家的评分，这么写：
``` BASH
$ awk -F '\t' '/Minecraft/ {print $6, $8}' gamereviews.tsv | head
Minecraft for PC/Mac [Online Game Code] 4
Minecraft for PC/Mac [Online Game Code] 5
Xbox 360 Live Points Card 5
Minecraft for PC/Mac [Online Game Code] 2
Minecraft for PC/Mac [Online Game Code] 5
Minecraft - Xbox 360 5
Minecraft for PC/Mac [Online Game Code] 1
Nom Nom Galaxy  - PS4 [Digital Code] 4
Minecraft - Xbox One Digital Code 5
Minecraft for PC/Mac [Online Game Code] 4
```
确实过滤出来了`Minecraft`，但是同时，任何字段里面带有`Minecraft`的reviews都被统计进来了，包括任何提及它的别的游戏的reviews:
``` BASH
$ awk -F '\t' '/Minecraft/ {print $6, $8}' gamereviews.tsv | sort | uniq
8BitMMO [Game Connect] 2
Ace of Spades: Battle Builder [Online Game Code] 5
Agricultural Simulator Historical Farming [Download] 1
Bioschock Infinite: Clash in the Clouds 5
Blini Kids: Animals [Download] 5
Blockland 4
Blockland 5
Blockstorm [Download] 4
Borderlands 2 5
Call of Duty 4: Modern Warfare [Download] 5
# ...... more
```

所以还需要针对某个字段进行匹配：`pattern`可以写成`$6 ~ /Minecraft/ `来模糊匹配`06 product_title`里面有`Minecraft`的
``` BASH
$ awk -F '\t' ' $6 ~ /Minecraft/ {print $4,$6,$8} ' gamereviews.tsv | head 
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 4
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 5
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 2
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 5
B010BWCOWI Minecraft - Xbox 360 5
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 1
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 5
B00NMO0IA8 Minecraft - Xbox One Digital Code 5
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 4
B010KYDNDG Minecraft for PC/Mac [Online Game Code] 4
```

或者根据我们确认到的`04  product_id`值`B010KYDNDG`来准确匹配所有的`Minecraft for PC/Mac [Online Game Code]`，使用`$4 == "B010KYDNDG"`:
``` BASH
$ awk -F '\t' '$4 == "B010KYDNDG" {print $6, $8} ' gamereviews.tsv | head
Minecraft for PC/Mac [Online Game Code] 4
Minecraft for PC/Mac [Online Game Code] 5
Minecraft for PC/Mac [Online Game Code] 2
Minecraft for PC/Mac [Online Game Code] 5
Minecraft for PC/Mac [Online Game Code] 1
Minecraft for PC/Mac [Online Game Code] 5
Minecraft for PC/Mac [Online Game Code] 4
Minecraft for PC/Mac [Online Game Code] 4
Minecraft for PC/Mac [Online Game Code] 5
Minecraft for PC/Mac [Online Game Code] 5
```
已经精确匹配了`$4 == "B010KYDNDG"`，修改一下print的字段，依次打印`15:review_date, 13:review_headline, 08:star_rating`
``` BASH
$ awk -F '\t' '$4 == "B010KYDNDG" {print $15, $13, $8} ' gamereviews.tsv | head
2015-08-31 FUN 4
2015-08-31 ... have disks for games as a backup it was nice to be able to get the code then start ... 5
2015-08-30 Would rather a disk. There always seems to be ... 2
2015-08-29 Five Stars 5
2015-08-27 Very Disappointed Dad and Birthday Boy 1
2015-08-26 Five Stars 5
2015-08-24 Four Stars 4
2015-08-24 My son says it is fun. He likes it but we were a little ... 4
2015-08-24 MINECWAFT 5
2015-08-22 MINECRAFT!!! 5
```

总结一下：
* `Awk`的语法`pattern { action }`。
* 模糊正则匹配：`\regexp\`
* 针对字段模糊匹配： `$n ~ \regexp\` ,`~`表示匹配上, `!~`表示不匹配
* 针对字段精确匹配： `$n == "value"`

### Use printf