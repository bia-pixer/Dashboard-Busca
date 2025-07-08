import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import os
import random
from GoogleNews import GoogleNews
from pytrends.request import TrendReq
from telethon import TelegramClient
import asyncio
import plotly.graph_objects as go
import plotly.io as pio

# Define o tema padrão para todos os gráficos
pio.templates.default = "plotly_white"

def noticias_google(termo_busca, start_date, end_date, atualizar_consulta=False):
    """
    Retorna as manchetes de jornais e seus respectivos links relacionados ao 
    termo de busca. Realiza as buscas na região do Brasil e em português. A 
    primeira vez que o termo é buscado, gera um arquivo .csv com o retorno da API.
    As buscas subsequentes desse termo retornam o arquivo .csv.

    Parâmetros:
    termo_busca (str): Termo de pesquisa
    atualizar_consulta: Realizar nova solicitação via API
    """
    filename = termo_busca.replace(' ', '_')
    filepath = f'buscas/news/{filename}.csv'

    if atualizar_consulta:
        if os.path.exists(filepath):
            os.remove(filepath)

    try:
        df = pd.read_csv(filepath)
        df['link'] = df['link'].apply(lambda x: x.split('/&')[0])
        return df
    except:
        googlenews = GoogleNews(lang='pt', region='BR', 
                                start=start_date, end=end_date)

        googlenews.search(termo_busca)

        resultados = googlenews.result()

        df = pd.DataFrame(resultados)
        df['link'] = df['link'].apply(lambda x: x.split('/&')[0])

        df.to_csv(f'buscas/news/{filename}.csv', index=False)
        return df

def df_to_html_table(df):
    """
    Transforma um dataframe em uma tabela html. Aplica o hiperlink na manchete.
    """
    df['date'] = 'H' + df['date'].astype(str)
    df['manchete_linkada'] = df.apply(
        lambda row: f"<a href='{row['link']}' target='_blank'>{row['title']} </a>", axis=1
    )
    df.drop(columns=['datetime', 'img', 'title', 'link'], inplace=True)
    df = df[['media', 'manchete_linkada', 'date', 'desc']]
    df.columns = ['Fonte', 'Manchete', 'Data', 'Descrição']
    # Montando a tabela HTML manualmente
    table_html = "<table>"
    table_html += "<tr>"
    for col in df.columns:
        # cabeçalho
        header = 'Manchete' if col == 'Manchete' else col.capitalize()
        table_html += f"<th>{header}</th>"
    table_html += "</tr>"

    # Linhas
    for _, row in df.iterrows():
        table_html += "<tr>"
        for col in df.columns:
            table_html += f"<td>{row[col]}</td>"
        table_html += "</tr>"
    table_html += "</table>"
    return table_html

