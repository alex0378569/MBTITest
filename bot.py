#Шаг 1 - импорт необходимых модулей
import sqlite3
import json
import os
import signal
import threading
from queue import Queue

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import datetime

#Шаг 2 - объявление переменных с данными от теста
about = ['MBTI - это психологическая система, позволяющая выделить яркие черты человека на основе определенных типов личности.',
         'Классификация людей по группам (16 типов личности) происходит в соответствии с уникальными когнитивными функциями (иначе способностью воспринимать и обрабатывать  информацию, принимать решения и организовывать личный успех). В каждом из типов Кэтрин и Изабелль Майерс-Бриггс (основательницы типологии) выделили 4 основные группы функций:',
         f'1. I/E (экстраверсия и интроверсия) - отвечает за восполнение человеком утраченной энергии. \n 2. N/S (сенсорика и интуиция) - отвечает за тип восприятия информации из окружающей среды. \n 3. F/T - отвечает за способ принятия решений. \n 4. P/J - отвечает за предпочитаемый образ жизни человека. \n Более подробная и качественная расшифровка с рекомендациями в профессиональной сфере будет представлена в результате прохождения теста.',
         'Важно помнить, что деление людей на четкие типы - не более чем условность, однако принадлежность человека к определенной группе поможет подтолкнуть на мысль о сильных и слабых сторонах личности.', 'Если у вас будут возникать сомнения при принятии решения, то выбирайте вариант, кажущийся наиболее предпочтительным и комфортным для себя в большинстве жизненных ситуаций.']
