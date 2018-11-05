import os
import re
import json
from sys import argv
from datetime import datetime as dt
from datetime import date
from pickle import dump


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (dt, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def build_data(text):
    try:
        result = re.search(r'(\d{1,2}\/\d{1,2}\/\d{2}), (\d{2}:\d{2}) - (.*?): (?:(.+))?', text)
        my_date = result.group(1)
        time = result.group(2)
        date_time = dt.strptime(my_date + ' at ' + time, '%m/%d/%y at %H:%M')
        name = result.group(3)
        if ':' in result.group(3):
            name = re.search(r'(^\D+)[$:]', result.group(3)).group(1)
        message = result.group(4)
        return {'sender': name, 'time': date_time, 'text': message}
        # return {'date': date_time, 'name': name, 'message': message}
    except Exception as e:
        return False


def fix_data(text, last_entry):
    my_date = last_entry['time']
    name = last_entry['sender']
    return {'sender': name, 'time': my_date, 'text': text}
    # return {'date': my_date, 'name': name, 'message': text}


def thread_parse(subject):
    text_file = open('chat/{0}.txt'.format(subject), 'r', encoding='utf8')
    file_to_write = open('./result/{0}/{0}_input/{0}_messages.txt'.format(subject), 'w', encoding='utf8')
    lines = text_file.read().split('\n')  # array consist of each line of the txt file
    # welcoming message is at lines[0]
    file_to_write.write(lines[0] + '\n')
    lines.pop(0)  # pop the welcoming message
    for idx, line in enumerate(lines):
        if not line:
            lines.pop(idx)

    """in a group conversation the first 3 lines are kinda special
            so we need special treatment to determine the admin(sender)
            we already popped the welcoming message now we need to clean the 2 other lines
        """
    if not build_data(lines[0]):
        file_to_write.write(lines[0] + '\n')
        file_to_write.write(lines[1] + '\n')
        lines = lines[2:]

    master = []
    for line in lines:
        if not build_data(line):
            temp = fix_data(line, master[-1])
        else:
            temp = build_data(line)
        master.append(temp)

    users = [entry['sender'] for entry in master]
    participants = set(users)
    print('Participants', participants)

    # Pickle the messages
    with open('./result/{0}/{0}_input/{0}_messages.pkl'.format(subject), 'wb') as f:
        dump(master, f)
    # Json file
    with open('./result/{0}/{0}_input/{0}_messages.json'.format(subject), 'w') as outfile:
        json.dump(master, outfile, default=json_serial)
    # txt format
    for entry in master:
        file_to_write.write(
            entry['time'].strftime('%#m/%#d/%y, %H:%M') + ' - ' + entry['sender'] + ': ' + entry['text'] + '\n')

    return master


if __name__ == '__main__':
    # If ran independently, takes the HTML file path as input
    my_subject = argv[1]
    if not os.path.exists('./result/{0}/{0}_input'.format(my_subject)):
        os.makedirs('./result/{0}/{0}_input'.format(my_subject))
        os.makedirs('./result/{0}/{0}_plots'.format(my_subject))
    thread_parse(my_subject)
