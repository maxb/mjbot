import willie
import binascii
import os
import re
import struct
from urllib.parse import unquote, urlencode
from urllib.request import urlopen
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

def download_game(logname):
    target_fname = os.path.join(DIRECTORY, "{}.xml".format(logname))
    if os.path.exists(target_fname):
        with open(target_fname, 'rb') as f:
            data = f.read()
    else:
        resp = urlopen('http://e.mjv.jp/0/log/?' + logname)
        data = resp.read()
        with open(target_fname, 'wb') as f:
            f.write(data)
    return data

@willie.module.commands('waml')
def loglink_waml(bot, trigger):
    restofline = trigger.group(2)
    m = re.search(r'.*(20[0-9]{8}gm-[0-9a-f]{4}-[0-9]{4,5}-(?:[0-9a-f]{8}|x[0-9a-f]{12}))(&[&=%A-Za-z0-9]*)?.*', restofline)
    if m is None:
        bot.notice('usage: .waml tenhou-log-link', trigger.sender)
        return willie.module.NOLIMIT
    logname = m.group(1)
    logname = tenhouHash(logname)
    download_game(logname)
    httpresponse = urlopen('http://mahjong.maxb.eu/api/new_game/{}/{}'.format(logname, 'waml-s1'))
    bot.notice(httpresponse.read(), trigger.sender)
    return willie.module.NOLIMIT

@willie.module.commands('info')
def infocmd(bot, trigger):
    restofline = trigger.group(2)
    m = re.search(r'.*(20[0-9]{8}gm-[0-9a-f]{4}-[0-9]{4,5}-(?:[0-9a-f]{8}|x[0-9a-f]{12}))(&[&=%A-Za-z0-9]*)?.*', restofline)
    if m is None:
        bot.notice('usage: .info tenhou-log-link', trigger.sender)
        return willie.module.NOLIMIT
    logname = m.group(1)
    logname = tenhouHash(logname)
    xml = download_game(logname)
    httpresponse = urlopen('http://mahjong.maxb.eu/api/new_game/{}'.format(logname))
    bot.notice(httpresponse.read(), trigger.sender)
    game_info_to_irc(logname, xml, bot, trigger)
    return willie.module.NOLIMIT

@willie.module.rule(r'.*(20[0-9]{8}gm-[0-9a-f]{4}-[0-9]{4,5}-(?:[0-9a-f]{8}|x[0-9a-f]{12}))(&[&=%A-Za-z0-9]*)?.*')
def loglink(bot, trigger):
    if trigger.args[-1].startswith('.waml') or trigger.args[-1].startswith('.info'):
        return
    logname = trigger.group(1)
    logname = tenhouHash(logname)
    download_game(logname)
    httpresponse = urlopen('http://mahjong.maxb.eu/api/new_game/' + logname)
    bot.notice(httpresponse.read(), trigger.sender)
    return willie.module.NOLIMIT

def game_info_to_irc(logname, xml, bot, trigger):
    etree = ET.fromstring(xml)
    owari = etree.find('./*[@owari]').get('owari').split(',')
    un_tag = etree.find('UN')
    if un_tag.get('n3'):
        players = 4
    else:
        players = 3
    usernames = []
    scores = []
    uparams = [
        ('log', logname),
        ]
    for i in range(players):
        num = owari[i * 2 + 1]
        if num[0] != '-':
            num = "+" + num
        nx = 'n{}'.format(i)
        username = unquote(un_tag.get(nx))
        usernames.append(username)
        scores.append((
            username,
            num,
            float(num),
            i,
        ))
        uparams.append((nx, username))
    scores.sort(key=lambda x: x[2], reverse=True)
    trailer = trigger.group(2)
    viewpoint = handindex = None
    if trailer:
        for item in trailer.split('&'):
            bits = item.split('=', 1)
            if len(bits) == 2:
                k, v = bits
                if k == 'tw':
                    viewpoint = v
                elif k == 'ts':
                    handindex = v
    if handindex is not None:
        if viewpoint is not None:
            uparams.append(('tw', viewpoint))
        uparams.append(('ts', handindex))
    bot.notice("Replay: http://tenhou.net/0/?" + urlencode(uparams), trigger.sender)
    if handindex is None:
        if players == 4:
            bot.notice("Starting seats (ESWN): " + ", ".join(usernames), trigger.sender)
        else:
            bot.notice("Starting seats (ESW): " + ", ".join(usernames), trigger.sender)
    bot.notice("Scores: " + " ".join(("{}({})".format(name, score) for name, score, number, playerpos in scores)), trigger.sender)
