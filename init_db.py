import sqlite3
from aiogram.utils.markdown import text

# Creating table
def init_db():
    conn = sqlite3.connect("my.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS questions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT,
                question TEXT
                )''')
    # players_id, quests, scores sep - <,>, players sep - <!>, ans sep - <|>
    cursor.execute('''CREATE TABLE IF NOT EXISTS rooms(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT,
                players_id TEXT,
                players TEXT,
                quests TEXT
                )''')

# all columns have single data
    cursor.execute('''CREATE TABLE IF NOT EXISTS player(
                key TEXT,
                id INT,
                nickname TEXT,
                quest_id INT,
                answer TEXT,
                points INT
                )''')


    conn.commit()

# Loading data into a table
def load_db(name, data):
    conn = sqlite3.connect("my.db")
    cursor = conn.cursor()

    columns = str(tuple(data.keys())).replace("'",'')
    values = list(data.values())

    cursor.execute(
            'INSERT INTO ' + name + ' ' + columns +
            ' VALUES ('+str('?, '*len(values))[:-2]+')',
            tuple(values)
    )

    conn.commit()

def edit_db(name, data, id):
    conn = sqlite3.connect("my.db")
    cursor = conn.cursor()

    columns=''
    for c in data.keys():
        columns += c+'=?, '

    columns = columns[:-2]
    values = list(data.values())

    cursor.execute(
            'UPDATE ' + name +
            ' SET ' + columns +
            ' WHERE id = '+ id,
            tuple(values)
    )
    conn.commit()

# Removing a line from table
def remove(index, name):
    conn = sqlite3.connect("my.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ' + name + ' WHERE id = ' + index)
    conn.commit()

# Execution full data from table
def get_table(name, target=False):
    conn = sqlite3.connect("my.db")
    cursor = conn.cursor()
    if target:
        table = cursor.execute('SELECT * FROM '+name+
                               ' WHERE '+target[0]+' = ?',
                               (target[1],)).fetchall()
    else:
        table = cursor.execute('SELECT * FROM ' + name).fetchall()
    return table


def main():
    init_db()


if __name__ == '__main__':
    main()
