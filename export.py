# script to parse WhatsApp chat export format
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

message_count = 0
event_count = 0
authors = defaultdict(int)
message = None

def commit():
    print(message)

with io.open('chat-export.txt', mode='r', encoding='utf-8') as f:
    for line in f:
        m = re.match(message_pattern, line)
        if m:
            # finish multiline message
            if message:
                commit()

            message_count += 1
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

print(message_count, 'messages', len(authors), 'authors')

for author, messages in authors.items():
    print(author, messages)

print(event_count, 'events')

