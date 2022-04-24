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


def check_number(data):
    check = []
    for x in data:
        if isinstance(x, list):
            for y in x:
                if y:
                    if not [e for e in y if e not in f'+()- {string.digits}']:
                        try:
                            y = y.replace("'", '').replace('"', '')
                            y = '+' + y if y[0] != '+' else y
                            check.append(phonenumbers.parse(y))
                        except Exception:
                            pass
        else:
            if x:
                if not [e for e in x if e not in f'+()- {string.digits}']:
                    try:
                        x = x.replace("'", '').replace('"', '')
                        x = '+' + x if x[0] != '+' else x
                        check.append(phonenumbers.parse(x))
                    except Exception:
                        pass
    return check


def process_number(npt, multiple=False):
    unknown = ' — ???'
    if [x for x in npt if x not in f'+()- {string.digits}']:
        return npt + unknown if multiple else ''
    try:
        npt = npt.replace("'", '').replace('"', '')
        npt = '+' + npt if npt[0] != '+' else npt
        num = phonenumbers.parse(npt)
        tz = timezone.time_zones_for_number(num)
        now = datetime.now()
        dt = [[now.astimezone(pytz.timezone(x)).replace(tzinfo=None), x] for x in tz]
        srt = sorted(dt, key=lambda x: x[0])
        time = [datetime.strftime(x[0], '%I:%M %p, %d.%m.%Y') for x in srt]
        txt = f'{npt} — ' if multiple else ''
        res = f'{time[0]} - {time[-1]}' if len(time) > 1 and time[0] != time[-1] else time[0]
        geo = f' ({", ".join([x[1] for x in srt])})'
        out = txt + res + geo
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
        if check_number(data):
            data = ['\n' + '\n'.join([process_number(x, True) for x in e if x]) + '\n'
                    if isinstance(e, list) else process_number(e, len(data) > 1)
                    for e in data if e]
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
            res = data[start:] if start else data
            res = data[:-end] if end else data
            if not res:
                bot.send_message(user_id, 'An error occured.')
            elif len(res) > 4096:
                bot.send_message(user_id, 'The message is too long.')
            else:
                bot.send_message(user_id, res)
        else:
            bot.send_message(user_id, 'No valid number.')
    except Exception:
        bot.send_message(user_id, 'An error occured.')


bot = Bot(TOKEN)
update_queue = Queue()

dispatcher = Dispatcher(bot=bot, update_queue=update_queue)

dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.command('start'), start_message))
dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.text, handle_message))

thread = Thread(target=dispatcher.start, name='dispatcher')
thread.start()
