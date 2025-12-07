import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledText
from tkinter import font as tkfont
from tkinter import messagebox
import requests
import json
import os
import concurrent.futures
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"
CONTEXT_WINDOW = 8192
TECH_BIBLE_FILE = "project_context.md"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("AVISO: Chave GEMINI_API_KEY não encontrada no arquivo .env")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def load_tech_bible():
    try:
        with open(TECH_BIBLE_FILE, "r", encoding="utf-8") as f: 
            return f.read()
    except FileNotFoundError: 
        return "Nenhuma restrição global definida."

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

def call_gemini_api(prompt_context):
    headers = {'Content-Type': 'application/json'}
    
    system_instruction = """
    ROLE: Senior Fullstack Developer.
    TASK: Baseado na arquitetura (Blueprint) fornecida, gere o código real para um MVP.
    OUTPUT: Crie a estrutura de arquivos e o conteúdo dos arquivos principais. 
    Seja prático e forneça código executável.
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_instruction}\n\nBLUEPRINT:\n{prompt_context}"}]
        }]
    }
    
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Erro na API Gemini: {str(e)}"

TECH_BIBLE_CONTENT = load_tech_bible()

GLOBAL_INSTRUCTIONS = f"""
DIRETRIZES GERAIS:
1. NÃO GERE CÓDIGO IMPLEMENTADO. Gere arquitetura, lógica abstrata e diagramas estruturais.
2. FORMATO: Use Markdown. Seja técnico e direto.
3. PERSONALIDADE & FRONTEIRAS: Mantenha-se ESTRITAMENTE no seu personagem.

