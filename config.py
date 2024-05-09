HOME_DIR = '/home/student/FinallyProject/'

BOT_TOKEN_PATH = f'{HOME_DIR}creds/bot_token.txt'
FOLDER_ID_PATH = f'{HOME_DIR}creds/folder_id.txt'
IAM_TOKEN_PATH = f'{HOME_DIR}creds/iam_token.txt'

MAX_USERS = 10  # максимальное кол-во пользователей
MAX_GPT_TOKENS = 120  # максимальное кол-во токенов в ответе GPT
COUNT_LAST_MSG = 3  # кол-во последних сообщений из диалога

# лимиты для пользователя
MAX_USER_STT_BLOCKS = 10
MAX_USER_TTS_SYMBOLS = 7500
MAX_USER_GPT_TOKENS = 7500

LOGS = f'{HOME_DIR}logs.txt'  # файл для логов
DB_FILE = f'{HOME_DIR}database.db'  # файл для базы данных
SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. '
                                            'Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. '
                                            'Изображай человека'}]  # список с системным промтом