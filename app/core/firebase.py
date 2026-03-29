import firebase_admin
from firebase_admin import credentials, firestore, messaging
import os
import json
import threading
import time

def init_firebase():
    if not firebase_admin._apps:
        service_account = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)

def send_match_notifications(match_id: str, user_id1: str, user_id2: str):
    db = firestore.client()

    user1 = db.collection("users").document(user_id1).get().to_dict() or {}
    user2 = db.collection("users").document(user_id2).get().to_dict() or {}

    token1 = user1.get("fcmToken")
    token2 = user2.get("fcmToken")
    name1  = user1.get("name", "Кто-то")
    name2  = user2.get("name", "Кто-то")

    print(f"token1={token1}, token2={token2}")

    messages = []

    if token1:
        messages.append(messaging.Message(
            token=token1,
            data={
                "type": "match",
                "matchId": match_id,
                "otherUid": user_id2,
                "title": "У вас мэтч",      
                "body": f"Вы и {name2} понравились друг другу" 
            },
        ))

    if token2:
        messages.append(messaging.Message(
            token=token2,
            data={
                "type": "match",
                "matchId": match_id,
                "otherUid": user_id1,
                "title": "У вас мэтч",
                "body": f"Вы и {name1} понравились друг другу"
            },
        ))

    if messages:
        response = messaging.send_each(messages)
        print(f"Уведомления отправлены для матча {match_id}: {response.success_count} успешно")
    else:
        print(f"Матч {match_id}: токены не найдены, уведомления не отправлены")

    db.collection("matches").document(match_id).update({"notificationSent": True})


def send_message_notification(chat_id: str, sender_uid: str, text: str):
    db = firestore.client()

    chat = db.collection("chats").document(chat_id).get().to_dict() or {}
    member_uids = chat.get("memberUids", [])
    receiver_uid = next((uid for uid in member_uids if uid != sender_uid), None)
    if not receiver_uid:
        return

    sender = db.collection("users").document(sender_uid).get().to_dict() or {}
    receiver = db.collection("users").document(receiver_uid).get().to_dict() or {}

    token = receiver.get("fcmToken")
    sender_name = sender.get("name", "Кто-то")

    if not token:
        print(f"Нет токена для {receiver_uid}")
        return

    message = messaging.Message(
        token=token,
        data={
            "type": "message",
            "chatId": chat_id,
            "otherUid": sender_uid,
            "title": sender_name,
            "body": text if len(text) <= 100 else text[:97] + "..."
        },
    )

    response = messaging.send(message)
    print(f"Уведомление о сообщении отправлено: {response}")


def _messages_listener_loop():
    while True:
        try:
            db = firestore.client()
            done = threading.Event()

            def on_snapshot(col_snapshot, changes, read_time):
                for change in changes:
                    if change.type.name != "ADDED":
                        continue

                    msg_data = change.document.to_dict()

                    if msg_data.get("notificationSent"):
                        continue

                    sender_uid = msg_data.get("senderUid")
                    text = msg_data.get("text", "")
                    chat_id = change.document.reference.parent.parent.id

                    if not sender_uid or not text:
                        continue

                    print(f"Новое сообщение в чате {chat_id} от {sender_uid}")

                    try:
                        send_message_notification(chat_id, sender_uid, text)
                        # помечаем что уведомление отправлено
                        change.document.reference.update({"notificationSent": True})
                    except Exception as e:
                        print(f"Ошибка уведомления о сообщении: {e}")

            watch = db.collection_group("messages").on_snapshot(on_snapshot)
            print("Слушатель сообщений запущен")

            done.wait()

        except Exception as e:
            print(f"Слушатель сообщений упал, перезапускаем через 10 сек: {e}")
            time.sleep(10)


def start_messages_listener():
    thread = threading.Thread(target=_messages_listener_loop, daemon=True)
    thread.start()


def _listener_loop():
    while True:
        try:
            db = firestore.client()
            done = threading.Event()

            def on_snapshot(col_snapshot, changes, read_time):
                for change in changes:
                    if change.type.name != "ADDED":
                        continue

                    match_data = change.document.to_dict()
                    match_id = change.document.id

                    if match_data.get("notificationSent"):
                        continue

                    uids = match_data.get("uids", [])
                    if len(uids) < 2:
                        continue

                    print(f"Новый матч обнаружен: {match_id}")

                    user_id1 = uids[0]
                    user_id2 = uids[1]

                    try:
                        send_match_notifications(match_id, user_id1, user_id2)
                    except Exception as e:
                        print(f"Ошибка для матча {match_id}: {e}")

            watch = db.collection("matches").on_snapshot(on_snapshot)
            print("Слушатель матчей запущен")

            done.wait()

        except Exception as e:
            print(f"Слушатель упал, перезапускаем через 10 сек: {e}")
            time.sleep(10)

def start_matches_listener():
    thread = threading.Thread(target=_listener_loop, daemon=True)
    thread.start()