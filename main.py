from aiogram import Dispatcher, Bot, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.dispatcher.filters.state import State, StatesGroup

from random import choices, shuffle

from asyncio import sleep

from states import *
from init_db import *
from config import TOKEN
from cipher import *
import keyboards as kb

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# slots - number of slots in the room
global slots
slots = 6

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Привет! 👋\n'
                        'Давай сыграем в Смехлыст!', reply_markup=kb.greet_kb)


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    msg = text(bold('Узнать побольше обо мне:'),
          text('Как играть -', code('/howtoplay')),
          text('Как добавить свой вопрос в игру -', code('/questbasehelp')), sep='\n')
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['howtoplay'])
async def process_help_command(message: types.Message):
    msg = text(bold('Вcё что тебе нужно, чтобы поиграть:'),
          text('Чтобы создать комнату, введи -', code('/create')),
          text('Подключится к игре, -', code('/connect код')),
          text('Запустить игру в групповом чате, -', code('/play код')), sep='\n')
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['questbasehelp'])
async def process_help_command(message: types.Message):
    msg = text(bold('Хочешь улучшить базу вопросов?'),
          ('Тогда эти команды тебе помогут в этом:'),
          text('Посмотреть весь список вопросов, -', code('/questions')),
          text('Загрузить новый вопрос, -', code('/loadquestion Твой вопрос')),
          text('Удалить вопрос, -', code('/remove айди вопроса')), sep='\n')
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['loadquestion'])
async def process_loadquest_command(message: types.Message):
    try:
        question = message.text.partition(' ')[2]
        load_db('questions', {'author' : message.from_user.username,
                            'question' : question})
        await message.reply(text('Отлично! Вопрос', message.text,
                            'Успешно сохранён'), sep='\n')
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось выполнить команду')


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
        key = get_key(16)

        load_db('player', {'key' : key,
                           'id' : member["user"]["id"],
                           'nickname' : member["user"]["username"]
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
        room = get_table('player', ['key', mtext])

        if member["user"]["username"] in [p[2] for p in room]:
            await message.reply("Вы уже подключены к этой игре")
            return
        try:
            player_id = get_table('player', ['id', member["user"]["id"]])[0][1]
            if player_id is not None:
                await message.reply("Вы уже подключены к комнате")
                return
        except:

            load_db('player', {'key' : mtext,
                           'id' : member["user"]["id"],
                           'nickname' : member["user"]["username"]
                          })

            msg = text('Вы успешно подключились к комнате',
                   'Другие игроки:',
                   ", ".join([p[2] for p in room]), sep='\n')
            await message.reply(msg)

            room = get_table('player', ['key', mtext])
            if len(room) == slots:
                questions = get_table('questions')

                for _ in range(slots // 2):
                    full_quests = choices(list(questions), k = slots // 2)
                # doubleing and shuffleing quests list
                ranger = list(full_quests)
                for q in ranger:
                    full_quests.append(q)
                shuffle(full_quests)
                # Sending questions to all players
                for i in range(len(room)):
                    msg = text(bold("Продолжи фразу:"), full_quests[i][2], sep='\n')
                    await bot.send_message(room[i][1] , msg, parse_mode=ParseMode.MARKDOWN)
                    edit_db('player', {'quest_id' : full_quests[i][0]}, str(room[i][1]))
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось подключиться к комнате.')


@dp.message_handler(commands=['play'])
async def process_startgame_command(message: types.Message):
    try:
        key = message.text.partition(' ')[2]
        stats = get_table('player', ['key', key])

        if len(stats) < slots:
            await message.reply('В комнате недостаточно игроков')
            return

        players = [p[2] for p in stats]
        quests = [p[3] for p in stats]
        # Check answers and group by questions
        answers = {}
        for player in stats:
            if player[4] is None:
                await message.reply('Не все игроки подготовили ответы!')
                return
            try:
                answers[player[3]].append([player[4], [player[1], player[2]]])
            except:
                answers[player[3]] = [ [player[4], [ player[1], player[2] ]] ]

        msg = text(text('Поехали','!',sep=''),
                    'В игре участвуют:',
                    ", ".join(players), sep='\n')
        await bot.send_message(message.chat.id, msg)
        await sleep(5)

        # Здесь нужно отсортировать ответы игроков так, чтобы
        # к 1 вопросу шло 2 ответа
        # ✓ Выполнил выше в цикле


        for quest in answers:
            question = get_table('questions', ['id', str(quest)])[0][2]
            msg = text('Внимание, вопрос:', question, sep='\n')

            inline_kb = kb.generate_buttons(answers[quest][0][0], answers[quest][1][0])
            await bot.send_message(message.chat.id, msg, reply_markup=inline_kb)
            await sleep(20)

        # Get winner stage (after all questions)
        stats = get_table('player', ['key', key])
        points = [int(0 if point[5] is None else point[5]) for point in stats]
        winner = stats[points.index(max(points))][2]
        msg = text('Игра окончена!', 'Победитель:', winner, sep='\n')
        await bot.send_message(message.chat.id, msg)

        # Stage Clear <player> table
        # Deleting game session
        for player in stats:
            remove(str(player[1]), 'player')
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось запустить игру.')


@dp.callback_query_handler(lambda c: c.data == 'button1')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    print("Нажата 1 кнопка")



@dp.callback_query_handler(lambda c: c.data == 'button2')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    print("Нажата 2 кнопка")

# ловит все сообщения боту, записывает их как ответ к игре
@dp.message_handler()
async def get_answer(message: types.Message):
    try:
        id = message.from_user.id
        answer = message.text
        edit_db('player', {'answer' : answer}, str(id))
    except:
        return


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    
