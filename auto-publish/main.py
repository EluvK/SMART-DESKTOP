from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost, EditPost
from urllib.parse import urlparse
import frontmatter
import time
import os
from hashlib import md5, sha1
import json
import markdown
from mdx_gfm import GithubFlavoredMarkdownExtension
import re
import urllib.parse

config_file_txt = ""

if((os.path.exists(os.path.join(os.getcwd(), "local.config")) == True)):
    config_file_txt = os.path.join(os.getcwd(), "local.config")
else:
    config_file_txt = os.path.join(os.getcwd(), "sample.config")

config_info = {}


with open(config_file_txt, 'rb') as f:
    config_info = json.loads(f.read())

username = config_info["USERNAME"]
password = config_info["PASSWORD"]
xmlrpc_php = config_info["XMLRPC_PHP"]

try:
    if(os.environ["USERNAME"]):
        username = os.environ["USERNAME"]

    if(os.environ["PASSWORD"]):
        password = os.environ["PASSWORD"]

    if(os.environ["XMLRPC_PHP"]):
        xmlrpc_php = os.environ["XMLRPC_PHP"]
except:
    print("无法获取github的secrets配置信息,开始使用本地变量")


url_info = urlparse(xmlrpc_php)

domain_name = url_info.netloc


wp = Client(xmlrpc_php, username, password)

# 获取已发布文章id列表


def get_posts():
    print(time.strftime('%Y-%m-%d-%H-%M-%S')+"开始从服务器获取文章列表...")
    posts = wp.call(GetPosts(
        {'post_status': 'publish', 'post_type': 'post', 'number': 1000000000}))
    post_link_id_list = []
    for post in posts:
        post_link_id_list.append({
            "id": post.id,
            "title": post.title,
            "link": urllib.parse.unquote(post.link),
        })
    print("### 文章数量 : {0}".format(len(post_link_id_list)))
    return post_link_id_list

# 创建post对象


def create_post_obj(title, content, link, post_status, terms_names_post_tag, terms_names_category):
    post_obj = WordPressPost()
    post_obj.title = title
    post_obj.content = content
    post_obj.link = link
    post_obj.post_status = post_status
    post_obj.comment_status = "open"
    # print(post_obj.link)
    post_obj.terms_names = {
        # 文章所属标签，没有则自动创建
        'post_tag': terms_names_post_tag,
        # 文章所属分类，没有则自动创建
        'category': terms_names_category
    }

    return post_obj


# 新建文章
def new_post(title, content, link, post_status, terms_names_post_tag, terms_names_category):

    post_obj = create_post_obj(
        title=title,
        content=content,
        link=link,
        post_status=post_status,
        terms_names_post_tag=terms_names_post_tag,
        terms_names_category=terms_names_category)
    # 先获取id
    id = wp.call(NewPost(post_obj))
    # 再通过EditPost更新信息
    edit_post(id, title,
              content,
              link,
              post_status,
              terms_names_post_tag,
              terms_names_category)
    # print(id)
    return id


# 更新文章
def edit_post(id, title, content, link, post_status, terms_names_post_tag, terms_names_category):
    post_obj = create_post_obj(
        title,
        content,
        link,
        post_status,
        terms_names_post_tag,
        terms_names_category)
    res = wp.call(EditPost(id, post_obj))
    return res
    # print(res)

# 获取markdown文件中的内容


def try_substitue(content: str):
    # from: github.com/EluvK/Image_server/raw/master
    # to  : cdn.jsdelivr.net/gh/EluvK/Image_server
    return content.replace("github.com/EluvK/Image_server/raw/master",
                           "cdn.jsdelivr.net/gh/EluvK/Image_server")


def read_md(file_path):
    content = ""
    metadata = {}
    with open(file_path) as f:
        post = frontmatter.load(f)
        content = post.content
        metadata = post.metadata
    content = try_substitue(content)
    # print(content)
    return (content, metadata)


# 获取特定目录的markdown文件列表
def get_md_list(dir_path):
    md_list = []
    dirs = os.listdir(dir_path)
    for i in dirs:
        if os.path.splitext(i)[1] == ".md":
            md_list.append(os.path.join(dir_path, i))
    # print(md_list)
    return md_list

# 计算sha1


def get_sha1(filename):
    sha1_obj = sha1()
    with open(filename, 'rb') as f:
        sha1_obj.update(f.read())
    result = sha1_obj.hexdigest()
    # print(result)
    return result

# 将字典写入文件


