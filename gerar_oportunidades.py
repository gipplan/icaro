import os
import json
import difflib
from datetime import datetime
from google import genai
from google.genai import types

def carregar_playbook():
    path = "playbook.md"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Nenhum playbook personalizado encontrado. Siga as diretrizes de Diretor Sênior de PR."

def carregar_oportunidades_existentes():
    path = "oportunidades.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def sao_similares(texto1, texto2, limite=0.70):
    """
    Motor anti-repetição: Calcula a similaridade entre duas strings.
    Se forem mais de 70% iguais, consideramos como a mesma notícia.
    """
    return difflib.SequenceMatcher(None, texto1, texto2).ratio() > limite

def executar_varredura():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave da API não encontrada nas variáveis de ambiente.")
    
    client = genai.Client(api_key=api_key)
    playbook_context = carregar_playbook()
    hoje = datetime.now()
    data_hoje_str = hoje.strftime("%d/%m/%Y")

    print(f"🚀 Iniciando motor Í.C.A.R.O. Master (Data: {data_hoje_str})...")

    prompt = f"""
    Atue como Í.C.A.R.O., o motor de inteligência e curadoria editorial corporativa. Execute a varredura comercial diária identificando riscos e oportunidades de relações públicas. Foque nas 5 a 10 pautas mais quentes do dia.
    Data da varredura: {data_hoje_str}

    ⚠️ PRIORIDADE DE BUSCA: Dê prioridade máxima na varredura para identificar notícias reais sobre **iFood** e **Stone**. 
    **REGRA DE VERACIDADE ESTRITA:** Você SÓ deve incluir pautas para essas marcas se houver fatos factuais e comprovados na mídia nas últimas 48h. Se não houver fato noticioso sobre elas, NÃO INVENTE. Preencha a cota de pautas com outras marcas da lista que tenham notícias reais.

    Você deve executar OBRIGATORIAMENTE duas frentes de busca:

    **FRENTE 1: Radar de Marcas**
    Busque fatos relevantes ocorridos nas últimas 24/48 horas estritamente para a seguinte lista de clientes:
    - In Press: Canais Globo, Editora Globo, IDB Maraey, Maratona do Rio, Rio Open, Sail GP, ICT Costa Rica, Globo Internacional, Globo Portugal, Riot Games, Seara, happn, Fundação Mapfre, MAPFRE, Open Society, Fundação Ford Foundation, Sony Music, Taboaço, Reyou, Engie, Yara, RZK Energia, Siemens Energy, Abihpec, DSM, Bunge, Matrix, Agrolend, Ambev, Electrolux, Emma Colchões, Gallo, General Mills, Randstad, Unilever, Rexona, Americanas, Betano, Caixa Consórcio, Caixa Seguradora, Chevron, CNP, FenaSaúde, Firjan, IBS Energy, Karoon, Naturgy, Rio Mais, Prio, Seadrill, TAESA, Vibra, White Martins, Abecs, Atos, AWS, Black Rock, Banco Mercantil, BBCE, Cisco, CLARO, Equinix, FICO, HPE, Intelbras, Mercado Bitcoin, Iron Mountain, Madrona Advogados, Sicredi, Solis Investimentos, JOVI, PhizChat, Wiz, Cidade Center Norte, Mercado Livre, Mercado Pago, Natura, Avon, São Leopoldo Mandic, McDonalds, Compra Agora, Senac SP, SAEA, Insper, iFood, Klabin, Abasp, Penske, Bla Bla Car, IBJR, Corteva, ArcelorMittal, Localiza, Belgo Arames, Direcional, Farmax, Norsk Hydro, Grupo Sada, Vale, Veolia, GSK, Afya, Servier, Roche farma, Roche Dia, MV, Medsenior, Johnson & Johnson, Henkel, TIC Trens, Motiva (CCR), GOL/Smiles, IBGC, eureciclo, Mattel, Royal Canin, PepsiCo, Herbalife.
    - FleishmanHillard: Abrintel, Harsco, ICC, LANXESS, Oz, Bayer, HCor, Albert Einstein, Philips do Brasil, Philips Medical, Samsung, Stone, Kellanova, Google, Mastercard, Shein, State Grid, Hitachi, McKinsey, Abrabe, General Motors, Sicredi Brasília, ABDE, Belo Sun, Beiersdorf, Cury Construtora, Newell, Onçafari, Votorantim, Veracel, Softys, Guerbet.

    **FRENTE 2: Radar Macroeconômico (Setorial)**
    Identifique movimentações que gerem impacto crítico para os setores:
    - Tecnologia, IA e Eletroeletrônicos
    - E-commerce, Varejo e Logística
    - Energia, Mineração e Siderurgia (ESG)
    - Finanças e Fintechs
    - Aviação e Turismo

    **DIRETRIZES DA TÁTICA SUGERIDA:**
    Atue como um Diretor Sênior de Comunicação Corporativa. Use EXCLUSIVAMENTE as estratégias do playbook. 
    FUJA DO ÓBVIO: NUNCA sugira "fazer press release" ou "postar nas redes". Comece a recomendação com um verbo no gerúndio e justifique o impacto no negócio.

    --- INÍCIO DO PLAYBOOK ---
    {playbook_context}
    --- FIM DO PLAYBOOK ---

    FORMATO DE SAÍDA OBRIGATÓRIO (JSON Puro):
    Retorne APENAS uma lista JSON válida. Não use markdown fora do bloco JSON.
    [
      {{
        "titulo": "Título conciso da pauta (ou do tema macro)",
        "resumo_fato": "Resumo executivo do fato ou tendência identificada.",
        "recomendacao": "Sua tática estratégica baseada no playbook (verbo no gerúndio).",
        "tipo": "regulacao" | "tecnologia" | "operacao" | "concorrencia" | "esg" | "crise",
        "data": "{data_hoje_str}",
        "setor": "Setor do cliente ou macroeconomia",
        "marcas": ["Marcas envolvidas (Deixe vazio se for apenas setorial)"],
        "produtos": ["Entregáveis de PR baseados no playbook"],
        "link_noticia": "URL real da fonte",
        "imagem": ""
      }}
    ]
    """

    print("Enviando requisição (Gemini Native Search ativado)...")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.4 
        )
    )

    texto_resposta = response.text.strip()
    
    # Tratamento de formatação Markdown do Gemini
    if texto_resposta.startswith("```json"):
        texto_resposta = texto_resposta[7:]
    elif texto_resposta.startswith("```"):
        texto_resposta = texto_resposta[3:]

    if texto_resposta.endswith("```"):
        texto_resposta = texto_resposta[:-3]

    texto_resposta = texto_resposta.strip()

    try:
        novas_pautas = json.loads(texto_resposta)
    except json.JSONDecodeError as e:
        print("Erro ao decodificar JSON retornado pelo Gemini:", e)
        print("Conteúdo recebido:")
        print(texto_resposta)
        return

    pautas_existentes = carregar_oportunidades_existentes()
    
    # ---------------------------------------------------------
    # MOTOR DE BLOQUEIO POR SIMILARIDADE COM JANELA DE 75 DIAS
    # ---------------------------------------------------------
    textos_recentes = []
    for p in pautas_existentes:
        texto_limpo = f"{p.get('titulo', '')} {p.get('resumo_fato', '')}".strip().lower()
        data_str = p.get("data", "")
        
        try:
            data_pauta = datetime.strptime(data_str, "%d/%m/%Y")
            diff_dias = (hoje - data_pauta).days
            if diff_dias <= 75:
                textos_recentes.append(texto_limpo)
        except ValueError:
            textos_recentes.append(texto_limpo)

    pautas_adicionadas = 0
    for pauta in novas_pautas:
        texto_novo = f"{pauta.get('titulo', '')} {pauta.get('resumo_fato', '')}".strip().lower()
        
        eh_duplicada = False
        for txt_ext in textos_recentes:
            if sao_similares(texto_novo, txt_ext, limite=0.70):
                eh_duplicada = True
                print(f"Bloqueado por similaridade (>70%): {pauta.get('titulo')}")
                break
                
        if not eh_duplicada:
            pautas_existentes.insert(0, pauta) # Adiciona no topo da lista
            textos_recentes.append(texto_novo)
            pautas_adicionadas += 1

    # Salvando 100% do histórico (sem limite de corte)
    with open("oportunidades.json", "w", encoding="utf-8") as f:
        json.dump(pautas_existentes, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! {pautas_adicionadas} novas pautas integradas ao histórico completo do oportunidades.json.")

if __name__ == "__main__":
    executar_varredura()
