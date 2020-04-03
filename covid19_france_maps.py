#!/usr/bin/env python
# coding: utf-8

# In[29]:


from covid19_france_charts import import_data
import pandas as pd
from tqdm import tqdm
import json
import plotly.express as px
from datetime import datetime
import imageio
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


# ## Data import

# In[7]:


df, df_confirmed, dates = import_data()


# In[11]:


dict_insee = pd.read_excel('data/france/deces_quotidiens_departement.xlsx', header=[3], index_col=None, sheet_name=None, usecols='A:H', nrows=31)
dict_insee.pop('France sauf 13')
dict_insee.pop('Documentation')

for key in dict_insee:
    dict_insee[key]["dep"] = [key for i in range(len(dict_insee[key]))]
    
df_insee = pd.concat(dict_insee)
df_insee = df_insee.rename(columns={"Total des décès (2)": "dc20", "Total des décès (2).1": "dc19", "Total des décès (2).2": "dc18", "Date d'événement": "jour"})
df_insee = df_insee.drop(columns=['Remontées dématérialisées (1) (*)', 'Remontées dématérialisées (1) (**)', 'Remontées dématérialisées (1) (*)', 'Remontées dématérialisées (1)', 'Taux de dématérialisation   (1)/(2)'])
df_insee["moy1819"] = (df_insee["dc19"] + df_insee["dc20"])/2
df_insee["surmortalite20"] = (df_insee["dc20"] - df_insee["moy1819"])/df_insee["moy1819"]*100
df_insee['jour'] = pd.to_datetime(df_insee['jour'])
df_insee['jour'] = df_insee['jour'].dt.strftime('%Y-%m-%d')

dates_insee = list(dict.fromkeys(list(df_insee.dropna()['jour'].values))) 


# <br>
# <br>
# 
# ## Function definition

# In[18]:


with open('data/france/dep.geojson') as response:
    depa = json.load(response)
    
def map_gif(dates, imgs_folder, df, type_ppl, legend_title, min_scale, max_scale, colorscale, subtitle):
    i=1
    for date in tqdm(dates):
        if max_scale == -1:
            max_scale = df[type_ppl].max()
        df_map = pd.melt(df, id_vars=['jour','dep'], value_vars=[type_ppl])
        df_map = df_map[df_map["jour"] == date]

        data={}
        for dep in df_map["dep"].values:
            data[dep] = df_map[df_map["dep"] == dep]["value"]

        fig = px.choropleth(geojson=depa, 
                            locations=df_map['dep'], 
                            color=df_map['value'],
                            color_continuous_scale = colorscale,
                            range_color=(min_scale, max_scale),
                            featureidkey="properties.code",
                            scope='europe',
                            labels={'color':legend_title}
                                  )
        date_title = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B')
        
        fig.update_geos(fitbounds="locations", visible=False)
        
        var_hab = 'pour 100k. hab.'
        pourcent = ''
        
        val_mean = round(df_map['value'].mean(), 1)
        
        n = len(dates)
        progressbar = i * '█' + (n-i) * '░'
        i += 1
        
        if type_ppl == 'surmortalite20':
            var_hab = ''
            pourcent = " %"
            if val_mean < 0:
                val_mean = "– " + str(abs(val_mean))
            else:
                val_mean = "+ " + str(val_mean)
                
        val_mean = str(val_mean).replace(".", ",")
        
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            title={
            'text': "{}".format(date_title),
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
            titlefont = dict(
            size=30),
            annotations = [
                dict(
                    x=0.54,
                    y=0.08,
                    xref='paper',
                    yref='paper',
                    xanchor = 'center',
                    text='Source : INSEE. Auteur : @guillaumerozier.',
                    showarrow = False
                ),
                dict(
                    x=0.54,
                    y=0.03,
                    xref = 'paper',
                    yref = 'paper',
                    text = progressbar,
                    xanchor = 'center',
                    showarrow = False,
                    font=dict(
                        size=14
                            )
                ),
                dict(
                    x=0.07,
                    y=0.47,
                    xref='paper',
                    yref='paper',
                    xanchor='left',
                    text='Moyenne France',
                    showarrow = False,
                    font=dict(
                        size=14
                            )
                ),
                dict(
                    x=0.07,
                    y=0.50,
                    xref='paper',
                    yref='paper',
                    xanchor='left',
                    text='{}{}'.format(val_mean, pourcent),
                    showarrow = False,
                    font=dict(
                        size=25
                            )
                ),
                
                dict(
                    x=0.07,
                    y=0.45,
                    xref='paper',
                    yref='paper',
                    xanchor='left',
                    text = var_hab,
                    showarrow = False,
                    font=dict(
                        size=14
                            )
                ),
                dict(
                    x=0.55,
                    y=0.9,
                    xref='paper',
                    yref='paper',
                    text=subtitle,
                    showarrow = False,
                    font=dict(
                        size=20
                            )
                )]
             ) 
        
        fig.update_geos(
            #center=dict(lon=-30, lat=-30),
            projection_rotation=dict(lon=12, lat=30, roll=8),
            #lataxis_range=[-50,20], lonaxis_range=[0, 200]
        )
        fig.write_image(imgs_folder.format(date), scale=1, width=900, height=700)


