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
cd app && hypercorn home:app -b 0.0.0.0:10000 --log-file="-" --access-logformat='%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
```

**Environmental Variables**

 - `client_id`
 - `client_secret`
 - `server_name`
 - `location`
 - `TZ`
 - `PORT`
 - `PYTHON_VERSION`

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