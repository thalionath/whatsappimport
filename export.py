# script to parse WhatsApp chat export format
# Chat -> Options -> More -> Export Chat (e.g. Google Drive)
#
# The export format is a text file in UTF-8 with message entries of the form:
#  21.06.15, 10:27 - Bendicht Büchi: Guete Morge!
#
# The message body may be multiline (everything is LF separated):
#  21.06.15, 10:47 - Anna Saurer: juhuuu!!
#  juhuuu glace ässe!
#
# We ignore events that appear without colon ':' after the author:
#  21.06.15, 10:27 - ‎Bendicht Büchi hat dich hinzugefügt.
#

import io
import re
from collections import defaultdict
from datetime import datetime

# Match into 4 groups:
# (date), (time) - (author): (body)
message_pattern = re.compile(r'^([0-9]{2})\.([0-9]{2})\.([0-9]{2}),\s+([0-9]{2})\:([0-9]{2})\s+-\s+([^\n\r:]+): ([^\n\r]+)')

# Some events have a unicode marker after the hyphen sequence " - "
# u"\u200E" 0xE2808E https://www.fileformat.info/info/unicode/char/200e/index.htm
# But security code changes do not.
event_pattern = re.compile(r'^([0-9]{2})\.([0-9]{2})\.([0-9]{2}),\s+([0-9]{2})\:([0-9]{2})\s+-\s+' + u"\u200E" + '?')

event_count = 0
authors = defaultdict(int)
message = None
messages = list()

def commit():
    # print(message)
    messages.append(message)

with io.open('chat-export.txt', mode='r', encoding='utf-8') as f:
    for line in f:
        m = re.match(message_pattern, line)
        if m:
            # finish multiline message
            if message:
                commit()

            message = {
                'time': datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)), int(m.group(4)), int(m.group(5))),
                'author': m.group(6),
                'body': m.group(7)
            }
            # print(message)
            authors[message['author']] += 1
        elif re.match(event_pattern, line):
            event_count += 1
            message = None
        else:
            # consider everything else to be part of a multiline message body
            message['body'] += '\n' + line

# last message may have a multiline body
if message:
    commit()

def message_count_by_weeks(messages):
    weeks = defaultdict(int)
    for message in messages:
        iso = message['time'].isocalendar()
        label = str(iso[0]) + '/' + str(iso[1]).zfill(2)
        weeks[label] += 1
    return weeks

def message_count_by_hour_and_author(messages):
    authors = defaultdict(lambda: {k: 0 for k in range(24)})
    for message in messages:
        authors[message['author']][message['time'].hour] += 1
    return authors

data = message_count_by_weeks(messages)

for week in sorted(data):
    print(week, data[week], sep='\t')

data = message_count_by_hour_and_author(messages)

for user in sorted(data):
    print(user, end='\t')
    for hour in sorted(data[user]):
        print(data[user][hour], end='\t')
    print('')

print(len(messages), 'messages', len(authors), 'authors')

for author, messages in authors.items():
    print(author, messages)

print(event_count, 'events')
