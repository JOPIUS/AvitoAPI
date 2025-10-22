import datetime
from typing import Dict, Any, Optional


class MessageContent:
	"""Содержимое сообщения."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Содержимое сообщения.
			data – словарь данных содержимого.
		"""
		self.__Data = data
	
	@property
	def text(self) -> Optional[str]:
		"""Текст сообщения."""
		return self.__Data.get("text")
	
	@property
	def image(self) -> Optional[Dict[str, Any]]:
		"""Данные изображения."""
		return self.__Data.get("image")
	
	@property
	def link(self) -> Optional[Dict[str, Any]]:
		"""Данные ссылки."""
		return self.__Data.get("link")
	
	@property
	def location(self) -> Optional[Dict[str, Any]]:
		"""Данные геометки."""
		return self.__Data.get("location")
	
	@property
	def voice(self) -> Optional[Dict[str, Any]]:
		"""Данные голосового сообщения."""
		return self.__Data.get("voice")
	
	@property
	def item(self) -> Optional[Dict[str, Any]]:
		"""Данные объявления."""
		return self.__Data.get("item")


class Message:
	"""Сообщение в мессенджере."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Сообщение в мессенджере.
			data – словарь данных сообщения.
		"""
		self.__Data = data
	
	@property
	def id(self) -> str:
		"""Идентификатор сообщения."""
		return self.__Data.get("id", "")
	
	@property
	def author_id(self) -> int:
		"""ID автора сообщения."""
		return self.__Data.get("author_id", 0)
	
	@property
	def content(self) -> MessageContent:
		"""Содержимое сообщения."""
		return MessageContent(self.__Data.get("content", {}))
	
	@property
	def created(self) -> datetime.datetime:
		"""Время создания сообщения."""
		timestamp = self.__Data.get("created", 0)
		return datetime.datetime.fromtimestamp(timestamp)
	
	@property
	def direction(self) -> str:
		"""Направление сообщения (in/out)."""
		return self.__Data.get("direction", "")
	
	@property
	def message_type(self) -> str:
		"""Тип сообщения."""
		return self.__Data.get("type", "")
	
	@property
	def is_read(self) -> bool:
		"""Прочитано ли сообщение."""
		return self.__Data.get("is_read", False)
	
	@property
	def read_time(self) -> Optional[datetime.datetime]:
		"""Время прочтения сообщения."""
		timestamp = self.__Data.get("read")
		if timestamp:
			return datetime.datetime.fromtimestamp(timestamp)
		return None


class User:
	"""Пользователь в чате."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Пользователь в чате.
			data – словарь данных пользователя.
		"""
		self.__Data = data
	
	@property
	def id(self) -> int:
		"""ID пользователя."""
		return self.__Data.get("id", 0)
	
	@property
	def name(self) -> str:
		"""Имя пользователя."""
		return self.__Data.get("name", "")
	
	@property
	def profile_url(self) -> Optional[str]:
		"""URL профиля пользователя."""
		profile = self.__Data.get("public_user_profile", {})
		return profile.get("url")
	
	@property
	def avatar_url(self) -> Optional[str]:
		"""URL аватара пользователя."""
		profile = self.__Data.get("public_user_profile", {})
		avatar = profile.get("avatar", {})
		return avatar.get("default")


class Chat:
	"""Чат в мессенджере."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Чат в мессенджере.
			data – словарь данных чата.
		"""
		self.__Data = data
	
	@property
	def id(self) -> str:
		"""Идентификатор чата."""
		return self.__Data.get("id", "")
	
	@property
	def created(self) -> datetime.datetime:
		"""Время создания чата."""
		timestamp = self.__Data.get("created", 0)
		return datetime.datetime.fromtimestamp(timestamp)
	
	@property
	def updated(self) -> datetime.datetime:
		"""Время последнего обновления чата."""
		timestamp = self.__Data.get("updated", 0)
		return datetime.datetime.fromtimestamp(timestamp)
	
	@property
	def last_message(self) -> Optional[Message]:
		"""Последнее сообщение в чате."""
		message_data = self.__Data.get("last_message")
		if message_data:
			return Message(message_data)
		return None
	
	@property
	def users(self) -> list[User]:
		"""Пользователи в чате."""
		users_data = self.__Data.get("users", [])
		return [User(user_data) for user_data in users_data]
	
	@property
	def context(self) -> Optional[Dict[str, Any]]:
		"""Контекст чата."""
		return self.__Data.get("context")
	
	@property
	def item_id(self) -> Optional[int]:
		"""ID объявления (если чат связан с объявлением)."""
		context = self.context
		if context and context.get("type") == "item":
			return context.get("value", {}).get("id")
		return None
	
	@property
	def item_title(self) -> Optional[str]:
		"""Название объявления."""
		context = self.context
		if context and context.get("type") == "item":
			return context.get("value", {}).get("title")
		return None
	
	@property
	def item_price(self) -> Optional[str]:
		"""Цена объявления."""
		context = self.context
		if context and context.get("type") == "item":
			return context.get("value", {}).get("price_string")
		return None


class ChatsList:
	"""Список чатов."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Список чатов.
			data – словарь данных списка чатов.
		"""
		self.__Data = data
	
	@property
	def chats(self) -> list[Chat]:
		"""Список чатов."""
		chats_data = self.__Data.get("chats", [])
		return [Chat(chat_data) for chat_data in chats_data]


class MessagesList:
	"""Список сообщений."""
	
	def __init__(self, data: list):
		"""
		Список сообщений.
			data – массив данных сообщений.
		"""
		self.__Data = data if isinstance(data, list) else []
	
	@property
	def messages(self) -> list[Message]:
		"""Список сообщений."""
		return [Message(message_data) for message_data in self.__Data]