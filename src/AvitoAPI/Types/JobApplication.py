import datetime
from typing import Dict, Any, Optional, List


class JobApplication:
	"""Отклик на вакансию."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Отклик на вакансию.
			data – словарь данных отклика.
		"""
		self.__Data = data
	
	@property
	def id(self) -> int:
		"""ID отклика."""
		return self.__Data.get("id", 0)
	
	@property
	def vacancy_id(self) -> int:
		"""ID вакансии."""
		return self.__Data.get("vacancy_id", 0)
	
	@property
	def applicant_id(self) -> int:
		"""ID соискателя."""
		return self.__Data.get("applicant_id", 0)
	
	@property
	def status(self) -> str:
		"""Статус отклика (new, viewed, accepted, rejected)."""
		return self.__Data.get("status", "")
	
	@property
	def created_at(self) -> datetime.datetime:
		"""Время создания отклика."""
		timestamp = self.__Data.get("created_at")
		if timestamp:
			return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
		return datetime.datetime.now()
	
	@property
	def updated_at(self) -> datetime.datetime:
		"""Время обновления отклика."""
		timestamp = self.__Data.get("updated_at")
		if timestamp:
			return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
		return datetime.datetime.now()
	
	@property
	def applicant_name(self) -> str:
		"""Имя соискателя."""
		return self.__Data.get("applicant_name", "")
	
	@property
	def cover_letter(self) -> Optional[str]:
		"""Сопроводительное письмо."""
		return self.__Data.get("cover_letter")
	
	@property
	def cv_id(self) -> Optional[int]:
		"""ID резюме."""
		return self.__Data.get("cv_id")
	
	@property
	def rejection_reason(self) -> Optional[str]:
		"""Причина отказа."""
		return self.__Data.get("rejection_reason")


class Vacancy:
	"""Вакансия."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Вакансия.
			data – словарь данных вакансии.
		"""
		self.__Data = data
	
	@property
	def id(self) -> int:
		"""ID вакансии."""
		return self.__Data.get("id", 0)
	
	@property
	def title(self) -> str:
		"""Заголовок вакансии."""
		return self.__Data.get("title", "")
	
	@property
	def description(self) -> str:
		"""Описание вакансии."""
		return self.__Data.get("description", "")
	
	@property
	def salary_from(self) -> Optional[int]:
		"""Минимальная зарплата."""
		return self.__Data.get("salary_from")
	
	@property
	def salary_to(self) -> Optional[int]:
		"""Максимальная зарплата."""
		return self.__Data.get("salary_to")
	
	@property
	def salary_currency(self) -> Optional[str]:
		"""Валюта зарплаты."""
		return self.__Data.get("salary_currency")
	
	@property
	def region_id(self) -> int:
		"""ID региона."""
		return self.__Data.get("region_id", 0)
	
	@property
	def region_name(self) -> str:
		"""Название региона."""
		return self.__Data.get("region_name", "")
	
	@property
	def category_id(self) -> int:
		"""ID категории."""
		return self.__Data.get("category_id", 0)
	
	@property
	def category_name(self) -> str:
		"""Название категории."""
		return self.__Data.get("category_name", "")
	
	@property
	def status(self) -> str:
		"""Статус вакансии."""
		return self.__Data.get("status", "")
	
	@property
	def created_at(self) -> datetime.datetime:
		"""Время создания вакансии."""
		timestamp = self.__Data.get("created_at")
		if timestamp:
			return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
		return datetime.datetime.now()
	
	@property
	def updated_at(self) -> datetime.datetime:
		"""Время обновления вакансии."""
		timestamp = self.__Data.get("updated_at")
		if timestamp:
			return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
		return datetime.datetime.now()
	
	@property
	def url(self) -> str:
		"""URL вакансии."""
		return self.__Data.get("url", "")
	
	@property
	def applications_count(self) -> int:
		"""Количество откликов."""
		return self.__Data.get("applications_count", 0)


