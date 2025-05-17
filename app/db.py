import aiosqlite

DB_NAME = 'vst_database.db'

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                download_link TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS plugin_types (
                plugin_id INTEGER,
                type_id INTEGER,
                FOREIGN KEY(plugin_id) REFERENCES plugins(id),
                FOREIGN KEY(type_id) REFERENCES types(id),
                PRIMARY KEY (plugin_id, type_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS plugin_tags (
                plugin_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY(plugin_id) REFERENCES plugins(id),
                FOREIGN KEY(tag_id) REFERENCES tags(id),
                PRIMARY KEY (plugin_id, tag_id)
            )
        ''')
        await db.commit()

async def get_all_tags():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, name FROM tags") as cursor:
            return await cursor.fetchall()

async def get_all_types():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, name FROM types") as cursor:
            return await cursor.fetchall()

async def get_all_plugins(limit=5, offset=0):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT p.id, p.title, p.description, p.download_link, t.name 
            FROM plugins p
            JOIN plugin_types pt ON p.id = pt.plugin_id
            JOIN types t ON pt.type_id = t.id
            LIMIT ? OFFSET ?
        """, (limit, offset)) as cursor:
            plugins_data = await cursor.fetchall()

        result = []
        for plugin in plugins_data:
            plugin_id = plugin[0]
            # Получаем теги для каждого плагина
            tags_cursor = await db.execute("""
                SELECT t.name FROM tags t
                JOIN plugin_tags pt ON t.id = pt.tag_id
                WHERE pt.plugin_id = ?
            """, (plugin_id,))
            tags = [row[0] for row in await tags_cursor.fetchall()]
            result.append({
                "id": plugin[0],
                "title": plugin[1],
                "description": plugin[2],
                "download_link": plugin[3],
                "type": plugin[4],
                "tags": tags
            })

        return result

async def add_type(name):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("INSERT OR IGNORE INTO types (name) VALUES (?)", (name,))
        await db.commit()
        return cursor.lastrowid

async def add_tag(name):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        await db.commit()
        return cursor.lastrowid

async def add_plugin(title, description, link, type_id, tag_ids):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO plugins (title, description, download_link) VALUES (?, ?, ?)",
            (title, description, link)
        )
        plugin_id = cursor.lastrowid
        await db.execute(
            "INSERT INTO plugin_types (plugin_id, type_id) VALUES (?, ?)",
            (plugin_id, type_id)
        )
        for tag_id in tag_ids:
            await db.execute(
                "INSERT INTO plugin_tags (plugin_id, tag_id) VALUES (?, ?)",
                (plugin_id, tag_id)
            )
        await db.commit()
        return plugin_id

async def get_plugins_by_tags_and_type(plugin_type, tags):
    async with aiosqlite.connect(DB_NAME) as db:
        # Подготавливаем условия для WHERE
        conditions = []
        args = []

        if plugin_type:
            conditions.append("t.name = ?")
            args.append(plugin_type)

        if tags:
            conditions.append("ta.name IN ({})".format(','.join(['?'] * len(tags))))
            args.extend(tags)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Основной запрос
        query = f"""
            SELECT DISTINCT p.title, p.description, p.download_link
            FROM plugins p
            JOIN plugin_types pt ON p.id = pt.plugin_id
            JOIN types t ON pt.type_id = t.id
        """

        if tags:
            query += """
                JOIN plugin_tags pta ON p.id = pta.plugin_id
                JOIN tags ta ON pta.tag_id = ta.id
            """

        query += f"""
            WHERE {where_clause}
        """

        if tags:
            query += """
                GROUP BY p.id
                HAVING COUNT(DISTINCT ta.name) = ?
            """
            args.append(len(tags))

        async with db.execute(query, args) as cursor:
            return await cursor.fetchall()

async def get_total_plugin_count():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM plugins") as cursor:
            row = await cursor.fetchone()
            return row[0]