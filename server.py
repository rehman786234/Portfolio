from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import DatabaseManager

app = FastAPI(title="Rehman Ali Portfolio - Public API (User Side)")
db = DatabaseManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Models ====================
class ProjectIdRequest(BaseModel):
    id: int


class ContactMessageIn(BaseModel):
    name: str
    email: str
    subject: Optional[str] = ""
    message: str


# ==================== Helpers ====================
def normalize_project(p: dict) -> dict:
    """Normalize project dictionary keys for consistent frontend consumption."""
    p_dict = dict(p)
    name = (
        p_dict.get("ProjectName")
        or p_dict.get("projectName")
        or p_dict.get("projectname")
        or p_dict.get("name")
        or ""
    )
    desc = (
        p_dict.get("ProjectDesc")
        or p_dict.get("projectDesc")
        or p_dict.get("projectdesc")
        or p_dict.get("desc")
        or ""
    )
    p_dict["ProjectName"] = name
    p_dict["projectName"] = name
    p_dict["ProjectDesc"] = desc
    p_dict["projectDesc"] = desc

    images = p_dict.get("images") or []
    if not p_dict.get("thumbnail") and images:
        p_dict["thumbnail"] = images[0]

    return p_dict


def get_all_projects():
    try:
        with db.get_cursor() as (conn, cursor):
            cursor.execute(
                """
                SELECT p.*, first_image.image_url AS first_image_url
                FROM projects AS p
                LEFT JOIN LATERAL (
                    SELECT image_url
                    FROM images
                    WHERE project_id = p.id
                    ORDER BY id ASC
                    LIMIT 1
                ) AS first_image ON TRUE
                ORDER BY p.id DESC
                """
            )
            projects = cursor.fetchall()
            normalized = []
            for p in projects:
                p_dict = dict(p)
                first_image = p_dict.pop("first_image_url", None)
                p_dict["images"] = [first_image] if first_image else []
                normalized.append(normalize_project(p_dict))
            return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_single_project_details(project_id: int):
    try:
        with db.get_cursor() as (conn, cursor):
            cursor.execute(
                "SELECT * FROM images WHERE project_id = %s ORDER BY id ASC",
                (project_id,),
            )
            details = cursor.fetchall()
            return {"success": True, "details": details}
    except Exception as e:
        return {"success": False, "message": str(e)}


def fetch_basic_details():
    try:
        with db.get_cursor() as (conn, cursor):
            cursor.execute("SELECT * FROM roles ORDER BY id ASC")
            roles = cursor.fetchall()

            cursor.execute("SELECT * FROM basic_details LIMIT 1")
            details = cursor.fetchone()

            cursor.execute(
                """
                SELECT 
                    s.id,
                    s.skill_name,
                    s.skill_level,
                    s.cat_id,
                    c.category_name
                FROM skills s
                LEFT JOIN categories c 
                    ON c.id = s.cat_id
                ORDER BY s.id ASC;
                """
            )
            skills = cursor.fetchall()

            cursor.execute("SELECT * FROM education ORDER BY id ASC")
            education = cursor.fetchall()

            cursor.execute("SELECT * FROM contact_info ORDER BY id ASC")
            contacts = cursor.fetchall()

            return {
                "success": True,
                "message": "Data retrieved successfully",
                "roles": roles,
                "details": details,
                "skills": skills,
                "contacts": contacts,
                "education": education,
            }
    except Exception as e:
        return {"success": False, "message": str(e)}


# ==================== User-Side Public Routes (NO ADD/EDIT) ====================
@app.get("/")
def root():
    return {
        "message": "Rehman Ali Portfolio - Public API (User Side)",
        "mode": "read-only",
        "endpoints": [
            "/api/v3/rehmanali/portfolio/projects",
            "/api/v3/rehmanali/portfolio/basicdetails",
            "/api/v3/rehmanali/portfolio/project/detail",
            "/api/v3/contact",
        ],
    }


# Get Projects
@app.get("/api/v3/rehmanali/portfolio/projects")
@app.get("/rehmanali/portfolio/projects")
def list_projects(response: Response):
    response.headers["Cache-Control"] = (
        "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
    )
    projects = get_all_projects()
    return {"success": True, "projects": projects}


# Get Basic Details, Skills, Education, Roles, Contacts
@app.get("/api/v3/rehmanali/portfolio/basicdetails")
def get_details(response: Response):
    response.headers["Cache-Control"] = (
        "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
    )
    return fetch_basic_details()


# Get Project Images / Screenshots
@app.post("/api/v3/rehmanali/portfolio/project/detail")
def project_detail(req: ProjectIdRequest):
    return get_single_project_details(req.id)


@app.get("/api/v3/rehmanali/portfolio/project/{project_id}/detail")
def project_detail_get(project_id: int, response: Response):
    response.headers["Cache-Control"] = (
        "public, max-age=0, s-maxage=60, stale-while-revalidate=300"
    )
    return get_single_project_details(project_id)


# User Contact Form Submission
@app.post("/api/v3/contact")
def submit_contact(msg: ContactMessageIn):
    try:
        with db.get_cursor() as (conn, cursor):
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS contact_messages (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    subject VARCHAR(255),
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cursor.execute(
                """
                INSERT INTO contact_messages (name, email, subject, message)
                VALUES (%s, %s, %s, %s)
                """,
                (msg.name, msg.email, msg.subject, msg.message),
            )
            conn.commit()
        return {
            "success": True,
            "message": "Thank you! Your message has been received.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("server:app", port=9090, host="0.0.0.0", reload=True)