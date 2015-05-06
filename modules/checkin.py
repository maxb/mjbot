import willie
import time

class State:
    def __init__(self):
        self.checked_in = []
        self.last_check = time.time()

    def timed_expiry(self):
        now = time.time()
        if self.last_check + 21600 < now:
            del self.checked_in[:]
        self.last_check = now

state = State()

@willie.module.commands('cin')
def checkin(bot, trigger):
    state.timed_expiry()
    who = trigger.nick
    if who in state.checked_in:
        bot.reply("You are already checked in", notice=True)
    else:
        state.checked_in.append(who)
        num = len(state.checked_in)
        bot.notice("{} checked in - we now have {} player{}".format(trigger.nick, num, '' if num == 1 else 's'), trigger.sender)
    return willie.module.NOLIMIT

@willie.module.commands('cout')
def checkout(bot, trigger):
    state.timed_expiry()
    who = trigger.nick
    try:
        state.checked_in.remove(who)
        num = len(state.checked_in)
        bot.notice("{} checked out - we now have {} player{}".format(trigger.nick, num, '' if num == 1 else 's'), trigger.sender)
    except ValueError:
        bot.reply("You were not checked in", notice=True)
    return willie.module.NOLIMIT

@willie.module.commands('fout')
def forcecheckout(bot, trigger):
    state.timed_expiry()
    who = trigger.group(2)
    try:
        state.checked_in.remove(who)
        num = len(state.checked_in)
        bot.notice("{} checked {} out - we now have {} player{}".format(trigger.nick, who, num, '' if num == 1 else 's'), trigger.sender)
    except ValueError:
        bot.reply("{} was not checked in".format(who), notice=True)
    return willie.module.NOLIMIT

@willie.module.commands('list')
def list(bot, trigger):
    state.timed_expiry()
    num = len(state.checked_in)
    if num:
        bot.notice("We have {} player{}: ".format(num, '' if num == 1 else 's') + ", ".join(state.checked_in), trigger.sender)
    else:
        bot.notice("No players are currently checked in", trigger.sender)
    return willie.module.NOLIMIT
