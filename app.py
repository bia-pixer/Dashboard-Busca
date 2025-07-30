
import streamlit as st
import modules as m
import asyncio
import datetime as dt
from cookies_manager import CookieManager
import time
import json

# Configurações gerais da página -----------------------------------------------
st.set_page_config(layout='wide', 
                   page_title='Busca de Ativos Virtuais',
                   page_icon=':grey_question:')

st.title('Busca de Ativos Virtuais')

# Configuração da barra lateral ------------------------------------------------
st.sidebar.markdown('## Configure sua Busca!')

termo = st.sidebar.text_input('Digite um termo para pesquisa:*')

today = dt.datetime.now()
last_year = today.year - 1
start_date, end_date = st.sidebar.date_input('Selecione o período da busca:', 
                                             value=(dt.date(last_year, 1, 1), today))

token_adress = st.sidebar.text_input('Digite o endereço do token para a busca no block explorer:*')

explorer = st.sidebar.selectbox('Qual explorador de bloco você deseja usar?*',
                                options=['','Etherscan', 'BSCscan', 'Solscan'])

api_key = st.sidebar.text_input('Insira sua chave de API para o explorador escolhido:')    

twitter_max_tweets = st.sidebar.number_input('Número máximo de tweets a serem obtidos:', 
                                           min_value=1, max_value=1000000, value=10000)

telegram = st.sidebar.checkbox('Deseja realizar uma busca no Telegram?')
if telegram:
    telegram_phone = st.sidebar.text_input('Digite o número de telefone da sua conta:*', placeholder='+5521999999999')
    telegram_channel = st.sidebar.text_input('Digite o nome ou link do canal:*')
    telegram_message_limit = st.sidebar.number_input('Quantas mensagens deseja obter?', min_value=1, value=100)
    telegram_api_id = st.sidebar.text_input('API ID:')
    telegram_api_hash = st.sidebar.text_input('API Hash:')

    # Inicializa variáveis de estado
    if 'telegram_code_sent' not in st.session_state:
        st.session_state['telegram_code_sent'] = False
    if 'phone_code_hash' not in st.session_state:
        st.session_state['phone_code_hash'] = None
    if 'telegram_authenticated' not in st.session_state:
        st.session_state['telegram_authenticated'] = False
    if 'telegram_error' not in st.session_state:
        st.session_state['telegram_error'] = None

    if telegram_phone == '': telegram_phone = st.secrets["TELEGRAM_PHONE"]
    if telegram_api_id == '': telegram_api_id = st.secrets["TELEGRAM_API_ID"]
    if telegram_api_hash == '': telegram_api_hash = st.secrets["TELEGRAM_API_HASH"]

    if st.sidebar.button('Fazer Login no Telegram'):
        try:
            code_sent, telegram_code_hash = asyncio.run(m.connect_to_telegram(
                telegram_api_id, telegram_api_hash, telegram_phone, 
                code=None, code_hash=None)
                )
            if code_sent == 'code_sent':
                st.session_state['telegram_code_sent'] = True
                st.session_state['phone_code_hash'] = telegram_code_hash
                st.sidebar.success("Código enviado! Verifique seu Telegram.")
            elif code_sent == 'authenticated':
                st.session_state['telegram_authenticated'] = True
                st.sidebar.success("Autenticado com sucesso!")
            else:
                st.session_state['telegram_error'] = code_sent
                st.sidebar.error(code_sent)
        except Exception as e:
            st.session_state['telegram_error'] = str(e)
            st.sidebar.error(f"Erro: {e}")

    # Se o código já foi enviado, pede o código ao usuário
    if st.session_state['telegram_code_sent'] and not st.session_state['telegram_authenticated']:
        telegram_code = st.sidebar.text_input('Insira o código recebido:')
        if st.sidebar.button('Validar Código'):
            try:
                code_sent = asyncio.run(m.connect_to_telegram(
                    telegram_api_id, telegram_api_hash, telegram_phone, 
                    telegram_code, st.session_state['phone_code_hash']
                ))
                if code_sent == 'authenticated':
                    st.session_state['telegram_authenticated'] = True
                    st.sidebar.success("Autenticado com sucesso!")
                else:
                    st.session_state['telegram_error'] = code_sent
                    st.sidebar.error(code_sent)
            except Exception as e:
                st.session_state['telegram_error'] = str(e)
                st.sidebar.error(f"Erro: {e}")

    # Mensagem final
    if st.session_state['telegram_authenticated']:
        st.sidebar.success("Você está autenticado no Telegram!")

