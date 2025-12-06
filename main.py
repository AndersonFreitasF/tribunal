import streamlit as st
import requests
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="PITACO F.C.",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"
CONTEXT_WINDOW = 8192
SCORES_FILE = "council_memory.json"
TECH_BIBLE_FILE = "project_context.md"

GLOBAL_INSTRUCTIONS = """
DIRETRIZES GERAIS:
1. CONFIDENCE CHECK (OBRIGATÓRIO): Antes de responder, avalie sua confiança interna (0-100%).
   - Se Confiança < 80%: NÃO ADIVINHE. Declare: "⚠️ Baixa Confiança (<80%): [Motivo]".
   - Se Confiança >= 80%: Inicie a resposta com "✅ Confiança: [XX]%". Seja sincero e não minta sua confiança para passar dos 80 e ser bem visto
2. NÃO GERE CÓDIGO IMPLEMENTADO. Gere arquitetura, lógica abstrata e diagramas estruturais.
3. REGRA DE TRADE-OFF: Liste obrigatoriamente 1 Custo/Risco e 1 Ponto de Falha.
4. FORMATO: Use Markdown para repassar as informações. Seja técnico e direto.
5. PERSONALIDADE & FRONTEIRAS: 
   - Mantenha-se ESTRITAMENTE no seu personagem.
   - OMITA assuntos fora da sua alçada.
6. DEVER DE VETO: Se um colega sugerir algo que QUEBRA o seu domínio, CRITIQUE AGRESSIVAMENTE.
7. MENTALIDADE DE QUEBRA-CABEÇA: Você não está competindo. Você está fornecendo uma peça única para montar o todo.
"""

PROMPTS = {
    "INTERROGADOR": f"""
    ROLE: Analista de Requisitos Sênior.
    TAREFA: Analise o pedido e identifique lacunas que impedem a montagem do quebra-cabeça técnico.
    PERGUNTE SOBRE:
    1. Escopo Funcional (Essencial vs Nice-to-have).
    3. Regras de negocio que não foram especificadas
    4. FORMATO: Use Markdown para repassar as informações. Seja técnico e direto.
    5. PERSONALIDADE & FRONTEIRAS: 
   - Mantenha-se ESTRITAMENTE no seu personagem.
   - OMITA assuntos fora da sua alçada.
    """,

    "ESTETA": f"""
    ROLE: Head de Design & Developer Experience (DX).
    FOCO: Frontend Frameworks, UI/UX, Paleta de Cores, Ergonomia da API.
    TAREFA: Defina a "Cara" e o "Tato" do projeto.
    1. Stack Front/DX: Decida framework (Considere todos os frameworks do typescript/javascript). Justifique pelo DX.
    2. Design System: Sugira paleta de cores exata (Hex) e biblioteca de componentes (Shadcn, Material, TailwindUI).
    3. Usabilidade: Defina a navegação macro e feedback visual.
    """,

    "ARQUITETO": f"""
    ROLE: Arquiteto de Software & Tech Lead.
    FOCO: Estrutura de Pastas, Padrões de Projeto, Comunicação entre Módulos.
    TAREFA: Defina o esqueleto lógico.
    1. Organização: Monolito Modular vs Microservices?
    2. Padrões: Onde aplicar Factory, Strategy, Observer? Clean Architecture ou MVC simples?
    3. Fluxo: Diagrama Mermaid da comunicação entre módulos.
    4. Stack Back: Elysia vs Express? Node.js? Considere todos os frameworks e decida o melhor
    {GLOBAL_INSTRUCTIONS}
    """,

    "ARQUIVISTA": f"""
    ROLE: Engenheiro de Dados & DBA.
    FOCO: Modelagem E-R, Entidades, SQL vs NoSQL.
    TAREFA: Modele a persistência.
    1. Análise de Entidades: Quais as classes principais (Ex: User, Order)? Como se relacionam (1:N, N:N)?
    2. Veredito do Banco: Baseado nas relações, SQL (Postgres) ou NoSQL (Mongo)?
    3. Schema: Defina o esquema inicial e chaves.
    {GLOBAL_INSTRUCTIONS}
    """,

    "OTIMIZADOR": f"""
    ROLE: Engenheiro de Performance & Algoritmos.
    FOCO: Estruturas de Dados, Custo Computacional, Libs vs Native.
    TAREFA: Analise a eficiência.
    1. Quais libs devemos usar?
    2. Estruturas de Dados: Quais otimizações de codigos podemos fazer ainda na etapa de estruturação?
    3. Gargalos: Onde vai vazar memória? Onde teremos N+1 queries?
    {GLOBAL_INSTRUCTIONS}
    """,

    "OPS": f"""
    ROLE: SRE & Engenheiro de Infraestrutura.
    FOCO: Sizing (P/M/G), Escalabilidade, Hosting.
    TAREFA: Defina o tamanho e o lugar do projeto.
    1. T-Shirt Sizing: O projeto é P (Hobby), M (Startup) ou G (Enterprise)?
    2. Infra Realista: Se P, proíba K8s (use Vercel/Railway). Se G, desenhe Cluster.
    3. Escalabilidade: Como escalar verticalmente ou horizontalmente?
    {GLOBAL_INSTRUCTIONS}
    """,

    "PARANOICO": f"""
    ROLE: Engenheiro de Segurança (AppSec).
    FOCO: Auth Flows, Vulnerabilidades da Stack, Dados Sensíveis.
    TAREFA: Blinde o sistema.
    1. Autenticação: JWT, Session ou OAuth2? Adequado ao porte?
    2. Vetores de Ataque: Previna Injection (SQL/NoSQL), XSS, CSRF conforme a stack escolhida.
    {GLOBAL_INSTRUCTIONS}
    """,

    "MONTAGEM_DO_QUEBRA_CABECA": """
    ROLE: Tech Lead Integrador (Mediador).
    TAREFA: Monte o "Tabuleiro Inicial" juntando as peças dos agentes.
    1. Identifique as melhores peças de cada um.
    2. Resolva conflitos técnicos (Ex: Se OPS disse que é projeto PEQUENO, descarte sugestões complexas do Arquiteto).
    3. Gere um RESUMO TÉCNICO UNIFICADO.
    """,

    "VOTO_IDEIAS": """
    ROLE: Auditor Técnico.
    TAREFA: Analise o Tabuleiro Montado. Vote nas IDEIAS, não nas pessoas.
    Identifique 1 componente que deve ser REMOVIDO ou ALTERADO.
    SAIDA ESPERADA JSON: {"veto": "NOME_DA_IDEIA", "motivo": "...", "sugestao": "..."}
    """
}

