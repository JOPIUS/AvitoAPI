from AvitoAPI.Types.ShortTermRent import *
from AvitoAPI.Types.Info import *

import datetime
import requests
import json

class Info:
	"""Модуль API: информация о пользователе."""
	
	def __init__(self, profile: int | str, session: any = None):
		"""
		Модуль API: краткосрочная аренда.
			profile – номер профиля Авито;
			session – указатель на готовую сессию библиотеки requests.
		"""

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Номер профиля авито.
		self.__Profile = int(profile)
		# Модуль выполнения запросов.
		self.__Requests = session if session != None else requests.Session()
		
	def get_balance(self) -> Balance | None:
		"""Возвращает баланс кошелька."""
		
		# Выполнение запроса.
		Response = self.__Requests("GET", f"https://api.avito.ru/core/v1/accounts/{self.__Profile}/balance/")
		# Интерпретация ответа.
		Data = json.loads(Response.text)
		# Объектное представление баланса.
		BalanceObject = Balance(Data["real"], Data["bonus"])
		
		return BalanceObject
	
	def get_info(self) -> ProfileInfo | None:
		"""Возвращает информацию о пользователе."""
		
		# Выполнение запроса.
		Response = self.__Requests("GET", f"https://api.avito.ru/core/v1/accounts/self")
		# Интерпретация ответа.
		Data = json.loads(Response.text)
		# Объектное представление баланса.
		BalanceObject = ProfileInfo(Data)
		
		return BalanceObject

class ShortTermRent:
	"""Модуль API: краткосрочная аренда."""
	
	def __init__(self, profile: int | str, session: any = None):
		"""
		Модуль API: краткосрочная аренда.
			profile – номер профиля Авито;
			session – указатель на готовую сессию библиотеки requests.
		"""

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Номер профиля авито.
		self.__Profile = int(profile)
		# Модуль выполнения запросов.
		self.__Requests = session if session != None else requests.Session()
		
	def get_bookings(
			self,
			item_id: int | str,
			date_start: datetime.datetime,
			date_end: datetime.datetime,
			with_unpaid: bool = True
		) -> list[Booking] | None:
		
		"""
		Возвращает список броней по объявлению.
			item_id – идентификатор объявления;
			date_start – дата начала выборки;
			date_end – дата окончания выборки;
			with_unpaid – указывает, добавлять ли в выборку неоплаченные брони.
		"""
		# Параметры запроса.
		Params = {
			"date_start": str(date_start.date()),
			"date_end": str(date_end.date()),
			"with_unpaid": with_unpaid
		}
		# Выполнение запроса.
		Response = self.__Requests("GET", f"https://api.avito.ru/realty/v1/accounts/{self.__Profile}/items/{item_id}/bookings", params = Params)
		
		# Если запрос успешен.
		if Response.status_code == 200: 
			# Буфер преобразования.
			Bufer = list()
			# Полученные данные.
			Data = json.loads(Response.text)
			
			# Для каждого элемента.
			for Element in Data["bookings"]:
				# Сохранить преобразованные в объект данные.
				Bufer.append(Booking(Element))
				
			# Перезапись ответа буфером.
			Response = Bufer
		
		else:
			# Обнуление запроса.
			Response = None
		
		return Response
		
	def fill_estate_calendar(
			self,
			item_id: int | str,
		    bookings: BookingsDates
		) -> requests.Response:
		"""
		Заполняет календарь занятости объекта недвижимости.
			item_id – идентификатор объявления;
			bookings – даты бронирования объекта недвижимости.
		"""

		# Выполнение запроса.
		Response = self.__Requests("POST", f"https://api.avito.ru/core/v1/accounts/{self.__Profile}/items/{item_id}/bookings", json = {"bookings": bookings.get()})
		
		return Response
		
	def set_base_params(
			self,
		    item_id: int | str,
		    discounts: Discounts | None = None,
		    extra_guest_fee: int | None = None,
		    instant: Instant | None = None,
		    minimal_duration: int = None,
		    night_price: int | None = None,
		    refund: int | None = None
			
		) -> requests.Response:
		"""
		Задаёт базовые параметры.
			item_id – идентификатор объявления;
			discounts – список скидок для забронировавших определённое количество ночей;
			extra_guest_fee – стоимость доплаты за каждого гостя сверх одного;
			instant – параметры мгновенного бронирования;
			minimal_duration – минимальное количество ночей для бронирования;
			refund – количество дней, за которое можно отказаться от брони.
			
		"""
		
		# Тело запроса.
		Body = dict()
		# Заполнение тела.
		if type(discounts) == Discounts: Body["discount"] = discounts.get()
		if extra_guest_fee != None: Body["extra_guest_fee"] = int(extra_guest_fee)
		if type(instant) == Instant: Body["instant"] = instant.get()
		if minimal_duration != None: Body["minimal_duration"] = int(minimal_duration)
		if night_price != None: Body["night_price"] = int(night_price)
		if refund != None: Body["refund"] = {"days": int(refund)}
		# Выполнение запроса.
		Response = self.__Requests("POST", f"https://api.avito.ru/realty/v1/items/{item_id}/base", json = Body)
		
		return Response
	
	def update_parameters(self, item_id: int | str, periods: RentPeriods) -> requests.Response:
		"""
		Обновляет параметры для переданных диапазонов дат.
			item_id – идентификатор объявления;
			periods – параметры аредны в диапазонах дат.
		"""
		
		# Тело запроса.
		Body = {
			"prices": periods.get()
		}
		# Выполнение запроса.
		Response = self.__Requests("POST", f"https://api.avito.ru/realty/v1/accounts/{self.__Profile}/items/{item_id}/prices", json = Body)
		
		return Response

