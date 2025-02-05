import psycopg2

def connect_db():
    conn = psycopg2.connect(
        dbname="bot2",
        user="postgres",
        password="725090",
        host="localhost",
        port="5432"
    )
    return conn

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS default_words (
            english_word VARCHAR(255) PRIMARY KEY,
            russian_word VARCHAR(255) NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_words (
            user_id BIGINT REFERENCES users(user_id),
            english_word VARCHAR(255),
            russian_word VARCHAR(255),
            PRIMARY KEY (user_id, english_word)
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def add_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (user_id) VALUES (%s) "
        "ON CONFLICT (user_id) DO NOTHING",
        (user_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()

def user_exists(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM users WHERE user_id = %s", (user_id,)
    )
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

def add_word_to_db(user_id, english_word, russian_word):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_words (user_id, english_word, russian_word) "
        "VALUES (%s, %s, %s) "
        "ON CONFLICT (user_id, english_word) DO NOTHING",
        (user_id, english_word, russian_word),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_words_from_db(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    query = """
    SELECT english_word, russian_word FROM user_words WHERE user_id = %s
    UNION
    SELECT english_word, russian_word FROM default_words
    """

    cursor.execute(query, (user_id,))
    words = cursor.fetchall()

    cursor.close()
    conn.close()

    return words


def insert_default_words():
    conn = connect_db()
    cursor = conn.cursor()
    default_words = [
        ("hello", "привет"),
        ("world", "мир"),
        ("cat", "кот"),
        ("dog", "собака"),
        ("book", "книга"),
        ("computer", "компьютер"),
        ("sky", "небо"),
        ("sun", "солнце"),
        ("moon", "луна"),
        ("tree", "дерево")
    ]

    for eng, rus in default_words:
        cursor.execute("SELECT 1 FROM default_words WHERE english_word = %s", (eng,))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO default_words (english_word, russian_word) VALUES (%s, %s)",
                (eng, rus)
            )

    conn.commit()
    cursor.close()
    conn.close()
    return default_words

def remove_word_from_db(user_id, english_word):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM user_words WHERE user_id = %s AND english_word = %s",
        (user_id, english_word)
    )
    conn.commit()
    cursor.close()
    conn.close()

create_tables()
insert_default_words()