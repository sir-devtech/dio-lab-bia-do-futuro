import json
import os
import pandas as pd
import requests
import streamlit as st

# ============ CONFIGURAÇÃO ============
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "llama3"

# Caminho base relativo ao próprio arquivo, independente de onde o comando é rodado
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# ============ CARREGAR DADOS ============
with open(os.path.join(BASE_DIR, "perfil_investidor.json"), encoding="utf-8") as f:
    perfil = json.load(f)
transacoes = pd.read_csv(os.path.join(BASE_DIR, "transacoes.csv"))
historico = pd.read_csv(os.path.join(BASE_DIR, "historico_atendimento.csv"))
with open(os.path.join(BASE_DIR, "produtos_financeiros.json"), encoding="utf-8") as f:
    produtos = json.load(f)

# ============ MONTAR CONTEXTO ============
metas_txt = "\n".join(
    f"  - {m['meta']}: R$ {m['valor_necessario']} até {m['prazo']}"
    for m in perfil["metas"]
)

contexto = f"""DADOS DO CLIENTE:
- Nome: {perfil['nome']}, {perfil['idade']} anos, {perfil['profissao']}
- Renda: R$ {perfil['renda_mensal']} | Perfil: {perfil['perfil_investidor']}
- Objetivo: {perfil['objetivo_principal']}
- Patrimônio: R$ {perfil['patrimonio_total']} | Reserva atual: R$ {perfil['reserva_emergencia_atual']}
- Metas:
{metas_txt}

TRANSAÇÕES (últimos 3 meses):
{transacoes.to_string(index=False)}

ATENDIMENTOS ANTERIORES:
{historico.to_string(index=False)}

PRODUTOS DISPONÍVEIS PARA ENSINAR:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""

# ============ SYSTEM PROMPT ============
SYSTEM_PROMPT = """Você é o Edu, um educador financeiro amigável e didático.

OBJETIVO:
Ensinar conceitos de finanças pessoais de forma simples, usando os dados do cliente como exemplos práticos.

REGRAS:
- NUNCA recomende investimentos específicos, apenas explique como funcionam;
- JAMAIS responda a perguntas fora do tema ensino de finanças pessoais.
  Quando ocorrer, responda lembrando o seu papel de educador financeiro;
- Use os dados fornecidos para dar exemplos personalizados;
- Linguagem simples, como se explicasse para um amigo;
- Se não souber algo, admita: "Não tenho essa informação, mas posso explicar...";
- Sempre pergunte se o cliente entendeu;
- Responda de forma sucinta e direta, com no máximo 3 parágrafos.
"""

SAUDACAO = (
    f"Oi, {perfil['nome']}! 👋 Sou o Edu, seu educador financeiro. "
    "Posso te ajudar a entender conceitos de finanças, analisar seus gastos e aprender sobre investimentos. "
    "O que você quer aprender hoje?"
)

# ============ CHAMAR OLLAMA ============
def perguntar(historico_msgs: list[dict], nova_pergunta: str) -> str:
    """Envia a conversa acumulada ao Ollama e retorna a resposta do Edu."""
    historico_txt = ""
    for msg in historico_msgs:
        role = "Usuário" if msg["role"] == "user" else "Edu"
        historico_txt += f"{role}: {msg['content']}\n"

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"CONTEXTO DO CLIENTE:\n{contexto}\n\n"
        f"HISTÓRICO DA CONVERSA:\n{historico_txt}\n"
        f"Usuário: {nova_pergunta}\nEdu:"
    )

    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODELO, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["response"]
    except requests.exceptions.ConnectionError:
        return (
            "⚠️ Não consegui conectar ao Ollama. Verifique se ele está rodando com "
            "`ollama serve` e tente novamente."
        )
    except Exception as e:
        return f"⚠️ Erro inesperado ao chamar o modelo: {e}"

# ============ INTERFACE ============
st.set_page_config(page_title="Edu — Educador Financeiro", page_icon="🎓")

# Sidebar com resumo do perfil
with st.sidebar:
    st.header("👤 Perfil do Cliente")
    st.write(f"**Nome:** {perfil['nome']}")
    st.write(f"**Idade:** {perfil['idade']} anos")
    st.write(f"**Profissão:** {perfil['profissao']}")
    st.write(f"**Renda mensal:** R$ {perfil['renda_mensal']:,.2f}")
    st.write(f"**Perfil:** {perfil['perfil_investidor'].capitalize()}")
    st.divider()
    st.write(f"**Objetivo:** {perfil['objetivo_principal']}")
    reserva_pct = (perfil['reserva_emergencia_atual'] / perfil['metas'][0]['valor_necessario']) * 100
    st.progress(
        min(reserva_pct / 100, 1.0),
        text=f"Reserva: R$ {perfil['reserva_emergencia_atual']:,.0f} / R$ {perfil['metas'][0]['valor_necessario']:,.0f} ({reserva_pct:.0f}%)",
    )
    st.divider()
    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()

st.title("🎓 Edu — Educador Financeiro")

# Inicializar histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir saudação inicial se ainda não houver mensagens
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write(SAUDACAO)

# Exibir histórico acumulado
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input do usuário
if nova_pergunta := st.chat_input("Sua dúvida sobre finanças..."):
    st.session_state.messages.append({"role": "user", "content": nova_pergunta})
    st.chat_message("user").write(nova_pergunta)

    with st.spinner("Edu está pensando..."):
        resposta = perguntar(st.session_state.messages[:-1], nova_pergunta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})
    st.chat_message("assistant").write(resposta)
