import requests
import json
from typing import Dict, List, Optional


class Messenger:
	"""Модуль API: Мессенджер Авито."""
	
	def __init__(self, profile: int | str, session=None):
		"""
		Модуль API: Мессенджер Авито.
			profile – номер профиля Авито;
			session – указатель на готовую сессию библиотеки requests.
		"""
		# Номер профиля Авито
		self.__Profile = int(profile)
		# Модуль выполнения запросов
		self.__Requests = session if session is not None else requests.Session()
	
	def get_chats(self, chat_types: List[str] = None, unread_only: bool = False, 
				  item_ids: List[int] = None, limit: int = 100, offset: int = 0) -> requests.Response:
		"""
		Получает список чатов пользователя.
			chat_types – типы чатов для фильтрации (u2i, u2u);
			unread_only – получать только непрочитанные чаты;
			item_ids – получать чаты только по указанным объявлениям;
			limit – количество чатов для запроса (макс 100);
			offset – сдвиг для пагинации.
		"""
		params = {
			"limit": limit,
			"offset": offset,
			"unread_only": unread_only
		}
		
		if chat_types:
			params["chat_types"] = ",".join(chat_types)
		if item_ids:
			params["item_ids"] = ",".join(map(str, item_ids))
			
		response = self.__Requests("GET", f"https://api.avito.ru/messenger/v2/accounts/{self.__Profile}/chats", 
								   params=params)
		return response
	
	def get_messages(self, chat_id: str, limit: int = 100, offset: int = 0) -> requests.Response:
		"""
		Получает список сообщений из чата.
			chat_id – идентификатор чата;
			limit – количество сообщений (макс 100);
			offset – сдвиг для пагинации.
		"""
		params = {"limit": limit, "offset": offset}
		
		response = self.__Requests("GET", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/messages",
								   params=params)
		return response
	
	def send_message(self, chat_id: str, text: str) -> requests.Response:
		"""
		Отправляет текстовое сообщение в чат.
			chat_id – идентификатор чата;
			text – текст сообщения (макс 1000 символов).
		"""
		if len(text) > 1000:
			raise ValueError("Текст сообщения не может превышать 1000 символов")
			
		body = {
			"type": "text",
			"message": {
				"text": text
			}
		}
		
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/messages",
								   json=body)
		return response
	
	def mark_chat_read(self, chat_id: str) -> requests.Response:
		"""
		Отмечает чат как прочитанный.
			chat_id – идентификатор чата.
		"""
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/read")
		return response
	
	def delete_message(self, chat_id: str, message_id: str) -> requests.Response:
		"""
		Удаляет сообщение из чата.
			chat_id – идентификатор чата;
			message_id – идентификатор сообщения.
		"""
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/messages/{message_id}")
		return response
	
	def upload_image(self, image_file) -> requests.Response:
		"""
		Загружает изображение для отправки в сообщении.
			image_file – файл изображения (макс 24 МБ).
		"""
		files = {"uploadfile[]": image_file}
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/uploadImages",
								   files=files)
		return response
	
	def send_image_message(self, chat_id: str, image_id: str) -> requests.Response:
		"""
		Отправляет сообщение с изображением.
			chat_id – идентификатор чата;
			image_id – идентификатор загруженного изображения.
		"""
		body = {"image_id": image_id}
		
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/messages/image",
								   json=body)
		return response
	
	def add_to_blacklist(self, user_id: int, reason_id: int = 4, item_id: Optional[int] = None) -> requests.Response:
		"""
		Добавляет пользователя в черный список.
			user_id – ID пользователя для блокировки;
			reason_id – причина блокировки (1-спам, 2-мошенничество, 3-оскорбление, 4-другое);
			item_id – ID объявления (опционально).
		"""
		context = {"reason_id": reason_id}
		if item_id:
			context["item_id"] = item_id
			
		body = {
			"users": [{
				"user_id": user_id,
				"context": context
			}]
		}
		
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v2/accounts/{self.__Profile}/blacklist",
								   json=body)
		return response

	def get_webhooks(self) -> requests.Response:
		"""
		Получает список активных webhook подписок.
		"""
		response = self.__Requests("POST", "https://api.avito.ru/messenger/v1/subscriptions")
		return response
	
	def subscribe_webhook(self, url: str) -> requests.Response:
		"""
		Подписывается на webhook уведомления.
			url – URL для получения уведомлений.
		"""
		body = {"url": url}
		response = self.__Requests("POST", "https://api.avito.ru/messenger/v1/webhook/subscribe",
								   json=body)
		return response
	
	def unsubscribe_webhook(self, url: str) -> requests.Response:
		"""
		Отписывается от webhook уведомлений.
			url – URL для отключения уведомлений.
		"""
		body = {"url": url}
		response = self.__Requests("POST", "https://api.avito.ru/messenger/v1/webhook/unsubscribe",
								   json=body)
		return response