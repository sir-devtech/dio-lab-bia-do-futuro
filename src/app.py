import json
import os
import re
import pandas as pd
import requests
import streamlit as st

# ============ CONFIGURAÇÃO ============
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "phi3:mini"

# Caminho base relativo ao próprio arquivo, independente de onde o comando é rodado
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# ============ CARREGAR DADOS ============
with open(os.path.join(BASE_DIR, "perfil_investidor.json"), encoding="utf-8") as f:
    perfil = json.load(f)
transacoes = pd.read_csv(os.path.join(BASE_DIR, "transacoes.csv"))
historico = pd.read_csv(os.path.join(BASE_DIR, "historico_atendimento.csv"))
with open(os.path.join(BASE_DIR, "produtos_financeiros.json"), encoding="utf-8") as f:
    produtos = json.load(f)

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

NUMERO_PARA_MES = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}

CATEGORIAS = {
    "alimentacao": "alimentacao",
    "alimentação": "alimentacao",
    "moradia": "moradia",
    "transporte": "transporte",
    "saude": "saude",
    "saúde": "saude",
    "lazer": "lazer",
    "educacao": "educacao",
    "educação": "educacao",
    "beleza": "beleza",
    "poupanca": "poupanca",
    "poupança": "poupanca",
}

# ============ MONTAR CONTEXTO ============
metas_txt = "\n".join(
    f"  - {m['meta']}: R$ {m['valor_necessario']} até {m['prazo']}"
    for m in perfil["metas"]
)

# Filtra apenas o mês mais recente para reduzir tamanho do prompt
transacoes["data"] = pd.to_datetime(transacoes["data"])
mes_recente = transacoes["data"].max().to_period("M")
transacoes_recentes = transacoes[transacoes["data"].dt.to_period("M") == mes_recente].copy()
transacoes_recentes["data"] = transacoes_recentes["data"].dt.strftime("%Y-%m-%d")
historico_recente = historico.tail(3).to_string(index=False)

# Resumo de gastos por categoria
resumo_gastos = transacoes[transacoes["tipo"] == "saida"].groupby("categoria")["valor"].sum().sort_values(ascending=False)
resumo_txt = "\n".join(f"  - {cat}: R$ {val:.2f}" for cat, val in resumo_gastos.items())

# Lista simplificada de produtos
produtos_txt = "\n".join(
    f"  - {p['nome']} (risco {p['risco']}): {p['rentabilidade']} | aporte mínimo R$ {p['aporte_minimo']}"
    for p in produtos
)

contexto = f"""DADOS DO CLIENTE:
- Nome: {perfil['nome']}, {perfil['idade']} anos, {perfil['profissao']}
- Renda: R$ {perfil['renda_mensal']} | Perfil: {perfil['perfil_investidor']}
- Objetivo: {perfil['objetivo_principal']}
- Patrimônio: R$ {perfil['patrimonio_total']} | Reserva atual: R$ {perfil['reserva_emergencia_atual']}
- Metas:
{metas_txt}

GASTOS POR CATEGORIA (últimos 3 meses):
{resumo_txt}

TRANSAÇÕES DO MÊS MAIS RECENTE ({mes_recente}):
{transacoes_recentes.to_string(index=False)}

ATENDIMENTOS MAIS RECENTES:
{historico_recente}

PRODUTOS DISPONÍVEIS PARA ENSINAR:
{produtos_txt}
"""

# Contexto reduzido para chamadas ao LLM (sem tabela de transações)
contexto_llm = (
    f"Cliente: {perfil['nome']}, {perfil['idade']} anos, perfil {perfil['perfil_investidor']}. "
    f"Renda: R$ {perfil['renda_mensal']}. "
    f"Objetivo: {perfil['objetivo_principal']}. "
    f"Reserva atual: R$ {perfil['reserva_emergencia_atual']} de R$ {perfil['metas'][0]['valor_necessario']}. "
    f"Gastos recentes: {resumo_txt.replace(chr(10), '; ')}"
)

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

def formatar_moeda(valor: float) -> str:
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def detectar_categoria(pergunta: str) -> str | None:
    for termo, categoria in CATEGORIAS.items():
        if termo in pergunta:
            return categoria
    return None


