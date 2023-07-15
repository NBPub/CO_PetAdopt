import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
from wordcloud import WordCloud

pd.options.mode.chained_assignment = None

# 1) Cat/Dog count vs Age
async def age_count(adopt, updated, params, path, url_stamp):    
    with mpl.rc_context(params):
        plt.figure(figsize=(4,6))
        sns.histplot(data = adopt, y = 'age', hue='species', 
                     hue_order=['Cat','Dog'], element='step',multiple='layer', 
                     palette=['purple','green'])
        plt.ylabel('Pet Age')
        plt.xlabel('Adoptable Pets')
        plt.title('Pets by Age')
        plt.text(plt.xlim()[1], plt.ylim()[1]-0.22, updated, 
                 color='khaki', ha='right', va='top', size='small')
        plt.text(plt.xlim()[0], plt.ylim()[1]-0.22, url_stamp, 
                 color='salmon', ha='right', va='top', size='small')
        plt.savefig(Path(path,'home_count_vs_age.png'))
        plt.close()    


# 2) Dog Breed Mixes / Counts --> may nix
async def dog_breeds(dogs, updated, params, path, url_stamp):
    # remove "Dog" from breed names
    dogs['breed_1'] = dogs.breed_1.str.replace('Dog', '').str.rstrip()\
                                  .str.replace('  ',' ')
    dogs['breed_2'] = dogs.breed_2.str.replace('Dog', '').str.rstrip()\
                                  .str.replace('  ',' ')                                  
    
    # Get top 3s for graph text
    top3 = pd.DataFrame(dogs[dogs.breed_2.isnull()].value_counts('breed_1')[:3])
    top3txt1 = '\n'.join([f'{ind} ~ {top3.loc[ind,"count"]}' for ind in top3.index])
       
    breed_count = pd.DataFrame(\
index = pd.Series(np.append(dogs.breed_1.unique(),dogs.breed_2.unique())).unique(),
columns = ['count'])
    for ind in breed_count.index:
        breed_count.loc[ind,'count'] = \
        dogs[dogs.breed_1==ind].shape[0] + dogs[dogs.breed_2==ind].shape[0] 
    breed_count['count'] = breed_count['count'].astype('int')
    breed_count = breed_count.sort_values('count',ascending=False)[:3]
    top3txt2 = '\n'.join([f'{ind} ~ {breed_count.loc[ind,"count"]}' \
               for ind in breed_count.index])
    del breed_count, top3
    # graph
    with mpl.rc_context(params):
        sns.histplot(data = dogs[dogs.breed_2.notnull()], y = 'breed_1', 
                     x='breed_2', cmap='YlGn', shading='auto', 
                     edgecolors='face', cbar=True)
        plt.xticks(rotation=-85, size='small', fontweight='bold')
        plt.yticks(size='small', fontweight='bold')
        plt.ylabel('Primary')
        plt.xlabel(\
f'Secondary ({dogs.breed_2.notnull().sum()} out of {dogs.shape[0]} dogs)')
        plt.title('Dog Breeds', color='lightgreen', 
                  fontweight='bold')
        plt.text(plt.xlim()[1], plt.ylim()[1]-1, updated, color='khaki',
                 ha='right', va='top')
        plt.text(plt.xlim()[0], plt.ylim()[1]-1, url_stamp, color='salmon',
                 ha='right', va='top')        
        plt.text(plt.xlim()[0]*1.1, plt.ylim()[0]*1.11, 
                 f"Top 3 no secondary breed: \n{top3txt1}", 
                 color='#7fff00', ha='right', va='top')
        plt.text(plt.xlim()[0]*1.1, plt.ylim()[0]*1.4, 
                 f"Top 3 overall: \n{top3txt2}", 
                 color='#7fff00', ha='right', va='top')    
        
        plt.grid(linewidth=0.5, color='#505050')    
        plt.savefig(Path(path,'home_dog_breeds.png'))     
        plt.close()    