class CV:
	"""Резюме."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Резюме.
			data – словарь данных резюме.
		"""
		self.__Data = data
	
	@property
	def id(self) -> int:
		"""ID резюме."""
		return self.__Data.get("id", 0)
	
	@property
	def title(self) -> str:
		"""Заголовок резюме."""
		return self.__Data.get("title", "")
	
	@property
	def first_name(self) -> str:
		"""Имя."""
		return self.__Data.get("first_name", "")
	
	@property
	def last_name(self) -> str:
		"""Фамилия."""
		return self.__Data.get("last_name", "")
	
	@property
	def age(self) -> Optional[int]:
		"""Возраст."""
		return self.__Data.get("age")
	
	@property
	def gender(self) -> Optional[str]:
		"""Пол."""
		return self.__Data.get("gender")
	
	@property
	def salary_from(self) -> Optional[int]:
		"""Желаемая зарплата от."""
		return self.__Data.get("salary_from")
	
	@property
	def salary_to(self) -> Optional[int]:
		"""Желаемая зарплата до."""
		return self.__Data.get("salary_to")
	
	@property
	def salary_currency(self) -> Optional[str]:
		"""Валюта зарплаты."""
		return self.__Data.get("salary_currency")
	
	@property
	def region_id(self) -> int:
		"""ID региона."""
		return self.__Data.get("region_id", 0)
	
	@property
	def region_name(self) -> str:
		"""Название региона."""
		return self.__Data.get("region_name", "")
	
	@property
	def experience_years(self) -> Optional[int]:
		"""Опыт работы в годах."""
		return self.__Data.get("experience_years")
	
	@property
	def education_level(self) -> Optional[str]:
		"""Уровень образования."""
		return self.__Data.get("education_level")
	
	@property
	def skills(self) -> List[str]:
		"""Навыки."""
		return self.__Data.get("skills", [])
	
	@property
	def about(self) -> str:
		"""О себе."""
		return self.__Data.get("about", "")
	
	@property
	def created_at(self) -> datetime.datetime:
		"""Время создания резюме."""
		timestamp = self.__Data.get("created_at")
		if timestamp:
			return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
		return datetime.datetime.now()
	
	@property
	def updated_at(self) -> datetime.datetime:
		"""Время обновления резюме."""
		timestamp = self.__Data.get("updated_at")
		if timestamp:
			return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
		return datetime.datetime.now()


class JobApplicationsList:
	"""Список откликов."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Список откликов.
			data – словарь данных списка откликов.
		"""
		self.__Data = data
	
	@property
	def applications(self) -> List[JobApplication]:
		"""Список откликов."""
		apps_data = self.__Data.get("applications", [])
		return [JobApplication(app_data) for app_data in apps_data]
	
	@property
	def total_count(self) -> int:
		"""Общее количество откликов."""
		return self.__Data.get("total_count", 0)


class VacanciesList:
	"""Список вакансий."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Список вакансий.
			data – словарь данных списка вакансий.
		"""
		self.__Data = data
	
	@property
	def vacancies(self) -> List[Vacancy]:
		"""Список вакансий."""
		vacancies_data = self.__Data.get("vacancies", [])
		return [Vacancy(vacancy_data) for vacancy_data in vacancies_data]
	
	@property
	def total_count(self) -> int:
		"""Общее количество вакансий."""
		return self.__Data.get("total_count", 0)


class CVList:
	"""Список резюме."""
	
	def __init__(self, data: Dict[str, Any]):
		"""
		Список резюме.
			data – словарь данных списка резюме.
		"""
		self.__Data = data
	
	@property
	def cvs(self) -> List[CV]:
		"""Список резюме."""
		cvs_data = self.__Data.get("cvs", [])
		return [CV(cv_data) for cv_data in cvs_data]
	
	@property
	def total_count(self) -> int:
		"""Общее количество резюме."""
		return self.__Data.get("total_count", 0)