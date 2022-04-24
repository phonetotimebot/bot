import phonenumbers
import string
import pytz

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


def check_phone(data):
    check = []
    for x in data:
        if isinstance(x, list):
            for y in x:
                if y:
                    if not [e for e in y if e not in f'+()- {string.digits}']:
                        try:
                            y = y.replace("'", '').replace('"', '')
                            y = '+' + y if y[0] != '+' else y
                            number = phonenumbers.parse(y)
                            check.append(number)
                        except Exception:
                            pass
        else:
            if x:
                if not [e for e in x if e not in f'+()- {string.digits}']:
                    try:
                        x = x.replace("'", '').replace('"', '')
                        x = '+' + x if x[0] != '+' else x
                        number = phonenumbers.parse(x)
                        check.append(number)
                    except Exception:
                        pass
    return check


def process_phone(npt, multiple=False):
    txt = f'{npt} — ' if multiple else ''
    if not [x for x in npt if x not in f'+()- {string.digits}']:
        try:
            npt = npt.replace("'", '').replace('"', '')
            npt = '+' + npt if npt[0] != '+' else npt
            number = phonenumbers.parse(npt)
            if phonenumbers.is_valid_number(number):
                tz = timezone.time_zones_for_number(number)
                now = datetime.now()
                dt = [[now.astimezone(pytz.timezone(x)).replace(tzinfo=None), x] for x in tz]
                srt = sorted(dt, key=lambda x: x[0])
                time = [datetime.strftime(x[0], '%I:%M %p, %d.%m.%Y') for x in srt]
                res = f'{time[0]} - {time[-1]}' if len(time) > 1 and time[0] != time[-1] else time[0]
                geo = f' ({", ".join([x[1] for x in srt])})'
                out = f'{txt}{res}{geo}'
            else:
                out = txt + 'Invalid phone number.'
        except Exception:
            out = txt + 'An error occured.'
    else:
        out = txt + 'No phone number.'
    return out


def handle_message(update, context):
    bot = context.bot
    user = update.effective_user
    user_id = user['id']
    message = update.effective_message
    txt = message.text
    try:
        data = [x.split(', ') if ', ' in x else x for x in txt.split('\n')]
        if check_phone(data):
            data = ['\n' + '\n'.join([process_phone(x, True) for x in e if x]) + '\n'
                    if isinstance(e, list) else process_phone(e, len(data) > 1)
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
            bot.send_message(user_id, 'No phone number.')
    except Exception:
        bot.send_message(user_id, 'An error occured.')


bot = Bot(TOKEN)
update_queue = Queue()

dispatcher = Dispatcher(bot=bot, update_queue=update_queue)

dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.command('start'), start_message))
dispatcher.add_handler(MessageHandler(Filters.chat_type.private & Filters.text, handle_message))

thread = Thread(target=dispatcher.start, name='dispatcher')
thread.start()
