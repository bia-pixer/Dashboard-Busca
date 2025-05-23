# Dashboard - Media Scanning

## O Dashboard possui o objetivo de fornecer as seguintes informações:
*   **Notícias**: Valor Econômico; Exame, InfoMoney (retornar os links para as notícias); **OK**
*   **Google Trends**: Número de menções, localização, termos relacionados; **OK**
*   **Twitter e Telegram**: Obter as últimas informações postadas e apresentar uma breve análise exploratória desses dados. Também fornece as bases completas para _download_; **OK**
*   _**Blockexplorers**_: Gráfico de transações (_Analytics_). **OK**

## Problemas
*   Falha da API do Google Trends;
*   Falha no display do gráfico de _Analytics_;
*   Incluir documentação.

## Melhorias
*   Os dados do Twitter pressupõe o uso de uma [ferramenta de _web scrapping_ do Twitter](https://apify.com/fastcrawler/tweet-fast-scraper), disponível via Apify. No momento, a aplicação obtém as informações de uma base de dados obtida no período grátis dessa mesma ferramenta;
*   Nova _feature_: Inclusão um resumo do conteúdo dos posts em redes sociais usando uma LLM, inclusive com análise de sentimento.

## Árvore do Projeto

<pre> Files Tree
/
└── Dashboard
    ├── __pycache__
    ├── .venv
    ├── app.py
    ├── modules.py
    ├── README.md
    ├── requirements.txt
    └── visuals.py
/
``` </pre>