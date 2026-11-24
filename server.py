from datetime import datetime, timedelta
from mcp.server.mcpserver import MCPServer
from db import get_conn, init_db

init_db()
mcp = MCPServer("JobApplicationTracker")


@mcp.resource("jobs://summary")
def get_pipeline_summary() -> str:
    """Returns a high-level summary of all job applications by status."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as total FROM applications GROUP BY status"
        ).fetchall()
    if not rows:
        return "No job applications tracked yet."
    lines = [f"- {r['status']}: {r['total']}" for r in rows]
    return "Job Application Pipeline Summary:\n" + "\n".join(lines)


@mcp.tool()
def list_applications(status: str | None = None) -> list[dict]:
    """List all tracked job applications, optionally filtered by status (Applied, Interviewing, Offer, Rejected)."""
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM applications WHERE LOWER(status) = LOWER(?) ORDER BY last_contact_date DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY last_contact_date DESC"
            ).fetchall()
    return [dict(r) for r in rows]


@mcp.tool()
def add_application(company: str, role: str, status: str = "Applied", notes: str = "") -> str:
    """Add a new job application to the tracker."""
    today = str(datetime.now().date())
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO applications (company, role, status, applied_date, last_contact_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (company, role, status, today, today, notes),
        )
    return f"Added application #{cur.lastrowid}: {role} at {company} (Status: {status})."


@mcp.tool()
def get_pending_followups(days_threshold: int = 7) -> list[dict]:
    """Find active applications (Applied or Interviewing) that haven't been contacted in at least `days_threshold` days."""
    cutoff = str((datetime.now() - timedelta(days=days_threshold)).date())
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, company, role, status, last_contact_date, notes
            FROM applications
            WHERE status IN ('Applied', 'Interviewing')
              AND last_contact_date <= ?
            ORDER BY last_contact_date ASC
            """,
            (cutoff,),
        ).fetchall()
    return [dict(r) for r in rows]


@mcp.tool()
def log_followup(company: str, new_status: str | None = None, note_update: str | None = None) -> str:
    """Record a follow-up for a company today, optionally updating its status and appending a note."""
    today = str(datetime.now().date())
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE LOWER(company) LIKE LOWER(?)",
            (f"%{company}%",),
        ).fetchone()
        if not row:
            return f"No application found matching company '{company}'."

        updated_status = new_status if new_status else row["status"]
        updated_notes = (
            f"{row['notes']} | [{today}] {note_update}".strip(" |")
            if note_update
            else row["notes"]
        )
        conn.execute(
            """
            UPDATE applications
            SET last_contact_date = ?, status = ?, notes = ?
            WHERE id = ?
            """,
            (today, updated_status, updated_notes, row["id"]),
        )
    return f"Updated {row['company']} ({row['role']}): last_contact_date={today}, status={updated_status}."


if __name__ == "__main__":
    mcp.run()
