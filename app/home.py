from pathlib import Path
from quart import g, Quart, redirect, render_template, url_for, abort, \
                  send_file #, request 
from dotenv import load_dotenv

from os import getenv#, unsetenv
from datetime import datetime, timedelta
import pandas as pd

from data_intake import token_request, petfinder_request
from table_maker import table_maker
from graph_maker import graph_maker

    # SETUP
app = Quart(__name__)
app.logger.info('Establish logger')

# Environmental Variables for API token, specify during build or in ".env"
load_dotenv() 


# App configuration: various directories, API settings
app.config.update({
    "pet_data": Path(app.root_path, 'data', 'adopt.parquet'),
    "org_data": Path(app.root_path, 'data', 'organizations.json'),
    "tables": Path(app.root_path, 'templates', 'tables'),
    "graphs":Path(app.root_path, 'static', 'graphs'),
    "client_id":getenv('client_id'),
    "client_secret":getenv('client_secret'),
    "location":getenv('location', 'Minneapolis, Minnesota'),
    "SERVER_NAME": getenv('server_name', 'localhost:5000'),
})

    ## BACKGROUND, DATA COLLECTION FUNCTIONS
# API request and file save, perform on startup and when data is stale
async def _fetch_data(startup):
    app.logger.info('Petfinder API requests . . .')
    token = await token_request(app.config["client_id"], 
                                app.config["client_secret"], app.logger)
    if type(token) == int:
        if startup:
            app.logger.critical(\
            '! first data request failed, application (should be) aborting !')
            return False
        else:
            adopt = orgs = pd.DataFrame()
    else:
        adopt, orgs = await petfinder_request(token, app.config["org_data"],
                                          app.config["pet_data"], 
                                          app.config['location'], app.logger)
    # ensure data was made
    if adopt.empty or orgs.empty:
        app.logger.error('Error performing Petfinder API request(s)')
        return False
    return True

# load saved data to memory, update if old
async def _load_data():
    # organizations from JSON, adoptable pets from PARQUET
    org = pd.read_json(app.config["org_data"])
    adopt = pd.read_parquet(app.config["pet_data"])  
    # time saved ~ token['start_time'] more accurate, could write to file
    updated = datetime.fromtimestamp(app.config["pet_data"].stat().st_mtime)     
    # check data
    await _check_data(updated)
    
    return org, adopt, updated


# make tables, graphs from data. utilize in templates. add more tasks later
async def _use_data(fresh_data):
    if not fresh_data:
        app.logger.warning('No new data, not updating graphs and tables.')
        return
    orgs, adopt, updated = await _load_data()
    app.logger.info('Creating tables, data exports . . .')
    await table_maker(orgs.copy(), adopt.copy(), app.config["tables"], 
                      app.root_path, url_for('pet_table', _external=True), 
                      app.logger)
    app.logger.info('Creating graphs. . .')
    await graph_maker(adopt.copy(), app.config["graphs"], updated, 
                      url_for('home', _external=True))
            
   
# check data for staleness
async def _check_data(updated):
    app.logger.info('updated')
    app.logger.info(updated.strftime('%x %X'))
    app.logger.info('now')
    app.logger.info(datetime.now().strftime('%x %X'))
    
    if not updated or datetime.now() - updated > timedelta(hours=3):
        app.logger.info('Data check: refreshing old data') if updated else \
        app.logger.info('Application startup, first data request')
        success = await _fetch_data(False)    
        await _use_data(success)
        

    # APPLICATION
# first API request on startup, save and use data, to be updated periodically
@app.before_serving
async def startup():
    # true first startup
    if not app.config["org_data"].exists() and \
    not app.config["pet_data"].exists(): 
        await _check_data(None)
    else:
        # server restart, check data before loading
        app.logger.info('Server restarting, checking last data update . . .')
        _,_,updated = await _load_data()
        await _check_data(updated)
    
# attach data to "G" to serve requests
@app.before_request
async def attach_data(): 
    if not hasattr(g, "org") or not hasattr(g, "adopt") \
    or not hasattr(g, "updated"):
        g.org, g.adopt, g.updated = await _load_data()


    # Routes
# Home Page, tabular breakdown, welcome, oldest listings / graphs / wordclouds
@app.route("/")
@app.route("/home")
async def home():
    org, adopt, updated = g.org, g.adopt, g.updated
    indicator = 'success' if datetime.now() - updated < timedelta(hours=13) \
                else 'danger'
    updated = updated.strftime('%x %X')
    pet_count = adopt.shape[0]
    adopt['updated'] = pd.to_datetime(adopt.updated)
    adopt = adopt.sort_values('updated')[:4]
    return await render_template("home.html", org=org, updated=updated, 
                                 indicator=indicator, pets=adopt, 
                                 pet_count=pet_count)

# all pet data, styled table. link to downloads
@app.route("/table")
async def pet_table():
    updated = g.updated
    return await render_template("pet_table.html", updated=updated)

