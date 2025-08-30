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
import llm_helper.dataExtractorLlm_agent as DE
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
    
    def upsert(self, table, key_column, data):
        columns = ', '.join([f'"{col}"' for col in data.keys()])
        values = [data[col] for col in data.keys()]
        placeholders = ', '.join(['%s'] * len(values))
        update_stmt = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in data.keys() if col != key_column])
        query = f'''
            INSERT INTO "{table}" ({columns})
            VALUES ({placeholders})
            ON CONFLICT ("{key_column}") DO UPDATE SET
            {update_stmt};
        '''
        self.execute_query(query, values)

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
    success = True
    try:
        db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
        for feature in features:
            domain = feature.get('domain')
            feat = feature.get('feature')
            desc = feature.get('feature_description')
            query = "INSERT INTO feature (domain, feature, feature_description) VALUES (%s, %s, %s);"
            try:
                res = db.execute_query(query, (domain.lower(), feat, desc))
                results.append(res)
            except Exception as e:
                print(f"Query failed: {e}")
                db.connection.rollback()
                success = False
        
        domain = features[0].get('domain').lower()
        # Crating domain table         
        query = "SELECT table_name \
        FROM information_schema.tables \
        WHERE table_schema = 'public' \
        AND table_type = 'BASE TABLE';"
        try:
            res = db.execute_query(query)
            print(res)
            table_list = [item[0] for item in res]
            if domain not in table_list:
                print(f'need to add {domain} table') 
                query = f"select feature from feature where domain = '{domain}';"
                res = db.execute_query(query)
                feature_names = [item[0] for item in res]
                
                print('feature name : ',res)
                print('feature name : ',feature_names)
                columns = ', '.join([f'"{feat.replace(" ", "_").replace("/", "_").replace("&", "_").lower()}" TEXT' for feat in feature_names])
                print(f'columns:{columns}')
                # query = f'''
                #     CREATE TABLE "{domain}" (
                #         id SERIAL PRIMARY KEY,
                #         created_at timestamp without time zone DEFAULT now(),
                #         software TEXT,
                #         {columns},
                #         CONSTRAINT fk_software FOREIGN KEY (software) REFERENCES softwares(software_name)
                #     );
                #     '''
                query = f'''
                    CREATE TABLE "{domain}" (
                        id SERIAL PRIMARY KEY,
                        created_at timestamp without time zone DEFAULT now(),
                        software TEXT,
                        {columns},
                        CONSTRAINT fk_software FOREIGN KEY (software) REFERENCES softwares(software_name)
                    );

                    ALTER TABLE "{domain}" ADD CONSTRAINT {domain}_software_unique UNIQUE (software);
                    '''

                db.execute_query(query)
        except Exception as e:
            print(f"Query failed: {e}")
            db.connection.rollback()
            success = False
        db.close()
        if success:
            return {"status": "success", "inserted": len(results)}
        else:
            return {"status": "fail"}
    except Exception as e:
        print(f'Error:{e}')
        db.close()
        

@app.get("/view_all_features", response_class=HTMLResponse)
async def receive_domain_features(request: Request):
    try:
        db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
        
        query = "SELECT * FROM public.feature;"
        try:
            res = db.execute_query(query)
        except Exception as e:
            print(f"Query failed: {e}")
            db.connection.rollback()
        db.close()
        return templates.TemplateResponse(
            "view_all_features.html",
            {
                "request": request,
                "features" : res
            }
        )
    except Exception as e:
        print(f'Error:{e}')
        db.close()

