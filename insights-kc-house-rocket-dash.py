
# bibliotecas
import pandas as pd
import numpy as np
import plotly.express as px
from matplotlib import pyplot as plt
import streamlit as st
from datetime import datetime



# definindo formato de exibição
pd.set_option('display.float_format', lambda x: '%.2f' % x)
plt.rcParams['figure.figsize'] = (11, 7)



@st.cache(allow_output_mutation=True)
def get_data(path):
    data = pd.read_csv(path)
    return data

def config_feature(data):
    # Verificando valores nulos
    data.isnull().sum()

    # Retirando os valores em branco
    data.dropna(how='any', inplace=True)

    # Removendo atributos que não agregam à solução do problema
    data = data.drop(columns=['sqft_living15', 'sqft_lot15'])

    # Removendo registros duplicados
    data = data.drop_duplicates(subset='id')

    return data

def overview_data(data):

    st.title('House Rocket 🏠')
    st.write('House Rocket is a fictional real estate company that wants to use data science to'
             'your favor to find better business opportunities. '
             'The Companys Core Business is to buy real estate at a '
             'low price to resell it at a higher price and thus guarantee a profit.\n\n'
             'The Dashboard below will present alternatives for decision making, as well as hypotheses for insights '
             'taken from the available data.\n\n')

    st.title('Statistic Descriptive')
    # Estatística descritiva
    num_attributes = data.select_dtypes(include=['int64', 'float64'])




    # Tendencia central
    media = pd.DataFrame(num_attributes.apply(np.mean))
    mediana = pd.DataFrame(num_attributes.apply(np.median))
    std = pd.DataFrame(num_attributes.apply(np.std))

    # Dispersão
    std = pd.DataFrame(num_attributes.apply(np.std))
    max_ = pd.DataFrame(num_attributes.apply(np.max))
    min_ = pd.DataFrame(num_attributes.apply(np.min))

    df1 = pd.concat([max_, min_, media, mediana, std], axis=1).reset_index()
    df1.columns = ['attributes', 'mean', 'median', 'std', 'max', 'min']

    st.dataframe(df1)

    return df1