CONTEXTO TÉCNICO DO PROJETO (TECH BIBLE):
{TECH_BIBLE_CONTENT}
"""

PROMPTS = {
    "INTERROGADOR": f"""
    ROLE: Analista de Requisitos Sênior.
    TAREFA: Analise o pedido e identifique lacunas.
    PERGUNTE SOBRE:
    1. Escopo Funcional (Essencial vs Nice-to-have).
    2. Regras de negocio não especificadas.
    {GLOBAL_INSTRUCTIONS}
    """,

    "ESTETA": f"""
    ROLE: Head de Design & Developer Experience (DX).
    FOCO: Frontend Frameworks, UI/UX, Paleta de Cores, Ergonomia da API.
    TAREFA: Defina a "Cara" e o "Tato" do projeto.
    1. Stack Front/DX: Decida framework. Justifique pelo DX.
    2. Design System: Sugira paleta (Hex) e lib de componentes.
    3. Usabilidade: Navegação e feedback.
    4. Linguagem Visual: Decida o estilo visual do projeto e sugira as cores baseadas no estilo decidido.Use a seguinte lista para escolher: 
    -.  **ÓLEO SOBRE TELA:** Texturas de pinceladas, bordas irregulares, tipografia serifada pesada, tons terrosos.
    -  **SUMI-E (TINTA):** Minimalismo oriental, alto contraste P&B, texturas de papel de arroz, espaço negativo.
    -  **LIGNE CLAIRE:** Flat design absoluto, contornos pretos finos (1px), cores sólidas saturadas, sem degradês.
    -  **VINTAGE 1930:** Granulação de filme, fontes retrô, formas arredondadas, paleta Technicolor desbotada.
    -  **1-BIT DITHERING:** Brutalismo monocromático, pontilhismo para sombras, fontes monoespaçadas.
    -  **GLASSMORPHISM 2.0:** Transparências foscas, bordas brilhantes, gradientes sutis (Estilo Apple Vision).
    """,

    "ARQUITETO": f"""
    ROLE: Arquiteto de Software & Tech Lead.
    FOCO: Estrutura de Pastas, Padrões, Comunicação entre Módulos.
    TAREFA: Defina o esqueleto lógico.
    1. Organização: Monolito vs Microservices?
    2. Padrões: Qual design patter usar?
    3. Fluxo: Diagrama Mermaid.
    4. Stack Back: Decida framework e linguagem.
    {GLOBAL_INSTRUCTIONS}
    """,

    "ARQUIVISTA": f"""
    ROLE: Engenheiro de Dados & DBA.
    FOCO: Modelagem E-R, SQL vs NoSQL.
    TAREFA: Modele a persistência.
    1. Entidades: Classes principais e relações caso seja existam relações.
    2. Banco: SQL ou NoSQL?
    3. Schema: Esquema inicial. Nomes de tabelas no plural, chaves estrangeiras explícitas.
    {GLOBAL_INSTRUCTIONS}
    """,

    "OTIMIZADOR": f"""
    ROLE: Engenheiro de Performance & Algoritmos.
    FOCO: Estruturas de Dados, Custo, Libs.
    TAREFA: Analise a eficiência.
    1. Libs recomendadas.
    2. Otimizações estruturais.
    3. Gargalos de memória/query.
    {GLOBAL_INSTRUCTIONS}
    """,

    "OPS": f"""
    ROLE: SRE & Engenheiro de Infraestrutura.
    FOCO: Sizing, Escalabilidade, Hosting.
    TAREFA: Defina o tamanho e lugar.
    1. T-Shirt Sizing: P (Hobby), M (Startup) ou G (Enterprise)?
    2. Infra Realista: Proíba K8s se P.
    3. Escalabilidade.
    {GLOBAL_INSTRUCTIONS}
    """,

    "PARANOICO": f"""
    ROLE: Engenheiro de Segurança (AppSec).
    FOCO: Auth Flows, Vulnerabilidades.
    TAREFA: Blinde o sistema.
    1. Autenticação: JWT, Session, OAuth2?
    2. Vetores de Ataque: Injection, XSS, CSRF.
    {GLOBAL_INSTRUCTIONS}
    """,

    "MONTAGEM_DO_QUEBRA_CABECA": """
    ROLE: Tech Lead Integrador (Mediador).
    TAREFA: Monte o "Esquema Inicial" juntando as ideias dos agentes.
    1. Identifique as melhores ideias de cada um.
    2. Resolva conflitos técnicos baseados na TECH BIBLE.
    3. Gere um RESUMO TÉCNICO UNIFICADO.
    """,

    "VOTO_IDEIAS": """
    ROLE: Auditor Técnico.
    TAREFA: Analise o Esquema Montado. Vote nas IDEIAS, não nas pessoas.
    Identifique 1 componente que deve ser REMOVIDO ou ALTERADO.
    SAIDA ESPERADA JSON: {"veto": "NOME_DA_IDEIA", "motivo": "...", "sugestao": "..."}
    """
}

AGENTES_ATIVOS = ["ESTETA", "ARQUIVISTA", "ARQUITETO", "OTIMIZADOR", "PARANOICO", "OPS"]

class PitacoApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("TRIBUNAL // THOUGHT CABINET")
        self.geometry("600x950")
        
        style = ttk.Style()
        
        self.colors = {
            "bg": "#1a1a1a",
            "panel": "#242424",
            "text": "#dcdccc",
            "accent": "#d65d0e",
            "success": "#98971a",
            "danger": "#cc241d",
            "muted": "#928374",
            "blue": "#458588"
        }

        self.fonts = {
            "header": ("Georgia", 14, "bold"),
            "body": ("Courier New", 10),
            "ui": ("Impact", 10)
        }

        style.configure(".", background=self.colors["bg"], foreground=self.colors["text"], font=self.fonts["body"])
        style.configure("TFrame", background=self.colors["bg"])
        
        style.configure(
            "Disco.TButton",
            font=self.fonts["ui"],
            background=self.colors["accent"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(10, 10)
        )
        style.map("Disco.TButton", background=[('active', '#bf4d00'), ('disabled', '#3c3836')])

        style.configure(
            "Header.TLabel",
            font=self.fonts["header"],
            foreground="#fabd2f",
            background=self.colors["bg"]
        )

        self.step = 0
        self.transcript = "/// INICIANDO LOG DE PENSAMENTO ///\n"
        self.problema = ""
        self.respostas_user = ""
        self.ideias_iniciais = {}
        self.esquema_montado = ""
        self.blueprint_final = ""
        self.vetos = []
        self.final_adjust = ""
        self.is_saved = False
        
        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill=BOTH, expand=True)

        self.sidebar = ttk.Frame(self.main_container, width=8, bootstyle="warning")
        self.sidebar.pack(side=LEFT, fill=Y, padx=(0, 20))

        self.content_area = ttk.Frame(self.main_container)
        self.content_area.pack(side=LEFT, fill=BOTH, expand=True)

        self.lbl_header = ttk.Label(self.content_area, text="TRIBUNAL // NOVO CASO", style="Header.TLabel")
        self.lbl_header.pack(anchor="w", pady=(0, 20))

        self.dynamic_frame = ttk.Frame(self.content_area)
        self.dynamic_frame.pack(fill=BOTH, expand=True)

        self.render_step_0()

    def clear_content(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

    def check_restart(self):
        if self.is_saved or self.step < 4:
            self.reset_app()
        else:
            resposta = messagebox.askyesno(
                "CASO NÃO ARQUIVADO", 
                "O Diagrama ainda não foi salvo.\nSe voltar agora, os dados serão perdidos.\n\nDeseja voltar mesmo assim?"
            )
            if resposta:
                self.reset_app()

    def reset_app(self):
        self.step = 0
        self.transcript = "/// RESET ///\n"
        self.problema = ""
        self.respostas_user = ""
        self.ideias_iniciais = {}
        self.esquema_montado = ""
        self.blueprint_final = ""
        self.vetos = []
        self.is_saved = False
        self.render_step_0()

    def render_step_0(self):
        self.clear_content()
        self.lbl_header.config(text="1. CONCEITUALIZAÇÃO")
        
        ttk.Label(self.dynamic_frame, text="QUAL O PROBLEMA, DETETIVE?", font=("Courier New", 12, "bold")).pack(anchor="w")
        ttk.Label(self.dynamic_frame, text="Descreva o sistema abstrato.", font=("Courier New", 9, "italic"), foreground=self.colors["muted"]).pack(anchor="w", pady=(0, 10))
        
        self.txt_problema = ScrolledText(
            self.dynamic_frame, 
            height=10, 
            font=("Courier New", 10),
            background="#0f0f0f", 
            foreground="#dcdccc",
            relief="flat",
            borderwidth=1,
            insertbackground="white"
        )
        self.txt_problema.pack(fill=X, pady=10)
        
        ttk.Button(
            self.dynamic_frame, 
            text="[INTERNALIZAR PENSAMENTO] ➤", 
            style="Disco.TButton", 
            command=self.process_step_0
        ).pack(anchor="e", pady=20)

    def process_step_0(self):
        texto = self.txt_problema.text.get("1.0", END).strip()
        if texto:
            self.problema = texto
            self.step = 1
            self.render_step_1()

    def render_step_1(self):
        self.clear_content()
        self.lbl_header.config(text="2. INTERROGATÓRIO")
        
        ttk.Label(self.dynamic_frame, text=f"> CASO: {self.problema[:40]}...", foreground=self.colors["muted"]).pack(anchor="w")
        
        self.loading_lbl = ttk.Label(self.dynamic_frame, text="[LOGIC] Analisando lacunas...", foreground="#458588")
        self.loading_lbl.pack(pady=20)
        
        threading.Thread(target=self.run_interrogator, daemon=True).start()

    def run_interrogator(self):
        resp = call_ollama("INTERROGADOR", PROMPTS["INTERROGADOR"], self.problema, temperature=0.6)
        self.transcript += f"\n\n[INTERROGADOR]:\n{resp}"
        self.after(0, lambda: self.show_interrogator_result(resp))

    def show_interrogator_result(self, result):
        self.loading_lbl.destroy()
        
        ttk.Label(self.dynamic_frame, text="INTERROGADOR [Fácil]:", font=("Impact", 11), foreground="#d3869b").pack(anchor="w")
        
        txt_display = ScrolledText(self.dynamic_frame, height=12, font=("Courier New", 10), background="#1d2021", foreground="#dcdccc")
        txt_display.insert(END, result)
        txt_display.text.configure(state='disabled')
        txt_display.pack(fill=X, pady=10)
        
        ttk.Label(self.dynamic_frame, text="DETALHES ADICIONAIS:").pack(anchor="w")
        self.txt_respostas = ScrolledText(self.dynamic_frame, height=6, background="#0f0f0f", foreground="#dcdccc")
        self.txt_respostas.pack(fill=X, pady=10)
        
        ttk.Button(self.dynamic_frame, text="[PROCEDER] ➤", style="Disco.TButton", command=self.process_step_1).pack(anchor="e", pady=10)

    def process_step_1(self):
        self.respostas_user = self.txt_respostas.text.get("1.0", END).strip()
        self.step = 2
        self.render_step_2()

    def render_step_2(self):
        self.clear_content()
        self.lbl_header.config(text="3. O TRIBUNAL")
        
        ttk.Label(self.dynamic_frame, text="As vozes na sua cabeça começam a discutir...", font=("Courier New", 10, "italic")).pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(self.dynamic_frame, orient=HORIZONTAL, length=100, mode='determinate', bootstyle="danger")
        self.progress_bar.pack(fill=X, pady=20)
        
        self.log_text = ScrolledText(
            self.dynamic_frame, 
            height=20, 
            background="#1d2021", 
            foreground="#83a598", 
            font=("Courier New", 9),
            relief="flat"
        )
        self.log_text.pack(fill=BOTH, expand=True)
        
        self.btn_avancar = ttk.Button(self.dynamic_frame, text="[SINTETIZAR] ➤", style="Disco.TButton", command=self.process_step_2, state=DISABLED)
        self.btn_avancar.pack(anchor="e", pady=10)

        threading.Thread(target=self.run_agents_parallel, daemon=True).start()

    def run_agents_parallel(self):
        contexto = f"PROJETO: {self.problema}\nDETALHES: {self.respostas_user}"
        total_agents = len(AGENTES_ATIVOS)
        completed = 0
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_agent = {}
            for agente in AGENTES_ATIVOS:
                prompt = f"Analise o contexto. Lembre-se: Confidence Check obrigatório. Seja específico na sua área.\nCONTEXTO:\n{contexto}"
                future = executor.submit(call_ollama, agente, PROMPTS[agente], prompt, False, 0.5)
                future_to_agent[future] = agente
            
            for future in concurrent.futures.as_completed(future_to_agent):
                agente = future_to_agent[future]
                try:
                    resp = future.result()
                    self.ideias_iniciais[agente] = resp
                    self.transcript += f"\n\n[{agente}]:\n{resp}"
                    self.after(0, lambda a=agente, r=resp: self.update_log(a, r))
                except Exception as e:
                    self.after(0, lambda a=agente, err=e: self.update_log(a, f"ERRO: {err}"))
                
                completed += 1
                self.after(0, lambda c=completed, t=total_agents: self.update_progress(c, t))

        self.after(0, lambda: self.log_text.insert(END, "\n>> O INTEGRADOR ESTÁ UNINDO AS PEÇAS...\n"))
        
        resumo_pecas = "\n\n".join([f"[{k} SUGESTÃO]:\n{v}" for k, v in self.ideias_iniciais.items()])
        prompt_integrador = f"CONTEXTO DO PROJETO: {contexto}\n\nIDEIAS SUGERIDAS:\n{resumo_pecas}"
        
        tabuleiro = call_ollama("INTEGRADOR", PROMPTS["MONTAGEM_DO_QUEBRA_CABECA"], prompt_integrador, temperature=0.3)
        self.esquema_montado = tabuleiro
        self.transcript += f"\n\n[ESQUEMA INICIAL]:\n{tabuleiro}"
        
        self.after(0, lambda: self.show_integrator_result(tabuleiro))

    def update_log(self, agent, text):
        self.log_text.insert(END, f"[{agent}] [SUCESSO]\n")
        self.log_text.see(END)

    def update_progress(self, val, total):
        self.progress_bar['value'] = (val / total) * 100

    def show_integrator_result(self, text):
        self.log_text.insert(END, f"\n[ESQUEMA MONTADO]:\n{text[:5000]}...\n")
        self.log_text.see(END)
        self.btn_avancar.config(state=NORMAL)

    def process_step_2(self):
        self.step = 3
        self.render_step_3()

    def render_step_3(self):
        self.clear_content()
        self.lbl_header.config(text="4. PARANOIA CRÍTICA")
        
        ttk.Label(self.dynamic_frame, text="Alguém discorda? Sempre alguém discorda.", foreground=self.colors["danger"]).pack(anchor="w")
        self.lbl_audit = ttk.Label(self.dynamic_frame, text="[LOGIC] Verificando integridade...", foreground="#fabd2f")
        self.lbl_audit.pack(pady=10)
        
        self.veto_display = ScrolledText(self.dynamic_frame, height=15, background="#282828", foreground="#fb4934", font=("Courier New", 10))
        self.veto_display.pack(fill=BOTH, expand=True, pady=10)
        
        frame_adjust = ttk.Labelframe(self.dynamic_frame, text="AUTHORITY [MÉDIO]", padding=10, bootstyle="secondary")
        frame_adjust.pack(fill=X, pady=10)
        
        ttk.Label(frame_adjust, text="Deseja forçar alguma troca?").pack(anchor="w")
        self.entry_adjust = ttk.Entry(frame_adjust)
        self.entry_adjust.pack(fill=X, pady=5)
        
        self.btn_final = ttk.Button(self.dynamic_frame, text="[ASSINAR SENTENÇA] ➤", style="Disco.TButton", command=self.process_step_3, state=DISABLED)
        self.btn_final.pack(anchor="e", pady=10)
        
        threading.Thread(target=self.run_audit_parallel, daemon=True).start()

    def run_audit_parallel(self):
        self.vetos = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for agente in AGENTES_ATIVOS:
                prompt_auditoria = f"""
                VOCÊ É O {agente}.
                ESQUEMA ATUAL:
                {self.esquema_montado}
                
                TAREFA: Analise se alguma decisão tomada acima prejudica sua área ou viola a TECH BIBLE.
                Se estiver tudo ok, retorne json vazio.
                """
                futures.append(executor.submit(call_ollama, agente, PROMPTS["VOTO_IDEIAS"], prompt_auditoria, True, 0.2))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    resp = future.result()
                    if "{" in resp:
                        resp = resp[resp.find("{"):resp.rfind("}")+1]
                    
                    data = json.loads(resp)
                    if data.get("veto"):
                        veto_item = {
                            "autor": "Auditor", 
                            "alvo": data["veto"],
                            "motivo": data["motivo"],
                            "sugestao": data.get("sugestao", "N/A")
                        }
                        self.vetos.append(veto_item)
                        self.after(0, lambda v=veto_item: self.display_veto(v))
                except: pass
        
        self.after(0, self.finish_audit)

    def display_veto(self, veto):
        msg = f"⚠ VETO em '{veto['alvo']}':\nMotivo: {veto['motivo']}\nSugestão: {veto['sugestao']}\n{'-'*30}\n"
        self.veto_display.insert(END, msg)

    def finish_audit(self):
        self.lbl_audit.config(text="Auditoria Concluída.", foreground=self.colors["success"])
        if not self.vetos:
            self.veto_display.insert(END, ">>> NENHUMA OBJEÇÃO ENCONTRADA.\n")
        self.btn_final.config(state=NORMAL)

    def process_step_3(self):
        self.final_adjust = self.entry_adjust.get().strip()
        self.step = 4
        self.render_step_4()

    def render_step_4(self):
        self.clear_content()
        self.lbl_header.config(text="5. A SOLUÇÃO")
        
        ttk.Label(self.dynamic_frame, text="O diagrama se forma na sua frente.", foreground="#b8bb26").pack(anchor="w")
        self.lbl_generating = ttk.Label(self.dynamic_frame, text="[Calculando] Finalizando diagrama...", foreground="#d3869b")
        self.lbl_generating.pack(pady=10)
        
        self.final_text = ScrolledText(self.dynamic_frame, background="#1d2021", foreground="#dcdccc", font=("Courier New", 10), height=20)
        self.final_text.pack(fill=BOTH, expand=True)
        
        self.btn_frame = ttk.Frame(self.dynamic_frame)
        self.btn_frame.pack(fill=X, pady=20)
        
        threading.Thread(target=self.run_final_blueprint, daemon=True).start()

    def run_final_blueprint(self):
        vetos_str = json.dumps(self.vetos) if self.vetos else "Nenhum"
        prompt_final = f"""
        CONTEXTO ORIGINAL: {self.problema}
        ESQUEMA DRAFT: {self.esquema_montado}
        CRÍTICAS/VETOS DOS ESPECIALISTAS: {vetos_str}
        AJUSTE FINAL DO USUÁRIO: {self.final_adjust}
        TECH BIBLE: {TECH_BIBLE_CONTENT}
        
        TAREFA:
        Reescreva a arquitetura final resolvendo os vetos.
        Se o OPS definiu o tamanho como P (Pequeno), simplifique tudo.
        Inclua diagrama Mermaid.
        """
        
        blueprint = call_ollama("INTEGRADOR", "Gere o Blueprint Final consolidado.", prompt_final, temperature=0.3)
        self.blueprint_final = blueprint 
        
        self.after(0, lambda: self.show_final_options())

    def show_final_options(self):
        self.lbl_generating.config(text="DIAGRAMA PRONTO. AGUARDANDO DECISÃO.", foreground=self.colors["success"])
        self.final_text.insert(END, self.blueprint_final)
        
        self.btn_restart = ttk.Button(
            self.btn_frame, 
            text="[VOLTAR AO INÍCIO]", 
            style="Disco.TButton", 
            bootstyle="secondary",
            command=self.check_restart
        )
        self.btn_restart.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        self.btn_save = ttk.Button(
            self.btn_frame, 
            text="[SALVAR DIAGRAMA]", 
            style="Disco.TButton", 
            command=self.save_diagram
        )
        self.btn_save.pack(side=LEFT, fill=X, expand=True, padx=5)

        self.btn_gen_code = ttk.Button(
            self.btn_frame, 
            text="[GERAR CÓDIGO (NUVEM)]", 
            style="Disco.TButton", 
            bootstyle="info",
            command=self.start_gen_code
        )
        self.btn_gen_code.pack(side=RIGHT, fill=X, expand=True, padx=(5, 0))

    def save_diagram(self):
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs("output", exist_ok=True)
            filepath = f"output/blueprint_{ts}.md"
            
            with open(filepath, "w", encoding="utf-8") as f: 
                f.write(self.blueprint_final)
            
            self.is_saved = True
            self.btn_save.config(state=DISABLED, text="[SALVO] ✔")
            messagebox.showinfo("SUCESSO", f"Diagrama salvo em:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("ERRO", f"Falha ao salvar: {e}")

    def start_gen_code(self):
        self.lbl_generating.config(text="[UPLINK] Enviando dados para Gemini 3.0...", foreground=self.colors["blue"])
        self.btn_gen_code.config(state=DISABLED)
        
        self.final_text.delete("1.0", END)
        self.final_text.insert(END, ">>> INICIANDO PROTOCOLO DE CONSTRUÇÃO...\n")
        
        threading.Thread(target=self.run_gemini_coder, daemon=True).start()

    def run_gemini_coder(self):
        code_result = call_gemini_api(self.blueprint_final)
        
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs("code_output", exist_ok=True)
        filepath = f"code_output/code_mvp_{ts}.md"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_result)
            
        self.after(0, lambda: self.show_code_result(code_result, filepath))

    def show_code_result(self, code, path):
        self.lbl_generating.config(text=f"CÓDIGO GERADO: {path}", foreground=self.colors["success"])
        self.final_text.delete("1.0", END)
        self.final_text.insert(END, code)
        self.btn_gen_code.config(text="[CONSTRUÍDO] ✔")

if __name__ == "__main__":
    app = PitacoApp()
    app.mainloop()