
import streamlit as st
import modules as m
import asyncio

# Credenciais ------------------------------------------------------------------
api_key_etherscan = 'NQA5MKM8HEAZ7ICX1RU6531N1Y12W56QCS'
api_key_bscscan = 'Y9VF33DJPMEM1QVA5YCJ8NVC9J5NAYGAJE'
api_key = None

# Configurações gerais da página -----------------------------------------------
st.set_page_config(layout='wide', 
                   page_title='Busca de Ativos Virtuais',
                   page_icon=':grey_question:')

st.title('Busca de Ativos Virtuais')

# Configuração da barra lateral ------------------------------------------------
st.sidebar.markdown('## Configure sua Busca!')

termo = st.sidebar.text_input('Digite um termo para pesquisa: *')
token_adress = st.sidebar.text_input('Digite o endereço do token para a busca no block explorer: *')

explorer = st.sidebar.selectbox(label='Qual explorador de bloco você deseja usar? *',
                                options=['','Etherscan', 'BSCscan', 'Solscan'])
if (explorer == 'Etherscan') or (explorer == 'BSCscan'):
    api_key = st.sidebar.text_input(label='Insira sua chave de API para o explorador escolhido:')    

telegram = st.sidebar.checkbox(label='Deseja realizar uma busca no Telegram?')
if telegram:
    telegram_channel = st.sidebar.text_input(label='Digite o nome ou link do canal: *')
    telegram_message_limit = st.sidebar.text_input(label='Quantas mensagens deseja obter?')
    telegram_api_id = st.sidebar.text_input(label='API ID:')
    telegram_api_hash = st.sidebar.text_input(label='API Hash:')

if st.sidebar.button(label='Buscar'):
    # Só mostra as informações de pesquisa se todo o necessário estiver preenchido
    if termo and token_adress and explorer:

        st.write(f'Você buscou pelo termo: {termo}')

        # ----------------------------------------------------------------------
        # Gráfico do block explorer --------------------------------------------  
        # ----------------------------------------------------------------------
        etherscan, bscscan, solscan = (False, False, False)
        if explorer == 'Etherscan':
            etherscan = True
            if api_key is None: api_key = api_key_etherscan
        elif explorer == 'BSCscan':
            bscscan = True
            if api_key is None: api_key = api_key_bscscan 
        elif explorer == 'Solscan':
            solscan = True    

        explorer_data_1, explorer_data_2 =  m.blockchain_data(address=token_adress,
                                                              api_key_etherscan=api_key.strip(),
                                                              api_key_bscscan=api_key.strip(),
                                                              etherscan=etherscan,
                                                              bscscan=bscscan,
                                                              solscan=solscan)
        if explorer_data_1 and explorer_data_2:
            fig = m.explorer_graph(explorer_data_1, explorer_data_2)
            st.plotly_chart(fig)
        else:
            st.warning('Falha na busca de dados transacionais dos tokens via ' \
            'exploradores de bloco.')

        # ----------------------------------------------------------------------
        # Notícias -------------------------------------------------------------
        # ----------------------------------------------------------------------
        st.subheader('Principais Notícias', divider='gray')
        news_df = m.noticias_google(termo)
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

        st.download_button(label='Clique aqui para fazer o download da base de dados completa da busca na rede X/Twitter',
                           data=twitter_df.to_csv(), 
                           file_name='twitter_scrapping_data.csv',
                           on_click='ignore', 
                           icon=':material/download:')

        # ----------------------------------------------------------------------
        # Telegram -------------------------------------------------------------
        # ----------------------------------------------------------------------
        if telegram:
            st.subheader('Diagnóstico de Dados do Telegram', divider='gray')
            if telegram_channel:
                # telegram_df = m.activate_telegram_search(telegram_channel)
                import pandas as pd
                telegram_df = pd.read_csv('buscas/telegram/2025-05-23_53390.csv')
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
    st.markdown('2. 10 notícias mais recentes sobre o termo buscado;')
    st.markdown('3. Estatísticas do Google Trends;')
    st.markdown('4. Análise das publicações que contém o termo buscado no X;')
    st.markdown('5. Análise da atividade em canal especificado no Telegram.')
    st.write('Para iniciar sua busca, preencha todos os campos obrigatórios, ' \
    'sinalizados com asterisco (*), no menu lateral.')