qs = {
    'intro_extra': [f"""1. В социальном взаимодействии вы склонны:  \n\nI. Больше слушать  \n\nII. Больше разговаривать (рассказывать о чем-либо)?""", f"""2. В повседневности вы: \n\nI. Сначала предаетесь рефлексии и анализу, а потом действуете  \n\nII. Сначала сразу реагируете на события, а потом задумываетесь над сделанным""", f"""3. Обычно вы: \n\nI. Первым не проявляете инициативы при знакомстве с людьми \n\nII. Стараетесь (как правило, сами того не замечая) ознакомиться с собеседником первыми""", f"""4. Ваш предпочтительный тип отдыха после утомительного труда:\n
I.  Пребывание наедине с собой, занимаясь любимым делом
\n\nII. Нахождение в компании друзей (хочу разрядиться в соц.среде - не люблю одиночество)""", f"""5. Опишите в двух словах вашу позицию в различных мероприятиях (например концерты/дискотеки/викторины):\n
I. Обычно держусь "особняком", не люблю выходить на публику, наблюдаю за событиями. Активная соц. позиция "разряжает" меня
\nII. Обычно расслабляюсь и могу в любой момент проявить себя: заводить новые знакомства или поучаствовать в энергичном движе"""],

    'sense_intuit':[f"""6. Ваш наиболее предпочитаемый тип получения информации: \n\nI. Факты и конкретные действия - больше опираюсь на реальные модели или инструкции. Более приземлен и не 'витаю в облаках'. Чаще отмечаю, что вижу ситуацию 'в деталях' и могу быстро отреагировать на изменения в настоящем.
\nII. Предпочитаю черпать информацию из идей или концепций, которых вижу в предмете наблюдения/интересующих темах. Любые ассоциации, скрытые взаимосвязи помогают формировать общую картину настоящего. Чаще отмечаю, что вижу ситуацию 'глобально'.""", f"""7. Ваш стиль решения проблем:
\nI. Обычно анализирую ситуацию и на основе раннее имеющихся знаний и опыта принимаю решения. Могу обратиться к конкретной инструкции или источнику (люди/статьи) для большей информации. Менее склонен(на) на доверие к интуиции.
\nII. Обычно полагаюсь на интуицию и/или внутренние ощущения, иногда могу найти решение проблемы совершенно неожиданным для себя образом (внезапный инсайт), соединяю точки между кусками данных бессознательно. Случалось, что не замечал(а) очевидных вещей перед глазами.""", f"""8. Какой жанр фильмов/книг для вас более привлекателен?\n
I. Контент, основанный на реальных событиях или документальных фактах (детектив, криминал, биографии, драмы, исторический или военный жанр, роман, психологическая драма)
\nII. Контент, основанный на воображаемых событиях (фэнтези, фантастика, хоррор, утопия или антиутопия)
""", f"""9. Какие из перечисленных качеств вы цените больше в других людях?\n
I. Практичность, прагматизм, предсказуемость, ловкость
\nII. Оригинальность, склонность к инновациям, непредсказуемость""", f"""10. Как вы относитесь к деталям?\n
I.  Сначала обращаю внимание на мелочи и детали, а затем строю выводы и общую картину относительно увиденного. Большое значение могу придать  источникам из реального мира, при необходимости обращаюсь к интуитивным домыслам.
\nII. Детали менее значимы; при получении фактов сначала интуитивно строю общую картину, а затем добавляю отдельные элементы (детали) для углубленного понимания.
"""],

    'feel_think': [f"""11. При решении внезапно возникшей проблемы вы скорее обратите внимание на:\n
I. Эмоциональную (=субъективную) сторону вопроса (спектр фокуса 'внутрь', рефлексивные вопросы и возможное обращение к мнению значимых людей). Вероятнее всего 'прочувствуете' ситуацию, дабы с точностью разобраться в решении проблемы.
\nII. Логическую (=объективную) сторону вопроса (спектр фокуса на поиск причин и следствий, анализ ситуации и 'мозговой штурм' (порой несвязанных рассуждений))""", f"""12. Работая в команде, вы с большей вероятностью:\n
I. Буду обращать внимание на 'атмосферу', царящую среди членов команды: я смогу найти решение через субъективный подход (не всегда логичный) в задачах и/или сглаживание 'острых углов' между участниками команды; стараюсь мотивировать/вдохновлять остальных через оригинальные предложения.
\nII. Буду стараться четко и прямолинейно решать поставленные задачи, в меньшей степени полагаясь на мнение и отношение к моим действиям окружающих; для меня прежде всего важна эффективность команды и поиск логичных решений (часто граничит с пренебрежением чувств членов команды, что может вызвать конфликт). Приоритет в сторону справедливых оценок и объективной критики.
""", f"""13. Как вы реагируете на критику?\n
I. Непроизвольно эмоционирую: могу сильно огорчиться/обидеться, затем отдалиться от этого человека. Но после 'бури' стараюсь понять, почему меня критикуют и прихожу к определенным выводам
\nII. Подхожу с аналитической точки зрения (безлично): не взирая на негативную окраску, пытаюсь логически понять, что и как мне изменить.""", f"""14. Как вы относитесь к компромиссам?\n
I. Ориентируюсь на ощущение, что компромиссы необходимо в первую очередь для стабилизации отношений (большее внимание на эмоциональную составляющую, логический исход может повременить)
\nII.  Считаю, что объективная справедливость одна, а значит должна быть логически обоснована (ценю компромиссы, если они оправданы с моей точки зрения, в противном случае отношусь нейтрально)""", f"""15. При выборе подарка близкому человеку вы скорее всего:\n
I. Буду опираться на личные ощущения: что вызовет у друга приятное удивление? Полезность и практичность подарка, как правило, оставляете на второй план.
\nII. Проанализирую, чем пользуется или мог бы пользоваться друг (в ближайшем будущем). Подарок должен быть, прежде всего, полезным и нужным."""],

    'perc_judge':[ f"""16. Стиль организации вашего дня (возьмите в пример свободный день):\n
I. Не строю далеких планов или графиков, предпочитаю реагировать на обстоятельства по мере возникновения; спокойно 'плыву по течению' и проживаю каждую минуту по своему усмотрению; 'списки дел' не нужны.
\nII. Заранее создаю определенный распорядок дня (или следую списку дел), ценю рутину. Считаю, что должен(на) извлечь хотя-бы минимальную пользу от настоящего, поэтому отношусь к проведению времени организованно.""", f"""17. Как вы относитесь к переменам? \n
I. Легко адаптируюсь и могу подстроиться под изменения без усилий; не считаю чем-то критичным, ведь перемены всегда к лучшему.
\nII. С усилием адаптируюсь к нововведениям. Могу огорчиться, если ранние ожидания не оправдались, но в целом нейтрально. Требуется определенное количество времени, чтобы 'влиться в поток' и стабилизировать дела. """, f"""18. Какие ситуации вызывают у вас больший стресс?\n
I. Требование со стороны окружающих/ситуации детального обдумывания плана действий, работа по расписанию или четкому графику без возможности 'лирического отсутпления'.  Рутина или 'жизнь по расписанию'- создание Дьявола.
\nII. Требование мгновенного ответа на вопрос или внезапное решение (когда нет времени на обдумывание, а в приоритете срочность), а также действовать (решать проблемы) в послений момент.
""", f"""19. При планировании поездки вы:\n
I. Беру самое необходимое (по собственному усмотрению) и принимаю решение о посещении мест; спонтанность и неожиданности вызывают у меня интерес. А вдруг я увижу то, что никогда не видел(а) в своей жизни?
\nII. Составляю продуманный план (в голове или внешнем носителе) мест для посещения; заблаговременно беспокоюсь о необходимых вещах и склонен(на) перепроверять документы/ценные бумаги.""", f"""20. При написании контрольной/проверочной работы или теста (о котором знали заранее) вы скорее всего:\n
I. Оцениваю свои возможности в соответствии с отведенным временем, обычно пишу сразу в чистовике и исправляю ошибки по мере продвижения; часто могу не подготавливаться заранее, но пишу работы на удовлетворительный результат.
\nII. Заранее отслеживаете, сколько примерно времени вам потребуется на выполнение того или иного задания; можете быть уверены в знаниях (тк готовились к работе дома) или расписываете все на черновике, после проверки переписывая на чистовик. Не любите спешку, перепроверяете каждый ответ."""]
}

