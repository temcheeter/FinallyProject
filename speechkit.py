import requests
from creds import get_creds
iam_token, folder_id = get_creds()


def speech_to_text(data):
    # iam_token, folder_id для доступа к Yandex SpeechKit
    iam_token = 't1.9euelZqeiomNj8jLipDMi4ycy5iezu3rnpWamZCbksqZns2Ois-KkpOPmsnl8_cDSztO-e8wdzgw_t3z90N5OE757zB3ODD-zef1656VmsrGmMabyJbHmZvHnc7IzJaO7_zF656VmsrGmMabyJbHmZvHnc7IzJaOveuelZqOnc_NkIqNjZGPzoyQi5qcyrXehpzRnJCSj4qLmtGLmdKckJKPioua0pKai56bnoue0oye.c0ICHRNm3M17dOV6d_0icIZ9KJaha_x9Q7KKzGwyBzAVCC3HYsW9jSJAa2JxyerZkshUCZrCLrQ_sRbf8AwDAA'
    folder_id = 'b1gpk923r09kr4aijb0s'

    # Указываем параметры запроса
    params = "&".join([
        "topic=general",  # используем основную версию модели
        f"folderId={folder_id}",
        "lang=ru-RU"  # распознаём голосовое сообщение на русском языке
    ])

    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {iam_token}',
    }

    # Выполняем запрос
    response = requests.post(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers,
        data=data
    )

    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
    else:
        return False, "При запросе в SpeechKit возникла ошибка"


def text_to_speech(text):
    # iam_token, folder_id для доступа к Yandex SpeechKit
    iam_token = 't1.9euelZqeiomNj8jLipDMi4ycy5iezu3rnpWamZCbksqZns2Ois-KkpOPmsnl8_cDSztO-e8wdzgw_t3z90N5OE757zB3ODD-zef1656VmsrGmMabyJbHmZvHnc7IzJaO7_zF656VmsrGmMabyJbHmZvHnc7IzJaOveuelZqOnc_NkIqNjZGPzoyQi5qcyrXehpzRnJCSj4qLmtGLmdKckJKPioua0pKai56bnoue0oye.c0ICHRNm3M17dOV6d_0icIZ9KJaha_x9Q7KKzGwyBzAVCC3HYsW9jSJAa2JxyerZkshUCZrCLrQ_sRbf8AwDAA'
    folder_id = 'b1gpk923r09kr4aijb0s'
    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {iam_token}',
    }
    data = {
        'text': text,  # текст, который нужно преобразовать в голосовое сообщение
        'lang': 'ru-RU',  # язык текста - русский
        'voice': 'omazh',  # мужской голос Филиппа
        'speed': 1.3,
        'emotion': 'evil',
        'folderId': folder_id
    }
    # Выполняем запрос
    response = requests.post(
        'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize',
        headers=headers,
        data=data
    )
    if response.status_code == 200:
        return True, response.content  # возвращаем статус и аудио
    else:
        return False, "При запросе в SpeechKit возникла ошибка"