# 3) Word Cloud - pet tags
async def tag_cloud(adopt, updated, font, path, url_stamp):
    tags = []
    for pet_tags in adopt.tags:
        words = pet_tags.split(' | ')
        tags.extend([word.replace(' ','') for word in words if word])
    
    tags = tags*10
    tags = ' '.join(tags)   
    plt.figure(figsize=(10,10), facecolor='#696969')
    wordcloud = WordCloud(colormap='viridis_r',min_font_size=12, 
                          background_color='#696969', width=800, height=800, 
                          font_path=str(font), prefer_horizontal=0.7)
    wordcloud.generate(tags)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")   
    plt.text(plt.xlim()[1], plt.ylim()[1], updated, color='salmon',
             ha='right', va='top', fontsize='large', fontweight='bold')
    plt.text(plt.xlim()[0], plt.ylim()[1], url_stamp, color='salmon',
                 ha='left', va='top', fontsize='large', fontweight='bold')
    plt.tight_layout(pad=0.2)
    plt.savefig(Path(path,'home_pet_tags_cloud.png')) 
    plt.close()    


# 3) Word Cloud - cat colors, dog colors
async def color_clouds(adopt, updated, font, path, url_stamp):
    for pet_type in ['Cat','Dog']:
        color_list = []
        for pet_color in adopt[adopt.species == pet_type].colors:
            words = pet_color.split(' / ')
            color_list.extend([word for word in words if word])
        color_list = ' '.join(color_list)
        color_list = color_list*5 
        
        plt.figure(figsize=(10,10), facecolor='#696969')
        wordcloud = WordCloud(colormap='viridis_r',min_font_size=20, 
                          background_color='#696969', width=800, height=800, 
                          font_path=str(font), prefer_horizontal=0.7)  
        wordcloud.generate(color_list)
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")    
        plt.text(plt.xlim()[1], plt.ylim()[1], updated, color='salmon',
                 ha='right', va='top', fontsize='large', fontweight='bold')
        plt.text(plt.xlim()[0], plt.ylim()[1], url_stamp, color='salmon',
                 ha='left', va='top', fontsize='large', fontweight='bold')        
        plt.tight_layout(pad=0.2)
        plt.savefig(Path(path,f'home_{pet_type.lower()}_colors_cloud.png')) 
        plt.close()    



async def graph_maker(adopt, save_path, data_updated, url_stamp):
    
    # folder in static directory
    save_path.mkdir(exist_ok=True)
    url_stamp = url_stamp[:-4]
    
    # style settings
    sns.set_style('darkgrid')
    rc_params = {
'figure.figsize':(6,4),'figure.facecolor':'grey', 'grid.linewidth':2,
'axes.titlesize':'large','axes.titlecolor':'gainsboro', 
'axes.titleweight':'bold', 'axes.labelsize':'x-large', 
'axes.labelcolor':'gainsboro', 'axes.labelweight':'bold',
'xtick.labelcolor':'white','xtick.labelsize':'large',
'ytick.labelcolor':'white','ytick.labelsize':'large',
'savefig.bbox':'tight','savefig.dpi':300,
    }
    data_updated = data_updated.strftime('%x %X')
    font_path = Path(save_path.parent, 'fonts', 'DejaVuSansCondensed-Bold.ttf')
    
    # Basics: 
    # 1) Cat/Dog count vs Age
    await age_count(adopt, data_updated, rc_params, save_path, url_stamp)    
    # 2) Dog Breed Mixes / Counts --> may nix
    await dog_breeds(adopt[(adopt.species=='Dog')], data_updated, rc_params,
                    save_path, url_stamp)        
    # Word Clouds  
    # 3) All tags
    await tag_cloud(adopt, data_updated, font_path, save_path, url_stamp)  
    # 4) Cat, Dog Colors
    await color_clouds(adopt, data_updated, font_path, save_path, url_stamp) 