user_state = {}
USER_FILE = 'user_state.json'

#Шаг 3 - работа с базой данных
query_queue = Queue()
result_queue = Queue()

def execute_query(query_queue, result_queue):
    con = sqlite3.connect('sixteen_pers.db')
    cur = con.cursor()
    while True:
        query = query_queue.get()
        if query is None:
            break
        cur.execute(query)
        result = cur.fetchall()
        result_queue.put(result)

        query_queue.task_done()

    con.close()
def thread_func(query_queue, result_queue, table_name, column_name):
    query = f'SELECT {column_name} FROM {table_name}'
    query_queue.put(query)
    result = result_queue.get()

    return result


#Возвращаю базовый словарь
def create_user_state():
   return  {'user_id':'', 'stage': 'intro_extra', 'index': 0, 'intro': 0, 'extra': 0, 'sense': 0, 'intuit': 0, 'think': 0, 'feel': 0, 'perceive': 0, 'judge': 0, 'feedback': ''}

#Загрузка состояния словаря
def load_user_state():
  global user_state
  if os.path.exists(USER_FILE):
      try:
       with open(USER_FILE, 'r') as file:
          file_content = file.read()
          if file_content:
              user_state = json.loads(file_content)
              print('User state loaded from file.')
          else:
              print('User state is empty, start with empty state')
              user_state = {}
      except json.JSONDecodeError as e:
          print(f'Error decoding json from file: {e}, start with empty state')
          user_state = {}

  else:
      print('No user state file found, starting with empty state.')
      user_state = {}

#Сохранение user_state в файл
def save_user_state():
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_state, f, ensure_ascii=False)
    print('User state saved to file.')

#Шаг 4 - создание бота
bot = telebot.TeleBot('7624758679:AAFHmqzPyIUooaZ8Z9Zyylmjhg1PKzr8nCM', parse_mode='HTML')

#Шаг 5 - основная 'магия' или реализация алгоритма диалога
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global user_state

    date = datetime.datetime.now()
    hour = date.hour
    time = ''
    if 0 <= hour < 4:
        time = '🌔 Доброй ночи'
    elif 4 <= hour < 12:
        time = '☀ Доброе утро'
    elif 12 <= hour < 17:
        time = '🕊 Добрый  день'
    elif 17 <= hour < 24:
        time = '🌃 Добрый  вечер'

    user_state = create_user_state()
    user_state['first_mssg'] = message.message_id

    welcome_message = bot.send_message(message.chat.id, f'<b>{time}, <i>{message.from_user.first_name}</i></b>.\n\nДанный бот является тестом, позволяющим определить Ваш тип личности по системе типологии MBTI. Но перед началом необходимо уточнить: хотите ознакомиться с основными концепциями системы МБТИ?', parse_mode='html' , reply_markup=get_kb(index=None,name='answ', letter=''))
    user_state['welcome_mssg'] = welcome_message.message_id
    save_user_state()


