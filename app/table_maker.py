import pandas as pd
from pathlib import Path
from quart import url_for

pd.options.mode.chained_assignment = None


# Cats, Dogs by Organization for home page
async def home_table(orgs, adopt, path):    
    x = orgs[['name','Dog','Cat']]
    sums = {'dog': x['Dog'].sum(), 'cat': x['Cat'].sum()}
    x.rename(columns={'Dog':f'Dogs &#128054; {sums["dog"]}',
                      'Cat':f'Cats &#128008; {sums["cat"]}', 
                      'name':'Organization'}, 
             inplace=True)
    x.index.rename('CO Pet Page', inplace=True)
    x.style\
.background_gradient(subset=[f'Dogs &#128054; {sums["dog"]}'], cmap='Greens', 
                     vmin=0, low=0.1)\
.background_gradient(subset=[f'Cats &#128008; {sums["cat"]}'], cmap='Purples', 
                     vmin=0, low=0.1)\
.format(lambda v: 
  f'<a class="btn btn-sm btn-primary"\
    href="{orgs[orgs["name"]==v].website.values[0]}">{v}\
    [{orgs[orgs["name"]==v].address.values[0]}]</a>\
    ',
  subset='Organization')\
.format_index(lambda v: 
  f'<a class="btn btn-sm btn-info" href="{url_for("org",org_id=v)}">{v}</a>')\
.set_table_styles([
            {'selector': 'td:hover',
             'props': 'background-color: #e9967a; color:#2f4f4f;'},
            {'selector': 'td', 
             'props': 'font-size:1.25em;font-weight:bold;text-align:center;'}
                        ])\
.to_html(buf=Path(path,'home_org_pet_count.html'), table_attributes = \
 'class="table table-dark table-bordered"')


# all data formatted for table page
async def big_table(orgs, adopt, path, table_url):
    adopt.index.rename(table_url, inplace=True)
    adopt.style\
.format(na_rep="")\
.format(lambda v: 
        f'<a class="btn btn-sm btn-info" href="{url_for("org", org_id=v)}">{v}</a>', 
        subset='orgID')\
.format(lambda v: 
        f'<a href="{orgs[orgs["name"]==v].website.values[0]}">{v}</a>', 
        subset='org')\
.format(lambda v: 
        f'<a class="btn btn-sm btn-primary" href="{v}">Adopt</a>', subset='URL')\
.format(lambda v: '&#128054;' if v=='Dog' else '&#128008;', subset='species')\
.format(lambda v: '&#10004;' if v else ('&#10060;' if v==False else ''), 
        subset=adopt.columns[11:20])\
.format(lambda v: ', '.join([f'<a href={val}>{i}</a>' for i,val in \
        enumerate(v.split(' | '))]), subset=['pics_thumb','pics_full'])\
.format(lambda v: pd.to_datetime(v).strftime('%x %X'), subset='updated')\
.format_index(lambda v:f'{adopt.loc[v,"name"]} |\
    <a class="btn btn-sm btn-info mb-1" href="{url_for("pet_page",pet_id=v)}">{v}</a>\
    <img src="{adopt.loc[v,"pics_thumb"].split(" | ")[0]}" />')\
.set_table_styles([
    {'selector': 'td:hover','props': 'color:#e9967a;'},
    {'selector': 'td','props': 'font-weight:bold;text-align:center;'}
                 ])\
.to_html(buf = Path(path,'all_pets_table.html'), table_attributes = \
    'class="table table-sm table-dark table-bordered table-hover align-middle"')      


# raw data in various file types, user can save from table page
async def export_saver(adopt, root_path, logger):
    folder = Path(root_path, 'static','data_exports')
    folder.mkdir(exist_ok=True)
    
    adopt.to_csv(Path(folder, 'adopt.csv'))
    adopt.to_excel(Path(folder, 'adopt.xlsx'))
    try:
        adopt.to_xml(Path(folder, 'adopt.xml'))
    except Exception as e:
        logger.warning(e)
    adopt.to_html(Path(folder, 'adopt.html'))


# wrapper function for above
async def table_maker(orgs, adopt, save_path, root_path, table_url, logger):
    
    # folder in static directory    
    save_path.mkdir(exist_ok=True)

    # 1) Export data to various formats for user download
    await export_saver(adopt, root_path, logger)    
    # 2) Organization cats/dogs count for home page
    await home_table(orgs, adopt, save_path)
    # 3) Big Table - all pets
    await big_table(orgs, adopt, save_path, table_url)




    
