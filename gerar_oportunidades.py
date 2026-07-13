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

def obter_link_noticia_real(marca):
    """Faz uma busca real na web e retorna o link da primeira notícia encontrada sobre a marca"""
    termo_busca = f"notícias {marca} brasil"
    try:
        with DDGS() as ddgs:
            # Busca os resultados em texto focando no Brasil
            resultados = list(ddgs.text(termo_busca, region='br-pt', max_results=1))
            if resultados and 'href' in resultados[0]:
                return resultados[0]['href']
    except Exception as e:
        print(f"⚠️ Nota: Falha ao buscar notícia para '{marca}': {e}")
        
    # Último recurso caso a busca web falhe
    return f"https://www.google.com/search?q=noticias+{marca.replace(' ', '+')}"

def executar_radar():
    print("🚀 Inicializando o motor Í.C.A.R.O. v3 (Com Links Reais e Tags Restritas)...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERRO CRÍTICO: A variável de ambiente 'GEMINI_API_KEY' não foi encontrada!")
        exit(1)
        
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"❌ ERRO CRÍTICO ao inicializar o cliente GenAI: {e}")
        exit(1)

    # A data do dia da coleta
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")

    prompt_sistema = f"""
    Você é um analista de inteligência de mercado focado em Relações Públicas e Comunicação Corporativa.
    Sua tarefa é analisar o mercado das últimas 24 horas e identificar riscos e oportunidades reais para a seguinte lista de clientes ativos:
    
    - In Press Porter Novelli: Canais Globo, Editora Globo, IDB Maraey, Maratona do Rio, Rio Open, Sail GP, ICT Costa Rica, Globo Internacional, Globo Portugal, Riot Games, Seara, happn, Fundação Mapfre, MAPFRE, Open Society, Fundação Ford Foundation, Sony Music (Institucional), Taboaço, Reyou (Bravo Cosméticos), Engie, Yara, RZK Energia - Thopen, Siemens Energy, Abihpec, DSM, Bunge, Matrix, Agrolend, Ambev, Electrolux, Emma Colchões, Gallo, General Mills, Randstad, Unilever, Rexona, Americanas, Betano, Caixa Consórcio, Caixa Seguradora, Chevron, CNP, FenaSaúde, Firjan, IBS Energy, Karoon, Naturgy, Rio Mais, Prio, Seadrill, TAESA, Vibra, White Martins, Abecs, Atos, AWS, Black Rock, Banco Mercantil, BBCE, Cisco, CLARO, Equinix, FICO, HPE, Intelbras, Mercado Bitcoin, Iron Mountain, Madrona Advogados, Sicredi, Solis Investimentos, JOVI, PhizChat, Wiz, Cidade Center Norte, Mercado Livre, Mercado Pago, Natura (e Avon), São Leopoldo Mandic, McDonalds, Compra Agora, Senac SP, SAEA, Insper, iFood, Klabin, Abasp, Penske, Bla Bla Car, IBJR, Corteva, ArcelorMittal, Localiza, Belgo Arames, Direcional, Farmax, Norsk Hydro, Grupo Sada, Vale, Veolia, GSK, Afya, Servier, Roche farma, Roche Dia, MV, Medsenior, Johnson & Johnson, Henkel, TIC Trens, Motiva (CCR), GOL/Smiles, IBGC, eureciclo, Mattel, Royal Canin, PepsiCo, Herbalife.

    - FleishmanHillard: Abrintel, Harsco, ICC (International Chamber of Commerce Brazil), LANXESS, Oz, Bayer, HCor, Albert Einstein, Philips do Brasil, Philips Medical, Samsung (B2B / B2C / LATAM), Stone, Kellanova, Google, Mastercard, Shein, State Grid, Hitachi, McKinsey, Abrabe, General Motors, Sicredi Brasília, ABDE, Belo Sun, Beiersdorf, Cury Construtora, Newell, Onçafari, Votorantim, Veracel, Softys, Guerbet.

    Retorne EXCLUSIVAMENTE um array JSON válido contendo as oportunidades, sem nenhum texto antes ou depois.
    Siga este modelo estrito:
    [
        {{
            "agencia": "Nome exato da Agência (In Press Porter Novelli ou FleishmanHillard)",
            "setor": "Setor macro da oportunidade",
            "marcas": ["Marca1"],
            "descricao": "Texto analítico resumido com o gatilho e impacto de até 300 caracteres.",
            "produtos": ["Serviço 1", "Serviço 2"]
        }}
    ]

    REGRAS OBRIGATÓRIAS:
    1. "produtos": Você DEVE escolher DE 1 A 3 opções EXCLUSIVAMENTE desta lista exata: [Assessoria de Imprensa, Relações Governamentais, Comunicação Interna, Presença Digital, Influenciadores, Campanha, PR Stunt, Posicionamento Executivo, Mídia]. NUNCA invente ou use termos fora desta lista.
    2. Só retorne oportunidades baseadas em fatos ou tendências reais do mercado para as marcas listadas.
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

    print("\n🧠 Solicitando análise de cenários ao Gemini...")
    configuracao_json = types.GenerateContentConfig(response_mime_type="application/json")

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
            print(f"✅ Sucesso! Processado usando: {modelo_utilizado}")
            break
        except Exception as e:
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
        exit(1)

    print("🔍 Processando links reais, datas estritas e imagens inteligentes...")
    for op in novas_oportunidades:
        
        # 1. Carimba a data real de HOJE via Python, impedindo a IA de errar
        op["data"] = data_hoje
        
        marca_principal = op.get("marcas", ["Mercado"])[0]
        setor = op.get("setor", "corporativo")
        
        # 2. Busca uma imagem específica da Marca + Setor
        op["imagem"] = obter_imagem_noticia_segura(marca_principal, setor)
        
        # 3. Busca o link de uma notícia real daquela marca na internet
        op["link_noticia"] = obter_link_noticia_real(marca_principal)

    print("💾 Resgatando histórico e gravando dados...")
    arquivo_json = "oportunidades.json"
    dados_existentes = []
    
    if os.path.exists(arquivo_json):
        try:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                dados_existentes = json.load(f)
        except Exception:
            pass
            
    # Remove duplicatas baseadas na marca + descrição para o arquivo não crescer com itens iguais
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
