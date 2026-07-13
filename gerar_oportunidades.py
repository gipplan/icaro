import os
import json
import datetime
import re
from google import genai
from google.genai import types
from duckduckgo_search import DDGS

def obter_imagem_noticia_segura(termo_busca):
    """Busca uma imagem relacionada usando DuckDuckGo com SafeSearch Estrito"""
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.images(termo_busca, safesearch='on', max_results=1))
            if resultados and 'image' in resultados[0]:
                return resultados[0]['image']
    except Exception as e:
        print(f"⚠️ Nota: Não foi possível coletar imagem para '{termo_busca}': {e}")
    
    return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600"

def executar_radar():
    print("🚀 Inicializando o motor Í.C.A.R.O. com Histórico de Dados...")
    
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

    prompt_sistema = f"""
    Você é um analista de inteligência de mercado focado em Relações Públicas e Comunicação Corporativa.
    Hoje é {data_hoje}.
    Sua tarefa é analisar o mercado das últimas 24 horas e identificar riscos e oportunidades reais para a seguinte lista de clientes ativos:
    
    - In Press Porter Novelli: Canais Globo, Editora Globo, IDB Maraey, Maratona do Rio, Rio Open, Sail GP, ICT Costa Rica, Globo Internacional, Globo Portugal, Riot Games, Seara, happn, Fundação Mapfre, MAPFRE, Open Society, Fundação Ford Foundation, Sony Music (Institucional), Taboaço, Reyou (Bravo Cosméticos), Engie, Yara, RZK Energia - Thopen, Siemens Energy, Abihpec, DSM, Bunge, Matrix, Agrolend, Ambev, Electrolux, Emma Colchões, Gallo, General Mills, Randstad, Unilever, Rexona, Americanas, Betano, Caixa Consórcio, Caixa Seguradora, Chevron, CNP, FenaSaúde, Firjan, IBS Energy, Karoon, Naturgy, Rio Mais, Prio, Seadrill, TAESA, Vibra, White Martins, Abecs, Atos, AWS, Black Rock, Banco Mercantil, BBCE, Cisco, CLARO, Equinix, FICO, HPE, Intelbras, Mercado Bitcoin, Iron Mountain, Madrona Advogados, Sicredi, Solis Investimentos, JOVI, PhizChat, Wiz, Cidade Center Norte, Mercado Livre, Mercado Pago, Natura (e Avon), São Leopoldo Mandic, McDonalds, Compra Agora, Senac SP, SAEA, Insper, iFood, Klabin, Abasp, Penske, Bla Bla Car, IBJR, Corteva, ArcelorMittal, Localiza, Belgo Arames, Direcional, Farmax, Norsk Hydro, Grupo Sada, Vale, Veolia, GSK, Afya, Servier, Roche farma, Roche Dia, MV, Medsenior, Johnson & Johnson, Henkel, TIC Trens, Motiva (CCR), GOL/Smiles, IBGC, eureciclo, Mattel, Royal Canin, PepsiCo, Herbalife.

    - FleishmanHillard: Abrintel, Harsco, ICC (International Chamber of Commerce Brazil), LANXESS, Oz, Bayer, HCor, Albert Einstein, Philips do Brasil, Philips Medical, Samsung (B2B / B2C / LATAM), Stone, Kellanova, Google, Mastercard, Shein, State Grid, Hitachi, McKinsey, Abrabe, General Motors, Sicredi Brasília, ABDE, Belo Sun, Beiersdorf, Cury Construtora, Newell, Onçafari, Votorantim, Veracel, Softys, Guerbet.

    Retorne EXCLUSIVAMENTE um array JSON válido contendo as novas oportunidades de hoje, sem nenhum texto antes ou depois.
    Siga este modelo estrito:
    [
        {{
            "data": "{data_hoje}",
            "agencia": "Nome exato da Agência (In Press Porter Novelli ou FleishmanHillard)",
            "setor": "Setor macro da oportunidade",
            "marcas": ["Marca1", "Marca2"],
            "descricao": "Texto analítico resumido com o gatilho e impacto de até 300 caracteres.",
            "produtos": ["Serviço 1", "Serviço 2"],
            "palavra_chave_imagem": "Termo em inglês simples e corporativo para buscar uma imagem conceitual da notícia",
            "link_noticia": "URL real de uma matéria em portal de notícias confiável que valide e embase esta oportunidade"
        }}
    ]

    REGRAS OBRIGATÓRIAS:
    1. "produtos" refere-se EXCLUSIVAMENTE aos serviços de PR e Comunicação que a NOSSA AGÊNCIA vai vender/oferecer para o cliente (Exemplos: Gestão de Crise, Media Training, Relações Governamentais, Press Release, Thought Leadership, Auditoria de Imagem).
    2. A "data" deve ser sempre exatamente {data_hoje}.
    3. Só retorne oportunidades baseadas em fatos reais ou movimentações verossímeis do mercado atual para essas marcas específicas.
    """

    print("🔍 Consultando a API do Google para descobrir os modelos liberados...")
    modelos_prioritarios = []
    
    try:
        for m in client.models.list():
            nome_limpo = m.name.replace('models/', '')
            if 'gemini' in nome_limpo and ('flash' in nome_limpo or 'pro' in nome_limpo):
                modelos_prioritarios.append(nome_limpo)
        print(f"✅ Modelos autorizados encontrados! Top 3: {modelos_prioritarios[:3]}")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível mapear dinamicamente. Erro: {e}")
        modelos_prioritarios = ['gemini-1.5-flash-002', 'gemini-1.5-pro-002', 'gemini-1.5-flash-8b']

    if not modelos_prioritarios:
        modelos_prioritarios = ['gemini-1.5-flash-002', 'gemini-1.5-pro-002']

    print("\n🧠 Solicitando análise de cenários ao Gemini...")
    
    configuracao_json = types.GenerateContentConfig(
        response_mime_type="application/json"
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
            print(f"✅ Sucesso! Conectado e processado usando o modelo: {modelo_utilizado}")
            break
        except Exception as e:
            print(f"⚠️ Modelo {modelo} indisponível ou falhou. Motivo: {e}")
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
            
        print(f"✅ Análise do dia concluída. {len(novas_oportunidades)} novas oportunidades estruturadas.")
    except Exception as e:
        print(f"❌ ERRO ao decodificar o JSON gerado pelo modelo {modelo_utilizado}: {e}")
        print(f"Retorno bruto obtido pela IA que causou a falha:\n{resposta.text}")
        exit(1)

    print("🖼️ Buscando imagens contextuais...")
    for op in novas_oportunidades:
        termo = op.get("palavra_chave_imagem", "corporate business")
        op["imagem"] = obter_imagem_noticia_segura(termo)
        if "palavra_chave_imagem" in op:
            del op["palavra_chave_imagem"]
        
        if "link_noticia" not in op or not op["link_noticia"]:
            op["link_noticia"] = f"[https://www.google.com/search?q=noticias](https://www.google.com/search?q=noticias)+{'+'.join(op.get('marcas', ['mercado']))}"

    print("💾 Resgatando histórico e gravando dados...")
    
    arquivo_json = "oportunidades.json"
    dados_existentes = []
    
    # Tenta ler o arquivo antigo para não perder os dados
    if os.path.exists(arquivo_json):
        try:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                dados_existentes = json.load(f)
            print(f"📂 Histórico encontrado com {len(dados_existentes)} oportunidades antigas.")
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível ler o histórico anterior. Começando uma nova lista. Erro: {e}")
            
    # Junta as novidades no TOPO da lista
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