# Software Accuring pahse
@app.get("/sofware_accuring", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("sofware_accuring.html", {"request": request, "message": "Hello from FastAPI!"})

@app.get("/domain_update", response_class=JSONResponse)
async def receive_domain_features(request: Request):

        domain_name = request.query_params.get("domain")
        software = request.query_params.get("software")
        software_link = request.query_params.get("software_link")
        db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
        
        query = "INSERT INTO public.softwares (domain, software_name, software_url) VALUES (%s, %s, %s);"
        try:
            res = db.execute_query(query, (domain_name.lower(), software.lower(), software_link.lower()))
            db.close()
        except Exception as e:
            print(f"Query failed: {e}")
            db.connection.rollback()
            db.close()
            return {"status": "fail"}
        return {"status": "success", }


@app.get("/show_domain_software", response_class=HTMLResponse)
def show_domain_software(request: Request):
    db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
        
    query = "SELECT \
            d.domain, \
            array_agg(f.feature) AS features, \
            array_agg(DISTINCT s.software_name) FILTER (WHERE s.software_name IS NOT NULL) AS softwares \
            FROM \
            domains d \
            LEFT JOIN \
            feature f ON d.domain = f.domain \
            LEFT JOIN \
            softwares s ON d.domain = s.domain \
            GROUP BY \
            d.domain \
            LIMIT 10;" 
    try:
        res = db.execute_query(query)
        db.close()
    except Exception as e:
        print(f"Query failed: {e}")
        db.connection.rollback()
        db.close()
    print(res)
    return templates.TemplateResponse(
        "show_domain_software.html",
        {
            "request": request,
            "features": res
        }
    )
    
# get_data_for_domain
@app.get("/get_data_for_domain", response_class=JSONResponse)
def get_data_for_domain(request: Request):
    domain = request.query_params.get("domain")
    print(f'domain: {domain}')
    db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
    query = f"""
        SELECT 
            s.domain,
            s.software_name,
            s.software_url,
            array_agg(f.feature) AS features,
            array_agg(f.feature_description) AS feature_desc
        FROM softwares s
        LEFT JOIN feature f ON s.domain = f.domain
        WHERE s.domain = %s
        GROUP BY s.domain, s.software_name, s.software_url;
    """
    try:
        res = db.execute_query(query, (domain,))
        
        for domain_val, software_name, software_url, features, features_desc in res:
            # Call your LLM agent to get JSON summary dict per software
            json_data = DE.llm_agent(domain_val, software_name, software_url, features, features_desc)
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from LLM agent for software {software_name}: {e}")
            # Prepare column-value dict for insert based on your table schema
            crm_row = {"software": software_name}
            
            # Normalize keys if needed, assuming json_data keys match DB columns or map accordingly
            for key, val in json_data.items():
                col_name = key.lower().replace(" ", "_").replace("/", "_").replace("&", "_")
                # You can choose to store either 'details', 'summarizer', or both
                crm_row[col_name] = json.dumps(val) if isinstance(val, dict) else val
            
            # Build dynamic insert/update statement using your DB helper
            db.upsert(table="crm", key_column="software", data=crm_row)

        db.close()
        return {'status': 'success'}
    except Exception as e:
        print(f"Query failed: {e}")
        db.connection.rollback()
        db.close()
        return {'status': 'error', 'detail': str(e)}



@app.get("/view_data_for_domain", response_class=HTMLResponse)
def view_data_for_domain(request: Request):
    domain = request.query_params.get("domain")
    print(f'domain: {domain}')
    db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
    query = f'SELECT * FROM {domain};'
    try:
        res = db.execute_query(query)
        db.close()
        # print(res)
        # Get column names
        col_query = f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = '{domain}' AND column_name != 'id' AND column_name != 'created_at' AND column_name != 'software';
        """
        db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
        col_res = db.execute_query(col_query)
        db.close()
        feature_cols = [item[0] for item in col_res]
        # Process rows
        data = []
        for row in res:
            software = row[2]  # assuming software is at index 2
            features = []
            for idx, col in enumerate(feature_cols):
                json_str = row[3 + idx]  # adjust index as needed
                if json_str:
                    try:
                        feature_data = json.loads(json_str)
                        features.append({
                            "feature": col,
                            "summarizer": feature_data.get("summarizer", ""),
                            "details": feature_data.get("details", "")
                        })
                    except Exception:
                        features.append({
                            "feature": col,
                            "summarizer": "",
                            "details": json_str
                        })
            data.append({
                "software": software,
                "features": features
            })
        print('\n\n\n\n\n',data)
        # return {"status": "success", "data": data}
        return templates.TemplateResponse(
            "view_data_for_domain.html",
            {
                "request": request,
                "features": data
            }
        )
    except Exception as e:
        print(f"Query failed: {e}")
        db.connection.rollback()
        db.close()
        return templates.TemplateResponse(
            "na_data.html",{"request": request}
        )






# # get_data_for_domain
# @app.get("/view_data_for_domain", response_class=JSONResponse)
# def view_data_for_domain(request: Request):
#     domain = request.query_params.get("domain")
#     print(f'domain: {domain}')
#     db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
        
#     query = f'SELECT * FROM {domain};'
#     try:
#         res = db.execute_query(query)
#         db.close()
#         print(res)
#     except Exception as e:
#         print(f"Query failed: {e}")
#         db.connection.rollback()
#         db.close()
#     print(res)
#     return {'status':'sucess'}
    # return templates.TemplateResponse(
    #     "view_data_for_domain.html",
    #     {
    #         "request": request,
    #         "features": res
    #     }
    # )







# @app.get("/get_data_for_domain", response_class=JSONResponse)
# def get_data_for_domain(request:Request):
#     domain = request.query_params.get("domain")
#     print(f'domain : {domain}')
#     db = PostgresDB(USER, PASSWORD, HOST, PORT, DBNAME)
#     query = f"SELECT  \
#             s.domain,  \
#             s.software_name,  \
#             s.software_url,  \
#             array_agg(f.feature) AS features,  \
#             array_agg(f.feature_description) AS feature_desc \
#             FROM  \
#             softwares s \
#             LEFT JOIN \
#             feature f ON s.domain = f.domain \
#             WHERE  \
#             s.domain = '{domain}' \
#             GROUP BY  \
#             s.domain, s.software_name, s.software_url;" 
#     # try:
#     res = db.execute_query(query)
#     db.close()
#     print(res)
#     for domain, software_name, software_url, features, features_desc in res:
#         json_data = DE.llm_agent(domain, software_name, software_url, features, features_desc)
#         print(json_data, end='\n\n\n\n')
#     # except Exception as e:
#     #     print(f"Query failed: {e}")
#     #     db.connection.rollback()
#     #     db.close()
#     return {'status':'sucess'}
