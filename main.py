import requests
import json
import csv
import time
import re
from typing import Dict, Optional, Any


class KinopoiskAPIParser:
    """Парсер через официальное API Kinopoisk.dev"""

    def __init__(self):
        self.base_url = "https://api.kinopoisk.dev/v1.4/movie"
        self.search_url = "https://api.kinopoisk.dev/v1.4/movie/search"
        self.api_key = "CP3ZGS9-NCMMF19-KTFSFDQ-9T0492W"  # Ваш API ключ

    def search_movie(self, movie_name: str) -> Optional[Dict[str, Any]]:
        """Поиск фильма через API"""
        try:
            print(f"🔍 Ищем фильм в базе Kinopoisk...")

            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            params = {
                'query': movie_name,
                'limit': 5,  # Показываем 5 результатов для выбора
                'selectFields': ['id', 'name', 'alternativeName', 'year', 'poster', 'rating']
            }

            response = requests.get(self.search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('docs') and len(data['docs']) > 0:
                return data['docs']

            return None

        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                print("❌ Ошибка: Неверный API ключ или закончились запросы")
            elif response.status_code == 429:
                print("❌ Ошибка: Превышен лимит запросов")
            else:
                print(f"❌ Ошибка API: {e}")
            return None
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
            return None

    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о фильме по ID"""
        try:
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.get(f"{self.base_url}/{movie_id}", headers=headers, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"❌ Ошибка при получении деталей фильма: {e}")
            return None

    def parse_movie_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Парсинг данных из API ответа"""
        # Обрабатываем рейтинг
        rating = api_data.get('rating', {})
        rating_kp = rating.get('kp', 'Нет рейтинга')
        if isinstance(rating_kp, (int, float)) and rating_kp > 0:
            rating_kp = str(round(rating_kp, 1))

        # Обрабатываем жанры
        genres = [genre.get('name', '') for genre in api_data.get('genres', []) if genre.get('name')]
        if not genres:
            genres = ['Неизвестно']

        # Обрабатываем страны
        countries = [country.get('name', '') for country in api_data.get('countries', []) if country.get('name')]
        if not countries:
            countries = ['Неизвестно']

        # Обрабатываем актеров
        actors = []
        for person in api_data.get('persons', []):
            if person.get('enProfession') == 'actor' and person.get('name'):
                actors.append(person['name'])
            if len(actors) >= 10:  # Ограничиваем 10 актерами
                break
        if not actors:
            actors = ['Информация недоступна']

        # Обрабатываем режиссеров
        directors = []
        for person in api_data.get('persons', []):
            if person.get('enProfession') == 'director' and person.get('name'):
                directors.append(person['name'])
        if not directors:
            directors = ['Информация недоступна']

        # Обрабатываем описание
        description = api_data.get('description', 'Описание недоступно')
        if not description or description == 'null':
            description = 'Описание недоступно'

        return {
            'name': api_data.get('name', 'Неизвестно'),
            'original_name': api_data.get('alternativeName', 'Неизвестно'),
            'year': api_data.get('year', 'Неизвестно'),
            'rating_kp': rating_kp,
            'genres': genres,
            'countries': countries,
            'description': description,
            'persons': {
                'actors': actors,
                'directors': directors
            },
            'movie_length': api_data.get('movieLength', 'Неизвестно'),
            'age_rating': api_data.get('ageRating', 'Неизвестно'),
            'poster_url': api_data.get('poster', {}).get('url', 'Нет постера')
        }

    def select_movie_from_results(self, search_results: list) -> Optional[Dict[str, Any]]:
        """Позволяет пользователю выбрать фильм из результатов поиска"""
        if not search_results:
            return None

        print(f"\n🎬 Найдено фильмов: {len(search_results)}")
        print("=" * 50)

        for i, movie in enumerate(search_results, 1):
            name = movie.get('name', 'Неизвестно')
            alt_name = movie.get('alternativeName', '')
            year = movie.get('year', 'Неизвестно')
            rating = movie.get('rating', {}).get('kp', 'Нет рейтинга')

            if alt_name and alt_name != name:
                print(f"{i}. {name} ({alt_name}) - {year} - ★ {rating}")
            else:
                print(f"{i}. {name} - {year} - ★ {rating}")

        print("\nВыберите номер фильма (или 0 для отмены):")
        try:
            choice = int(input("🎥 Ваш выбор: ").strip())
            if choice == 0:
                return None
            if 1 <= choice <= len(search_results):
                return search_results[choice - 1]
            else:
                print("❌ Неверный выбор")
                return None
        except ValueError:
            print("❌ Пожалуйста, введите число")
            return None

    def get_movie_data(self, movie_name: str) -> Optional[Dict[str, Any]]:
        """Основной метод получения данных о фильме"""
        search_results = self.search_movie(movie_name)

        if not search_results:
            return None

        # Если нашли только один результат, используем его
        if len(search_results) == 1:
            selected_movie = search_results[0]
            print(f"✅ Автоматически выбран: {selected_movie.get('name', 'Неизвестно')}")
        else:
            selected_movie = self.select_movie_from_results(search_results)
            if not selected_movie:
                return None

        # Получаем детальную информацию
        movie_id = selected_movie.get('id')
        if movie_id:
            print(f"📥 Загружаем детальную информацию...")
            detailed_data = self.get_movie_details(movie_id)
            if detailed_data:
                return self.parse_movie_data(detailed_data)

        # Если не удалось получить детали, используем базовые данные
        return self.parse_movie_data(selected_movie)

    def save_to_json(self, data: Dict[str, Any], filename: str):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON сохранен: {filename}")
        except Exception as e:
            print(f"❌ Ошибка сохранения JSON: {e}")

    def save_to_csv(self, data: Dict[str, Any], filename: str):
        try:
            flat_data = data.copy()

            # Обрабатываем вложенные структуры
            flat_data['genres'] = ', '.join(flat_data.get('genres', ['Неизвестно']))
            flat_data['countries'] = ', '.join(flat_data.get('countries', ['Неизвестно']))
            flat_data['actors'] = ', '.join(flat_data.get('persons', {}).get('actors', ['Неизвестно']))
            flat_data['directors'] = ', '.join(flat_data.get('persons', {}).get('directors', ['Неизвестно']))

            # Удаляем вложенные структуры
            flat_data.pop('persons', None)

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=flat_data.keys())
                writer.writeheader()
                writer.writerow(flat_data)
            print(f"💾 CSV сохранен: {filename}")
        except Exception as e:
            print(f"❌ Ошибка сохранения CSV: {e}")


