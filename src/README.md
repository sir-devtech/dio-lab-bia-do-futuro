# Edu — Educador Financeiro 🎓

Assistente virtual de educação financeira desenvolvido como projeto final do lab **"Construa seu Assistente Virtual com Inteligência Artificial"** da DIO.

## Sobre o Agente

O **Edu** é um educador financeiro personalizado que usa os dados reais do cliente para ensinar conceitos de finanças pessoais de forma simples e prática. Ele **não recomenda investimentos** — apenas educa.

**Cliente simulado:** Ana Lima, 28 anos, Designer Gráfica, perfil conservador, objetivo de construir reserva de emergência.

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.14 | Runtime |
| Streamlit | Interface web |
| Ollama + phi3:mini | LLM local (2.2 GB, roda sem GPU) |
| pandas | Análise de transações |

## Como Rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Baixar o modelo (só na primeira vez)
ollama pull phi3:mini

# 3. Iniciar o Ollama
ollama serve

# 4. Rodar o app (da raiz do repositório)
streamlit run src/app.py
```

> **Windows:** Se `ollama` não for reconhecido, use o caminho completo:
> `C:\Users\<seu-usuario>\AppData\Local\Programs\Ollama\ollama.exe`

## Melhorias implementadas nesta versão

- **Modelo trocado:** `llama3` → `phi3:mini` (2.2 GB, responde em segundos no CPU)
- **Arquitetura híbrida:** respostas determinísticas instantâneas para perguntas de validação + streaming token a token para perguntas abertas
- **Histórico multi-turno** via `st.session_state` (contexto preservado entre mensagens)
- **Sidebar** com perfil do cliente e progress bar da reserva de emergência
- **Saudação personalizada** com o nome da Ana Lima
- **Tratamento de erros** se Ollama não estiver rodando
- **Caminhos robustos** com `os.path.abspath` (funciona de qualquer diretório)
- **Base de dados enriquecida:** 38 transações em 3 meses (ago–out/2025)

## Demonstração

Os vídeos de demonstração estão na pasta [`/videos`](../videos/).

## Estrutura do Projeto

```
├── src/
│   └── app.py              # Aplicação principal
├── data/
│   ├── perfil_investidor.json
│   ├── transacoes.csv
│   ├── historico_atendimento.csv
│   └── produtos_financeiros.json
├── docs/
│   ├── 01-documentacao-agente.md
│   ├── 02-base-conhecimento.md
│   ├── 03-prompts.md
│   ├── 04-metricas.md
│   └── 05-pitch.md
├── videos/                 # Gravações da demonstração
└── requirements.txt
```

