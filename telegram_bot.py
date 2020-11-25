#!/usr/bin/env python3
#coding=utf-8

import requests
import datetime



class BotHandler:
    def __init__(self, token):
            self.token = token
            self.api_url = "https://api.telegram.org/bot{}/".format(token)

    #url = "https://api.telegram.org/bot<token>/"

    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def get_first_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[0]
        else:
            last_update = None

        return last_update


token = '' 
CalUpdaterBot = BotHandler(token) 

def main():
    #CalUpdaterBot.send_message(590859681, 'test')
    
    new_offset = 0
    print('Telegram-Bot LAUNCHING...')
        
    while True:
        all_updates=CalUpdaterBot.get_updates(new_offset)

        if len(all_updates) > 0:
            for current_update in all_updates:
                print(current_update)
                first_update_id = current_update['update_id']
                first_chat_id = current_update['message']['chat']['id']

                with open('chat_Ids.txt') as f:
                        input = f.readlines()
                        idExists = any(str(first_chat_id) in s for s in input)

                if not idExists:
                    with open('chat_Ids.txt', 'a') as out:
                        out.write(str(first_chat_id))

                if 'text' not in current_update['message']:
                    chat_text='New member'
                else:
                    chat_text = current_update['message']['text']
                
                # Suche Vornamen
                if 'first_name' in current_update['message']:
                    first_chat_name = current_update['message']['chat']['first_name']
                elif 'new_chat_member' in current_update['message']:
                    first_chat_name = current_update['message']['new_chat_member']['username']
                elif 'from' in current_update['message']:
                    first_chat_name = current_update['message']['from']['first_name']
                else:
                    first_chat_name = "unknown"

                if chat_text == '/start' or chat_text == '/Start':
                    CalUpdaterBot.send_message(first_chat_id, 'Hey ' + first_chat_name + ',\nsobald es Neuigkeiten im Stundenplan gibt, erfährst du sie von mir!')
                    new_offset = first_update_id + 1
                    idExists = False
                else:
                    CalUpdaterBot.send_message(first_chat_id, 'Sobald es Neuigkeiten im Stundenplan gibt, erfährst du sie von mir!')
                    new_offset = first_update_id + 1

                chat_text = ''


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