class Messenger:
	"""Модуль API: мессенджер Авито."""
	
	def __init__(self, profile: int | str, session: any = None):
		"""
		Модуль API: мессенджер.
			profile – номер профиля Авито;
			session – указатель на готовую сессию библиотеки requests.
		"""
		# Номер профиля авито.
		self.__Profile = int(profile)
		# Модуль выполнения запросов.
		self.__Requests = session if session != None else requests.Session()

	def get_chats(self, limit: int = 100, offset: int = 0, item_ids: list = None):
		"""Получение списка чатов"""
		params = {
			'limit': limit,
			'offset': offset
		}
		
		# unread_only не поддерживается API (возвращает 400)
		if item_ids:
			params['item_ids'] = ','.join(map(str, item_ids))
		
		response = self.__Requests("GET", f"https://api.avito.ru/messenger/v2/accounts/{self.__Profile}/chats", params=params)
		
		if response.status_code == 200:
			data = response.json()
			return data.get('chats', [])
		
		return response

	def get_messages(self, chat_id: str, limit: int = 100, offset: int = 0):
		"""Получение сообщений из чата"""
		params = {
			'limit': limit,
			'offset': offset
		}
		
		response = self.__Requests("GET", f"https://api.avito.ru/messenger/v3/accounts/{self.__Profile}/chats/{chat_id}/messages", params=params)
		
		if response.status_code == 200:
			return response.json()
		
		return response

	def send_message(self, chat_id: str, text: str):
		"""Отправка текстового сообщения"""
		if len(text) > 1000:
			raise ValueError("Максимальная длина сообщения 1000 символов")
		
		body = {
			"message": {
				"text": text
			},
			"type": "text"
		}
		
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/messages", json=body)
		
		return response

	def mark_chat_read(self, chat_id: str):
		"""Пометить чат как прочитанный"""
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/read")
		
		return response

	def upload_image(self, file_path: str):
		"""Загрузка изображения для отправки"""
		with open(file_path, 'rb') as file:
			files = {'uploadfile[]': file}
			response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/uploadImages", files=files)
		
		return response

	def send_image_message(self, chat_id: str, image_id: str):
		"""Отправка сообщения с изображением"""
		body = {
			"image_id": image_id
		}
		
		response = self.__Requests("POST", f"https://api.avito.ru/messenger/v1/accounts/{self.__Profile}/chats/{chat_id}/messages/image", json=body)
		
		return response


class Job:
	"""Модуль API: работа/вакансии Авито."""
	
	def __init__(self, profile: int | str, session: any = None):
		"""
		Модуль API: вакансии и отклики.
			profile – номер профиля Авито;
			session – указатель на готовую сессию библиотеки requests.
		"""
		# Номер профиля авито.
		self.__Profile = int(profile)
		# Модуль выполнения запросов.
		self.__Requests = session if session != None else requests.Session()

	def get_application_ids(self, updated_at_from: str = None, cursor: str = None, limit: int = 100):
		"""Получение идентификаторов откликов"""
		# Если updated_at_from не передан, используем дату 30 дней назад
		if not updated_at_from:
			from datetime import datetime, timedelta
			updated_at_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
		
		params = {
			'limit': limit
		}
		
		# updatedAtFrom обязателен
		params['updatedAtFrom'] = updated_at_from
			
		if cursor:
			params['cursor'] = cursor
		
		response = self.__Requests("GET", "https://api.avito.ru/job/v1/applications/get_ids", params=params)
		
		return response

	def get_applications_by_ids(self, application_ids: list):
		"""Получение откликов по идентификаторам"""
		if len(application_ids) > 100:
			raise ValueError("Максимальное количество ID в запросе: 100")
		
		body = {
			"ids": application_ids
		}
		
		response = self.__Requests("POST", "https://api.avito.ru/job/v1/applications/get_by_ids", json=body)
		
		if response.status_code == 200:
			data = response.json()
			return data.get('applications', [])
		
		return response

	def set_application_viewed(self, application_ids: list):
		"""Пометить отклики как просмотренные"""
		if len(application_ids) > 100:
			raise ValueError("Максимальное количество ID в запросе: 100")
		
		body = {
			"ids": application_ids
		}
		
		response = self.__Requests("POST", "https://api.avito.ru/job/v1/applications/set_is_viewed", json=body)
		
		return response

	def get_vacancies(self, status: str = None, limit: int = 100):
		"""Получение списка вакансий (примерный метод, нужно уточнить в API)"""
		params = {
			'limit': limit
		}
		
		if status:
			params['status'] = status
		
		# Это примерный путь, нужно найти правильный в документации
		response = self.__Requests("GET", f"https://api.avito.ru/job/v1/accounts/{self.__Profile}/vacancies", params=params)
		
		return response