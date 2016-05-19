import importlib
import psycopg2
import datetime

def class_to_numeric(coc):
    classes = {
        'C(I)': 'C1',
        'C(II)': 'C2',
        'C(III)': 'C3',
        'C(IV)': 'C4',
        'D(I)': 'D1',
        'D(II)': 'D2',
        'D(III)': 'D3',
        'PA(B)': 'PAB',
        'WO(B)': 'WOB'
    }
    if coc in classes:
        return classes[coc]
    else:
        return coc


def connect(cursor_factory=None):
    connection = psycopg2.connect(config['PSQL_CONNECTION'])
    return connection.cursor(cursor_factory=cursor_factory)


def commit(cursor):
    cursor.connection.commit()

def complete(cursor):
    commit(cursor)
    cursor.close()
    cursor.connection.close()


def rollback(cursor):
    cursor.connection.rollback()
    cursor.close()
    cursor.connection.close()


cfg = 'Config'
c = getattr(importlib.import_module('config'), cfg)
config = {}

for key in dir(c):
    if key.isupper():
        config[key] = getattr(c, key)

with open("regr_refs.txt") as f:
    lines = f.readlines()


cursor = connect()

not_found = 0
multiples = 0
updated = 0
commit_every = 2

commit_counter = commit_every
cursor = connect()
for line in lines:
    data = line.strip().split('\t')
    coc = class_to_numeric(data[2])
    date = datetime.datetime.strptime(data[1], '%d/%m/%Y').strftime('%Y-%m-%d')

    cursor.execute('select d.id from register r, register_details d where registration_no=%(no)s and date=%(date)s '
                   'and d.id = r.details_id and d.class_of_charge = %(coc)s', {
                        'no': data[0],
                        'date': date,
                        'coc': coc
                    })

    rows = cursor.fetchall()
    if len(rows) == 0:
        not_found += 1
        print("Row not found: {} {} {}".format(data[0], data[1], coc))
    elif len(rows) > 1:
        multiples += 1
        print("Multiples found: {} {} {}".format(data[0], data[1], coc))
    else:
        details_id = rows[0][0]
        try:
            cursor.execute("UPDATE regsiter_details SET priority_notice_no=%(pno)s WHERE id=%(id)s", {'pno': data[3], 'id': details_id})
            updated += 1
            commit_counter -= 1
            if commit_counter <= 0:
                commit(cursor)
                print("COMMIT")
                commit_counter = commit_every

        except Exception as e:
            print(str(e))


complete(cursor)

print("Rows updated: {}".format(updated))
print("No row found: {}".format(not_found))
print("Multiples:    {}".format(multiples))
