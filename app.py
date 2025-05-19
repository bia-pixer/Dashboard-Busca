
import streamlit as st
import modules as m
import plotly.figure_factory as ff

# Credenciais
api_key_etherscan = 'NQA5MKM8HEAZ7ICX1RU6531N1Y12W56QCS'
api_key_bscscan = 'Y9VF33DJPMEM1QVA5YCJ8NVC9J5NAYGAJE'

# Configurações gerais da página
st.set_page_config(layout='wide', 
                   page_title='Busca de Ativos Virtuais',
                   page_icon=':grey_question:')

st.title('Busca de Ativos Virtuais')

# Configuração da barra lateral ------------------------------------------------
st.sidebar.markdown("## Configure sua Busca!")

termo = st.sidebar.text_input("Digite um termo para pesquisa: *")
# if termo:
    # st.sidebar.write(f"Você pesquisou pelo termo: {termo}")

token_adress = st.sidebar.text_input("Digite o endereço do token para a busca no block explorer: *")

explorer = st.sidebar.selectbox(label='Qual explorador de bloco você deseja usar? *',
                                options=['','Etherscan', 'BSCscan', 'Solscan'])
if explorer:
    api_key = st.sidebar.text_input(label='Insira sua chave de API para o explorador escolhido:')


telegram = st.sidebar.checkbox(label='Deseja realizar uma busca no Telegram?')
if telegram:
    telegram_channel = st.sidebar.text_input(label='Digite o nome do canal:')

# Gráfico do block explorer ----------------------------------------------------
etherscan, bscscan, solscan = (False, False, False)
if explorer == 'Etherscan':
    etherscan = True
    if api_key is None: api_key = api_key_etherscan
elif explorer == 'BSCscan':
    bscscan = True
    if api_key is None: api_key = api_key_bscscan 
elif explorer == 'Solscan':
    solscan = True    

if token_adress:
    explorer_data_1, explorer_data_2 =  m.blockchain_data(address=token_adress,
                                                        api_key_etherscan=api_key,
                                                        api_key_bscscan=api_key,
                                                        etherscan=etherscan,
                                                        bscscan=bscscan,
                                                        solscan=solscan)
    fig = m.explorer_graph(explorer_data_1, explorer_data_2)
    st.plotly_chart(fig)

# Notícias ---------------------------------------------------------------------
st.subheader('Principais Notícias', divider='gray')

if termo:
    news_df = m.noticias_google(termo)
    news_df = m.df_to_html_table(news_df)
    st.markdown(news_df, unsafe_allow_html=True)

# Google Trends ----------------------------------------------------------------
st.subheader('Tendências', divider='gray')

# if termo: COM ERRO
    # dados_interesse, dados_regiao, relacionados = m.tendencia_google(termo)

# Telegram ---------------------------------------------------------------------