def detectar_mes(pergunta: str):
    for nome_mes, numero_mes in MESES.items():
        if nome_mes in pergunta:
            return numero_mes
    return None


def responder_gastos(pergunta: str) -> str | None:
    pergunta_normalizada = pergunta.lower()
    if "quanto gastei" not in pergunta_normalizada and "gastando mais" not in pergunta_normalizada:
        return None

    categoria = detectar_categoria(pergunta_normalizada)
    mes = detectar_mes(pergunta_normalizada) or mes_recente.month

    gastos = transacoes[transacoes["tipo"] == "saida"].copy()
    gastos_mes = gastos[gastos["data"].dt.month == mes]

    if "gastando mais" in pergunta_normalizada:
        if gastos_mes.empty:
            return "Não encontrei gastos para esse período, mas posso te ajudar a analisar outro mês."
        totais = gastos_mes.groupby("categoria")["valor"].sum().sort_values(ascending=False)
        categoria_top = totais.index[0]
        valor_top = totais.iloc[0]
        return (
            f"No mês de {NUMERO_PARA_MES[mes]}, sua maior despesa foi em {categoria_top}, "
            f"com R$ {formatar_moeda(valor_top)}. Se quiser, eu também posso quebrar esse valor por transação."
        )

    if not categoria:
        return "Posso calcular seus gastos por categoria. Tente perguntar, por exemplo: 'Quanto gastei com alimentação em outubro?'"

    gastos_categoria = gastos_mes[gastos_mes["categoria"] == categoria]
    total = float(gastos_categoria["valor"].sum())

    if total == 0:
        return f"No mês de {NUMERO_PARA_MES[mes]}, não encontrei gastos registrados em {categoria}."

    exemplos = ", ".join(
        f"{linha.descricao} (R$ {formatar_moeda(float(linha.valor))})"
        for linha in gastos_categoria[["descricao", "valor"]].itertuples(index=False)
    )
    return (
        f"Em {NUMERO_PARA_MES[mes]}, você gastou R$ {formatar_moeda(total)} com {categoria}. "
        f"As transações desse grupo foram: {exemplos}."
    )


def responder_recomendacao() -> str:
    produtos_adequados = ", ".join(produto["nome"] for produto in produtos[:3])
    return (
        "Eu não posso recomendar um investimento específico para você, mas posso te explicar opções mais conservadoras. "
        f"Como seu perfil é {perfil['perfil_investidor']}, faz sentido começar entendendo produtos como {produtos_adequados}. "
        "Se quiser, eu posso comparar essas opções de forma educativa."
    )


def responder_fora_do_escopo() -> str:
    return "Sou especializado em educação financeira. Posso te ajudar com gastos, reserva de emergência e investimentos básicos."


def responder_ativo_desconhecido() -> str:
    return "Não tenho essa informação na minha base atual. Posso explicar como avaliar um ativo ou falar dos produtos que estão no seu contexto."


