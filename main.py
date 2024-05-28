from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Define the database connection parameters
username = 'root'
password = ''
host = 'localhost'
database = 'pemilu2024'

# Create a connection to the database
try:
    cnx = mysql.connector.connect(
        user=username,
        password=password,
        host=host,
        database=database
    )
    cursor = cnx.cursor()

    # Create the voter table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS voter (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        dob DATE NOT NULL,
        gender ENUM('M', 'F') NOT NULL,
        voter_id INT NOT NULL UNIQUE
    )
    """)
    cnx.commit()

    # Create the votes table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        voter_id INT NOT NULL,
        paslon VARCHAR(50) NOT NULL,
        vote TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (voter_id) REFERENCES voter(voter_id)
    )
    """)
    cnx.commit()
except mysql.connector.Error as err:
    print(f"Error: {err}")

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def form_post(request: Request, name: str = Form(...), dob: str = Form(...), gender: str = Form(...), voter_id: int = Form(...), paslon: str = Form(...)):
    try:
        dob_parsed = datetime.strptime(dob, "%Y-%m-%d").date()
        if gender not in ['M', 'F']:
            return templates.TemplateResponse("form.html", {"request": request, "error": "Jenis kelamin hanya boleh M atau F."})

        cursor.execute("INSERT INTO voter (name, dob, gender, voter_id) VALUES (%s, %s, %s, %s)", (name, dob_parsed, gender, voter_id))
        cursor.execute("INSERT INTO votes (voter_id, paslon) VALUES (%s, %s)", (voter_id, paslon))
        cnx.commit()

        return templates.TemplateResponse("form.html", {"request": request, "message": "Vote has been successfully recorded!"})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return templates.TemplateResponse("form.html", {"request": request, "error": f"Database error: {err}"})
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
