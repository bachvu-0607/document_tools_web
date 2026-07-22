import aiosqlite

from app.core.config import settings


async def init_omr_db() -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS omr_sheets (
                id TEXT PRIMARY KEY,
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
        # Bang co the da ton tai tu truoc khi them cot "aligned" - them bang
        # ALTER TABLE (khong xoa du lieu cu) thay vi drop/tao lai.
        try:
            await conn.execute("ALTER TABLE omr_detections ADD COLUMN aligned INTEGER NOT NULL DEFAULT 1;")
        except aiosqlite.OperationalError:
            pass  # cot da ton tai roi, bo qua
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS omr_answer_keys (
                id TEXT PRIMARY KEY,
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
        await conn.commit()


async def save_sheet_record(
    sheet_id: str,
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
                (id, label, original_filename, stored_filename, content_type, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (sheet_id, label, original_filename, stored_filename, content_type, uploaded_at),
        )
        await conn.commit()


async def list_sheets() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT id, label, original_filename, stored_filename, content_type, uploaded_at
            FROM omr_sheets
            ORDER BY uploaded_at DESC;
            """,
        )
        return await cursor.fetchall()


async def get_sheet(sheet_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT id, label, original_filename, stored_filename, content_type, uploaded_at
            FROM omr_sheets
            WHERE id = ?;
            """,
            (sheet_id,),
        )
        return await cursor.fetchone()


async def find_sheet_usages(sheet_id: str) -> tuple[list[str], list[str]]:
    # Truoc khi xoa 1 phieu, can biet no co dang lam anh mau cho template nao
    # hoac lam nguon cho dap an nao khong - xoa mat anh goc trong khi template/
    # dap an van con tham chieu se lam hong tinh nang cham bai ve sau.
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
    id, name, reference_sheet_id, sbd_zone, sbd_digits, made_zone, made_digits,
    answer_blocks, num_choices, created_at
"""


async def save_template_record(
    template_id: str,
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
                (id, name, reference_sheet_id, sbd_zone, sbd_digits, made_zone,
                 made_digits, answer_blocks, num_choices, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                template_id, name, reference_sheet_id, sbd_zone, sbd_digits,
                made_zone, made_digits, answer_blocks, num_choices, created_at,
            ),
        )
        await conn.commit()


async def list_templates() -> list[aiosqlite.Row]:
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
    # nang cham bai voi dap an do.
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
                (sheet_id, template_id, sbd, sbd_ambiguous_digits, made,
                 made_ambiguous_digits, answers, ambiguous_questions, detected_at, aligned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sheet_id) DO UPDATE SET
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
                sheet_id, template_id, sbd, sbd_ambiguous_digits, made,
                made_ambiguous_digits, answers, ambiguous_questions, detected_at,
                int(aligned),
            ),
        )
        await conn.commit()


async def get_detection(sheet_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {DETECTION_COLUMNS} FROM omr_detections WHERE sheet_id = ?;",
            (sheet_id,),
        )
        return await cursor.fetchone()


ANSWER_KEY_COLUMNS = "id, name, template_id, source_sheet_id, sbd, made, answers, created_at"


async def save_answer_key_record(
    answer_key_id: str,
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
                (id, name, template_id, source_sheet_id, sbd, made, answers, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (answer_key_id, name, template_id, source_sheet_id, sbd, made, answers, created_at),
        )
        await conn.commit()


async def list_answer_keys() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {ANSWER_KEY_COLUMNS} FROM omr_answer_keys ORDER BY created_at DESC;",
        )
        return await cursor.fetchall()


async def get_answer_key(answer_key_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {ANSWER_KEY_COLUMNS} FROM omr_answer_keys WHERE id = ?;",
            (answer_key_id,),
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
                ({GRADED_RESULT_COLUMNS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sheet_id, answer_key_id) DO UPDATE SET
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
                result_id, class_name, sheet_id, sheet_label, answer_key_id, answer_key_name,
                sbd, made, correct_count, wrong_count, blank_count, ambiguous_count,
                score_10, int(aligned), saved_at,
            ),
        )
        await conn.commit()


async def get_graded_result_by_sheet_and_key(sheet_id: str, answer_key_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"""
            SELECT {GRADED_RESULT_COLUMNS} FROM omr_graded_results
            WHERE sheet_id = ? AND answer_key_id = ?;
            """,
            (sheet_id, answer_key_id),
        )
        return await cursor.fetchone()


async def list_graded_results() -> list[aiosqlite.Row]:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"""
            SELECT {GRADED_RESULT_COLUMNS} FROM omr_graded_results
            ORDER BY class_name ASC, sbd ASC, saved_at DESC;
            """,
        )
        return await cursor.fetchall()


async def get_graded_result(result_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            f"SELECT {GRADED_RESULT_COLUMNS} FROM omr_graded_results WHERE id = ?;",
            (result_id,),
        )
        return await cursor.fetchone()


async def delete_graded_result_record(result_id: str) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("DELETE FROM omr_graded_results WHERE id = ?;", (result_id,))
        await conn.commit()