def get_kb(index, name, letter):
    kb = InlineKeyboardMarkup(row_width=2)
    kb_test = ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
    kb_remove = ReplyKeyboardRemove()
    if name == 'answ':
        btn_1 = InlineKeyboardButton('Да', callback_data=f'answ_yes')
        btn_2 = InlineKeyboardButton('Нет, перейти к тесту', callback_data=f'answ_no')
        kb.add(btn_1, btn_2)
        return kb

    elif name == 'about':
        if index == 0:
          btn_next = InlineKeyboardButton('Далее', callback_data=f'about_{index + 1}')
          kb.add(btn_next)
          return kb

        elif 1 <= index < len(about) - 1:
          btn_next = InlineKeyboardButton('Далее', callback_data=f'about_{index + 1}')
          btn_prev = InlineKeyboardButton('Назад', callback_data=f'about_{index - 1}')
          kb.add(btn_next, btn_prev)
          return kb

        elif index == len(about) - 1:
            btn_prev = InlineKeyboardButton('Назад', callback_data=f'about_{index - 1}')
            btn_to_test = InlineKeyboardButton('Перейти к тесту', callback_data=f'answ_no')
            kb.add(btn_prev, btn_to_test)
            return kb

    elif name == 'test':
        btn_first = KeyboardButton('Первое')
        btn_second = KeyboardButton('Второе')
        kb_test.add(btn_first, btn_second)
        return kb_test

    elif name == 'results':
        return kb_remove

    elif name == 'final':
        if index == 0:
          btn_next = InlineKeyboardButton('Далее', callback_data=f'final_{index + 1}_{letter}')
          kb.add(btn_next)
          return kb

        elif 1 <= index < len(description) - 1:
          btn_next = InlineKeyboardButton('Далее', callback_data=f'final_{index + 1}_{letter}')
          btn_prev = InlineKeyboardButton('Назад', callback_data=f'final_{index - 1}_{letter}')
          kb.add(btn_next, btn_prev)
          return kb

        elif index == len(description) - 1:
            btn_prev = InlineKeyboardButton('Назад', callback_data=f'final_{index - 1}_{letter}')
            kb.add(btn_prev)
            return kb

    elif name == 'rate':
        rate = InlineKeyboardMarkup(row_width=2)
        btn_1 = InlineKeyboardButton('🌟', callback_data='rate_one')
        btn_2 = InlineKeyboardButton('🌟🌟', callback_data='rate_two')
        btn_3 = InlineKeyboardButton('🌟🌟🌟', callback_data='rate_three')
        btn_4 = InlineKeyboardButton('🌟🌟🌟🌟', callback_data='rate_four')
        btn_5 = InlineKeyboardButton('🌟🌟🌟🌟🌟', callback_data='rate_five')
        rate.add(btn_1, btn_2, btn_3, btn_4, btn_5)
        return rate


@bot.message_handler(content_types=['text'])
def process_stage(message):
    stage = user_state.get('stage')

    if stage == 'intro_extra':
        process_test_iande(message)
    elif stage == 'sense_intuit':
        process_test_sandi(message)
    elif stage == 'feeling_thinking':
        process_test_fandt(message)
    elif stage == 'perceive_judge':
        process_test_pandj(message)
    elif stage == 'results':
        process_results(message)
    elif stage == 'rate':
        send_rate_msg(message)
    elif stage == 'awaiting_feedback':
        handle_feedback(message)
    elif stage == 'final_feedback':
        final_feedback(message)
    elif stage == '':
        img = open('assets/meme.jpg', 'rb')
        bot.send_photo(message.chat.id, img, f'{message.text}?')
        img.close()