def add_feature(data):
    #  Transformações de datas
    data['year'] = 'NA'
    data['week_of_year'] = 'NA'
    data['month'] = 'NA'
    data['day'] = 'NA'
    data['date'] = pd.to_datetime(data['date'], format="%Y-%m-%d")
    data['date_'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
    data['year'] = data['date'].dt.year
    data['week_of_year'] = data['date'].dt.isocalendar().week
    data['month'] = data.date.dt.strftime("%Y-%m")
    data['day'] = data['date'].dt.day
    data['bathrooms'] = data['bathrooms'].round(0).astype('int64')
    data['floors'] = data['floors'].astype('int64')

    # correção de outlier
    # O registro com 33 quartos é um erro de digitação,
    # considerando que os valores de preço, sala de estar, terreno e
    # numero de banheiros estão na média dos imóveis de 3 quartos

    data.loc[data['bedrooms'] == 33, 'bedrooms'] = 3

    # Adicionando novas variaveis
    data['house_age_buyed'] = data['year'].apply(lambda x: 'old_house' if x <= 2014 else 'new_house')
    data['is_waterfront'] = data['waterfront'].apply(lambda x: 'no' if x == 0 else 'yes')
    data['house_age'] = data['yr_built'].apply(lambda x: 'old_house' if x <= 2000 else 'new_house')
    data['periods'] = data['yr_built'].apply(lambda x: 'before 1955' if x < 1955 else 'after 1955')
    data['dormitory_type'] = data['bedrooms'].apply(lambda x: 'studio' if x == 1 else
    'apartament' if x == 2 else
    'house' if x > 2 else 'NA')

    data['condition_type'] = data['condition'].apply(lambda x: 'bad' if x <= 2 else
    'regular' if (x == 3) | (x == 4) else
    'good')

    data['seasons'] = data['date'].apply(lambda x: 'Spring' if (x.day_of_year > 80) & (x.day_of_year <= 173) else
    'Summer' if (x.day_of_year > 173) & (x.day_of_year <= 267) else
    'Fall' if (x.day_of_year > 267) & (x.day_of_year <= 356) else
    'Winter')

    # Calculando a mediana
    price_median = data[['price', 'zipcode']].groupby('zipcode').median().reset_index()
    price_median = price_median.rename(columns={'price': 'region_price_median'})

    data = pd.merge(data, price_median, how='inner', on='zipcode')

    # Condicional de compra
    data['action'] = data[['price', 'region_price_median', 'condition']].apply(
        lambda x: 'buy' if (x['price'] < x['region_price_median']) & (x['condition'] >= 3)
        else 'dont buy', axis=1)

    # Condicional de venda
    data['sale_price'] = data[['action', 'price', 'region_price_median' ]].apply(
        lambda x: x['price'] * 1.3 if (x['price'] < x['region_price_median']) & (x['action'] == 'buy')
        else x['price'] * 1.1 if (x['price'] > x['region_price_median']) & (x['action'] == 'buy')
        else x['price'], axis=1)

    ## Lucro
    data['gain'] = data['sale_price'] - data['price']


    return data

def metrics_data(data):

    data = data.copy()

    # Dataset final de media de preço + sazonalidade

    df6 = data[['id', 'zipcode', 'price', 'lat','long','seasons', 'condition_type',
              'dormitory_type', 'house_age','year','yr_built', 'region_price_median',
              'action', 'sale_price', 'gain','is_waterfront', 'periods', 'sqft_basement', 'sqft_lot', 'bathrooms',
              'month', 'waterfront', 'date_' , 'date', 'grade' ]].sort_values(by='gain', ascending=False)



    st.sidebar.header('Menu Option')

    f_attributes = st.sidebar.multiselect('Enter coluns', df6.columns)
    f_zipcode = st.sidebar.multiselect('Enter zipcode', df6['zipcode'].unique())

    if (f_zipcode != []) & (f_attributes != []):
        df6 = df6.loc[df6['zipcode'].isin(f_zipcode), f_attributes]
    elif (f_zipcode != []) & (f_attributes == []):
        df6 = df6.loc[df6['zipcode'].isin(f_zipcode), :]
    elif (f_zipcode == []) & (f_attributes != []):
        df6 = df6.loc[:, f_attributes]
    else:
        df6 = df6.copy()

    st.title(' Data Overview')
    st.subheader('What properties should house rocket buy and at what price?')

    csv = df6.to_csv().encode('utf-8')
    st.download_button(
        label="Data Overview",
        data=csv,
        file_name='Data-Overview.csv',
        mime='text/csv',
    )
    st.dataframe(df6)

    st.header('Gain per Seasons')
    st.write('Once the property has been purchased, when is the best time to sell it and at what price?\n')
    st.write('If the purchase price is greater than the region median + seasonality:\n'
             ' - The sale price will be equal to the purchase price + 10%\n'
             'If the purchase price is less than the region median + seasonality\n'
             ' - The purchase price will be equal to the purchase price + 30%')

    fig = px.bar(df6[['seasons', 'price', 'sale_price', 'gain', 'lat', 'long']].groupby('seasons').sum().reset_index(),
                 x='seasons', y='gain', color='seasons', template='simple_white', text_auto='.3s',
                 # color_continuous_scale= "Purpor"
                 )
    st.plotly_chart(fig, use_container_width=True)


    return df6


def draw_map(data):
    # map
    houses = data[['id', 'price',  'lat','action', 'long']].copy()
    st.title('Suggestions Houses Buy Per Region')
    fig = px.scatter_mapbox( houses,
                             lat="lat",
                             lon="long",
                             color="action",
                             size="price",
                             color_continuous_scale=px.colors.cyclical.IceFire,
                             size_max=15,
                             zoom=10)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(height=600, margin={"r":0,"t":0,"l":0,"b":0})

    return fig

def commercial_distribution(data):
    st.sidebar.title('Commercial Options')


    # Avg Price per Year
    #filters
    min_year_built = int(data['yr_built'].min())
    max_year_built = int(data['yr_built'].max())

    st.sidebar.subheader('Select Max Year Built')
    f_year_built = st.sidebar.slider('Year Built', min_year_built,
                                                   max_year_built,
                                                   max_year_built)

    st.header('Average Price per Year Built')

    #data selection
    df = data.loc[data['yr_built'] < f_year_built]
    df = df[['yr_built', 'price']].groupby('yr_built').mean().reset_index()

    #plot
    fig= px.line(df,x='yr_built', y='price')
    st.plotly_chart(fig, use_container_width=True)


    # Avg Price per Day
    #filters
    min_date = datetime.strptime(data['date_'].min(), '%Y-%m-%d')
    max_date = datetime.strptime(data['date_'].max(), '%Y-%m-%d')

    st.sidebar.subheader('Select Max Date')
    f_date = st.sidebar.slider('Date', min_date,
                                                   max_date,
                                                   max_date)

    st.header('Average Price per Day')

    #data selection
    data['date']= pd.to_datetime((data['date']))
    df = data.loc[data['date'] < f_date]
    df = df[['date', 'price']].groupby('date').mean().reset_index()

    #plot
    fig= px.line(df,x='date', y='price')
    st.plotly_chart(fig, use_container_width=True)


    # ----- Histograma


    st.header('Price Distribution')

    st.sidebar.subheader('Select Max Price')

    #filter
    min_price= int(data['price'].min())
    max_price= int(data['price'].max())
    avg_price= int(data['price'].mean())

    #data selection
    f_price = st.sidebar.slider('Price', min_price, max_price, avg_price)
    df = data.loc[data['price']< f_price]

    #plot
    fig= px.histogram(df,x='price', nbins=50)
    st.plotly_chart(fig, use_container_width=True)

    return None

#===================== hipotese =======================

def insights(df6):
    st.title('Business Insight')
    data= df6.copy()
    c1, c2 = st.columns(2)

    #H1

    c1.subheader('Hipótese 1:  Imóveis com vista para a água são em média mais caros')
    h1 = data[['is_waterfront','price']].groupby('is_waterfront').mean().reset_index()
    h1_percent = (h1.loc[1, 'price'] - h1.loc[0, 'price'])*100 / h1.loc[0, 'price']
    c1.write(f'Diferença percentual de preços: {round(h1_percent,)} %, então a '
             f'afirmativa é falsa porque esse valor é maior que 30%')
    fig2 = px.bar(h1, x='is_waterfront', y='price', color= "is_waterfront",
                  template='simple_white', text_auto='.3s',
                  )
    c1.plotly_chart(fig2, use_container_width=True)

    #H2
    c2.subheader('H2: Imóveis com data de construção menor que 1955, são 50% mais baratos, na média.')
    h2 = data[[ 'periods','price']].groupby('periods').mean().reset_index()
    h2_percent = (h2.loc[0, 'price'] - h2.loc[1, 'price'])*100 / h2.loc[0, 'price']
    c2.write(f'Diferença percentual de preços: {round(h2_percent,)}%, então a afirmativa é falsa porque esse valor'
             f' é menor que 50%')

    fig3 = px.bar(h2, x='periods', y='price', color= "periods",
                  template='simple_white', text_auto='.3s',
                  )
    c2.plotly_chart(fig3, use_container_width=True)

    #H3

    c3, c4 = st.columns(2)

    c3.subheader('H3: Imóveis sem porão possuem área total (sqrt_lot), são 50% maiores do que com porão.')
    data['basement'] = data['sqft_basement'].apply(lambda x: 'yes' if x!=0 else 'no')
    h3 = data[['basement','sqft_lot']].groupby('basement').mean().reset_index()
    h3_percent = (h3.loc[0, 'sqft_lot'] - h3.loc[1, 'sqft_lot'])*100 / h3.loc[0, 'sqft_lot']
    c3.write(f'Diferença percentual de preços: {round(h3_percent,)}%, então a afirmativa é falsa porque esse valor'
             f' é menor que 50%')

    fig4 = px.bar(h3, x='basement', y='sqft_lot', color= "basement",
                  template='simple_white', text_auto='.3s',
                  )
    c3.plotly_chart(fig4, use_container_width=True)

    #H4

    c4.subheader('H4: O crescimento do preço dos imóveis YoY ( Year over Year ) é de 10%')
    data['year_over_year'] = data['year'].apply(lambda x: '2014' if x!= 2015 else '2015')
    h4 = data[['year_over_year','price']].groupby('year_over_year').mean().reset_index()
    h4_percent = (h4.loc[1, 'price'] - h4.loc[0, 'price'])*100 / h4.loc[0, 'price']

    c4.write(f'Diferença percentual de preços: {round(h4_percent,)}%, então a afirmativa é falsa porque esse '
          f'valor é menor que 10%')

    fig5 = px.bar(h4, x='year_over_year', y='price', color= "year_over_year",
                  template='simple_white', text_auto='.3s',
                  )
    c4.plotly_chart(fig5, use_container_width=True)

    # Plot
    c5, c6 = st.columns((1, 1))

    #H5

    h5 = data.copy()
    c5.subheader('H5: Imóveis com 3 banheiros tem um crescimento MoM (Month over Month) de 15% em média')
    h5 = h5[h5['bathrooms'] == 3]  # Filtragem para imoveis com 3 banheiros
    h5 = h5[['bathrooms', 'month', 'price']].groupby('month').mean().reset_index()
    h5.drop(columns='bathrooms', inplace=True)
    h5_percent = (h5.loc[0, 'price'] - h5.loc[1, 'price'])*100 / h5.loc[0, 'price']

    c5.write(f'Diferença percentual de preços: {round(h5_percent,)}%, então a afirmativa é falsa porque esse '
          f'valor é menor que 10%')
    fig6 = px.line(h5, x='month', y='price',template='simple_white')
    c5.plotly_chart(fig6, use_container_width=True)

    #H6
    h61= data.copy()

    c6.subheader('H6: Os apartamentos com vista para o mar são em  média de 50% a 60% mais baratos do que as casas.')
    h6 = h61[((h61['dormitory_type'] == 'apartament') | (h61['dormitory_type'] == 'house')) & (h61['is_waterfront'] == 'yes') ]
    house = h6[['dormitory_type', 'is_waterfront', 'price']].groupby('dormitory_type').mean().reset_index()
    h6_percent = ((house.loc[1, 'price'] - house.loc[0, 'price'])*100 / house.loc[1, 'price'])

    c6.write(f'Diferença percentual de preços: {round(h6_percent,)}%, então a afirmativa é verdadeira porque esse '
          f'valor é está entre 50% e 60%')
    fig7 = px.bar(house, x='dormitory_type', y='price', color= "dormitory_type",
                  template='simple_white', text_auto='.3s',
                  )
    c6.plotly_chart(fig7, use_container_width=True)
    #Plot
    c7, c8 = st.columns((1, 1))
#
    ## H7
    h7 = data.copy()
    c7.subheader('H7: O valor de imoveis com vista para o mar no verão é 30% mais cara do que no inverno em média')
    h7 = h7[((h7['seasons'] == 'Summer') | (h7['seasons'] == 'Winter')) & (h7['is_waterfront'] == 'yes') ]
    h7.drop(columns='is_waterfront', inplace=True)
    h7 = h7[['seasons', 'price']].groupby('seasons').mean().reset_index()
    h7_percent = ((h7.loc[0, 'price'] - h7.loc[1, 'price'])*100 / h7.loc[1, 'price'])

    c7.write(f'Diferença percentual de preços: {round(h7_percent,)}%, então a afirmativa é verdadeira porque esse '
          f'valor é está entre 50% e 60%')
    fig8 = px.bar(h7, x='seasons', y='price', color= "seasons",
                  template='simple_white', text_auto='.3s',
                  )
    c7.plotly_chart(fig8, use_container_width=True)

    # H8:
    h8= data.copy()

    c8.subheader('H8: O valor de imoveis de condição regular é até 10% mais barata que os demais em média.')
    h8['condition_type'] = h8['condition_type'].apply(lambda x: 'regular' if x == 'regular' else 'others')
    h8 = h8[['condition_type', 'price']].groupby('condition_type').mean().reset_index()
    h8_percent = ((h8.loc[0, 'price'] - h8.loc[1, 'price'])*100 / h8.loc[1, 'price'])

    c8.write(f'Diferença percentual de preços: {round(h8_percent,)}% , então a afirmativa é verdadeira porque esse valor é '
          f'até 10% mais barato que as demais')
    fig9 = px.bar(h8, x='condition_type', y='price', color= "condition_type",
                  template='simple_white', text_auto='.3s',
                  )
    c8.plotly_chart(fig9, use_container_width=True)

    #Plot
    c9, c10 = st.columns((1, 1))


    # H9:
    h9= data.copy()

    c9.subheader('H9: O valor de imoveis antigos é 10% maior que os novos por ano de construção.')
    h9 = h9[['house_age', 'price']].groupby('house_age').mean().reset_index()
    h9_percent = ((h9.loc[0, 'price'] - h9.loc[1, 'price'])*100 / h9.loc[0, 'price'])

    c9.write(f'Diferença percentual de preços: {round(h9_percent,)}% , então a afirmativa é Falsa porque esse valor é '
          f'15% mais barato que as demais')
    fig10 = px.bar(h9, x='house_age', y='price', color= "house_age",
                  template='simple_white', text_auto='.3s',
                  )
    c9.plotly_chart(fig10, use_container_width=True)


    # H10
    h10= data.copy()

    c10.subheader('H10: Casas com um alto grau de qualidade e design são até 50% mais caras em nédia.')
    h10['grade'] = h10['grade'].apply(lambda x: 'high' if x >= 11 else 'low')
    h10 = h10[['grade', 'price']].groupby('grade').mean().reset_index()
    h10_percent = ((h10.loc[0, 'price'] - h10.loc[1, 'price'])*100 / h10.loc[1, 'price'])

    c10.write(f'Diferença percentual de preços: {round(h10_percent,)}%, então a afirmativa é Falsa porque esse valor é mais alto que 50%')
    fig10 = px.bar(h10, x='grade', y='price', color= "grade",
                  template='simple_white', text_auto='.3s',
                  )
    c10.plotly_chart(fig10, use_container_width=True)

    return None


if __name__ == '__main__':

    st.set_page_config(layout="wide")

    # extract
    # get data
    path = 'kc_house_data.csv'

    # dataset
    data = get_data(path)
    data = config_feature(data)
    df1 = overview_data(data)
    data = add_feature(data)
    data = metrics_data(data)
    fig = draw_map(data)
    st.plotly_chart(fig)
    commercial_distribution(data)
    insights(data)





