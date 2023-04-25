from aiogram import Dispatcher, Bot, types, executor
from aiogram.types import ParseMode
from aiogram.utils.markdown import text, bold, italic, code, pre

from random import randrange, shuffle

from asyncio import sleep
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
        key = get_key(16)
        load_db('rooms', {'key' : key,
                          'players_id' : str(member["user"]["id"]),
                          'players' : member["user"]["username"]
                         })
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

# Делим нацело кол-во игроков на 2, находим остаток от деления
# Если остаток 0, созаём строку в answers с двумя последними игроками
# Если 1, то скип

# Целая часть от деления - это quest_number
@dp.message_handler(commands=['connect'])
async def process_questview_command(message: types.Message):
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        mtext = message.text.partition(' ')[2]
        room = get_table('rooms', ['key', mtext])[0]

        #if member["user"]["username"] in room[3].split('!'):
            #await message.reply("Вы уже подключены к этой игре")
            #return

        player_id = get_table('player', ['id', member["user"]["id"]])[0][1]
        if player_id is not None:
            await message.reply("Вы уже подключены к комнате")
            return

        load_db('player', {'key' : mtext,
                           'id' : member["user"]["id"],
                           'nickname' : member["user"]["username"]
                          })

        players = text(room[3], member["user"]["username"], sep='!')
        ids = text(room[2], str(member["user"]["id"]), sep=',')
        edit_db('rooms', { 'players_id' : ids,
                           'players' : players
                         }, str(room[0]))

        msg = text('Вы успешно подключились к комнате',
                   'Другие игроки:',
                   ", ".join(room[3].split('!')), sep='\n')
        await message.reply(msg)
        # slots - количество слотов в комнате (в дальнейшем будет указываться создателем)
        slots = 4
        if len(players.split('!')) == slots:
            questions = get_table('questions')
            quests = ''
            quest_text = []
            for _ in range(slots // 2):
                quest = list(questions).pop(randrange(len(questions)))
                quest_text.append([str(quest[0]), quest[2]])
                quests += str(quest[0]) + ','
            quests = quests[:-1]

            edit_db('rooms', { 'quests' : quests }, str(room[0]))
            ranger = list(quest_text)
            for t in ranger:
                quest_text.append(t)
            shuffle(quest_text)
            ids = ids.split(',')
            for i in range(len(ids)):
                msg = text(bold("Продолжи фразу:"), quest_text[i][1], sep='\n')
                await bot.send_message(ids[i] , msg, parse_mode=ParseMode.MARKDOWN)
                edit_db('player', {'quest_id' : quest_text[i][0]}, str(ids[i]))

        # ✓ Как только игроки набрались (в табл player
        # будут заполнены первые 3 колонки),
        # ✓ Заполнится в табл rooms 2 случайных вопроса (n/2)
        # ✓ Первый вопрос получат 2 случайных игрока, второй - остальные
        # ✓ Номера вопросов занесутся в табл player
        # ✓ Сработает рассылка с просьбой продолжить фразу
        # ✓ Первое сообщение игрока после рассылки будет записано
        # в табл как answer
        # ✓ Если все ответили на вопрос, в табл. rooms заносится
        # параметр ready = 1

    except:
        await message.reply('Ошибка!\n'
                            'Не удалось подключиться к комнате.')


# Необходимо полностью переработать, отказаться от таблицы answers
@dp.message_handler(commands=['play'])
async def process_startgame_command(message: types.Message):
    try:
        key = message.text.partition(' ')[2]
        room = get_table('rooms', ['key', key])[0]
        stats = get_table('player', ['key', key])

        if len(stats) < 4:
            await message.reply('В комнате недостаточно игроков')
            return

        players = room[3].split('!')
        quests = room[4].split(',')
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
            msg = text('Внимание, вопрос:', italic(question), sep='\n')

            inline_kb = kb.generate_buttons(answers[quest][0][0], answers[quest][1][0])
            await bot.send_message(message.chat.id, msg,
            parse_mode=ParseMode.MARKDOWN, reply_markup=inline_kb)
            await sleep(20)

        # Get winner stage (after all questions)
        stats = get_table('player', ['key', key])
        points = [int(0 if point[5] is None else point[5]) for point in stats]
        winner = stats[points.index(max(points))][2]
        msg = text('Игра окончена!', 'Победитель:', winner, sep='\n')
        await bot.send_message(message.chat.id, msg)

        # Stage Clear <player> and <room> table
        # Deleting game session
        remove(str(room[0]), 'rooms')
        for player in stats:
            remove(str(player[1]), 'player')
    except:
        await message.reply('Ошибка!\n'
                            'Не удалось запустить игру.')

@dp.message_handler(commands=['1'])
async def process_command_1(message: types.Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    await bot.send_message(message.chat.id, member["user"]["username"],
    reply_markup=kb.inline_kb1)


@dp.message_handler(commands=['2'])
async def process_command_1(message: types.Message):
    await bot.send_message(message.from_user.id, message.from_user.id)


@dp.callback_query_handler(lambda c: c.data == 'button1')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    print("Нажата 1 кнопка")
    #await bot.send_message(callback_query.from_user.id, 'Нажата первая кнопка!')



@dp.callback_query_handler(lambda c: c.data == 'button2')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    print("Нажата 2 кнопка")

# ловит все сообщения боту, записывает их как ответ к игре
@dp.message_handler()
async def get_answer(message: types.Message):
    try:
        id = message.from_user.id
        saved_answer = get_table('player', ['id', id])[0][4]

        if saved_answer is not None:
            return
        answer = message.text
        edit_db('player', {'answer' : answer}, str(id))
    except:
        return


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
