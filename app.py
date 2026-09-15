import os
import re
import time
import streamlit as st
from google import genai
from google.genai import types

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Risco AG & FBC - Decision Engine & Credit Rating",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização CSS para interface limpa e profissional
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    .block-container {
        padding-top: 2rem !important;
        max-width: 95% !important;
    }
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    h1, h2, h3, h4, h5, h6, label, p, span, .stMarkdown {
        color: #f8fafc !important;
    }
    code {
        background-color: transparent !important;
        color: #f8fafc !important;
        border: none !important;
        padding: 0 !important;
        font-family: inherit !important;
        font-size: inherit !important;
        font-weight: inherit !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1e293b !important;
        border: 2px dashed #475569 !important;
        border-radius: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #334155 !important;
        color: #ffffff !important;
        border: 1px solid #64748b !important;
        border-radius: 6px !important;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #475569 !important;
        color: #ffffff !important;
    }
    [data-testid="stFileUploaderDropzone"] span, 
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderFileData"] {
        color: #cbd5e1 !important;
    }
    .stButton>button {
        background-color: #10b981 !important;
        color: #0f172a !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        width: 100% !important;
        font-size: 1.05rem !important;
    }
    .stButton>button:hover {
        background-color: #34d399 !important;
        color: #0f172a !important;
    }
    .stAlert {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Obtém a chave configurada nos Secrets
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")).strip()

# Cabeçalho
st.title("RISCO AG / FBC")
st.caption("Motor de Decisão, Auditoria do Passivo Judicial e Rating de Crédito Agrícola")

st.markdown("---")

# Layout Principal
col_left, col_right = st.columns([4, 8])

with col_left:
    st.subheader("Envio do Processo")
    uploaded_file = st.file_uploader("Arraste ou selecione o PDF integral dos autos:", type=["pdf"])
    
    btn_processar = st.button("Gerar Rating e Diagnóstico", disabled=(uploaded_file is None))

SYSTEM_INSTRUCTION = """
Você é um Comitê de Risco de Crédito e Inteligência de Concessão especializado em Agronegócio. Sua função é auditar o passivo judicial exposto no processo analisado sob a ótica EXCLUSIVA de TOMADA DE DECISÃO DE CRÉDITO para uma futura operação de financiamento/fomento ao produtor/tomador avaliado.

Você NÃO é o advogado das partes no processo. Portanto, NUNCA dê sugestões de estratégia de cobrança, execução, medidas judiciais contra o réu ou peticionamento.

Sua análise deve responder à pergunta principal: "Qual o impacto deste processo no risco de crédito do tomador e sob quais condições e garantias ele pode ser financiado?"

AO ANALISAR OS AUTOS, OBEDEÇA RIGOROSAMENTE À SEGUINTE ESTRUTURA DE DIAGNÓSTICO:

1. DADOS DE IDENTIFICAÇÃO E MATERIALIDADE
   - Identificação das Partes e Juízo.
   - Classe Processual e Origem do Débito.
   - Valor do Passivo Judicial Atualizado e Materialidade da Exposição.

2. AVALIAÇÃO DE EXPOSIÇÃO E SENSIVILIDADE OPERACIONAL
   - Risco de Constrição Imediata: Avaliar o risco real de o tomador sofrer bloqueio de contas (SISBAJUD), retenção de grãos em Tradings ou arresto de safras durante o ciclo do novo financiamento.
   - Comportamento de Defesa: Avaliar se o devedor demonstrou inércia/revelia ou se há teses defensivas com potencial de anulação da dívida.

3. PARECER DO COMITÊ DE CRÉDITO E RECOMENDAÇÃO DE CONCESSÃO
   - Diagnóstico Final de Rating de Crédito (Ex: Risco Baixo, Moderado, Alto ou Crítico).
   - Recomendação Final de Financiamento: (Aprovado / Aprovado com Condicionantes / Desfavorável).
   - Estruturação de Garantias e Exigências Mitigatórias: Indicar detalhadamente as garantias requeridas caso se opte por financiar o cliente (ex: Alienação Fiduciária de Imóvel Rural com margem superior, CPR Física com Penhor de 1ª Categoria sobre área isenta de litígio, Avalista/Fiador de alto patrimônio, Travamento de recebíveis/Contrato de venda futura com Tradings de primeira linha).

REGRA DE FORMATAÇÃO:
- Escreva todos os valores estritamente no formato R$ 0,00 (ex: R$ 130.958,18).
- NUNCA utilize crases (` `) para destacar valores, números, IDs ou datas.
"""

with col_right:
    st.subheader("📊 Diagnóstico de Risco & Decisão de Crédito")
    
    if btn_processar and uploaded_file is not None:
        if not api_key:
            st.error("Chave de API não configurada. Verifique as 'Secrets' no painel do Streamlit Cloud.")
        else:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Analisando autos sob a ótica de Risco e Concessão de Crédito..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    arquivo_processo = client.files.upload(file=temp_path)
                    
                    config = types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                    )
                    
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[
                            arquivo_processo,
                            "Realize o diagnóstico completo de Risco e Decisão de Concessão de Crédito deste tomador com base nos autos, seguindo rigorosamente a estrutura definida nas instruções do sistema.",
                        ],
                        config=config,
                    )
                    
                    client.files.delete(name=arquivo_processo.name)
                    os.remove(temp_path)
                    
                    if response and response.text:
                        st.success("Análise de Concessão de Crédito concluída com sucesso!")
                        
                        # Formatação para exibição limpa dos valores
                        texto_formatado = response.text
                        texto_formatado = re.sub(r'R\s+(\d)', r'R$ \1', texto_formatado)
                        texto_formatado = re.sub(r'R\$\s*', r'R$ ', texto_formatado)
                        
                        st.markdown(texto_formatado)
                    else:
                        st.error("Não foi possível obter resposta do modelo. Tente novamente.")
                        
                except Exception as e:
                    st.error(f"Erro no processamento: {str(e)}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    else:
        st.info("Aguardando upload de arquivo PDF para gerar o parecer de crédito e a matriz de mitigação.")
