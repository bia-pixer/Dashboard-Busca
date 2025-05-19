import pandas as pd
import requests
import time
import os
from GoogleNews import GoogleNews
from pytrends.request import TrendReq
import plotly.graph_objects as go

# Chaves de API
api_key_etherscan = 'NQA5MKM8HEAZ7ICX1RU6531N1Y12W56QCS'
api_key_bscscan = 'Y9VF33DJPMEM1QVA5YCJ8NVC9J5NAYGAJE'
endereco = '0xdAC17F958D2ee523a2206206994597C13D831ec7' # Tether

def noticias_google(termo_busca, atualizar_consulta=False):
    """
    Retorna as manchetes de jornais e seus respectivos links relacionados ao termo de busca.
    Realiza as buscas na região do Brasil e em português.
    A primeira vez que o termo é buscado, gera um arquivo .csv com o retorno da API.
    As buscas subsequentes desse termo retornam o arquivo .csv.

    Parâmetro:
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
        googlenews = GoogleNews(lang='pt', region='BR')

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

    # linhas
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
            txs = resp.json()

            df = pd.DataFrame(txs)
            df['blockTime'] = pd.to_datetime(df['blockTime'], unit='s')
            df['date'] = df['blockTime'].dt.date

            # O campo de valor transferido pode variar, exemplo para transferências de SOL
            df['lamports'] = df['lamport'].astype(float)
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

    fig.add_trace(go.Scatter(
        x=total_transferences.index,
        y=total_transferences,
        name='Valor Total Transferido ($)',
        mode='lines',
        yaxis='y1',
        line=dict(color='#28724F')
    ))

    fig.add_trace(go.Bar(
        x=num_of_transferences.index,
        y=num_of_transferences,
        name='Número de Transferências',
        yaxis='y2',
        marker_color='#F2A900'
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