# download pet data table, append update time to filename
@app.route("/table/export/<extension>")
async def download_table(extension):
    updated = g.updated
    extension = extension.lower()
    if extension not in ['csv','html','xlsx','xml', 'parquet', 'html_f']:
        abort(404, description="Filetype not available, valid extensions are: \
CSV, HTML, XLSX, XML, and Parquet.")
    
    # Prepare file
    if extension == 'html_f': # formatted HTML table
        extension = 'html'
        file = Path(app.root_path, 'templates', 'tables', 'all_pets_table.html')
    elif extension == 'parquet':
        file =  Path(app.root_path, 'data', 'adopt.parquet')
    else:
        file = Path(app.root_path, 'static', 'data_exports', f'adopt.{extension}')  
    if not file.exists():
        abort(404, description='Requested file is missing. Submit issue if \
problem persists.')
        
    return await send_file(file, as_attachment=True, 
    attachment_filename = f"adoptions_{updated.strftime('%xT%X')}.{extension}")

# list of cats, option to filter by orgID    
@app.route("/pets/cats", defaults={'org_id':None})
@app.route("/pets/cats/<org_id>")
async def all_cats(org_id):
    org, adopt, updated = g.org, g.adopt, g.updated
    adopt = adopt[adopt.species == 'Cat']
    
    org_id = org_id.upper() if org_id and org_id.upper() in adopt.orgID.values\
                            else None
    if org_id:
        adopt = adopt[adopt.orgID == org_id]
    
    org = org[org.index.isin(adopt.orgID.unique())]    
    return await render_template("cat_list.html", cats=adopt, catorg=org,
                                  updated=updated, org_id=org_id)

# list of dogs, option to filter by orgID
@app.route("/pets/dogs", defaults={'org_id':None})
@app.route("/pets/dogs/<org_id>")
async def all_dogs(org_id):
    org, adopt, updated = g.org, g.adopt, g.updated
    adopt = adopt[adopt.species == 'Dog']
    
    org_id = org_id.upper() if org_id and org_id.upper() in adopt.orgID.values\
                            else None
    if org_id:
        adopt = adopt[adopt.orgID == org_id]
    
    org = org[org.index.isin(adopt.orgID.unique())]   
    return await render_template("dog_list.html", dogs=adopt, dogorg=org,
                                  updated=updated, org_id=org_id)

# Pet Page    
@app.route("/pet/<int:pet_id>")
async def pet_page(pet_id):
    org, adopt, updated = g.org, g.adopt, g.updated
    if pet_id not in adopt.index:
        abort(404, description="Specified PetID does not exist.")
    adopt = adopt.loc[pet_id,:]
    org = org.loc[adopt.orgID,:]
    return await render_template("pet_page.html", pet=adopt, petorg=org,
                                  updated=updated)

# Random Pet Page, redirect after random sample
@app.route("/pets/random")
async def random_pet_page():
    adopt = g.adopt
    choice = adopt.sample(1).index[0]
    return redirect(url_for('pet_page',pet_id=choice))
    
# list of adoption organizations  
@app.route("/organizations")
async def org_landing():
    org, updated = g.org, g.updated
    return await render_template("org_list.html", org=org, updated=updated)

# Organization Page    
@app.route("/organization/<org_id>")
async def org(org_id):
    org, adopt, updated = g.org, g.adopt, g.updated
    org_id = org_id.upper() if org_id else None
    if org_id not in org.index:
        abort(404, description="Specified OrganizationID does not exist.")
    
    org = org.loc[org_id, :]
    cats = adopt[(adopt.orgID == org_id) & (adopt.species == 'Cat')]
    cats = {ind:cats.loc[ind,'name'] for ind in cats.index}
    dogs = adopt[(adopt.orgID == org_id) & (adopt.species == 'Dog')]
    dogs = {ind:dogs.loc[ind,'name'] for ind in dogs.index}
    del adopt
    return await render_template("org_page.html", org=org, dogs=dogs, cats=cats,
                                  updated=updated)

# ping page, keep server alive
@app.route("/ping")
async def ping_page():
    return '=^..^='

# Error handler(s)
@app.errorhandler(404)
async def error_page(e):
    return await render_template('error404.html', e=e), 404  

# if name == main, running in dev environment. debug mode
if __name__ == "__main__":
    app.logger.setLevel(10)
    app.run(debug = True)
# else setup logging for "production" Hypercorn deployment.
else:   
    app.config.update({"SERVER_NAME": getenv('server_name', 'localhost:8000')})
    import logging
    hypercorn_logger = logging.getLogger('hypercorn.error')
    hypercorn_logger.addHandler(logging.StreamHandler())
    hypercorn_logger.setLevel(20)
    app.logger.handlers = hypercorn_logger.handlers
    app.logger.setLevel(hypercorn_logger.level)