AGENTES_ATIVOS = ["ESTETA", "ARQUIVISTA", "ARQUITETO", "OTIMIZADOR", "PARANOICO", "OPS"]

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r") as f: return json.load(f)
        except: pass
    return {k: 0 for k in AGENTES_ATIVOS}

def save_scores(scores):
    with open(SCORES_FILE, "w") as f: json.dump(scores, f, indent=2)

def load_tech_bible():
    try:
        with open(TECH_BIBLE_FILE, "r", encoding="utf-8") as f: return f.read()
    except FileNotFoundError: return "Nenhuma restrição global definida."

def call_ollama(agent_name, system_prompt, user_input, json_mode=False, temperature=0.5):
    full_prompt = f"SYSTEM:\n{system_prompt}\n\nCONTEXT:\n{user_input}"
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {"num_ctx": CONTEXT_WINDOW, "temperature": temperature}
    }
    if json_mode: payload["format"] = "json"

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        return "{}" if json_mode else f"Erro de conexão: {e}"

if "step" not in st.session_state: st.session_state.step = 0
if "transcript" not in st.session_state: st.session_state.transcript = "### LOG DE MONTAGEM ###\n"
if "problema" not in st.session_state: st.session_state.problema = ""
if "respostas_user" not in st.session_state: st.session_state.respostas_user = ""
if "pecas_iniciais" not in st.session_state: st.session_state.pecas_iniciais = {}
if "tabuleiro_montado" not in st.session_state: st.session_state.tabuleiro_montado = ""
if "blueprint_final" not in st.session_state: st.session_state.blueprint_final = ""

