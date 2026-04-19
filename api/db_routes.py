"""SQLite database management endpoints — table browser, raw SQL query, full CRUD."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.db import get_db

router = APIRouter(prefix="/api/db", tags=["database"])

ALLOWED_TABLES = frozenset({
    "runs", "functions", "generated_tests",
    "proposed_fixes", "test_failures", "fix_attempts",
})


def _validate_table(table: str) -> None:
    if table not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail=f"Unknown table: {table}")


def _get_columns(db: Session, table: str) -> list[dict]:
    rows = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return [{"name": row[1], "type": row[2]} for row in rows]


@router.get("/tables")
def list_tables(db: Session = Depends(get_db)):
    result = []
    for table in sorted(ALLOWED_TABLES):
        cols = _get_columns(db, table)
        if not cols:
            continue  # table doesn't exist in this DB file yet
        count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        result.append({"table": table, "row_count": count, "columns": cols})
    return result


@router.post("/query")
def raw_query(body: dict, db: Session = Depends(get_db)):
    sql = (body.get("sql") or "").strip()
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    try:
        result = db.execute(text(sql))
        cols = list(result.keys())
        rows = [dict(zip(cols, row)) for row in result.fetchall()]
        return {"columns": cols, "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{table}")
def list_rows(
    table: str,
    page: int = 1,
    limit: int = 50,
    filter_col: str = "",
    filter_val: str = "",
    db: Session = Depends(get_db),
):
    _validate_table(table)
    offset = (page - 1) * limit
    where = ""
    params: dict = {"limit": limit, "offset": offset}

    if filter_col and filter_val:
        valid_cols = {c["name"] for c in _get_columns(db, table)}
        if filter_col not in valid_cols:
            raise HTTPException(status_code=400, detail=f"Unknown column: {filter_col}")
        where = f"WHERE {filter_col} LIKE :filter_val"
        params["filter_val"] = f"%{filter_val}%"

    rows_result = db.execute(text(f"SELECT * FROM {table} {where} LIMIT :limit OFFSET :offset"), params)
    cols = list(rows_result.keys())
    rows = [dict(zip(cols, row)) for row in rows_result.fetchall()]

    count_params = {k: v for k, v in params.items() if k == "filter_val"}
    total = db.execute(text(f"SELECT COUNT(*) FROM {table} {where}"), count_params).scalar()
    return {"table": table, "page": page, "limit": limit, "total": total, "columns": cols, "rows": rows}


@router.post("/{table}", status_code=201)
def create_row(table: str, body: dict, db: Session = Depends(get_db)):
    _validate_table(table)
    valid_cols = {c["name"] for c in _get_columns(db, table)}
    data = {k: v for k, v in body.items() if k in valid_cols and k != "id"}
    if not data:
        raise HTTPException(status_code=400, detail="No valid columns provided")
    cols_str = ", ".join(data.keys())
    vals_str = ", ".join(f":{k}" for k in data.keys())
    result = db.execute(text(f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str})"), data)
    db.commit()
    return {"id": result.lastrowid}


@router.put("/{table}/{row_id}")
def update_row(table: str, row_id: int, body: dict, db: Session = Depends(get_db)):
    _validate_table(table)
    valid_cols = {c["name"] for c in _get_columns(db, table)}
    data = {k: v for k, v in body.items() if k in valid_cols and k != "id"}
    if not data:
        raise HTTPException(status_code=400, detail="No valid columns provided")
    set_str = ", ".join(f"{k} = :{k}" for k in data.keys())
    data["_id"] = row_id
    db.execute(text(f"UPDATE {table} SET {set_str} WHERE id = :_id"), data)
    db.commit()
    return {"updated": row_id}


@router.delete("/{table}/{row_id}", status_code=204)
def delete_row(table: str, row_id: int, db: Session = Depends(get_db)):
    _validate_table(table)
    db.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": row_id})
    db.commit()
