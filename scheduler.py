from sql import connect_dictCursor
from smtp.smtp import send_email

from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler


def print_info(info):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\t' + info)


def v2ray_database_update():
    sql_connect, sql_cursor = connect_dictCursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_level_update = f"update v2ray_user set user_level = 0 where level_expire<='{now}' "
    sql_cursor.execute(user_level_update)
    print_info("user level updated")
    sql_connect.commit()
    user_today_traffic_update = f"update v2ray_user set today_up=0, today_down=0 "
    sql_cursor.execute(user_today_traffic_update)
    sql_connect.commit()
    print_info("user today's traffic updated")
    node_today_traffic_update = f"update v2ray_node set today_in_up=0, today_in_down=0, today_out_up=0, today_out_down=0"
    sql_cursor.execute(node_today_traffic_update)
    sql_connect.commit()
    print_info("node today's traffic updated")
    sql_cursor.close()
    sql_connect.close()


def v2ray_expire_email():
    now = datetime.now()
    threshold = (now + timedelta(days=3)).day
    sql_connect, sql_cursor = connect_dictCursor()
    sql_cursor.execute("select u.name_,u.email,v.level_expire from users u inner join v2ray_user v on u.uid=v.uid")
    users = sql_cursor.fetchall()
    sql_cursor.close()
    sql_connect.close()
    for user in users:
        if user['level_expire'].day == threshold:
            html_render_info = {
                'user_name': user['name_'],
                'expire_date': user['level_expire'].strftime("%Y年%m月%d日")
            }
            email_title_info = {
                'address': user['email'],
                'subject': 'SoraPort订阅过期通知'
            }
            send_email('v2ray_level_expire.html', html_render_info=html_render_info, email_title_info=email_title_info)
    print_info("v2ray expiry email routine")


scheduler = BlockingScheduler()
scheduler.add_job(v2ray_database_update, 'cron', hour=0, minute=0, second=0)
scheduler.add_job(v2ray_expire_email, 'cron', hour=10, minute=0, second=0)
scheduler.start()