def build_gif(file_gif, imgs_folder, dates):
    i=0
    with imageio.get_writer(file_gif, mode='I', duration=0.3) as writer: 
        for date in tqdm(dates):
            image = imageio.imread(imgs_folder.format(date))
            writer.append_data(image)
            i+=1
            if i==len(dates):
                for k in range(4):
                    writer.append_data(image)


# <br>
# 
# <br>
# 
# <br>
# 
# <br>
# 
# ## Function calls

# In[30]:


# GIF carte nb réanimations par habitant
imgs_folder = "images/charts/france/dep-map-img/{}.png"
sub = 'Nombre de <b>personnes en réanimation</b> <br>par habitant de chaque département.'
map_gif(dates, imgs_folder, df = df, type_ppl = "rea_deppop", legend_title="réan./100k hab", min_scale = 0, max_scale=-1, colorscale ="Reds", subtitle=sub)
build_gif(file_gif = "images/charts/france/dep-map.gif", imgs_folder = "images/charts/france/dep-map-img/{}.png", dates=dates)


# In[ ]:



# GIF carte décès cumulés par habitant
imgs_folder = "images/charts/france/dep-map-img-dc-cum/{}.png"
sub = 'Nombre de <b>décès cumulés</b> <br>par habitant de chaque département.'
map_gif(dates[1:], imgs_folder, df = df, type_ppl = "dc_deppop", legend_title="décès/100k hab", min_scale = 0, max_scale=-1, colorscale ="Reds", subtitle=sub)
build_gif(file_gif = "images/charts/france/dep-map-dc-cum.gif", imgs_folder = "images/charts/france/dep-map-img-dc-cum/{}.png", dates=dates[1:])


# In[ ]:


# GIF carte décès quotidiens 
imgs_folder = "images/charts/france/dep-map-img-dc-journ/{}.png"
sub = 'Nombre de <b>décès quotidien</b> <br>par habitant de chaque département.'
map_gif(dates[1:], imgs_folder, df = df, type_ppl = "dc_new_deppop", legend_title="décès/100k hab", min_scale = 0, max_scale=-1, colorscale ="Reds", subtitle=sub)
build_gif(file_gif = "images/charts/france/dep-map-dc-journ.gif", imgs_folder = "images/charts/france/dep-map-img-dc-journ/{}.png", dates=dates[1:])


# In[ ]:


# INSEE
# GIF mortalité par rapport à 2018 et 2019
imgs_folder = "images/charts/france/dep-map-surmortalite-img/{}.png"
ppl = "surmortalite20"
sub = 'Comparaison de la <b>mortalité journalière</b> entre 2020 <br>et les deux années précédentes.'
map_gif(dates_insee, imgs_folder, df = df_insee.dropna(), type_ppl = ppl, legend_title="Sur-mortalité (%)", min_scale=-80, max_scale=80, colorscale = ["green", "white", "red"], subtitle = sub)
build_gif(file_gif = "images/charts/france/dep-map-surmortalite.gif", imgs_folder = imgs_folder, dates=dates_insee)