def tendencia_google(termo, periodo='today 12-m', regiao='worldwide'):
    """
    Obtém dados do Google Trends para um termo específico
    
    Parâmetros:
    termo (str): Termo de pesquisa
    periodo (str): Período temporal (padrão: últimos 12 meses)
    regiao (str): Código ISO do país (padrão: Worldwide)
    
    Retorna:
    tuple: (dados_temporais, dados_regionais, pesquisas_relacionadas)
    """
    
    # Configurar conexão com retry automático
    pytrends = TrendReq(
        hl='pt-BR',          # Idioma português do Brasil
        tz=180,              # Fuso horário UTC-3 (Brasília)
        retries=3,           # Tentativas de reconexão
        backoff_factor=0.5,  # Intervalo exponencial entre tentativas
        requests_args={'headers': {'User-Agent': 'Mozilla/5.0'}}
    )
    
    try:
        # Construir payload da requisição
        pytrends.build_payload(
            kw_list=[termo],
            cat=0,            # Todas as categorias
            timeframe=periodo,
            geo=regiao,
            gprop=''          # Tipo de busca (web)
        )
        
        # Coletar dados temporais
        dados_tempo = pytrends.interest_over_time()
        if not dados_tempo.empty:
            dados_tempo = dados_tempo.drop(columns=['isPartial'], errors='ignore')
        
        # Coletar dados regionais
        dados_regiao = pytrends.interest_by_region(
            resolution='COUNTRY',
            inc_low_vol=True
        ).sort_values(by=termo, ascending=False)
        
        # Coletar pesquisas relacionadas
        relacionados = pytrends.related_queries()
        pesquisas_relacionadas = {
            'top': relacionados[termo]['top'].head(5),
            'rising': relacionados[termo]['rising'].head(5)
        }
        
        return dados_tempo, dados_regiao, pesquisas_relacionadas
    
    except Exception as e:
        print(f"Erro na coleta de dados: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), {}

def blockchain_data(address, 
                    api_key_etherscan, api_key_bscscan, solscan_token=None, 
                    etherscan=False, bscscan=False, solscan=False):
    """
    Obtém dados de Etherscan, BscScan ou Solscan.
    Retorna três séries individuais (ou DataFrames): 
    - total transfer value by date
    - number of transfers by date
    """
    # Etherscan
    if etherscan:
        try:
            print("Obtendo dados via Etherscan...")
            base_url = 'https://api.etherscan.io/api'
            params = {
                'module': 'account',
                'address': address,
                'apikey': api_key_etherscan
            }

            # Transações normais
            normal_txs = requests.get(
                base_url,
                params={**params, 'action': 'txlist', 'sort': 'asc'}
            ).json()['result']

            # Agrupamento por data
            df = pd.DataFrame(normal_txs)
            df['timeStamp'] = pd.to_datetime(df['timeStamp'], unit='s')
            df['date'] = df['timeStamp'].dt.date
            df['value'] = pd.to_numeric(df['value']) / 10**18  # ETH

            # Total transfer value by date
            total_transfer_value = df.groupby('date')['value'].sum()
            # Number of transfers by date
            num_transfers = df.groupby('date').size()

            return total_transfer_value, num_transfers

        except Exception as e:
            print(f"Falha no Etherscan: {e}")
            time.sleep(2)
            return None, None

    # BscScan
    elif bscscan:
        try:
            base_url = 'https://api.bscscan.com/api'
            params = {
                'module': 'account',
                'address': address,
                'apikey': api_key_bscscan
            }

            # Transações BEP-20
            bep20_txs = requests.get(
                base_url,
                params={**params, 'action': 'tokentx', 'sort': 'asc'}
            ).json()['result']

            df = pd.DataFrame(bep20_txs)
            df['timeStamp'] = pd.to_datetime(df['timeStamp'], unit='s')
            df['date'] = df['timeStamp'].dt.date
            df['value'] = pd.to_numeric(df['value']) / 10**18  # BNB ou token, depende do contrato

            # Total transfer value by date
            total_transfer_value = df.groupby('date')['value'].sum()
            # Number of transfers by date
            num_transfers = df.groupby('date').size()

            return total_transfer_value, num_transfers

        except Exception as e:
            print(f"Falha no BscScan: {e}")
            time.sleep(2)
            return None, None

    # Solscan
    elif solscan:
        try:
            # Solscan API pública não requer token, mas pode ser usado para limites maiores
            headers = {'Accept': 'application/json'}
            if solscan_token:
                headers['Authorization'] = f'Bearer {solscan_token}'

            # Transações SPL (token transfers)
            url_txs = f'https://public-api.solscan.io/account/transactions?address={address}&limit=1000'
            resp = requests.get(url_txs, headers=headers)
            if resp.status_code != 200:
                print(f"Erro HTTP {resp.status_code} ao acessar Solscan: {resp.text}")
                print("Resposta vazia do Solscan.")
                return None, None
            txs = resp.json()
            if not isinstance(txs, list):
                print("Resposta inesperada do Solscan:", txs)
                return None, None

            df = pd.DataFrame(txs)
            df['blockTime'] = pd.to_datetime(df['blockTime'], unit='s')
            df['date'] = df['blockTime'].dt.date

            # O campo de valor transferido pode variar, exemplo para transferências de SOL
            df['lamports'] = df['lamports'].astype(float)
            df['value'] = df['lamports'] / 1e9  # 1 SOL = 1e9 lamports

            # Total transfer value by date
            total_transfer_value = df.groupby('date')['value'].sum()
            # Number of transfers by date
            num_transfers = df.groupby('date').size()

            return total_transfer_value, num_transfers

        except Exception as e:
            print(f"Falha no Solscan: {e}")
            return None, None

def explorer_graph(total_transferences, num_of_transferences):
    fig = go.Figure()
    fig.update_layout(template='plotly_white')

    fig.add_trace(go.Bar(
        x=num_of_transferences.index,
        y=num_of_transferences,
        name='Número de Transferências',
        yaxis='y1',
        marker_color='#F2A900'
    ))

    fig.add_trace(go.Scatter(
        x=total_transferences.index,
        y=total_transferences,
        name='Valor Total Transferido ($)',
        mode='lines+markers',
        yaxis='y2',
        line=dict(color='#28724F', width=4),
        marker=dict(symbol='circle', size=8, color='#28724F')
    ))

    fig.update_layout(
        title='Transferências do Token',
        xaxis=dict(title='Data'),
        yaxis=dict(
            title='Valor Total Transferido ($)'
        ),
        yaxis2=dict(
            title='Número de Transferências',
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0.1, y=1.1, orientation='h')
    )
    return fig

def twitter_diagnosis(file_name):
    df= pd.read_csv(f'buscas/twitter/{file_name}.csv')

    # Seleciona as colunas de interesse
    columns= ['author/followers', 'author/isBlueVerified', 'author/name', 
            'author/username', 'createdAt', 'isQuote', 'isReply', 'lang', 
            'likeCount', 'quoteCount', 'replyCount', 'retweetCount', 'text', 
            'viewCount']
    df = df[columns]

    # Ajusta coluna de data e cria coluna de número de tweets por dia
    df['createdAt'] = pd.to_datetime(df['createdAt'])
    df['date'] = df['createdAt'].dt.date
    tweets_por_dia = df.groupby('date').size()

    # GRÁFICO: Número de tweets diários com o termo buscado
    graph_1 = go.Figure()

    graph_1.add_trace(go.Scatter(x=tweets_por_dia.index, y=tweets_por_dia,
                            line=dict(color='#28724F', width=4)))
        
    graph_1.update_layout(title='Número de tweets diários com o termo buscado')
    graph_1.update_yaxes(title_text='Quantidade de tweets')

    # GRÁFICO: Matriz de Correlação Entre os Indicadores de Engajamento
    corr_map = ['author/followers', 'likeCount', 'retweetCount', 'replyCount', 'viewCount']
    corr_map = df[corr_map].corr()
    labels = ['Seguidores', 'Likes', 'Retweets', 'Respostas', 'Visualizações']
    heatmap = go.Figure(data=go.Heatmap(z=corr_map, 
                                    x=labels, y = labels,
                                    colorscale='Viridis_R',
                                    text=np.round(corr_map, 2),
                                    texttemplate='%{text}',
                                    textfont={'size':14}))
    heatmap.update_layout(title='Matriz de Correlação Entre os Indicadores de Engajamento')

    # TABELA: Perfis mais ativos
    perfis_ativos = df.groupby('author/username')['text'].count()
    total_amount_of_posts = perfis_ativos.sum()
    perfis_ativos = pd.DataFrame(perfis_ativos)
    perfis_ativos['pct_total'] = perfis_ativos['text'].apply(lambda x: (x/total_amount_of_posts * 100).round(2)) 
    perfis_ativos.sort_values(by='text', ascending=False, inplace=True)
    perfis_ativos.columns = ['Quantidade de Tweets', 'Total de Tweets Sobre o Tema (%)']

    # TABELA: Engajamento
    engajamento_perfil = pd.DataFrame(index=df['author/username'].unique())

    # Engajamento Total = likes + quotes + replies + retweets
    table = df.groupby('author/username')[['likeCount', 'quoteCount', 'replyCount', 'retweetCount']].sum()
    table['Engajamento Total'] = table.sum(axis=1)
    table.sort_index(ascending=True, inplace=True)
    engajamento_perfil['Engajamento Total'] = table['Engajamento Total']

    seguidores = df.groupby('author/username')['author/followers'].max()
    seguidores.sort_index(ascending=True, inplace=True)

    # Engajamento dos Seguidores = Engajamento Total / Número de seguidores
    engajamento_perfil['Engajamento dos Seguidores (%)'] = table['Engajamento Total'] / seguidores * 100

    # Engajamento Médio por Tweet = Engajamento Total / Número de Tweets
    num_of_tweets = df.groupby('author/username')['text'].count()
    num_of_tweets.sort_index(ascending=True, inplace=True)
    engajamento_perfil['Engajamento Médio por Tweet (%)'] = table['Engajamento Total'] / num_of_tweets * 100
    engajamento_perfil = engajamento_perfil.round(2)

    # Ordena tabela de engajamento
    engajamento_perfil.sort_values(by=['Engajamento Total', 'Engajamento dos Seguidores (%)', 'Engajamento Médio por Tweet (%)'],
                                   ascending=False, inplace=True)

    # Tweets mais relevantes
    tweets_relevantes = ['createdAt', 'author/username', 'text', 'viewCount', 'likeCount']
    columns = ['Data', 'Username', 'Tweet', 'Visualizações', 'Curtidas']
    tweets_relevantes = df[tweets_relevantes]
    tweets_relevantes.sort_values(by=['viewCount', 'likeCount'], ascending=False, inplace=True)
    tweets_relevantes.columns = columns

    return graph_1, heatmap, perfis_ativos, engajamento_perfil, tweets_relevantes, df

async def send_telegram_code(api_id, api_hash, phone):
    client = TelegramClient('session_name', api_id, api_hash)
    await client.connect()
    result = await client.send_code_request(phone=phone)
    await client.disconnect()
    return result.phone_code_hash

async def connect_to_telegram(api_id, api_hash, phone, code, code_hash):
    client = TelegramClient('session_name', api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        if code is None:
            code_hash = await send_telegram_code(api_id, api_hash, phone)
            return 'code_sent', code_hash
        else:
            try:
                await client.sign_in(phone=phone, code=code, phone_code_hash=code_hash)
                await client.disconnect()
                return 'authenticated'
            except Exception as e:
                await client.disconnect()
                return f'Erro de autenticação: {e}'

async def telegram_data(channel_username, api_id, api_hash, message_limit):
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start()

    channel = await client.get_entity(channel_username)

    messages = []
    async for message in client.iter_messages(channel, limit=message_limit):
        sender = await message.get_sender()
        # Tenta obter o nome do usuário; se não houver, marca como 'Desconhecido'
        sender_name = (
            (sender.first_name or '') + ' ' + (sender.last_name or '')
            if sender and (sender.first_name or sender.last_name)
            else 'Desconhecido'
        )
        messages.append({
            'message_id': message.id,
            'date': message.date,
            'content': message.text,
            'sender_name': sender_name.strip()
        })
        await asyncio.sleep(1)

    df = pd.DataFrame(messages)
    await client.disconnect()
    now = datetime.now()
    df.to_csv(f'buscas/telegram/{now.date()}_{random.randint(0, 100000)}.csv', index=False)

    return df

def activate_telegram_search(channel_username, api_id, api_hash, message_limit):
    import nest_asyncio
    nest_asyncio.apply()
    import asyncio

    df = asyncio.run(telegram_data(channel_username, api_id=api_id, 
                                   api_hash=api_hash, message_limit=message_limit))
    return df

def telegram_diagnosis(df):
    # df['date'] = pd.to_numeric(df['date'], errors='coerce')
    df['date'] = pd.to_datetime(df['date']) # , unit='s')
    df['day'] = df['date'].dt.date
    messages_per_day = df.groupby('day').size()
    messages_per_day.sort_index(ascending=True, inplace=True)

    # Gráfico: Número de mensagens por dia no canal
    graph = go.Figure()
    graph.add_trace(go.Scatter(x=messages_per_day.index, y=messages_per_day.values,
                    line=dict(color='#28724F', width=4)))
    graph.update_layout(title='Quantidade de Mensagens Postadas por Dia')
    graph.update_yaxes(title_text='Número de Mensagens')

    # Tabela: Perfis mais ativos
    active_profiles = df.groupby('sender_name')['content'].count()
    active_profiles.sort_values(ascending=False, inplace=True)
    active_profiles.index.name = 'Username'
    active_profiles.name = 'Mensagens Enviadas'
    active_profiles = pd.DataFrame(active_profiles)

    return graph, active_profiles
