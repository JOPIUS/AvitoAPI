import requests
import json
from typing import Dict, List, Optional


class Job:
	"""Модуль API: Авито.Работа."""
	
	def __init__(self, profile: int | str, session=None):
		"""
		Модуль API: Авито.Работа.
			profile – номер профиля Авито;
			session – указатель на готовую сессию библиотеки requests.
		"""
		# Номер профиля Авито
		self.__Profile = int(profile)
		# Модуль выполнения запросов
		self.__Requests = session if session is not None else requests.Session()
	
	def get_vacancies(self, limit: int = 20, offset: int = 0) -> requests.Response:
		"""
		Получает список вакансий пользователя.
			limit – количество вакансий для запроса;
			offset – сдвиг для пагинации.
		"""
		params = {
			"limit": limit,
			"offset": offset
		}
		
		response = self.__Requests("GET", f"https://api.avito.ru/job/v1/accounts/{self.__Profile}/vacancies",
								   params=params)
		return response
	
	def get_vacancy(self, vacancy_id: int) -> requests.Response:
		"""
		Получает информацию о конкретной вакансии.
			vacancy_id – идентификатор вакансии.
		"""
		response = self.__Requests("GET", f"https://api.avito.ru/job/v1/vacancies/{vacancy_id}")
		return response
	
	def get_applications(self, vacancy_id: Optional[int] = None, limit: int = 20, 
						 offset: int = 0, status: Optional[str] = None) -> requests.Response:
		"""
		Получает список откликов на вакансии.
			vacancy_id – идентификатор конкретной вакансии (опционально);
			limit – количество откликов для запроса;
			offset – сдвиг для пагинации;
			status – статус отклика (new, viewed, accepted, rejected).
		"""
		params = {
			"limit": limit,
			"offset": offset
		}
		
		if vacancy_id:
			params["vacancy_id"] = vacancy_id
		if status:
			params["status"] = status
			
		response = self.__Requests("GET", f"https://api.avito.ru/job/v1/accounts/{self.__Profile}/applications",
								   params=params)
		return response
	
	def get_application(self, application_id: int) -> requests.Response:
		"""
		Получает подробную информацию об отклике.
			application_id – идентификатор отклика.
		"""
		response = self.__Requests("GET", f"https://api.avito.ru/job/v1/applications/{application_id}")
		return response
	
	def update_application_status(self, application_id: int, status: str, 
								  rejection_reason: Optional[str] = None) -> requests.Response:
		"""
		Обновляет статус отклика.
			application_id – идентификатор отклика;
			status – новый статус (viewed, accepted, rejected);
			rejection_reason – причина отказа (при статусе rejected).
		"""
		body = {"status": status}
		
		if status == "rejected" and rejection_reason:
			body["rejection_reason"] = rejection_reason
			
		response = self.__Requests("PUT", f"https://api.avito.ru/job/v1/applications/{application_id}",
								   json=body)
		return response
	
	def get_cv(self, cv_id: int) -> requests.Response:
		"""
		Получает информацию о резюме.
			cv_id – идентификатор резюме.
		"""
		response = self.__Requests("GET", f"https://api.avito.ru/job/v1/cv/{cv_id}")
		return response
	
	def search_cv(self, query: Optional[str] = None, region_id: Optional[int] = None,
				  salary_from: Optional[int] = None, salary_to: Optional[int] = None,
				  limit: int = 20, offset: int = 0) -> requests.Response:
		"""
		Поиск резюме по критериям.
			query – поисковый запрос;
			region_id – идентификатор региона;
			salary_from – минимальная зарплата;
			salary_to – максимальная зарплата;
			limit – количество результатов;
			offset – сдвиг для пагинации.
		"""
		params = {
			"limit": limit,
			"offset": offset
		}
		
		if query:
			params["query"] = query
		if region_id:
			params["region_id"] = region_id
		if salary_from:
			params["salary_from"] = salary_from
		if salary_to:
			params["salary_to"] = salary_to
			
		response = self.__Requests("GET", "https://api.avito.ru/job/v1/cv/search", params=params)
		return response
	
	def get_dictionaries(self, dictionary_id: Optional[str] = None) -> requests.Response:
		"""
		Получает справочники для работы с API (профессии, регионы и т.д.).
			dictionary_id – идентификатор конкретного справочника.
		"""
		if dictionary_id:
			response = self.__Requests("GET", f"https://api.avito.ru/job/v1/dictionaries/{dictionary_id}")
		else:
			response = self.__Requests("GET", "https://api.avito.ru/job/v1/dictionaries")
		return response
	
	def create_vacancy(self, title: str, description: str, salary_from: Optional[int] = None,
					   salary_to: Optional[int] = None, region_id: int = 1, 
					   category_id: int = 1, **kwargs) -> requests.Response:
		"""
		Создает новую вакансию.
			title – заголовок вакансии;
			description – описание вакансии;
			salary_from – минимальная зарплата;
			salary_to – максимальная зарплата;
			region_id – идентификатор региона;
			category_id – идентификатор категории;
			**kwargs – дополнительные параметры.
		"""
		body = {
			"title": title,
			"description": description,
			"region_id": region_id,
			"category_id": category_id
		}
		
		if salary_from:
			body["salary_from"] = salary_from
		if salary_to:
			body["salary_to"] = salary_to
			
		# Добавляем дополнительные параметры
		body.update(kwargs)
		
		response = self.__Requests("POST", f"https://api.avito.ru/job/v1/accounts/{self.__Profile}/vacancies",
								   json=body)
		return response
	
	def update_vacancy(self, vacancy_id: int, **kwargs) -> requests.Response:
		"""
		Обновляет существующую вакансию.
			vacancy_id – идентификатор вакансии;
			**kwargs – параметры для обновления.
		"""
		response = self.__Requests("PUT", f"https://api.avito.ru/job/v1/vacancies/{vacancy_id}",
								   json=kwargs)
		return response
	
	def deactivate_vacancy(self, vacancy_id: int) -> requests.Response:
		"""
		Деактивирует вакансию.
			vacancy_id – идентификатор вакансии.
		"""
		response = self.__Requests("DELETE", f"https://api.avito.ru/job/v1/vacancies/{vacancy_id}")
		return response