def process_test_iande(message):
    try:
     i_e = qs['intro_extra']
     curr_index = user_state['index']

     if message.text == 'Первое':
         user_state['intro'] += 1
         curr_index += 1
         user_state['index'] = curr_index
         save_user_state()
         if curr_index < len(i_e):
             bot.send_message(chat_id=message.chat.id, text=f'{i_e[curr_index]}', reply_markup=get_kb(index = None, name='test',  letter=None))
         else:
             user_state['stage'] = 'sense_intuit'
             user_state['index'] = 0
             save_user_state()
             process_test_sandi(message)

     elif message.text == 'Второе':
        user_state['extra'] += 1
        curr_index += 1
        user_state['index'] = curr_index
        save_user_state()
        if curr_index < len(i_e):
            bot.send_message(chat_id=message.chat.id, text=f'{i_e[curr_index]}', reply_markup=get_kb(index=None, name='test',  letter=None))
        else:
            user_state['stage'] = 'sense_intuit'
            user_state['index'] = 0
            save_user_state()
            process_test_sandi(message)

     else:
        bot.send_message(chat_id=message.chat.id, text='Я не понимаю вас. Пожалуйста, введите "Первое" или "Второе" в соответствии с тем, что вам больше резонирует.')

    except KeyError as e:
        load_user_state()

def process_test_sandi(message):
    s_i = qs['sense_intuit']
    curr_index = user_state['index']

    if message.text == 'Первое':
        user_state['sense'] += 1
        if curr_index < len(s_i):
            bot.send_message(chat_id=message.chat.id, text=f'{s_i[curr_index]}', reply_markup=get_kb(index=None, name='test',  letter=None))
            curr_index += 1
            user_state['index'] = curr_index
            save_user_state()
        else:
            user_state['stage'] = 'feeling_thinking'
            user_state['index'] = 0
            save_user_state()
            process_test_fandt(message)

    elif message.text == 'Второе':
        user_state['intuit'] += 1
        if curr_index < len(s_i):
            bot.send_message(chat_id=message.chat.id, text=f'{s_i[curr_index]}', reply_markup=get_kb(index=None, name='test',  letter=None))
            curr_index += 1
            user_state['index'] = curr_index
            save_user_state()
        else:
            user_state['stage'] = 'feeling_thinking'
            user_state['index'] = 0
            save_user_state()
            process_test_fandt(message)
    else:
        bot.send_message(chat_id=message.chat.id, text='Я не понимаю вас. Пожалуйста, введите "Первое" или "Второе" в соответствии с тем, что вам больше резонирует.')

def process_test_fandt(message):
    f_t = qs['feel_think']
    curr_index = user_state['index']

    if message.text == 'Первое':
        user_state['feel'] +=1
        if curr_index < len(f_t):
            bot.send_message(chat_id=message.chat.id, text=f'{f_t[curr_index]}', reply_markup=get_kb(index=None, name='test',  letter=None))
            curr_index += 1
            user_state['index'] = curr_index
            save_user_state()
        else:
            user_state['stage'] = 'perceive_judge'
            user_state['index'] = 0
            save_user_state()
            process_test_pandj(message)

    elif message.text == 'Второе':
        user_state['think'] +=1
        if curr_index < len(f_t):
            bot.send_message(chat_id=message.chat.id, text=f'{f_t[curr_index]}', reply_markup=get_kb(index=None, name='test',  letter=None))
            curr_index += 1
            user_state['index'] = curr_index
            save_user_state()
        else:
            user_state['stage'] = 'perceive_judge'
            user_state['index'] = 0
            save_user_state()
            process_test_pandj(message)

    else:
        bot.send_message(chat_id=message.chat.id, text='Я не понимаю вас. Пожалуйста, введите "Первое" или "Второе" в соответствии с тем, что вам больше резонирует.')

