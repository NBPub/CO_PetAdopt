import pandas as pd
import requests
from datetime import datetime, timedelta


# Request Authorization token for API calls, lasts one hour
async def token_request(client_id, client_secret, logger):
    URL = 'https://api.petfinder.com/v2/oauth2/token'
    params = {  # authorization, time marker for expiry
    'grant_type':'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret
            }
    stamp = datetime.now()
    
    # request token
    r = requests.post(URL, data=params)
    if r.status_code == 200:
        token = r.json()
        token['start_time'] = stamp
        token['expire_time'] = stamp + timedelta(minutes=60)
        logger.info(\
'Acess token granted, expires at %s', token['expire_time'].strftime('%x %X'))   
    else:
        logger.warning('Failed to retrieve authorization token! \
status code: %s', r.status_code)
        try: # successful, but bad, request. provide error message
            err = r.json()
            logger.warning('\t%s: %s', err['title'], err['hint'])
        except:
            pass
        token = r.status_code      
    return token


# Get list of organizations in specified location, then list of pets from orgs
async def petfinder_request(token, org_path, adopt_path, location, logger):
    # Make folder if needed
    org_path.parent.mkdir(exist_ok=True)

    # add token information to header for authorization
    auth = {'Authorization': f"{token['token_type']} {token['access_token']}"}
    
    # Organizations endpoint
    URL = 'https://api.petfinder.com/v2/organizations?'
    params = {'location':location, 'sort':'distance', 'limit':100}
    URL = f"{URL}{'&'.join([f'{key}={val}' for key,val in params.items()])}"
    
    # could include check to see if requests within time limit
    # if datetime.now() < token['expire_time']:
    r = requests.get(URL, headers=auth)
    
    if r.status_code != 200:
        organizations = pd.DataFrame()
        logger.warning('Failed retrieving organizations from petfinder. \
status code: %s', r.status_code)
    else:
        organizations = r.json()['organizations']
    
    # Organizations to DataFrame, drop no website, extract city from address
        organizations = pd.DataFrame(organizations).set_index('id')
        organizations.dropna(subset='website', inplace=True)
        organizations.address = [addr.get('city') for addr in organizations.address]
        organizations.drop(columns = ['hours','url','distance','_links'], 
                           inplace=True)        
        logger.info('%s adoption organizations found', organizations.shape[0])
       
   
    # Adoptable Pets endpoint
    URL = 'https://api.petfinder.com/v2/animals?'
    params = {'organization':','.join(organizations.index), 'status':'adoptable',
              'page':1, 'limit':100}    
    animals = []
    failcount = 0 # prevent continous failed requests, allow up to 5
    
    # Max 100 pets returned per request, repeat until all pets added
    while datetime.now() < token['expire_time']:
        URL = f"{URL}{'&'.join([f'{key}={val}' for key,val in params.items()])}"
        r = requests.get(URL, headers=auth)
        
        if r.status_code !=200:
            logger.warning('Failed retrieving pets from petfinder, Page %s. \
status code: %s', params["page"], r.status_code)            
            if params['page'] == 0:
                logger.warning('Terminating Petfinder requests')
                break
            failcount += 1
            logger.warning('%s out of 5 allowed failures', failcount)
            continue
        
        animals.extend(r.json()['animals'])
        params['page'] += 1       
        if len(r.json()['animals']) < 100 or failcount > 4:
            break
    
    logger.info('%s adoptable pets found,', len(animals))
    
    # return empty for failed requests
    if not animals:
        return pd.DataFrame(), organizations
    
    # Pets to DataFrame
    adopt = pd.DataFrame(columns = [
        'orgID', 'org', 'URL', 'species','gender','age','size','coat', 
        'colors', 'breed_1', 'breed_2', 'breed_mixed',
        'env_children', 'env_dogs', 'env_cats', 'spayed_neutered',
        'house_trained', 'declawed', 'special_needs', 'shots_current', 
        'tags', 'name','description', 'pics_thumb', 'pics_full', 'updated'])    

    for pet in animals: # could do JSON --> DataFrame flat conversion instead
        ind = pet['id']
        adopt.loc[ind, 'orgID'] = pet.get('organization_id')
        if pet.get('organization_id') in organizations.index:
            adopt.loc[ind, 'org'] = \
                organizations.loc[pet.get('organization_id'),'name']
        adopt.loc[ind, 'URL'] = pet.get('url')
        adopt.loc[ind, 'name'] = pet.get('name')
        adopt.loc[ind, 'description'] = pet.get('description')

        adopt.loc[ind, 'species'] = pet.get('species')
        
        adopt.loc[ind, 'gender'] = pet.get('gender')
        adopt.loc[ind, 'age'] = pet.get('age')
        adopt.loc[ind, 'size'] = pet.get('size')
        adopt.loc[ind, 'coat'] = pet.get('coat')
        
        adopt.loc[ind, 'colors'] = ' / '.join(
            [val for val in pet.get('colors').values() if val])
        
        adopt.loc[ind, 'breed_1'] = pet.get('breeds').get('primary')
        adopt.loc[ind, 'breed_2'] = pet.get('breeds').get('secondary')
        adopt.loc[ind, 'breed_mixed'] = pet.get('breeds').get('mixed')

        adopt.loc[ind, 'env_children'] = pet.get('environment').get('children')
        adopt.loc[ind, 'env_dogs'] = pet.get('environment').get('dogs')
        adopt.loc[ind, 'env_cats'] = pet.get('environment').get('cats')
        
        adopt.loc[ind, 'spayed_neutered'] = pet.get('attributes').get('spayed_neutered')
        adopt.loc[ind, 'house_trained'] = pet.get('attributes').get('house_trained')
        adopt.loc[ind, 'declawed'] = pet.get('attributes').get('declawed')
        adopt.loc[ind, 'special_needs'] = pet.get('attributes').get('special_needs')
        adopt.loc[ind, 'shots_current'] = pet.get('attributes').get('shots_current')

        adopt.loc[ind, 'tags'] = ' | '.join(pet.get('tags'))
                                          
        adopt.loc[ind, 'pics_thumb'] = ' | '.join([photo.get('medium') 
                                       for photo in pet.get('photos')])
        adopt.loc[ind, 'pics_full'] = ' | '.join([photo.get('full') 
                                       for photo in pet.get('photos')])
                                          
        adopt.loc[ind, 'updated'] = pet.get('status_changed_at')
    
    # Add dogs/cats to orgs, remove those with 0 total
    if not organizations.empty and not adopt.empty:            
        counts = pd.DataFrame(adopt.value_counts(['orgID','species']))                      
        for ind in counts.index:
            organizations.loc[ind[0],ind[1]] = counts.loc[ind,'count']   
        organizations.dropna(subset=['Dog','Cat'], how='all', inplace=True)
        organizations[['Dog','Cat']] = organizations[['Dog','Cat']]\
                                                    .fillna(0).astype('int')   
                                                                                                    
    # Save Files
    adopt.to_parquet(adopt_path)
    organizations.to_json(org_path)
    logger.info('. . . processed data saved')     
    
    return adopt, organizations 