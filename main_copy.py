from fastapi import FastAPI
from databases import Database
from supabase import create_client, Client
from dotenv import load_dotenv
import os , json
from pydantic import BaseModel
from models.models import DomainModel
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import llm_helper.feature_extractor as FE
from fastapi.responses import JSONResponse

# Load API key from .env file
load_dotenv()
# SUPABASE_API_KEY = os.environ.get("EXPO_PUBLIC_SUPABASE_KEY")
# SUPABASE_API_URL = os.environ.get("EXPO_PUBLIC_SUPABASE_URL")
# POSTGRES_SQL_URL = os.environ.get("POSTGRES_SQL_URL")



# # Supabase credentials (replace with your project values)
# SUPABASE_URL = SUPABASE_API_URL
# SUPABASE_ANON_KEY = SUPABASE_API_KEY
# DATABASE_URL = POSTGRES_SQL_URL


import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")


# PostgreSQL connection class
class PostgresDB:
    def __init__(self, user, password, host, port, dbname):
        try:
            self.connection = psycopg2.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                dbname=dbname
            )
            print("Connection successful!")
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connection = None

    def execute_query(self, query, params=None):
        if not self.connection:
            print("No connection available.")
            return None
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            if query.strip().lower().startswith("select"):
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = cursor.rowcount
        except Exception as e:
            print(f"Query failed: {e}")
            result = None
        cursor.close()
        return result

    def close(self):
        if self.connection:
            self.connection.close()
            print("Connection closed.")

# Usage example
# db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
# result = db.execute_query("SELECT NOW();")
# print("Current Time:", result)
# db.close() # Call when shutting down the app

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# Add CORS middleware
origins = [
    "http://127.0.0.1:8000",  # your frontend URL
    "http://localhost:8000",
    # add other origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # allowed origins
    allow_credentials=True,
    allow_methods=["*"],        # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],        # allow all headers
)
# # Connect asynchronously to PostgreSQL (via Supabase)
# database = Database(DATABASE_URL)

# # Optional: Initialize Supabase client for API interactions
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# @app.on_event("startup")
# async def startup():
#     await database.connect()

# @app.on_event("shutdown")
# async def shutdown():
#     await database.disconnect()

@app.get("/return_supabe")
async def read_root():
    # Example query to fetch rows from a "notes" table (make sure it exists)
    query = "SELECT * FROM notes"
    results = await database.fetch_all(query=query)
    return {"notes": results}

@app.get("/feature")
async def get_features_data():
    # Getitng features data table 
    query = "SELECT * FROM feature"
    results = await database.fetch_all(query=query)
    return {"notes":results}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "Hello from FastAPI!"})

@app.post("/domain")
async def receive_domain(domain_data: DomainModel):
    domain_name = domain_data.domain
    print(f"Received domain: {domain_name}")
    # You can add logic here to save or process the domain name as needed
    return {"domain": domain_name}

@app.get("/request_domain_features", response_class=HTMLResponse)
async def receive_domain_features(request: Request):
    domain_name = request.query_params.get("domain")
    print(f"Feature extraction requested for domain: {domain_name}")
    # Add your feature extraction logic here
    feature_result = FE.feature_extractor_function(domain_name)
    cleaned_str = feature_result.replace("```json", "")
    cleaned_str = cleaned_str.replace("```", "")
    # print(f'fe:{cleaned_str}')
    feature_data = json.loads(cleaned_str)
    keys_list = list(feature_data.keys())  # convert dict_keys to list
    first_key = keys_list[0]
    return templates.TemplateResponse(
        "show_extracted_features.html",
        {
            "request": request,
            "domain": domain_name,
            "features": feature_data[first_key]
        }
    )

# @app.post("/request_domain_features", response_class=HTMLResponse)
# async def receive_domain_features(request: Request, domain_data: DomainModel):
#     domain_name = domain_data.domain
#     print(f"Feature extraction requested for domain: {domain_name}")

#     return templates.TemplateResponse("show_extracted_features.html", {"request": request, "message": "Hello from FastAPI!"})


@app.get("/feature_accuring_domain", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("extract_feature.html", {"request": request, "message": "Hello from FastAPI!"})

@app.post('/updating_feature_supabase', response_class=JSONResponse)
async def updating_feature_supabase(request: Request):
    data = await request.json()
    features = data.get('features', [])
    results = []
    try:
        db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
        for feature in features:
            domain = feature.get('domain')
            feat = feature.get('feature')
            desc = feature.get('feature_description')
            query = "INSERT INTO feature (domain, feature, feature_description) VALUES (%s, %s, %s);"
            try:
                res = db.execute_query(query, (domain, feat, desc))
                results.append(res)
            except Exception as e:
                print(f"Query failed: {e}")
                db.connection.rollback()
        db.close()
        return {"status": "success", "inserted": len(results)}
    except Exception as e:
        print(f'Error:{e}')
        db.close()