def process_test_pandj(message):
    p_j = qs['perc_judge']
    curr_index = user_state['index']

    if message.text == 'Первое':
      user_state['perceive'] += 1
      if curr_index < len(p_j) - 1:
         bot.send_message(chat_id=message.chat.id, text=f'{p_j[curr_index]}', reply_markup=get_kb(index=None, name='test',  letter=None))
         curr_index += 1
         user_state['index'] = curr_index
         save_user_state()
      elif curr_index == len(p_j) - 1:
          last_mssg = bot.send_message(chat_id=message.chat.id, text=f'{p_j[-1]}', reply_markup=get_kb(index=None, name='results', letter=None))
          user_state['last_mssg'] = last_mssg.message_id
          user_state['stage'] = 'results'
          user_state['index'] = 0
          save_user_state()
          try:
              bot.delete_message(chat_id=message.chat.id, message_id=user_state['last_mssg'])
          except telebot.apihelper.ApiTelegramException as e:
              print(f"Error deleting last message: {e}")
          process_results(message)

    elif message.text == 'Второе':
      user_state['judge'] += 1
      if curr_index < len(p_j) - 1:
         bot.send_message(chat_id=message.chat.id, text=f'{p_j[curr_index]}', reply_markup=get_kb(index=None, name='test',  letter=None))
         curr_index += 1
         user_state['index'] = curr_index
         save_user_state()
      elif curr_index == len(p_j) - 1:
          last_mssg = bot.send_message(chat_id=message.chat.id, text=f'{p_j[-1]}', reply_markup=get_kb(index=None, name='results', letter=None))
          user_state['last_mssg'] = last_mssg.message_id
          user_state['stage'] = 'results'
          user_state['index'] = 0
          save_user_state()
          try:
              bot.delete_message(chat_id=message.chat.id, message_id=user_state['last_mssg'])
          except telebot.apihelper.ApiTelegramException as e:
              print(f"Error deleting last message: {e}")
          process_results(message)

    else:
        bot.send_message(chat_id=message.chat.id, text='Я не понимаю вас. Пожалуйста, введите "Первое" или "Второе" в соответствии с тем, что вам больше резонирует.')

def process_results(message):
    outcome_type = []

    global description
    description = []

    intro = user_state['intro']
    extra = user_state['extra']
    sense = user_state['sense']
    intuit = user_state['intuit']
    think = user_state['think']
    feel = user_state['feel']
    perceive = user_state['perceive']
    judge = user_state['judge']

    if intro > extra:
        outcome_type.append('i')
    else:
        outcome_type.append('e')

    if sense > intuit:
        outcome_type.append('s')
    else:
        outcome_type.append('n')

    if think > feel:
        outcome_type.append('t')
    else:
        outcome_type.append('f')

    if perceive > judge:
        outcome_type.append('p')
    else:
        outcome_type.append('j')

    letters = ''.join(outcome_type)

    db_thread = threading.Thread(target=execute_query, args=(query_queue, result_queue))
    db_thread.start()

    thread_queue = []
    columns = ['main_letters', 'cognitive', 'pluses', 'minuses', 'work', 'persons']

    for column in columns:
        thread = threading.Thread(target=lambda q, r, l, c: description.extend(thread_func(q, r, l, c)), args=(query_queue, result_queue, letters, column))
        thread_queue.append(thread)
        thread.start()

    for thread_one in thread_queue:
        thread_one.join()

    query_queue.put(None)
    db_thread.join()

    chat_id = message.chat.id
    description = [item[0] for item in description]

    send_markup_message(message, chat_id, letters)

def send_markup_message(message, chat_id, letters):
    bot.send_message(chat_id=chat_id,  text=f'Ваш тип личности - {letters}! \n\n {description[0]}', parse_mode='HTML', reply_markup=get_kb(index=0, name='final', letter=letters))

    user_state['stage'] = 'rate'
    save_user_state()
    send_rate_msg(message)

def send_rate_msg(message):
    bot.send_message(chat_id=message.chat.id, text=f'Благодарю за прохождение теста, {message.from_user.first_name}! Пожалуйста, оцените работу бота и качество подачи материала.', reply_markup=get_kb(index=None, name='rate', letter=None))

def send_feedback(message):
    bot.send_message(chat_id=message.chat.id, text='И последнее: не могли бы вы оставить краткий комментарий с вашим мнением относительно работы бота? Любая точка зрения важна при сборе статистики.')
    user_state['stage'] = 'awaiting_feedback'
    save_user_state()

