import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройки подключения - ВАШ ПАРОЛЬ
DB_PASSWORD = "1234"  # ИЗМЕНИТЕ НА СВОЙ ПАРОЛЬ


class Database:
    def __init__(self):
        self.conn = None

    def get_connection(self):
        """Установка соединения с БД"""
        try:
            if not self.conn or self.conn.closed:
                logger.info("Подключение к базе данных...")
                self.conn = psycopg2.connect(
                    dbname='Cinema',
                    user='postgres',
                    password=DB_PASSWORD,
                    host='127.0.0.1',
                    port='5432'
                )
                logger.info("✅ Подключение успешно установлено")
            return self.conn
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Универсальный метод для выполнения запросов"""
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                logger.debug(f"Выполнение запроса: {query[:100]}...")
                cur.execute(query, params or ())

                if fetch_one:
                    result = cur.fetchone()
                    logger.debug(f"Получена 1 запись")
                    return result
                elif fetch_all:
                    result = cur.fetchall()
                    logger.debug(f"Получено {len(result)} записей")
                    return result
                else:
                    conn.commit()
                    logger.debug(f"Запрос выполнен, затронуто строк: {cur.rowcount}")
                    return cur.rowcount

        except Exception as e:
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            logger.error(f"Запрос: {query}")
            logger.error(f"Параметры: {params}")
            return None if fetch_one or fetch_all else 0

    # ========== ФИЛЬМЫ ==========
    def get_movies(self):
        """Получение всех фильмов"""
        query = "SELECT id, title, duration, genre, age_rating FROM movies ORDER BY id"
        result = self.execute_query(query, fetch_all=True)
        logger.info(f"get_movies: {len(result) if result else 0} фильмов")
        return result or []

    def add_movie(self, title, duration, genre, age_rating):
        """Добавление нового фильма"""
        query = """
            INSERT INTO movies (title, duration, genre, age_rating) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id
        """
        result = self.execute_query(query, (title, duration, genre, age_rating), fetch_one=True)
        return result['id'] if result else None

    def update_movie(self, movie_id, title, duration, genre, age_rating):
        """Обновление фильма"""
        query = """
            UPDATE movies 
            SET title = %s, duration = %s, genre = %s, age_rating = %s
            WHERE id = %s
        """
        return self.execute_query(query, (title, duration, genre, age_rating, movie_id)) > 0

    def delete_movie(self, movie_id):
        """Удаление фильма"""
        query = "DELETE FROM movies WHERE id = %s"
        return self.execute_query(query, (movie_id,)) > 0

    # ========== СЕАНСЫ ==========
    def get_sessions(self):
        """Получение всех сеансов"""
        try:
            query = """
                SELECT 
                    s.id,
                    to_char(s.session_date, 'DD.MM.YYYY') as date,
                    s.session_date as date_raw,
                    to_char(s.start_time, 'HH24:MI') as start_time,
                    to_char(s.end_time, 'HH24:MI') as end_time,
                    m.title as movie,
                    m.duration,
                    m.genre,
                    m.age_rating,
                    h.hall_number as hall
                FROM sessions s
                JOIN movies m ON s.movie_id = m.id
                JOIN halls h ON s.hall_id = h.id
                ORDER BY s.session_date, s.start_time
            """
            result = self.execute_query(query, fetch_all=True)
            logger.info(f"get_sessions: найдено {len(result) if result else 0} сеансов")
            if result:
                for session in result:
                    logger.info(
                        f"  - {session['date']} {session['start_time']}: {session['movie']} (Зал {session['hall']})")
            return result or []
        except Exception as e:
            logger.error(f"Ошибка в get_sessions: {e}")
            return []

    def get_session_by_id(self, session_id):
        """Получение информации о конкретном сеансе"""
        query = """
            SELECT 
                s.id,
                to_char(s.session_date, 'DD.MM.YYYY') as date,
                s.session_date as date_raw,
                to_char(s.start_time, 'HH24:MI') as start_time,
                to_char(s.end_time, 'HH24:MI') as end_time,
                m.id as movie_id,
                m.title as movie,
                m.duration,
                m.genre,
                m.age_rating,
                h.id as hall_id,
                h.hall_number as hall,
                h.rows_count,
                h.seats_per_row,
                t.id as tariff_id,
                t.tariff_name,
                t.price
            FROM sessions s
            JOIN movies m ON s.movie_id = m.id
            JOIN halls h ON s.hall_id = h.id
            JOIN tariffs t ON s.tariff_id = t.id
            WHERE s.id = %s
        """
        return self.execute_query(query, (session_id,), fetch_one=True)

    def add_session(self, movie_id, hall_id, session_date, start_time, end_time, tariff_id):
        """Добавление нового сеанса"""
        query = """
            INSERT INTO sessions (movie_id, hall_id, session_date, start_time, end_time, tariff_id) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            RETURNING id
        """
        params = (movie_id, hall_id, session_date, start_time, end_time, tariff_id)
        result = self.execute_query(query, params, fetch_one=True)
        return result['id'] if result else None

    def update_session(self, session_id, movie_id, hall_id, session_date, start_time, end_time, tariff_id):
        """Обновление сеанса"""
        query = """
            UPDATE sessions 
            SET movie_id = %s, hall_id = %s, session_date = %s, 
                start_time = %s, end_time = %s, tariff_id = %s
            WHERE id = %s
        """
        params = (movie_id, hall_id, session_date, start_time, end_time, tariff_id, session_id)
        return self.execute_query(query, params) > 0

    def delete_session(self, session_id):
        """Удаление сеанса"""
        query = "DELETE FROM sessions WHERE id = %s"
        return self.execute_query(query, (session_id,)) > 0

    # ========== ТАРИФЫ ==========
    def get_tariffs(self):
        """Получение всех тарифов"""
        query = "SELECT id, tariff_name as name, price FROM tariffs ORDER BY id"
        result = self.execute_query(query, fetch_all=True)
        logger.info(f"get_tariffs: {len(result) if result else 0} тарифов")
        return result or []

    def add_tariff(self, name, price):
        """Добавление нового тарифа"""
        query = "INSERT INTO tariffs (tariff_name, price) VALUES (%s, %s) RETURNING id"
        result = self.execute_query(query, (name, price), fetch_one=True)
        return result['id'] if result else None

    def update_tariff(self, tariff_id, name, price):
        """Обновление тарифа"""
        query = "UPDATE tariffs SET tariff_name = %s, price = %s WHERE id = %s"
        return self.execute_query(query, (name, price, tariff_id)) > 0

    def delete_tariff(self, tariff_id):
        """Удаление тарифа"""
        query = "DELETE FROM tariffs WHERE id = %s"
        return self.execute_query(query, (tariff_id,)) > 0

    # ========== МЕСТА ==========
    def get_seats(self, hall_id):
        """Получение всех мест в зале"""
        query = """
            SELECT id, row_number as row, seat_number as seat, seat_type as type 
            FROM seats 
            WHERE hall_id = %s 
            ORDER BY row_number, seat_number
        """
        result = self.execute_query(query, (hall_id,), fetch_all=True)
        logger.info(f"get_seats: {len(result) if result else 0} мест")
        return result or []

    # ========== БИЛЕТЫ ==========
    def get_sold_tickets(self, session_id):
        """Получение проданных билетов на сеанс"""
        query = """
            SELECT 
                t.id, 
                t.customer_name, 
                t.price, 
                t.payment_method,
                s.row_number, 
                s.seat_number, 
                s.seat_type,
                s.id as seat_id
            FROM tickets t
            JOIN seats s ON t.seat_id = s.id
            WHERE t.session_id = %s AND t.is_returned = false
        """
        result = self.execute_query(query, (session_id,), fetch_all=True)
        logger.info(f"get_sold_tickets: {len(result) if result else 0} билетов")
        return result or []

    def buy_ticket(self, session_id, seat_id, customer_name, price, payment_method):
        """Покупка билета"""
        query = """
            INSERT INTO tickets (session_id, seat_id, customer_name, price, payment_method, is_returned) 
            VALUES (%s, %s, %s, %s, %s, false) 
            RETURNING id
        """
        params = (session_id, seat_id, customer_name, price, payment_method)
        result = self.execute_query(query, params, fetch_one=True)
        return result['id'] if result else None

    def return_ticket(self, ticket_id):
        """Возврат билета"""
        query = "UPDATE tickets SET is_returned = true WHERE id = %s"
        return self.execute_query(query, (ticket_id,)) > 0

    # ========== ПОЛЬЗОВАТЕЛИ ==========
    def get_users(self):
        """Получение всех пользователей"""
        try:
            query = "SELECT id, username, role, full_name FROM users ORDER BY id"
            result = self.execute_query(query, fetch_all=True)
            logger.info(f"get_users: найдено {len(result) if result else 0} пользователей")
            if result:
                for user in result:
                    logger.info(f"  - {user['username']} ({user['role']})")
            return result or []
        except Exception as e:
            logger.error(f"Ошибка в get_users: {e}")
            return []

    def authenticate(self, username, password):
        """Авторизация пользователя"""
        query = """
            SELECT id, username, role, full_name 
            FROM users 
            WHERE username = %s AND password = %s
        """
        result = self.execute_query(query, (username, password), fetch_one=True)
        logger.info(f"authenticate: {username} - {'успешно' if result else 'неудачно'}")
        return result

    def add_user(self, username, password, role, full_name):
        """Добавление нового пользователя"""
        query = """
            INSERT INTO users (username, password, role, full_name) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id
        """
        params = (username, password, role, full_name)
        result = self.execute_query(query, params, fetch_one=True)
        return result['id'] if result else None

    def update_user(self, user_id, username, password, role, full_name):
        """Обновление пользователя"""
        if password:
            query = "UPDATE users SET username = %s, password = %s, role = %s, full_name = %s WHERE id = %s"
            params = (username, password, role, full_name, user_id)
        else:
            query = "UPDATE users SET username = %s, role = %s, full_name = %s WHERE id = %s"
            params = (username, role, full_name, user_id)
        return self.execute_query(query, params) > 0

    def delete_user(self, user_id):
        """Удаление пользователя"""
        query = "DELETE FROM users WHERE id = %s"
        return self.execute_query(query, (user_id,)) > 0


# Создаем глобальный экземпляр
db = Database()

# Проверяем подключение при запуске
if __name__ == "__main__":
    try:
        conn = db.get_connection()
        logger.info("✅ База данных готова к работе")

        # Проверяем все таблицы
        tables = {
            'movies': db.get_movies(),
            'sessions': db.get_sessions(),
            'tariffs': db.get_tariffs(),
            'users': db.get_users()
        }

        for name, data in tables.items():
            logger.info(f"  {name}: {len(data)} записей")
            if data:
                logger.info(f"    Пример: {data[0]}")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")