if st.sidebar.button('Buscar'):
    # Só mostra as informações de pesquisa se todo o necessário estiver preenchido
    if termo and token_adress and explorer:
        # ----------------------------------------------------------------------
        # Gráfico do block explorer --------------------------------------------  
        # ----------------------------------------------------------------------
        etherscan, bscscan, solscan = (False, False, False)
        if explorer == 'Etherscan':
            etherscan = True
            if api_key == '': api_key = st.secrets["ETHERSCAN_API_KEY"]
        elif explorer == 'BSCscan':
            bscscan = True
            if api_key == '': api_key = st.secrets["BSCSCAN_API_KEY"] 
        elif explorer == 'Solscan':
            solscan = True
            if api_key == '': api_key = None

        explorer_data_1, explorer_data_2 =  m.blockchain_data(address=token_adress.strip(),
                                                              api_key_etherscan=api_key,
                                                              api_key_bscscan=api_key,
                                                              etherscan=etherscan,
                                                              bscscan=bscscan,
                                                              solscan=solscan)

        if (explorer_data_1 is not None) and (explorer_data_2 is not None):
            column1, column2 = st.columns(2)
            column1.metric('Transferências Totais - Net Value (US$)', 
                           value=explorer_data_1.sum().round(2),
                           delta=explorer_data_1[0].round(2))
            column2.metric('Quantidade de Transferências', value=explorer_data_2.sum())

            fig = m.explorer_graph(explorer_data_1, explorer_data_2)
            st.plotly_chart(fig)
        else:
            st.warning('Falha na busca de dados transacionais dos tokens via ' \
            'exploradores de bloco.')

        # ----------------------------------------------------------------------
        # Notícias -------------------------------------------------------------
        # ----------------------------------------------------------------------
        st.subheader('Principais Notícias', divider='gray')
        news_df = m.noticias_google(termo, start_date, end_date, atualizar_consulta=True)
        news_df = m.df_to_html_table(news_df)
        st.markdown(news_df, unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # Google Trends --------------------------------------------------------
        # ----------------------------------------------------------------------
        st.subheader('Tendências', divider='gray')
        try:
            dados_interesse, dados_regiao, relacionados = m.tendencia_google(termo)
        except:
            st.warning('Falha na API do Google Trends.')

        # ----------------------------------------------------------------------
        # X/Twitter ------------------------------------------------------------
        # ----------------------------------------------------------------------
        st.subheader('Diagnóstico de Dados do X/Twitter', divider='gray')

        # manager = CookieManager(tempo_bloqueio_minutos=1)

        # for i in range(10):
        #    cookie_info = manager.proximo_cookie()
        #    if cookie_info:
        #        idx =  cookie_info["indice"]
        #        cookie = cookie_info["cookie"]
        #        # st.write(f"Requisição #{i+1}: Usando cookie de índice {idx} – {cookie}")
        #        manager.marcar_bloqueado(idx)
        #   else:
        #        st.warning("Todos os cookies estão temporariamente bloqueados. Aguardando desbloqueio...")
        #        time.sleep(60)  # Aguarda 1 minuto antes de tentar novamente

        #st.success("Teste finalizado!")
        #t.write(f"Cookies disponíveis após teste: {manager.total_disponiveis()}")
        #st.write(f"Cookies bloqueados após teste: {manager.total_bloqueados()}")
        pool = st.secrets["cookies"]["pool"]
        cookies = json.loads(pool)

        twitter_df = m.fetch_tweets_apify( st.secrets["APIFY_CLIENT_TOKEN"], 
                                          search_terms=[termo], 
                                          cookies=cookies,
                                          max_items=twitter_max_tweets)
        st.dataframe(twitter_df, hide_index=True)

        if termo.lower() == 'nelore coin':
            filename = termo.replace(' ', '_')
            fig1, fig2, table1, table2, table3, twitter_df = m.twitter_diagnosis(filename)

            column1, column2 = st.columns(2)

            column1.plotly_chart(fig1)
            column1.write('**Perfis Mais Ativos**')
            column1.dataframe(table1)

            column2.plotly_chart(fig2)
            column2.write('**Engajamento por Perfil**')
            column2.dataframe(table2)

            st.write('**Tweets mais relevantes**')
            st.dataframe(table3.head(10), hide_index=True)

            st.download_button('Clique aqui para fazer o download da base de dados completa da busca na rede X/Twitter',
                            data=twitter_df.to_csv(), 
                            file_name='twitter_scrapping_data.csv',
                            on_click='ignore', 
                            icon=':material/download:')
        else:
            st.warning('No momento, só há dados disponíveis para o token Nelore Coin (NLC).')

        # ----------------------------------------------------------------------
        # Telegram -------------------------------------------------------------
        # ----------------------------------------------------------------------
        if telegram:
            st.subheader('Diagnóstico de Dados do Telegram', divider='gray')
            if telegram_channel:
                telegram_df = m.activate_telegram_search(telegram_channel,
                                                         api_id=telegram_api_id,
                                                         api_hash=telegram_api_hash,
                                                         message_limit=int(telegram_message_limit))
                fig3, table4 = m.telegram_diagnosis(telegram_df)
                    
                column1, column2 = st.columns(2)
                column1.plotly_chart(fig3)
                column2.write('**Perfis Mais Ativos**')
                column2.dataframe(table4.head(10), hide_index=False, 
                                column_config={'Username': st.column_config.TextColumn(width='large')})
                st.write('**Base de dados completa da busca no canal do Telegram**')
                st.dataframe(telegram_df, hide_index=True)
            else:
                st.warning('Insira o nome do canal para realizar a busca no Telegram.')
    elif termo or token_adress or explorer:
        st.warning("Preencha todos os campos obrigatórios antes de buscar os dados.")

else:
    st.write('Seja bem-vindo!')
    st.write('Essa é uma ferramenta para facilitar a busca por ativos virtuais ' \
       'em investigação. Aqui estão reunidas os principais dados e análises mais ' \
        'recorrentes relacionados à essa categoria de ativos. As informações ' \
        'disponibilizadas são:')
    st.markdown('1. Gráfico de transações (obtidas via _block explorers_);')
    st.markdown('2. Notícias mais recentes sobre o termo buscado;')
    st.markdown('3. Estatísticas do Google Trends;')
    st.markdown('4. Análise das publicações que contém o termo buscado no X;')
    st.markdown('5. Análise da atividade em canal especificado no Telegram.')
    st.write('Para iniciar sua busca, preencha todos os campos obrigatórios, ' \
    'sinalizados com asterisco (*), no menu lateral.')