#Шаг 6 - обработка отзывов от пользователя
@bot.message_handler(func=lambda message: user_state.get('stage') == 'awaiting_feedback')
def handle_feedback(message):
    feedback_text = message.text

    if feedback_text:
        user_state['feedback'] = feedback_text
        user_state['stage'] = 'final_feedback'
        save_user_state()
        bot.send_message(chat_id=message.chat.id, text='Вы уверены, что хотите оставить отзыв? Пожалуйста, напишите "Да" или "Нет" (с прописной буквы)')
    else:
        bot.send_message(chat_id=message.chat.id, text='Отзыв не может быть пустым.')

@bot.message_handler(func=lambda message:  user_state.get('stage') == 'final_feedback')
def final_feedback(message):
    final_state = message.text

    if final_state == 'Да':
        bot.send_message(chat_id=message.chat.id, text='Ваш отзыв успешно сохранен! Спасибо за мнение.')
        user_state['stage'] = ''
        save_user_state()
    elif final_state == 'Нет':
        user_state['feedback'] = ''
        bot.send_message(chat_id=message.chat.id, text='Вы можете переписать ваш отзыв.')
        user_state['stage'] = 'awaiting_feedback'
        save_user_state()
    else:
        bot.send_message(chat_id=message.chat.id, text='Пожалуйста, отправьте "Да" или "Нет" (с прописной буквы).')

#Шаг 7 - обработка ключевых запросов от кнопок, включенных в сообщения бота
@bot.callback_query_handler(func=lambda call: True)
def main(call):
    user_id = call.message.from_user.id
    if 'answ' in call.data:
        user_state['user_id'] = user_id
        save_user_state()
        if 'yes' in call.data:
            if  user_state['first_mssg'] != '':
              try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=user_state['first_mssg'])
              except telebot.apihelper.ApiTelegramException as e:
                  print(f"Error deleting first message: {e}")
              else:
                bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'{about[0]}',
                reply_markup=get_kb(index=0, name='about', letter=None))


        elif 'no' in call.data:
            i_e = qs['intro_extra']
            if user_state['first_mssg'] != '':
             try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=user_state['first_mssg'])
             except telebot.apihelper.ApiTelegramException as e:
                print(f"Error deleting first message: {e}")
            try:
              edited = bot.edit_message_text(chat_id=call.message.chat.id, message_id=user_state['welcome_mssg'], text='Загрузка данных...')
              bot.send_message(chat_id=call.message.chat.id, text=f'{i_e[0]}', reply_markup=get_kb(index=0, name='test', letter=None))
              bot.delete_message(chat_id=call.message.chat.id, message_id=edited.message_id)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Error deleting welcome message: {e}")

    elif 'about' in call.data:
        index = int(call.data.split('_')[1])
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'{about[index]}',reply_markup=get_kb(index, name='about', letter=None))

    elif 'final' in call.data:
        index = int(call.data.split('_')[1])
        p_t = call.data.split('_')[2]
        pre = ''
        if index == 0:
            pre = f'Ваш тип личности - {p_t}'
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'{pre}\n {description[index]}', parse_mode='HTML', reply_markup=get_kb(index=index, name='final', letter= p_t))

    elif call.data.startswith('rate'):
        end = call.data.split('_')[1]
        if end == 'one' or end == 'two':
            bot.answer_callback_query(callback_query_id=call.id, text='Спасибо за оценку! В ближайшем будущем бот будет дополняться, так что неточности в работе будут сведены к 0. Жду вас снова!^^')
            send_feedback(call.message)

        elif end == 'three' or end == 'four':
            bot.answer_callback_query(callback_query_id=call.id, text='Благодарю за оценку. В ближайшем будущем бот будет дополняться, так что я постараюсь пофиксить прошлые ошибки. Жду вас снова!^^')
            send_feedback(call.message)

        elif end == 'five':
            bot.answer_callback_query(callback_query_id=call.id, text='Очень рада, что вам понравилось! В ближайшем будущем бот будет дополняться, добавится новая информация по психологии личности. Жду вас снова!^^ ')
            send_feedback(call.message)

#Доп. защита данных при сбросе сервера
def signal_handler(sig, frame):
    print('Saving user_state and exiting')
    save_user_state()
    exit(0)

signal.signal(signal.SIGINT, signal_handler) # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # Завершение процесса (например, Heroku)


#Шаг 8 - запуск бота
if __name__ == '__main__':
    load_user_state()
    bot.polling(none_stop=True)
