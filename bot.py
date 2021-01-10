# -*- coding: utf-8 -*-

import configparser
import datetime

try:
    from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
    import vk_api
    import requests
except:
    logger.critical('Установите необходимые модули через команду \'pip install -r requirements.txt\' перед запуском скрипта.'); exit()

def key_generation():
    return ''.join(k for k in list(random.choice(string.ascii_letters + string.digits) for i in range(random.randint(20, 30))))

def vk_send_message_to_user(vk, user_id, message, attachments = None, keyboard = None):
    vk.messages.send(user_id = int(user_id), random_id = vk_api.utils.get_random_id(), message=message, attachment = attachments, keyboard = keyboard)

def vk_send_message_to_chat(vk, chat_id, message, attachments = None, keyboard = None):
    vk.messages.send(chat_id = int(chat_id), random_id = vk_api.utils.get_random_id(), message=message, attachment = attachments, keyboard = keyboard)

MAX_NICKNAME_LENGTH = 30 # max count of symbols in nicknames

config = configparser.ConfigParser()
config.read("settings.ini", encoding="utf8") 


vk_group_token = config['VK']['token'][1:-1]
vk_group_id = int(config['VK']['group_id'][1:-1])
vk_admin_id = int(config['VK']['admin_id'][1:-1])

# requirement for some features which you can't do from group, like vk.users.get() etc.
vk_common_login = config['VK Common']['login'][1:-1]
vk_common_password = config['VK Common']['password'][1:-1]

try:
    vk_session = vk_api.VkApi(token=vk_group_token)
    longpoll = VkBotLongPoll(vk_session, vk_group_id)
    vk = vk_session.get_api()

except Exception as exception:
    print(f'Не удалось войти от имени группы: \n\n{exception}'); exit()

try:
    vk_session = vk_api.VkApi(login=vk_common_login, password=vk_common_password)
    vk_session.auth()

    vk_common = vk_session.get_api()

except Exception as exception:
    print(f'Не удалось войти от имени страницы: \n\n{exception}'); exit()

chat = {}

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.from_user:
            if event.obj.text.lower() == 'начать':
                vk_send_message_to_user(vk, event.obj.from_id, f'Hail Шаховстану! Сейчас в беседе {len(chat.keys())} людей. Чтобы начать общаться, введи команду \'.ник (Ваш ник)\'. Этой же командой потом его можно сменить. Приятного общения!')

            elif event.obj.text.startswith('.ник '):
                new_nickname = ' '.join(word for word in event.obj.text.split(' ')[1:]).strip()
                
                if new_nickname in chat.values():
                    vk_send_message_to_user(vk, event.obj.from_id, f'Пользователь с ником {new_nickname} уже есть в чате.')

                elif len(new_nickname) > MAX_NICKNAME_LENGTH:
                    vk_send_message_to_user(vk, event.obj.from_id, f'Ник {new_nickname} содержит в себе больше {MAX_NICKNAME_LENGTH} символов. Такие ники недопустимы в чате.')

                else:
                    if event.obj.from_id in chat.keys():
                        for user_id in chat.keys():
                            vk_send_message_to_user(vk, user_id, f'<{chat[event.obj.from_id]}> стал <{new_nickname}>!')

                        chat[event.obj.from_id] = new_nickname

                    else:
                        chat[event.obj.from_id] = new_nickname

                        for user_id in chat.keys():
                            vk_send_message_to_user(vk, user_id, f'<{new_nickname}> присоединился к чату!')

            elif event.obj.text.lower().startswith('.лс '):
                if event.obj.from_id in chat.keys():
                    target_nickname = event.obj.text[event.obj.text.find('('):event.obj.text.find(')')+event.obj.text.count(')')][1:-1]
                    message = event.obj.text[event.obj.text.find(')') + 2:]

                    if target_nickname in chat.values():
                        vk_send_message_to_user(vk, list(chat.keys())[list(chat.values()).index(target_nickname)], f'Личное сообщение от {chat[event.obj.from_id]}: \n{message}')
                        vk_send_message_to_user(vk, event.obj.from_id, 'Личное сообщение отправлено!')
                    elif chat[event.obj.from_id] == target_nickname:
                        vk_send_message_to_user(vk, event.obj.from_id, 'Самому себе личное сообщение отправить нельзя.')
                    else:
                        vk_send_message_to_user(vk, event.obj.from_id, 'Пользователя с таким ником нет в чате!')

                else:
                    vk_send_message_to_user(vk, event.obj.from_id, 'Ты не в чате! Напиши \'Начать\', чтобы увидеть справку по боту')

            elif event.obj.text.lower() == '.выход':
                if event.obj.from_id in chat.keys():

                    for user_id in chat.keys():
                        vk_send_message_to_user(vk, user_id, f'<{chat[event.obj.from_id]}> покинул чат!')

                    chat.pop(event.obj.from_id)

                    vk_send_message_to_user(vk, event.obj.from_id, 'Вы вышли из чата! Вновь зайти в него вы сможете, задав себе новый ник.')
                else:
                    vk_send_message_to_user(vk, event.obj.from_id, 'Вы и не были в чате!')

            elif event.obj.text.lower() == '.онлайн':
                vk_send_message_to_user(vk, event.obj.from_id, f'Онлайн участников: {len(chat)}')
                vk_send_message_to_user(vk, event.obj.from_id, 'Список ников участников: \n' + '\n'.join(f'<{nick}>' for nick in list(chat.values())))

            else:
                if event.obj.from_id in chat.keys():
                    for user_id in chat.keys():
                        if not event.obj.attachments:
                            vk_send_message_to_user(vk, user_id, f'<{chat[event.obj.from_id]}>\n{event.obj.text}')
                else:
                    vk_send_message_to_user(vk, event.obj.from_id, 'Ты не в чате! Напиши \'Начать\', чтобы увидеть справку по боту')
        elif event.from_chat:
            if event.obj.text.lower() == '.шаховы':
                if vk_common.users.get(user_ids=event.obj.from_id)[0]['last_name'].startswith('Шахов'):
                    vk_send_message_to_chat(vk, event.chat_id, vk_common.wall.get(owner_id=-vk_group_id, count=1)['items'][0]['text'])
                else:
                    vk_send_message_to_chat(vk, event.chat_id, 'Ты не достоин. Ты не шахов. Только шахов может вызвать своих.')
