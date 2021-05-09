from flask import Blueprint, request, session
import json
from urllib.parse import urlparse
from sql import connect_dictCursor
from datetime import datetime

from smtp.smtp import send_email


def format_time(datetime_obj):
    timedelta_obj = datetime.now() - datetime_obj
    if timedelta_obj.days == 0:
        time_str = str(timedelta_obj)
        time_str_list = time_str.split(':')
        time_str_list[2] = time_str_list[2][0:2]
        time_list = []
        for value in time_str_list:
            time_list.append(int(value))

        if time_list[0] == time_list[1] == time_list[2] == 0:
            return '刚刚'
        elif time_list[0] == time_list[1] == 0:
            return str(time_list[2]) + '秒前'
        elif time_list[0] == 0:
            return str(time_list[1]) + '分钟前'
        else:
            return str(time_list[0]) + '小时前'
    elif timedelta_obj.days <= 7:
        return str(timedelta_obj)[0:1] + '天前'
    else:
        return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")


def load(url):
    sql_connect, sql_cursor = connect_dictCursor()
    sql_cursor.execute(f"SELECT * FROM comment WHERE url='{url}'")
    sql_fetch = sql_cursor.fetchall()
    comment_parent = []
    comment_child = []
    for item in sql_fetch:
        if item['replyTo'] is None:
            comment_parent.append(item)
        else:
            comment_child.append(item)
    comment_parent.sort(key=lambda x: x['time'], reverse=True)
    comment_child.sort(key=lambda x: (x['parent'], x['time']))
    for i in range(len(comment_parent)):
        comment_parent[i]['time'] = format_time(comment_parent[i]['time'])
    for i in range(len(comment_child)):
        comment_child[i]['time'] = format_time(comment_child[i]['time'])
    comment_obj = {
        'parent': comment_parent,
        'child': comment_child
    }
    try:
        comment_obj['login_user'] = {'name': session['name'], 'email': session['email']}
    except KeyError:
        pass
    comment_json = json.dumps(comment_obj)
    sql_cursor.close()
    sql_connect.close()
    return comment_json


comment = Blueprint('comment', __name__)


@comment.route('/comment', methods=['GET', 'POST'])
def comment_ajax():
    url = urlparse(request.referrer).path
    if request.method == 'GET':
        return load(url)
    elif request.method == 'POST':
        sql_connect, sql_cursor = connect_dictCursor()
        form = {}
        for value, key in request.form.items():
            if key == '':
                form[value] = 'NULL'
            else:
                form[value] = key
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql_cursor.execute(
            f"INSERT INTO comment (url,uid,name,email,comment,time,parent,replyTo) VALUES ('{url}','{form['uid']}','{form['name']}','{form['email']}','{form['comment']}','{now}',{form['parent']},{form['replyTo']})")
        comment_id = sql_connect.insert_id()
        sql_connect.commit()
        # email to parent
        if form['replyTo'] != 'NULL':
            sql_cursor.execute(f"select * from comment where id={form['replyTo']}")
            fetch = sql_cursor.fetchone()
            html_render_info = {
                'parent_name': fetch['name'],
                'parent_comment': fetch['comment'],
                'child_name': form['name'],
                'child_comment': form['comment'],
                'comment_url': 'http://sorapage' + url + '#comment' + str(comment_id)
            }
            email_title_info = {
                'address': fetch['email'],
                'subject': 'SoraPage评论回复通知'
            }
            send_email('comment_notify_parent.html',
                       html_render_info=html_render_info,
                       email_title_info=email_title_info)
        # email to Sora
        if form['uid'] != '1':
            html_render_info = {
                'url': 'http://sorapage' + url + '#comment' + str(comment_id),
                'name': form['name'],
                'email': form['email'],
                'comment': form['comment']
            }
            email_title_info = {
                'address': 'sora@sorapage.com',
                'subject': 'SoraPage New Comment Notification'
            }
            send_email('comment_notify_sora.html',
                       html_render_info=html_render_info,
                       email_title_info=email_title_info)
        sql_cursor.close()
        sql_connect.close()
        return load(url)
