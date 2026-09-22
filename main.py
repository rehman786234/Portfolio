from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import DatabaseManager
import uvicorn
from pydantic import BaseModel
app = FastAPI(title="UserSide Api of portfolio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

db = DatabaseManager()

# Model for Project details
class Projects(BaseModel):
    id: int
def fetch_projects():
    conn = cursor = None
    try:
        conn, cursor = db.getConnection()
        cursor.execute("SELECT * FROM projects")
        rows = cursor.fetchall()
        # Convert rows to dicts if cursor returns tuples.
        # Better: use a dict cursor in DatabaseManager.
        if rows and not isinstance(rows[0], dict):
            columns = [c[0] for c in cursor.description]
            rows = [dict(zip(columns, r)) for r in rows]
        return rows
    finally:
        if conn is not None and cursor is not None:
            db.closeConnection(conn, cursor)
def get_project_details(id:int):
    try:
        conn, cursor = db.getConnection()
        cursor.execute('SELECT * FROM images WHERE project_id = %s ',(id,))
        details = cursor.fetchall()
        
        return {
            'success':True,
            'details':details
        }
    except Exception as e:
        return {
            'success':False,
            'message': str(e)
        }
    finally:
        db.closeConnection(conn, cursor)
def fetch_details():
    try:
        conn, cursor = db.getConnection()
        cursor.execute("SELECT * FROM roles")
        roles = cursor.fetchall()
        cursor.execute('SELECT * FROM basic_details')
        details = cursor.fetchone()
        cursor.execute("""SELECT 
    s.skill_name,
    s.skill_level,
    c.category_name
FROM skills s
INNER JOIN categories c 
    ON c.id = s.cat_id;""")
        skills = cursor.fetchall()
        cursor.execute("SELECT * FROM education")
        education = cursor.fetchall()
        cursor.execute('SELECT * FROM contact_info')
        contacts = cursor.fetchall()
        return {
            'success':True,
            'message':'Here my data',
            'roles':roles,
            'details':details,
            'skills':skills,
            'contacts': contacts,
            'education':education
        }
    except Exception as e:
        return {
            'success':False,
            'message': str(e)
        }
    finally:
        db.closeConnection(conn, cursor)

@app.get("/api/v3/rehmanali/portfolio/projects")
def get_projects():
    try:
        projects = fetch_projects()
    except Exception as e:
        # Log the real exception server-side
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, "projects": projects}

@app.get("/api/v3/rehmanali/portfolio/basicdetails")
def get_details():
    return fetch_details()

@app.post("/api/v3/rehmanali/portfolio/project/detail")
def project_detail(project : Projects):
    pro_id = project.id
    return get_project_details(pro_id)

if __name__ == '__main__':
    uvicorn.run('main:app',port=9990, host='localhost',reload=True)
