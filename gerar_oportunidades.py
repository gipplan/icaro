import os
import json
import datetime
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
    print("🚀 Inicializando o motor Í.C.A.R.O. com o SDK unificado...")
    
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

    # PROMPT CORRIGIDO: Estrutura de Array [] explicitamente declarada com {{ }} para não quebrar o Python
    prompt_sistema = f"""
    Você é um analista de inteligência de mercado focado em Relações Públicas e Comunicação Corporativa.
    Hoje é {data_hoje}.
    Sua tarefa é analisar o mercado das últimas 24 horas e identificar riscos e oportunidades reais para a seguinte lista de clientes ativos:
    - In Press Porter Novelli: Claro, Mercado Livre, Mercado Pago, Ambev, Prio, Vibra, Naturgy, Engie, Seara, PepsiCo, Prio, Gerdau, Einstein.
    - FleishmanHillard: Google, Shein, Stone, Mastercard, Samsung, Bayer, McKinsey, Cury Construtora.

    Gere um array em formato JSON estrito contendo as oportunidades.
    A sua resposta DEVE ser um array de objetos `[]`. Siga rigorosamente este formato:
    [
        {{
            "data": "{data_hoje}",
            "agencia": "Nome exato da Agência",
            "setor": "Setor macro da oportunidade",
            "marcas": ["Marca1", "Marca2"],
            "descricao": "Texto analítico resumido com o gatilho e impacto de até 300 caracteres.",
            "produtos": ["Serviço 1", "Serviço 2"],
            "palavra_chave_imagem": "Termo em inglês simples e corporativo para buscar uma imagem conceitual da notícia",
            "link_noticia": "URL real de uma matéria em portal de notícias confiável que valide e embase esta oportunidade"
        }}
    ]

    ATENÇÃO PARA AS REGRAS:
    1. "produtos" refere-se EXCLUSIVAMENTE aos serviços de PR e Comunicação que a NOSSA AGÊNCIA vai vender/oferecer para o cliente (Exemplos: Gestão de Crise, Media Training, Relações Governamentais, Press Release, Thought Leadership, Auditoria de Imagem). NÃO inclua os produtos comerciais vendidos pela marca.
    2. A "data" deve ser sempre exatamente {data_hoje}.
    3. RETORNE APENAS O CÓDIGO JSON VÁLIDO.
    """

    print("🔍 Consultando a API do Google para descobrir os modelos liberados para a sua chave...")
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
        
        # Sistema de limpeza de segurança caso a IA mande formatação de texto ao redor do JSON
        if conteudo_bruto.startswith("```"):
            conteudo_bruto = conteudo_bruto.replace("```json", "").replace("```", "").strip()
            
        oportunidades = json.loads(conteudo_bruto)
        print(f"✅ Análise de dados concluída. {len(oportunidades)} oportunidades estruturadas.")
    except Exception as e:
        print(f"❌ ERRO ao decodificar o JSON gerado pelo modelo {modelo_utilizado}: {e}")
        print(f"Retorno bruto obtido pela IA que causou a falha:\n{resposta.text}")
        exit(1)

    print("🖼️ Buscando imagens contextuais...")
    for op in oportunidades:
        termo = op.get("palavra_chave_imagem", "corporate business")
        op["imagem"] = obter_imagem_noticia_segura(termo)
        if "palavra_chave_imagem" in op:
            del op["palavra_chave_imagem"]
        
        if "link_noticia" not in op or not op["link_noticia"]:
            op["link_noticia"] = f"[https://www.google.com/search?q=noticias](https://www.google.com/search?q=noticias)+{'+'.join(op.get('marcas', ['mercado']))}"

    print("💾 Gravando dados estruturados em oportunidades.json...")
    try:
        with open("oportunidades.json", "w", encoding="utf-8") as f:
            json.dump(oportunidades, f, ensure_ascii=False, indent=4)
        print("🎉 Processo finalizado com sucesso!")
    except Exception as e:
        print(f"❌ ERRO ao gravar o arquivo de saída: {e}")
        exit(1)

if __name__ == "__main__":
    executar_radar()
