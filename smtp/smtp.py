# send_email(html_name, html_render_info, email_title_info)
# html_name 所有html模板文件均放置在smtp文件夹，顶层只提供带后缀.html文件名，底层自动拼接路径
# html_render_info 以object数据类型传参
# email_title_info = {
#     'address': 'receive@qq.com',
#     'subject': 'Test'
# }

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
import os

from flask import current_app
from jinja2 import Template

from config import SMTP_CONFIG


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_email(html_name, html_render_info, email_title_info):
    from_addr = "sora@sorapage.com"
    receive_addr = [email_title_info['address']]

    load_path = os.path.join(current_app.root_path, 'smtp/' + html_name)
    with open(load_path, encoding='utf-8') as html:
        template = Template(html.read())
        html_str = template.render(info=html_render_info)

    msg = MIMEText(html_str, 'html', 'utf-8')
    msg["from"] = Header(_format_addr("Sora<sora@sorapage.com>"))
    msg["To"] = Header(_format_addr(email_title_info['address']))
    msg["Subject"] = Header(email_title_info['subject'], "utf-8")

    smtpObj = smtplib.SMTP_SSL(SMTP_CONFIG['host'])
    smtpObj.login(SMTP_CONFIG['account'], SMTP_CONFIG['password'])
    smtpObj.sendmail(from_addr, receive_addr, msg.as_string())
