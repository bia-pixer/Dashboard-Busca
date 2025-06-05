import importlib
modulo = importlib.import_module('pip-system-certs')
import ssl
ssl._create_default_https_context = ssl._create_unverified_context  # Apenas para testes!
import pandas as pd
from pytrends.request import TrendReq
from trends_proxies import proxies
import time
import random

def tendencia_google(termo, periodo='today 12-m', regiao='BR'):
    """
    Obtém dados do Google Trends para um termo específico
    
    Parâmetros:
    termo (str): Termo de pesquisa
    periodo (str): Período temporal (padrão: últimos 12 meses)
    regiao (str): Código ISO do país (padrão: BR-Brasil)
    
    Retorna:
    tuple: (dados_temporais, dados_regionais, pesquisas_relacionadas)
    """
    
    # Configurar conexão com retry automático
    pytrends = TrendReq(
        hl='pt-BR',          # Idioma português do Brasil
        tz=180,              # Fuso horário UTC-3 (Brasília)
        retries=3,           # Tentativas de reconexão
        backoff_factor=0.5,  # Intervalo exponencial entre tentativas
        requests_args={'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }}, 
        proxies=proxies,
        timeout=(10,25)
    )
    
    try:
        time.sleep(random.uniform(2, 5))
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

dados_interesse, dados_regiao, relacionados = tendencia_google('eike token')
print(dados_interesse, dados_regiao, relacionados, end='\n\n')