with st.sidebar:
    st.header("Status")
    st.progress(st.session_state.step / 5)
    st.info("Modo: Colaborativo")
    
    st.divider()
    if st.button("Reiniciar"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.title(" PITACO F.C.")
st.markdown("---")

if st.session_state.step == 0:
    st.subheader("1. Estruturação Inicial")
    st.markdown("Descreva o sistema que vamos montar.")
    problema_input = st.text_area("Descrição do Projeto:", height=100)
    
    if st.button("Enviar Ideia") and problema_input:
        st.session_state.problema = problema_input
        st.session_state.step = 1
        st.rerun()

elif st.session_state.step == 1:
    st.subheader("2. Análise")
    st.info(f"Projeto: {st.session_state.problema}")
    
    if "briefing_text" not in st.session_state:
        with st.spinner("O Analista está verificando se faltam peças..."):
            resp = call_ollama("INTERROGADOR", PROMPTS["INTERROGADOR"], st.session_state.problema, temperature=0.6)
            st.session_state.briefing_text = resp
            st.session_state.transcript += f"\n\n[INTERROGADOR]:\n{resp}"
    
    st.markdown(st.session_state.briefing_text)
    respostas = st.text_area("Detalhes Adicionais (Crucial para o OPS definir o tamanho):", height=150)
    
    if st.button("Confirmar Requisitos"):
        st.session_state.respostas_user = respostas
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.subheader("3. Montagem Inicial (Especialistas)")
    contexto = f"PROJETO: {st.session_state.problema}\nDETALHES: {st.session_state.respostas_user}"
    
    if not st.session_state.pecas_iniciais:
        my_bar = st.progress(0, text="Especialistas analisando suas áreas...")
        
        for i, agente in enumerate(AGENTES_ATIVOS):
            prompt = f"Analise o contexto. Lembre-se: Confidence Check obrigatório. Seja específico na sua área.\nCONTEXTO:\n{contexto}"
            resp = call_ollama(agente, PROMPTS[agente], prompt, temperature=0.5)
            st.session_state.pecas_iniciais[agente] = resp
            st.session_state.transcript += f"\n\n[{agente}]:\n{resp}"
            my_bar.progress((i + 1) / len(AGENTES_ATIVOS))
        
        my_bar.empty()

    col1, col2 = st.columns(2)
    items = list(st.session_state.pecas_iniciais.items())
    half = len(items) // 2
    
    with col1:
        for k, v in items[:half]:
            with st.expander(f"Peça do {k}", expanded=True):
                st.markdown(v)
    with col2:
        for k, v in items[half:]:
            with st.expander(f"Peça do {k}", expanded=True):
                st.markdown(v)

    st.markdown("---")
    st.subheader("Estruturação provisoria")
    
    if not st.session_state.tabuleiro_montado:
        with st.spinner("O Integrador está tentando encaixar as peças..."):
            resumo_pecas = "\n\n".join([f"[{k} SUGESTÃO]:\n{v}" for k, v in st.session_state.pecas_iniciais.items()])
            prompt_integrador = f"CONTEXTO DO PROJETO: {contexto}\n\nIDEIAS SUGERIDAS:\n{resumo_pecas}"
            
            tabuleiro = call_ollama("INTEGRADOR", PROMPTS["MONTAGEM_DO_QUEBRA_CABECA"], prompt_integrador, temperature=0.3)
            st.session_state.tabuleiro_montado = tabuleiro
            st.session_state.transcript += f"\n\n[TABULEIRO INICIAL]:\n{tabuleiro}"

    st.markdown(st.session_state.tabuleiro_montado)
    
    if st.button("Avançar para Refinamento"):
        st.session_state.step = 3
        st.rerun()

elif st.session_state.step == 3:
    st.subheader("4. Ajuste Fino e Vetos")
    st.info("Os agentes agora vão olhar para o Tabuleiro Montado e apontar peças que não encaixam.")
    
    if "vetos" not in st.session_state:
        st.session_state.vetos = []
        with st.spinner("Auditando o sistema..."):
            for agente in AGENTES_ATIVOS:
                prompt_auditoria = f"""
                VOCÊ É O {agente}.
                TABULEIRO ATUAL:
                {st.session_state.tabuleiro_montado}
                
                TAREFA: Analise se alguma decisão tomada acima prejudica sua área.
                Se estiver tudo ok, retorne json vazio.
                """
                resp = call_ollama(agente, PROMPTS["VOTO_IDEIAS"], prompt_auditoria, json_mode=True, temperature=0.2)
                
                try:
                    data = json.loads(resp)
                    if data.get("veto"):
                        st.session_state.vetos.append({
                            "autor": agente,
                            "alvo": data["veto"],
                            "motivo": data["motivo"],
                            "sugestao": data.get("sugestao", "N/A")
                        })
                except: pass

    if st.session_state.vetos:
        st.warning(f"Foram identificados {len(st.session_state.vetos)} pontos de atrito:")
        for v in st.session_state.vetos:
            st.error(f"**{v['autor']}** vetou **'{v['alvo']}'**")
            st.markdown(f"Motivo: *{v['motivo']}*")
            st.success(f"Sugestão: {v['sugestao']}")
            st.divider()
    else:
        st.success("✅ Nenhuma peça fora do lugar! Consenso atingido.")

    st.markdown("### Instruções Finais para o Humano")
    user_adjustment = st.text_input("Deseja forçar alguma troca de peça?", "")

    if st.button("Gerar Blueprint Final"):
        st.session_state.final_adjust = user_adjustment
        st.session_state.step = 4
        st.rerun()

elif st.session_state.step == 4:
    st.subheader("5. A Imagem Final (Blueprint)")
    
    if not st.session_state.blueprint_final:
        with st.spinner("Colando as peças..."):
            vetos_str = json.dumps(st.session_state.vetos) if "vetos" in st.session_state else "Nenhum"
            prompt_final = f"""
            CONTEXTO ORIGINAL: {st.session_state.problema}
            TABULEIRO DRAFT: {st.session_state.tabuleiro_montado}
            CRÍTICAS/VETOS DOS ESPECIALISTAS: {vetos_str}
            AJUSTE FINAL DO USUÁRIO: {st.session_state.get('final_adjust', 'Nenhum')}
            
            TAREFA:
            Reescreva a arquitetura final resolvendo os vetos.
            Se o OPS definiu o tamanho como P (Pequeno), simplifique tudo.
            Inclua diagrama Mermaid.
            """
            
            blueprint = call_ollama("INTEGRADOR", "Gere o Blueprint Final consolidado.", prompt_final, temperature=0.3)
            st.session_state.blueprint_final = blueprint
            
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs("output", exist_ok=True)
            with open(f"output/blueprint_{ts}.md", "w") as f: f.write(blueprint)

    st.markdown(st.session_state.blueprint_final)
    
    st.download_button(
        label="📥 Baixar Blueprint",
        data=st.session_state.blueprint_final,
        file_name="blueprint_puzzle.md",
        mime="text/markdown"
    )
    
    with st.expander("Ver Log Completo"):
        st.text(st.session_state.transcript)