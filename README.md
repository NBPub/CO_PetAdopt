# [CO Pet Adoptions](https://CentralOregonPetAdoptions.onrender.com)

Local, up-to-date adoptable pet information.

***IN PROGRESS***

Python Quart / Hypercorn project deployed on Render.

### alpha deployment

**Build**

```
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

**Start**

```
cd app && hypercorn home:app -b 0.0.0.0:10000 --log-file="-" --access-logfile="-" --access-logformat='%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
```

### Python

 - Web Application
   - Quart
   - Hypercorn
 - Data
   - requests
   - pandas
   - pyarrow
 - Graphs
   - matplotlib
   - seaborn
   - wordcloud

### Resources

 - [DejaVuSans Font](https://dejavu-fonts.github.io/)
 - Petfinder API
 - Bootstrap
 
## Docs for L8R

### EV Table


| Name | Example | Description, Specifications |
|------|---------|-----------------------------|
| client_id | abcdefg123456 | Petfinder API authorization, use with **client_secret** to requet token for API requests |
| client_secret | 123456abcdefg | Petfinder API authorization, use with **client_id** to requet token for API requests |
| location | 90210 | Location to center adoption organization and pet searches. Can be input as zip code (shown), `<city>, <state>`, or `<latitiude>,<longitude>`. See more. |
| TZ |America/Los_Angeles | Valid [TZ identifier](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). Use to ensure server deployment matches your local time. |
| server_name | localhost:5000 | Required to build URLs for tables and graphs when made on startup. Defaults to a suitable local deployment value if not specified. |
| |  | 										   |
| PORT | 10000 | *Render Deployment only* - shouldn't be needed, but moving to 10000 and specifying to the build system seems to facilitate deployment. |
| PYTHON_VERSION | 3.11.2 | *Render Deployment only* - certain packages need newer Python versions. For example, use at least 3.8 for Quart. |