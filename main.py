from aiogram import Dispatcher, Bot, types, executor
from aiogram.types import ParseMode
from aiogram.utils.markdown import text, bold, italic, code, pre

from time import sleep
#member = await bot.get_chat_member(message.chat.id, message.from_user.id)

from init_db import *
from config import TOKEN
from cipher import *
import keyboards as kb

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Привет! 👋\n'
                        'Давай сыграем в Смехлыст!', reply_markup=kb.greet_kb)


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    msg = text(bold('Я могу ответить на следующие команды:'),
               '/loadquestion', '/questions', '/remove', sep='\n')
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['loadquestion'])
async def process_loadquest_command(message: types.Message):
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        mtext = message.text.partition(' ')[2]
        load_db('questions', {'author' : member["user"]["username"],
                              'question' : mtext
                             })
        await message.reply(mtext + '\nУспешно записан!')
    except:
        await message.reply('Ошибка!\n'
                            'Вопрос не записан, '
                            'проверьте корректность введённой команды.')


@dp.message_handler(commands=['questions'])
async def process_questview_command(message: types.Message):
    try:
        quests = get_table('questions')
        await message.reply(str(quests))
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось получить список вопросов.')


@dp.message_handler(commands=['remove'])
async def process_removequest_command(message: types.Message):
    try:
        mtext = message.text.partition(' ')[2]
        remove(mtext, 'questions')
        await message.reply('Вопрос успешно удалён!')
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось удалить вопрос, '
                            'проверьте корректность введённой команды.')


@dp.message_handler(commands=['create'])
async def process_questview_command(message: types.Message):
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        key = get_key(8)
        load_db('rooms', {'key' : key,
                          'players' : member["user"]["username"],
                         })
        msg = text(bold('Комната успешно создана,'),
                   text('Код комнаты:', code(str(key))), sep='\n')
        await message.reply(msg, parse_mode=ParseMode.MARKDOWN)
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось создать комнату.')


@dp.message_handler(commands=['connect'])
async def process_questview_command(message: types.Message):
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        mtext = message.text.partition(' ')[2]
        room = get_table('rooms', ['key', mtext])[0]
        players = text(room[2], member["user"]["username"], sep='!')
        edit_db('rooms', { 'players' : players }, str(room[0]))
        msg = text(bold('Вы успешно подключились к комнате'),
                   text('Другие игроки:',
                   italic(", ".join(room[2].split('!')))), sep='\n')
        await message.reply(msg, parse_mode=ParseMode.MARKDOWN)
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось подключиться к комнате.')


@dp.message_handler(commands=['play'])
async def process_startgame_command(message: types.Message):
    try:
        key = message.text.partition(' ')[2]
        room = get_table('rooms', ['key', key])[0]
        players = room[2].split('!')
        answers = get_table('answers', ['key', key])
        quests = room[4].split(',')

        if len(players) != len(str(room[3])):
            await message.reply('Не все игроки подготовили ответы!')
            return

        players_string = ", ".join(players)
        msg = text(text(bold('Поехали'),'!',sep=''),
                    'В игре участвуют:',
                    italic(players_string), sep='\n')
        await bot.send_message(message.chat.id, msg,
        parse_mode=ParseMode.MARKDOWN)
        sleep(5)
        for idx in range(len(quests)):
            question = get_table('questions', ['id', str(quests[idx])])[0][2]
            msg = text('Внимание, вопрос:', italic(question), sep='\n')
            answer_list = answers[idx][2].split('|')
            player_list = answers[idx][1].split('!')
            inline_kb = kb.generate_buttons(answer_list[0], answer_list[1])
            await bot.send_message(message.chat.id, msg,
            parse_mode=ParseMode.MARKDOWN, reply_markup=inline_kb)
            sleep(20)
        room = get_table('rooms', ['key', key])[0]
        scores = room[5].split(',')
        winner = players[scores.index(max(scores))]
        msg = text(text(bold('Игра окончена'),'!',sep=''),
                        'Победитель:', winner, sep='\n')
        await bot.send_message(message.chat.id, msg,
        parse_mode=ParseMode.MARKDOWN)
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось запустить игру.')

@dp.message_handler(commands=['1'])
async def process_command_1(message: types.Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    await bot.send_message(message.chat.id, member["user"]["username"],
    reply_markup=kb.inline_kb1)


@dp.callback_query_handler(lambda c: c.data == 'button1')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    #await bot.send_message(callback_query.from_user.id, 'Нажата первая кнопка!')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