def write_dic_info_to_file(dic_info, file):
    dic_info_str = json.dumps(dic_info, indent=2, ensure_ascii=False)
    file = open(file, 'w', encoding='utf-8')
    file.write(dic_info_str)
    file.close()
    return True


def write_dic_info_to_file_md(dic_info: dict, file):
    # for j in dic_info:

    # dic_info_str = json.dumps(dic_info, indent=2, ensure_ascii=False)

    # print(dic_info_str)
    file = open(file, 'w', encoding='utf-8')
    for id, link in dic_info.items():
        file.write("* " + id + ": " + link + '\n')
    # file.write(dic_info_str)
    file.close()
    return True


# 将文件读取为字典格式
def read_dic_from_file(file):
    file_byte = open(file, 'r')
    file_info = file_byte.read()
    dic = json.loads(file_info)
    file_byte.close()
    return dic


def rebuild_posted_articles_list_file(infos: list, file_dir: str):
    res = {}

    for info in infos:
        key = info['id']
        link = info['link']
        res[key] = '['+info['title']+']('+info['link']+')'

    write_dic_info_to_file_md(res, file_dir)

# ---------------------


def get_sha1_dict(file):
    result = {}
    if(os.path.exists(file) == True):
        result = read_dic_from_file(file)
    else:
        write_dic_info_to_file({}, file)
    return result


def update_posted_articles():
    # 获取网站数据库中已有的文章列表
    post_link_id_list = get_posts()

    # print(post_link_id_list)

    # 写入本地文件
    rebuild_posted_articles_list_file(post_link_id_list, 'posted_articles.md')


def handle_folder(folder_path: str, sha1_list):
    print("handle articles in {0}".format(folder_path))

    default_status = "draft" if folder_path == "../draft" else "publish"

    md_list = get_md_list(os.path.join(os.getcwd(), folder_path))
    for md in md_list:
        file_name = os.path.basename(md)
        id = file_name.split(".")[0]
        if id.isdigit():
            file_name = '.'.join(file_name.split(".")[1:-1])

            # check_sha1_or_update()
            if id not in sha1_list or sha1_list[id] != get_sha1(md):
                print("alread_posted: but not same [id: {0}, name: {1}]".format(
                    id, file_name))

                (content, metadata) = read_md(md)
                title = metadata.get("title", "")
                if not title:
                    title = file_name
                _terms_names_post_tag = metadata.get("tags",  "")
                _terms_names_category = metadata.get("categories", "未分类")
                _post_status = metadata.get(
                    "status", default_status)  # draft or publish
                content = markdown.markdown(
                    content, extensions=['tables', 'fenced_code', 'md_in_html', 'mdx_gfm'])
                print("  -> dbg: ", id, title, file_name)
                if edit_post(id, title, content, link=file_name, post_status=_post_status,
                             terms_names_post_tag=_terms_names_post_tag, terms_names_category=_terms_names_category):
                    sha1_list[id] = get_sha1(md)
                else:
                    print("   -> dbg: update false")

            else:
                print("alread_posted: [id: {0}, name: {1}]".format(
                    id, file_name))
                pass

        else:
            print("not posted: ", file_name)
            pure_file_name = '.'.join(file_name.split(".")[:-1])
            # do_post_and_rename_file()
            (content, metadata) = read_md(md)
            # 获取title
            title = metadata.get("title", "")
            if not title:
                title = pure_file_name
            _terms_names_post_tag = metadata.get("tags",  "")
            _terms_names_category = metadata.get("categories", "未分类")
            _post_status = metadata.get(
                "status", default_status)  # draft or publish
            content = markdown.markdown(
                content, extensions=['tables', 'fenced_code', 'md_in_html', 'mdx_gfm'])

            # print(title, content, file_name.split(".")[0], post_status, terms_names_post_tag, terms_names_category)
            new_id = new_post(title, content, link=pure_file_name,  post_status=_post_status,
                              terms_names_post_tag=_terms_names_post_tag, terms_names_category=_terms_names_category)
            sha1_list[new_id] = get_sha1(md)
            os.rename(os.path.join(os.getcwd(), folder_path) + '/' + file_name,
                      os.path.join(os.getcwd(), folder_path) + '/' + str(new_id) + '.' + file_name)

    return sha1_list


def main():
    posted_sha1_list = get_sha1_dict(
        os.path.join(os.getcwd(), "./posted_sha1.md"))

    posted_sha1_list = handle_folder("../articles", posted_sha1_list)
    posted_sha1_list = handle_folder("../draft", posted_sha1_list)

    # use total update in the end
    write_dic_info_to_file(posted_sha1_list, "posted_sha1.md")

    update_posted_articles()
    return


main()
