import pandas as pd
import random

df = pd.read_csv('sales_modified4.csv')
data=pd.read_csv("driver.csv")

# neighbourhood_coordinates = {
#     "Dongmyeon": (37.8891, 127.8446),
#     "Hyoja 3-dong": (37.8712, 127.7234),
#     "Hupyeong 1-dong": (37.88808609419926, 127.74569940448187),
#     "Hupyeong 2-dong": (37.87717030678474, 127.74815651853106),
#     "Seoksa-dong": (37.860064545776545, 127.75035599944543),
#     "Soyang-dong": (37.88449408540045, 127.72697668947013),
#     "Toegye-dong": (37.855455790945335, 127.73142623358554),
#     "Hupyeong 3-dong": (37.877472625707476, 127.75453174424321),
#     "Shin Sa Udon": (37.92462383066562, 127.7287004840907),
#     "Gangnam-dong": (37.86022705370432, 127.70133893486938),
#     "Hyoja 1-dong": (37.87227577164343, 127.72779143769736),
#     "Jo-un-dong": (37.878982978826805, 127.73130584113493),
#     "Gyo-dong": (37.882668947285346, 127.7367755218248),
#     "Yagsamyeong-dong": (37.876440197049874, 127.72461621981417),
#     "Geunhwa-dong": (37.885922819917226, 127.7145607594234),
#     "Dongnae-myeon": (37.84176039671483, 127.78319181349737),
#     "Sindong-myeon": (37.81356268642998, 127.70622987784363),
# }

neighborhood = {
    'City Centre': (51.455084, -2.591765),
    'Clifton': (51.455280, -2.619340),
    'Cotham': (51.464000, -2.598000),
    'Montpelier': (51.468000, -2.589000),
    'Stokes Croft': (51.462000, -2.590000),
    'Gloucester Road': (51.476000, -2.592000),
    'Bedminster': (51.440000, -2.600000),
    'Southville': (51.442000, -2.606000),
    'Easton': (51.463000, -2.561000),
    'St George': (51.464000, -2.548000),
    'Barton Hill': (51.454000, -2.570000),
    'Lawrence Hill': (51.457000, -2.574000),
    'Redfield': (51.459000, -2.558000),
    'Totterdown': (51.442000, -2.576000),
    'Kingsdown': (51.462000, -2.598000),
    'Ashley Down': (51.478000, -2.583000),
    'Old Market': (51.456000, -2.582000),
    'Brislington': (51.441000, -2.535000)
}

#REPLACE THIS WITH BRISTOL LOCATIONS 
location = []

for index, row in df.iterrows():
    place = row['place']
    if place in neighborhood:
        latitude, longitude = neighborhood[place]
        variation = 0.001
        new_lat = latitude +  random.uniform(-variation, variation)
        new_long = longitude + random.uniform(-variation, variation)
        location.append((f"{new_lat}, {new_long}"))
        #changed the format as was having a problem 
        #with the brackets when transferring to the database
  

df['location'] = location

#removes brackets
df['product_names'] = df['product_names'].str.strip('[]')
#removes ''
df['product_names'] = df['product_names'].replace({"'": "", '"': ""}, regex=True) 


list1=df['location'].unique()
print(len(list1))
df.to_csv('sales_modified4.csv', index=False)
print("location column added")
