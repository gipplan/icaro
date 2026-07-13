import os
import json
import datetime
import re
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

def obter_imagem_noticia_segura(marca, setor):
    """Busca uma imagem relacionada usando a marca e o setor no DuckDuckGo"""
    termo_busca = f"{marca} empresa {setor}"
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.images(termo_busca, safesearch='on', max_results=1))
            if resultados and 'image' in resultados[0]:
                return resultados[0]['image']
    except Exception as e:
        print(f"⚠️ Nota: Não foi possível coletar imagem para '{termo_busca}': {e}")
    
    return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600"

def executar_radar():
    print("🚀 Inicializando o motor Í.C.A.R.O. v5 (Com Google Search Real-Time)...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERRO CRÍTICO: A variável de ambiente 'GEMINI_API_KEY' não foi encontrada!")
        exit(1)
        
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ ERRO CRÍTICO ao inicializar o cliente GenAI: {e}")
        exit(1)

    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")

    # PROMPT focado em exigir que a IA use a ferramenta de busca do Google
    prompt_sistema = f"""
    Você é um analista de inteligência de mercado focado em Relações Públicas e Comunicação Corporativa.
    Hoje é {data_hoje}.
    
    SUA TAREFA OBRIGATÓRIA:
    Utilize a sua ferramenta integrada de busca (Google Search) para pesquisar de forma ativa notícias reais, fatos, lançamentos, crises ou movimentações de mercado ocorridas EXCLUSIVAMENTE NOS ÚLTIMOS 7 DIAS para as marcas listadas abaixo. 
    Não invente nada. Baseie-se unicamente nas notícias quentes encontradas pela busca web.

    Lista de clientes ativos para monitoramento:
    - In Press Porter Novelli: Canais Globo, Editora Globo, IDB Maraey, Maratona do Rio, Rio Open, Sail GP, ICT Costa Rica, Globo Internacional, Globo Portugal, Riot Games, Seara, happn, Fundação Mapfre, MAPFRE, Open Society, Fundação Ford Foundation, Sony Music (Institucional), Taboaço, Reyou (Bravo Cosméticos), Engie, Yara, RZK Energia - Thopen, Siemens Energy, Abihpec, DSM, Bunge, Matrix, Agrolend, Ambev, Electrolux, Emma Colchões, Gallo, General Mills, Randstad, Unilever, Rexona, Americanas, Betano, Caixa Consórcio, Caixa Seguradora, Chevron, CNP, FenaSaúde, Firjan, IBS Energy, Karoon, Naturgy, Rio Mais, Prio, Seadrill, TAESA, Vibra, White Martins, Abecs, Atos, AWS, Black Rock, Banco Mercantil, BBCE, Cisco, CLARO, Equinix, FICO, HPE, Intelbras, Mercado Bitcoin, Iron Mountain, Madrona Advogados, Sicredi, Solis Investimentos, JOVI, PhizChat, Wiz, Cidade Center Norte, Mercado Livre, Mercado Pago, Natura (e Avon), São Leopoldo Mandic, McDonalds, Compra Agora, Senac SP, SAEA, Insper, iFood, Klabin, Abasp, Penske, Bla Bla Car, IBJR, Corteva, ArcelorMittal, Localiza, Belgo Arames, Direcional, Farmax, Norsk Hydro, Grupo Sada, Vale, Veolia, GSK, Afya, Servier, Roche farma, Roche Dia, MV, Medsenior, Johnson & Johnson, Henkel, TIC Trens, Motiva (CCR), GOL/Smiles, IBGC, eureciclo, Mattel, Royal Canin, PepsiCo, Herbalife.

    - FleishmanHillard: Abrintel, Harsco, ICC (International Chamber of Commerce Brazil), LANXESS, Oz, Bayer, HCor, Albert Einstein, Philips do Brasil, Philips Medical, Samsung (B2B / B2C / LATAM), Stone, Kellanova, Google, Mastercard, Shein, State Grid, Hitachi, McKinsey, Abrabe, General Motors, Sicredi Brasília, ABDE, Belo Sun, Beiersdorf, Cury Construtora, Newell, Onçafari, Votorantim, Veracel, Softys, Guerbet.

    Retorne EXCLUSIVAMENTE um array JSON válido contendo as oportunidades reais mapeadas, sem nenhum texto antes ou depois.
    Siga este modelo estrito:
    [
        {{
            "agencia": "Nome exato da Agência (In Press Porter Novelli ou FleishmanHillard)",
            "setor": "Setor macro da oportunidade",
            "marcas": ["Marca Envolvida"],
            "descricao": "Texto analítico resumido com o gatilho factual recente e o impacto estratégico, contendo até 300 caracteres.",
            "produtos": ["Serviço 1", "Serviço 2"],
            "link_noticia": "URL real completa do artigo ou portal de notícias de onde você extraiu esta informação na busca do Google"
        }}
    ]

    REGRAS DE CONTEÚDO:
    1. "produtos": Escolha de 1 a 3 opções estritamente desta lista: [Assessoria de Imprensa, Relações Governamentais, Comunicação Interna, Presença Digital, Influenciadores, Campanha, PR Stunt, Posicionamento Executivo, Mídia].
    2. "link_noticia": Deve ser o link direto e real da matéria jornalística encontrada (Ex: g1.globo.com, exame.com, valor.globo.com, etc). Não envie links de busca genéricos.
    """

    print("🔍 Consultando a API do Google para descobrir os modelos liberados...")
    modelos_prioritarios = []
    try:
        for m in client.models.list():
            nome_limpo = m.name.replace('models/', '')
            if 'gemini' in nome_limpo and ('flash' in nome_limpo or 'pro' in nome_limpo):
                modelos_prioritarios.append(nome_limpo)
    except Exception:
        pass

    if not modelos_prioritarios:
        modelos_prioritarios = ['gemini-1.5-flash-002', 'gemini-1.5-pro-002']

    print("\n🧠 Solicitando análise com GOOGLE SEARCH GROUNDING ativado...")
    
    # ATIVAÇÃO DO MOTOR DE BUSCA DO GOOGLE DENTRO DA API DO GEMINI
    configuracao_json = types.GenerateContentConfig(
        response_mime_type="application/json",
        tools=[types.Tool(google_search=types.GoogleSearch())] # <-- A mágica acontece aqui
    )

    resposta = None
    modelo_utilizado = None

    for modelo in modelos_prioritarios:
        print(f"Tentando processamento com o modelo: {modelo}...")
        try:
            resposta = client.models.generate_content(
                model=modelo,
                contents=prompt_sistema,
                config=configuracao_json
            )
            modelo_utilizado = modelo
            print(f"✅ Sucesso! Processado usando o modelo com busca: {modelo_utilizado}")
            break
        except Exception as e:
            print(f"⚠️ Erro ao tentar o modelo {modelo}: {e}")
            continue

    if not resposta:
        print("❌ ERRO CRÍTICO: Nenhum dos modelos conseguiu processar a requisição.")
        exit(1)

    try:
        conteudo_bruto = resposta.text.strip()
        
        inicio_array = conteudo_bruto.find('[')
        fim_array = conteudo_bruto.rfind(']')
        
        if inicio_array != -1 and fim_array != -1:
            conteudo_limpo = conteudo_bruto[inicio_array:fim_array+1]
        else:
            conteudo_limpo = conteudo_bruto
            
        conteudo_limpo = re.sub(r'^```json\s*', '', conteudo_limpo, flags=re.MULTILINE)
        conteudo_limpo = re.sub(r'^```\s*', '', conteudo_limpo, flags=re.MULTILINE)
        conteudo_limpo = re.sub(r'\s*```$', '', conteudo_limpo).strip()
            
        novas_oportunidades = json.loads(conteudo_limpo)
        
        if isinstance(novas_oportunidades, dict):
            novas_oportunidades = [novas_oportunidades]
            
    except Exception as e:
        print(f"❌ ERRO ao decodificar o JSON: {e}")
        print(f"Retorno obtido:\n{resposta.text}")
        exit(1)

    print("🖼️ Buscando imagens inteligentes para os novos cenários...")
    for op in novas_oportunidades:
        # Carimba a data real de processamento do card
        op["data"] = data_hoje
        
        marca_principal = op.get("marcas", ["Mercado"])[0]
        setor = op.get("setor", "corporativo")
        
        # O Python agora só faz a busca da imagem conceitual
        op["imagem"] = obter_imagem_noticia_segura(marca_principal, setor)
        
        # Garante um fallback de link caso a IA não tenha preenchido o link_noticia
        if "link_noticia" not in op or not op["link_noticia"] or "[google.com/search](https://google.com/search)" in op["link_noticia"]:
            op["link_noticia"] = f"[https://news.google.com/search?q=](https://news.google.com/search?q=){marca_principal.replace(' ', '+')}+when:7d&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    print("💾 Resgatando histórico e gravando dados...")
    arquivo_json = "oportunidades.json"
    dados_existentes = []
    
    if os.path.exists(arquivo_json):
        try:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                dados_existentes = json.load(f)
        except Exception:
            pass
            
    dados_atualizados = novas_oportunidades + dados_existentes

    try:
        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados_atualizados, f, ensure_ascii=False, indent=4)
        print(f"🎉 Processo finalizado com sucesso! Total na base de dados: {len(dados_atualizados)}.")
    except Exception as e:
        print(f"❌ ERRO ao gravar o arquivo de saída: {e}")
        exit(1)

if __name__ == "__main__":
    executar_radar()