def main():
    parser = KinopoiskAPIParser()

    print("🎬 Парсер КиноПоиска")
    print("=" * 50)

    while True:
        print("\nВведите название фильма (или 'выход' для завершения):")
        movie_name = input("🎥 Название фильма: ").strip()

        if movie_name.lower() in ['выход', 'exit', 'quit']:
            print("👋 До свидания!")
            break

        if not movie_name:
            print("❌ Пожалуйста, введите название фильма")
            continue

        print(f"\n🔄 Обрабатываю запрос: {movie_name}")
        data = parser.get_movie_data(movie_name)

        if data:
            print("\n" + "=" * 60)
            print("✅ ДАННЫЕ УСПЕШНО ПОЛУЧЕНЫ!")
            print("=" * 60)
            print(f"🎭 Название: {data.get('name', 'Неизвестно')}")
            print(f"🌍 Оригинал: {data.get('original_name', 'Неизвестно')}")
            print(f"📅 Год: {data.get('year', 'Неизвестно')}")
            print(f"⭐ Рейтинг КП: {data.get('rating_kp', 'Нет рейтинга')}")
            print(f"🎭 Жанры: {', '.join(data.get('genres', ['Неизвестно']))}")
            print(f"🌍 Страны: {', '.join(data.get('countries', ['Неизвестно']))}")
            print(f"🎥 Режиссер: {', '.join(data.get('persons', {}).get('directors', ['Неизвестно']))}")
            print(f"👨‍🎤 Актеры: {', '.join(data.get('persons', {}).get('actors', ['Неизвестно'])[:3])}")
            print(f"⏱️  Длительность: {data.get('movie_length', 'Неизвестно')} мин")
            print(f"🔞 Возрастной рейтинг: {data.get('age_rating', 'Неизвестно')}+")
            desc = data.get('description', 'Нет описания')
            print(f"📖 Описание: {desc[:100]}{'...' if len(desc) > 100 else ''}")

            # Сохраняем
            filename_base = re.sub(r'[^\w\s]', '', movie_name).replace(' ', '_')
            parser.save_to_json(data, f"{filename_base}.json")
            parser.save_to_csv(data, f"{filename_base}.csv")

            print(f"\n🎉 Готово! Проверьте файлы:")
            print(f"   📄 {filename_base}.json")
            print(f"   📊 {filename_base}.csv")
        else:
            print(f"❌ Не удалось получить данные о фильме '{movie_name}'")
            print("💡 Попробуйте уточнить название")


if __name__ == "__main__":
    main()