import string
import pytz
import phonenumbers

from queue import Queue
from threading import Thread
from datetime import datetime
from phonenumbers import timezone

from telegram.bot import Bot
from telegram.ext import Dispatcher, Filters, MessageHandler

from bot.config import TOKEN


def start_message(update, context):
    bot = context.bot
    user = update.effective_user
    user_id = user['id']
    bot.send_message(user_id, 'Hi, send me one or more phone numbers (separated by newlines) to get the local time.')


def process_number(npt, multiple=False):
    unknown = ' — ???'
    if [x for x in npt if x not in f'+()- {string.digits}']:
        return npt + unknown if multiple else ''
    try:
        npt = npt.replace('\n', '').replace("'", '').replace('"', '')
        npt = '+' + npt if npt[0] != '+' else npt
        num = phonenumbers.parse(npt)
        tz = timezone.time_zones_for_number(num)
        now = datetime.now()
        dt = [[now.astimezone(pytz.timezone(x)).replace(tzinfo=None), x] for x in tz]
        srt = sorted(dt, key=lambda x: x[0])
        time = [datetime.strftime(x[0], '%I:%M %p, %d.%m.%Y') for x in srt]
        res = list(set([time[0], time[-1]]))
        geo = ", ".join([x[1] for x in srt])
        if multiple:
            txt = npt + ' — '
        else:
            txt = ''
        if len(res) == 2:
            out = f'{txt}{res[0]} - {res[1]} ({geo})'
        else:
            out = f'{txt}{res[0]} ({geo})'
    except Exception:
        if multiple:
            out = npt + unknown
        else:
            out = ''
    return out


def handle_message(update, context):
    bot = context.bot
    user = update.effective_user
    user_id = user['id']
    message = update.effective_message
    txt = message.text
    try:
        data = [x.split(', ') if ', ' in x else x for x in txt.split('\n')]
        data = ['\n' + '\n'.join([process_number(x, True) for x in e]) + '\n'
                if isinstance(e, list) else process_number(e, len(data) > 1) for e in data]
        data = '\n'.join(data)
        start, end = 0, 0
        for x in data:
            if x == '\n':
                start += 1
            else:
                break
        for x in data[::-1]:
            if x == '\n':
                end += 1
            else:
                break
        data = data[start:] if start else data
        data = data[:-end] if end else data
        if len(data) <= 4096:
            bot.send_message(user_id, data)
        else:
            bot.send_message(user_id, 'The message is too long.')
    except Exception as err:
        bot.send_message(user_id, err)


bot = Bot(TOKEN)
update_queue = Queue()

dispatcher = Dispatcher(bot=bot, update_queue=update_queue)

dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.command('start'), start_message))
dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.text, handle_message))

thread = Thread(target=dispatcher.start, name='dispatcher')
thread.start()
