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
        srt = sorted(dt, key = lambda x: x[0])
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
    npt = message.text
    data = npt.split('\n')
    res = '\n'.join([process_number(line, len(data) > 1) for line in data])
    if res:
        bot.send_message(user_id, res)
    else:
        bot.send_message(user_id, 'An error occured.')
        return None


bot = Bot(TOKEN)
update_queue = Queue()

dispatcher = Dispatcher(bot=bot, update_queue=update_queue)

dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.command('start'), start_message))
dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.text, handle_message))

thread = Thread(target=dispatcher.start, name='dispatcher')
thread.start()
