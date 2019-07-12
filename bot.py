from telegram.ext import Updater, CommandHandler
import config
import requests
import logging
import re
import json, time
import os
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

pku_cached = []
try:
    with open('pku_cached.json', 'r') as f:
        pku_cached = json.loads(f.read())
except:
    pass

last_get_time = 0
title_pattern = re.compile(r'<div\sclass="title\sl\slimit">(.*?)</div>')
node_pattern = re.compile(r'<div class="board l limit">(.*?)</div>')
author_pattern = re.compile(r'<div class="name limit">(.*?)</div>')
time_pattern = re.compile(r'<div class="time">(.*?)</div>')
link_pattern = re.compile(r'<div class="list-item list-item-topic"><a class="link" href="(.*?)"></a>')
pku_prefix = 'https://bbs.pku.edu.cn/v2/'

send_queue = []

def send_one():
    if len(send_queue)>0:
        bot.send_message(config.channel_chat_id, send_queue[0], parse_mode = 'html')
        del send_queue[0]

def send(x):
    s = '<b>{}</b>\n\n'.format(x['title'])
    s+= '<b>{}</b>\n🕒 {}\n💬 {}\n\n'.format(x['author'], x['time'], x['node'])
    s+= '{}'.format(pku_prefix+x['link'])
    send_queue.append(s)

def get_pku_bbs():
    global pku_cached
    global last_get_time
    now = time.time()
    if now - last_get_time > 5*60:
        last_get_time = now
        r = requests.get('https://bbs.pku.edu.cn/v2/hot-topic.php', timeout=15)
        r.encoding='utf-8'
        s = r.text
        titles = title_pattern.findall(s)
        nodes = node_pattern.findall(s)
        authors = author_pattern.findall(s)
        times = time_pattern.findall(s)
        links = link_pattern.findall(s)
        for x in pku_cached:
            x['ttl'] -= 1

        for i in range(100):
            flag = False
            for j in range(len(pku_cached)):
                if pku_cached[j]['link'] == links[i]:
                    pku_cached[j]['ttl'] = 100
                    flag = True
                    break
            if not flag:
                current = {
                    'title': titles[i].replace('&nbsp;',' '),
                    'node': nodes[i],
                    'author': authors[i],
                    'time': times[i],
                    'link': links[i],
                    'ttl' : 100,
                }
                send(current)
                pku_cached.append(current)
        i = 0
        while i < len(pku_cached):
            if pku_cached[i]['ttl'] < 0:
                del pku_cached[i]
            else:
                i += 1
    return


def check_wrapper(bot, context):
    get_pku_bbs()
def send_wrapper(bot, context):
    send_one()

updater = Updater(config.TOKEN)
bot = updater.bot
jq = updater.job_queue

check_job = jq.run_repeating(check_wrapper, interval = config.interval_in_mins * 60, first = 0)
send_job = jq.run_repeating(send_wrapper, interval = 5 * 60, first = 30)

updater.start_polling()
updater.idle()

print('saving...')
with open('pku_cached.json', 'w') as f:
    f.write(json.dumps(pku_cached))
print('saved')
