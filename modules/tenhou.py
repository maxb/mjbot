import willie
import binascii
import os
import struct
from urllib import unquote, urlencode, urlopen
from xml.etree import ElementTree as ET

DIRECTORY = os.path.expanduser('~/.willie/tenhou-game-xml')
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)

table = [
    22136, 52719, 55146, 42104, 
    59591, 46934, 9248,  28891,
    49597, 52974, 62844, 4015,
    18311, 50730, 43056, 17939,
    64838, 38145, 27008, 39128,
    35652, 63407, 65535, 23473,
    35164, 55230, 27536, 4386,
    64920, 29075, 42617, 17294,
    18868, 2081
]

def tenhouHash(game):
    code_pos = game.rindex("-") + 1
    code = game[code_pos:]
    if code[0] == 'x':
        a,b,c = struct.unpack(">HHH", binascii.a2b_hex(code[1:]))     
        index = 0
        if game[:12] > "2010041111gm":
            x = int("3" + game[4:10])
            y = int(game[9])
            index = x % (33 - y)
        first = (a ^ b ^ table[index]) & 0xFFFF
        second = (b ^ c ^ table[index] ^ table[index + 1]) & 0xFFFF
        return game[:code_pos] + "{:04x}{:04x}".format(first, second)
    else:
        return game

@willie.module.rule(r'.*(20[0-9]{8}gm-[0-9a-f]{4}-[0-9]{4,5}-([0-9a-f]{8}|x[0-9a-f]{12})).*')
def loglink(bot, trigger):
    logname = trigger.group(1)
    logname = tenhouHash(logname)
    target_fname = os.path.join(DIRECTORY, "{}.xml".format(logname))
    if os.path.exists(target_fname):
        with open(target_fname, 'rb') as f:
            data = f.read()
    else:
        resp = urlopen('http://e.mjv.jp/0/log/?' + logname)
        data = resp.read()
        with open(target_fname, 'wb') as f:
            f.write(data)
    etree = ET.fromstring(data)
    owari = etree.find('./*[@owari]').get('owari').split(',')
    un_tag = etree.find('UN')
    usernames = [
            unquote(un_tag.get('n0')),
            unquote(un_tag.get('n1')),
            unquote(un_tag.get('n2')),
            unquote(un_tag.get('n3')),
            ]
    scores = []
    for i in range(4):
        num = owari[i * 2 + 1]
        if num[0] != '-':
            num = "+" + num
        scores.append((
            usernames[i],
            num,
            float(num),
            i,
        ))
    scores.sort(key=lambda x: x[2], reverse=True)
    bot.say("Replay: http://tenhou.net/0/?" + urlencode((
        ('log', logname),
        #('tw', str(scores[0][3])),
        ('n0', usernames[0]),
        ('n1', usernames[1]),
        ('n2', usernames[2]),
        ('n3', usernames[3]),
        )))
    bot.say("Starting seats (ESWN): " + ", ".join(usernames))
    bot.say("Scores: " + " ".join(("{}({})".format(name, score) for name, score, number, playerpos in scores)))
    return willie.module.NOLIMIT
