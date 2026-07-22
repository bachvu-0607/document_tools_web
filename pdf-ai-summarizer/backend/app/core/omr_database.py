import aiosqlite

from app.core.config import settings


async def init_omr_db() -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS omr_sheets (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                label TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS omr_templates (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                reference_sheet_id TEXT NOT NULL,
                sbd_zone TEXT NOT NULL,
                sbd_digits INTEGER NOT NULL,
                made_zone TEXT NOT NULL,
                made_digits INTEGER NOT NULL,
                answer_blocks TEXT NOT NULL,
                num_choices INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS omr_detections (
                sheet_id TEXT PRIMARY KEY,
                user_id TEXT,
                template_id TEXT NOT NULL,
                sbd TEXT NOT NULL,
                sbd_ambiguous_digits TEXT NOT NULL,
                made TEXT NOT NULL,
                made_ambiguous_digits TEXT NOT NULL,
                answers TEXT NOT NULL,
                ambiguous_questions TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                aligned INTEGER NOT NULL DEFAULT 1
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS omr_answer_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                template_id TEXT NOT NULL,
                source_sheet_id TEXT NOT NULL,
                sbd TEXT NOT NULL,
                made TEXT NOT NULL,
                answers TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS omr_graded_results (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                class_name TEXT NOT NULL,
                sheet_id TEXT NOT NULL,
                sheet_label TEXT NOT NULL,
                answer_key_id TEXT NOT NULL,
                answer_key_name TEXT NOT NULL,
                sbd TEXT NOT NULL,
                made TEXT NOT NULL,
                correct_count INTEGER NOT NULL,
                wrong_count INTEGER NOT NULL,
                blank_count INTEGER NOT NULL,
                ambiguous_count INTEGER NOT NULL,
                score_10 REAL NOT NULL,
                aligned INTEGER NOT NULL,
                saved_at TEXT NOT NULL,
                UNIQUE(sheet_id, answer_key_id)
            );
        """)
        # Cac bang co the da ton tai tu truoc khi co tinh nang dang nhap - them
        # cot user_id bang ALTER TABLE (khong xoa du lieu cu) thay vi drop/tao
        # lai. Du lieu cu (chua co user_id) se mang gia tri NULL - vo hinh voi
        # moi tai khoan (khong ai truy van WHERE user_id = NULL khop ca), coi
        # nhu "khong co chu", an toan hon la gan bua cho 1 nguoi nao do.
        for table, column in [
            ("omr_sheets", "user_id"),
            ("omr_templates", "user_id"),
            ("omr_detections", "user_id"),
            ("omr_answer_keys", "user_id"),
            ("omr_graded_results", "user_id"),
        ]:
            try:
                await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT;")
            except aiosqlite.OperationalError:
                pass  # cot da ton tai roi, bo qua
        try:
            await conn.execute("ALTER TABLE omr_detections ADD COLUMN aligned INTEGER NOT NULL DEFAULT 1;")
        except aiosqlite.OperationalError:
            pass  # cot da ton tai roi, bo qua
        await conn.commit()


async def save_sheet_record(
    sheet_id: str,
    user_id: str,
    label: str,
    original_filename: str,
    stored_filename: str,
    content_type: str,
    uploaded_at: str,
) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute(
            """
            INSERT INTO omr_sheets
                (id, user_id, label, original_filename, stored_filename, content_type, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (sheet_id, user_id, label, original_filename, stored_filename, content_type, uploaded_at),
        )
        await conn.commit()


async def list_sheets(user_id: str) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT id, label, original_filename, stored_filename, content_type, uploaded_at
            FROM omr_sheets
            WHERE user_id = ?
            ORDER BY uploaded_at DESC;
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_sheet(sheet_id: str, user_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT id, label, original_filename, stored_filename, content_type, uploaded_at
            FROM omr_sheets
            WHERE id = ? AND user_id = ?;
            """,
            (sheet_id, user_id),
        )
        return await cursor.fetchone()


async def get_sheet_viewable(sheet_id: str, user_id: str) -> aiosqlite.Row | None:
    # Ban "long tay" hon get_sheet - dung cho 2 endpoint XEM anh (file/aligned),
    # khong dung cho xoa/liet ke. Anh phieu van rieng tu MAC DINH, nhung neu
    # anh do dang la anh mau cua it nhat 1 template (template dung CHUNG cho
    # ca nhom) thi ai cung xem duoc anh do - vi day la anh phieu trang, khong
    # co thong tin hoc sinh nao, va can hien thi thumbnail o man hinh Mau phieu
    # cho moi nguoi trong nhom.
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT id, label, original_filename, stored_filename, content_type, uploaded_at
            FROM omr_sheets
            WHERE id = ? AND (
                user_id = ?
                OR id IN (SELECT reference_sheet_id FROM omr_templates)
            );
            """,
            (sheet_id, user_id),
        )
        return await cursor.fetchone()


async def find_sheet_usages(sheet_id: str) -> tuple[list[str], list[str]]:
    # Truoc khi xoa 1 phieu, can biet no co dang lam anh mau cho template nao
    # hoac lam nguon cho dap an nao khong - xoa mat anh goc trong khi template/
    # dap an van con tham chieu se lam hong tinh nang cham bai ve sau. Khong can
    # loc them user_id o day - quyen so huu phieu da duoc kiem tra truoc do boi
    # ham goi, va template/dap an tro toi phieu nay chi co the do CUNG 1 nguoi
    # tao (khong ai tao duoc template tro toi phieu cua nguoi khac).
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        template_cursor = await conn.execute(
            "SELECT name FROM omr_templates WHERE reference_sheet_id = ?;",
            (sheet_id,),
        )
        template_names = [row["name"] for row in await template_cursor.fetchall()]

        answer_key_cursor = await conn.execute(
            "SELECT name FROM omr_answer_keys WHERE source_sheet_id = ?;",
            (sheet_id,),
        )
        answer_key_names = [row["name"] for row in await answer_key_cursor.fetchall()]

        return template_names, answer_key_names


async def delete_sheet_record(sheet_id: str) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("DELETE FROM omr_detections WHERE sheet_id = ?;", (sheet_id,))
        await conn.execute("DELETE FROM omr_sheets WHERE id = ?;", (sheet_id,))
        await conn.commit()


TEMPLATE_COLUMNS = """
    id, user_id, name, reference_sheet_id, sbd_zone, sbd_digits, made_zone, made_digits,
    answer_blocks, num_choices, created_at
"""


async def save_template_record(
    template_id: str,
    user_id: str,
    name: str,
    reference_sheet_id: str,
    sbd_zone: str,
    sbd_digits: int,
    made_zone: str,
    made_digits: int,
    answer_blocks: str,
    num_choices: int,
    created_at: str,
) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute(
            """
            INSERT INTO omr_templates
                (id, user_id, name, reference_sheet_id, sbd_zone, sbd_digits, made_zone,
                 made_digits, answer_blocks, num_choices, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                template_id, user_id, name, reference_sheet_id, sbd_zone, sbd_digits,
                made_zone, made_digits, answer_blocks, num_choices, created_at,
            ),
        )
        await conn.commit()


async def list_templates() -> list[aiosqlite.Row]:
    # Mau phieu DUNG CHUNG cho ca nhom (khong loc theo user_id) - toa do khoanh
    # vung khong co thong tin nhay cam, ai cung xem/dung duoc de cham bai.
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {TEMPLATE_COLUMNS} FROM omr_templates ORDER BY created_at DESC;",
        )
        return await cursor.fetchall()


async def get_template(template_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {TEMPLATE_COLUMNS} FROM omr_templates WHERE id = ?;",
            (template_id,),
        )
        return await cursor.fetchone()


async def find_template_usages(template_id: str) -> list[str]:
    # Dap an duoc tao tu 1 mau va khi cham bai luon can doc lai mau do (de biet
    # vi tri o tron) - xoa mat mau ma con dap an tham chieu se lam gay tinh
    # nang cham bai voi dap an do. Khong can loc user_id (ly do giong
    # find_sheet_usages o tren).
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT name FROM omr_answer_keys WHERE template_id = ?;",
            (template_id,),
        )
        return [row["name"] for row in await cursor.fetchall()]


async def delete_template_record(template_id: str) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("DELETE FROM omr_templates WHERE id = ?;", (template_id,))
        await conn.commit()


DETECTION_COLUMNS = """
    sheet_id, template_id, sbd, sbd_ambiguous_digits, made, made_ambiguous_digits,
    answers, ambiguous_questions, detected_at, aligned
"""


async def save_detection_record(
    sheet_id: str,
    user_id: str,
    template_id: str,
    sbd: str,
    sbd_ambiguous_digits: str,
    made: str,
    made_ambiguous_digits: str,
    answers: str,
    ambiguous_questions: str,
    detected_at: str,
    aligned: bool = True,
) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute(
            """
            INSERT INTO omr_detections
                (sheet_id, user_id, template_id, sbd, sbd_ambiguous_digits, made,
                 made_ambiguous_digits, answers, ambiguous_questions, detected_at, aligned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sheet_id) DO UPDATE SET
                user_id = excluded.user_id,
                template_id = excluded.template_id,
                sbd = excluded.sbd,
                sbd_ambiguous_digits = excluded.sbd_ambiguous_digits,
                made = excluded.made,
                made_ambiguous_digits = excluded.made_ambiguous_digits,
                answers = excluded.answers,
                ambiguous_questions = excluded.ambiguous_questions,
                detected_at = excluded.detected_at,
                aligned = excluded.aligned;
            """,
            (
                sheet_id, user_id, template_id, sbd, sbd_ambiguous_digits, made,
                made_ambiguous_digits, answers, ambiguous_questions, detected_at,
                int(aligned),
            ),
        )
        await conn.commit()


async def get_detection(sheet_id: str, user_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {DETECTION_COLUMNS} FROM omr_detections WHERE sheet_id = ? AND user_id = ?;",
            (sheet_id, user_id),
        )
        return await cursor.fetchone()


ANSWER_KEY_COLUMNS = "id, name, template_id, source_sheet_id, sbd, made, answers, created_at"


async def save_answer_key_record(
    answer_key_id: str,
    user_id: str,
    name: str,
    template_id: str,
    source_sheet_id: str,
    sbd: str,
    made: str,
    answers: str,
    created_at: str,
) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute(
            """
            INSERT INTO omr_answer_keys
                (id, user_id, name, template_id, source_sheet_id, sbd, made, answers, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (answer_key_id, user_id, name, template_id, source_sheet_id, sbd, made, answers, created_at),
        )
        await conn.commit()


async def list_answer_keys(user_id: str) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {ANSWER_KEY_COLUMNS} FROM omr_answer_keys WHERE user_id = ? ORDER BY created_at DESC;",
            (user_id,),
        )
        return await cursor.fetchall()


async def get_answer_key(answer_key_id: str, user_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {ANSWER_KEY_COLUMNS} FROM omr_answer_keys WHERE id = ? AND user_id = ?;",
            (answer_key_id, user_id),
        )
        return await cursor.fetchone()


async def delete_answer_key_record(answer_key_id: str) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("DELETE FROM omr_answer_keys WHERE id = ?;", (answer_key_id,))
        await conn.commit()


GRADED_RESULT_COLUMNS = """
    id, class_name, sheet_id, sheet_label, answer_key_id, answer_key_name, sbd, made,
    correct_count, wrong_count, blank_count, ambiguous_count, score_10, aligned, saved_at
"""


async def save_graded_result_record(
    result_id: str,
    user_id: str,
    class_name: str,
    sheet_id: str,
    sheet_label: str,
    answer_key_id: str,
    answer_key_name: str,
    sbd: str,
    made: str,
    correct_count: int,
    wrong_count: int,
    blank_count: int,
    ambiguous_count: int,
    score_10: float,
    aligned: bool,
    saved_at: str,
) -> None:
    # 1 phieu chi co 1 dong "da chot" cho moi dap an (UNIQUE sheet_id+answer_key_id)
    # - luu lai lan nua (vd sau khi sua khoanh) se CAP NHAT dong cu thay vi tao
    # ban ghi trung, tranh so diem bi nhan doi trong bang.
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute(
            f"""
            INSERT INTO omr_graded_results
                (id, user_id, {GRADED_RESULT_COLUMNS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sheet_id, answer_key_id) DO UPDATE SET
                user_id = excluded.user_id,
                class_name = excluded.class_name,
                sheet_label = excluded.sheet_label,
                answer_key_name = excluded.answer_key_name,
                sbd = excluded.sbd,
                made = excluded.made,
                correct_count = excluded.correct_count,
                wrong_count = excluded.wrong_count,
                blank_count = excluded.blank_count,
                ambiguous_count = excluded.ambiguous_count,
                score_10 = excluded.score_10,
                aligned = excluded.aligned,
                saved_at = excluded.saved_at;
            """,
            (
                result_id, user_id, class_name, sheet_id, sheet_label, answer_key_id, answer_key_name,
                sbd, made, correct_count, wrong_count, blank_count, ambiguous_count,
                score_10, int(aligned), saved_at,
            ),
        )
        await conn.commit()


async def get_graded_result_by_sheet_and_key(sheet_id: str, answer_key_id: str, user_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"""
            SELECT {GRADED_RESULT_COLUMNS} FROM omr_graded_results
            WHERE sheet_id = ? AND answer_key_id = ? AND user_id = ?;
            """,
            (sheet_id, answer_key_id, user_id),
        )
        return await cursor.fetchone()


async def list_graded_results(user_id: str) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"""
            SELECT {GRADED_RESULT_COLUMNS} FROM omr_graded_results
            WHERE user_id = ?
            ORDER BY class_name ASC, sbd ASC, saved_at DESC;
            """,
            (user_id,),
        )
        return await cursor.fetchall()


async def get_graded_result(result_id: str, user_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {GRADED_RESULT_COLUMNS} FROM omr_graded_results WHERE id = ? AND user_id = ?;",
            (result_id, user_id),
        )
        return await cursor.fetchone()


async def delete_graded_result_record(result_id: str) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("DELETE FROM omr_graded_results WHERE id = ?;", (result_id,))
        await conn.commit()
