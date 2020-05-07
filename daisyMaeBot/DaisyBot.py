import sys
sys.path.append('..')
import traceback

import genericBotBase.botbase as BotBase

log = BotBase.log
config = BotBase.config
bot = BotBase.bot

extensions = [
   'genericBotBase.cogs.admin',
   'genericBotBase.cogs.common',
   'genericBotBase.cogs.basic',
   'cogs.QueueCommands'
]

def main():
   BotBase.loadExtensions( extensions )
   BotBase.run()

if __name__ == '__main__':
   main()