RESPOSTAS_EDUCATIVAS = {
    "cdi": (
        "O CDI — Certificado de Depósito Interbancário — é uma taxa usada pelos bancos para emprestar dinheiro entre si. "
        "Na prática, ele funciona como referência para investimentos de renda fixa: CDBs, LCIs, LCAs e fundos DI costumam render um percentual do CDI. "
        "Por exemplo, um CDB que rende 100% do CDI vai render praticamente o mesmo que a taxa básica de juros. "
        "Para você, Ana, que tem perfil conservador, investimentos atrelados ao CDI são uma boa base para a reserva de emergência. "
        "Entendeu? Quer que eu explique como comparar produtos que rendem % do CDI?"
    ),
    "tesouro selic": (
        "O Tesouro Selic é um título público emitido pelo governo federal. Quando você compra, está emprestando dinheiro para o governo e recebendo juros. "
        "Ele acompanha a taxa Selic — a taxa básica de juros do Brasil — e tem liquidez diária, ou seja, você pode resgatar quando quiser sem perder rendimento. "
        "Para quem está montando reserva de emergência, como você Ana, o Tesouro Selic é uma das opções mais seguras e acessíveis: dá pra começar com R$ 30. "
        "A principal vantagem: segurança máxima (garantido pelo governo) com rendimento bem acima da poupança. "
        "Quer saber como comprar pelo Tesouro Direto?"
    ),
    "reserva de emergência": (
        "Reserva de emergência é um valor guardado para cobrir imprevistos — perda de emprego, doença, conserto urgente — sem precisar pegar empréstimo. "
        "A regra geral é ter de 3 a 6 meses de gastos mensais guardados. Com sua renda de R$ 4.500, isso seria entre R$ 13.500 e R$ 27.000. "
        f"Você já tem R$ {perfil['reserva_emergencia_atual']:,.0f} guardados — são {(perfil['reserva_emergencia_atual']/perfil['metas'][0]['valor_necessario']*100):.0f}% da sua meta de R$ {perfil['metas'][0]['valor_necessario']:,.0f}. Ótimo progresso! "
        "O ideal é deixar essa reserva em investimentos com liquidez diária, como Tesouro Selic ou CDB de liquidez diária. "
        "Quer dicas de como acelerar essa meta?"
    ),
}

def resposta_deterministica(pergunta: str) -> str | None:
    pergunta_normalizada = pergunta.lower().strip()

    for chave, resposta in RESPOSTAS_EDUCATIVAS.items():
        if chave in pergunta_normalizada:
            return resposta

    if any(termo in pergunta_normalizada for termo in ["previsão do tempo", "previsao do tempo", "clima", "tempo amanhã", "tempo amanha"]):
        return responder_fora_do_escopo()

    if re.search(r"\b[a-z]{4}\d{1,2}\b", pergunta_normalizada) or "bovespa" in pergunta_normalizada:
        return responder_ativo_desconhecido()

    if any(termo in pergunta_normalizada for termo in ["recomenda", "recomendação", "recomendacao", "devo investir"]):
        return responder_recomendacao()

    return responder_gastos(pergunta_normalizada)


# ============ CHAMAR OLLAMA (STREAMING) ============
def stream_resposta(historico_msgs: list[dict], nova_pergunta: str):
    """Gerador que produz tokens do LLM um a um para streaming no Streamlit."""
    historico_txt = ""
    for msg in historico_msgs[-4:]:
        role = "Usuário" if msg["role"] == "user" else "Edu"
        historico_txt += f"{role}: {msg['content']}\n"

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"CONTEXTO:\n{contexto_llm}\n\n"
        f"HISTÓRICO:\n{historico_txt}\n"
        f"Usuário: {nova_pergunta}\nEdu:"
    )

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODELO,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 120,
                },
            },
            stream=True,
            timeout=90,
        )
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done", False):
                    break
    except requests.exceptions.ReadTimeout:
        yield "⚠️ O modelo demorou além do esperado. Tente uma pergunta mais curta."
    except requests.exceptions.ConnectionError:
        yield "⚠️ Não consegui conectar ao Ollama. Verifique se ele está rodando com `ollama serve`."
    except Exception as e:
        yield f"⚠️ Erro inesperado: {e}"

def main():
    st.set_page_config(page_title="Edu — Educador Financeiro", page_icon="🎓")

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

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.write(SAUDACAO)

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if nova_pergunta := st.chat_input("Sua dúvida sobre finanças..."):
        st.session_state.messages.append({"role": "user", "content": nova_pergunta})
        st.chat_message("user").write(nova_pergunta)

        resposta_imediata = resposta_deterministica(nova_pergunta)
        if resposta_imediata:
            import time
            def _stream_texto(texto):
                for palavra in texto.split(" "):
                    yield palavra + " "
                    time.sleep(0.04)
            with st.chat_message("assistant"):
                resposta = st.write_stream(_stream_texto(resposta_imediata))
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        else:
            with st.chat_message("assistant"):
                resposta = st.write_stream(stream_resposta(st.session_state.messages[:-1], nova_pergunta))
            st.session_state.messages.append({"role": "assistant", "content": resposta})


if __name__ == "__main__":
    main()
