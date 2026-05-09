# Passo a Passo de Execução

## Setup do Ollama

```bash
# 1. Instalar Ollama (ollama.com)
# 2. Baixar o modelo
ollama pull llama3

# 3. Testar se funciona
ollama run llama3 "Olá!"
```

## Código Completo

Todo o código-fonte está no arquivo `app.py`.

## Como Rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Garantir que Ollama está rodando
ollama serve

# 3. Rodar o app (da raiz do repositório)
streamlit run .\src\app.py
```

## Melhorias implementadas nesta versão

- **Histórico de conversa multi-turno** via `st.session_state`
- **Sidebar** com resumo do perfil e progress bar da reserva de emergência
- **Saudação inicial** personalizada com o nome do cliente
- **Tratamento de erros** se Ollama não estiver rodando
- **Caminhos de arquivo** robustos com `os.path` (funciona de qualquer diretório)
- **Cliente personalizado:** Ana Lima, 28 anos, Designer Gráfica, perfil conservador
- **Base de dados enriquecida:** 3 meses de transações (agosto a outubro/2025)

## Evidência de Execução

> Screenshot da aplicação rodando localmente. Adicionar imagem em `assets/` após gravar o pitch.

