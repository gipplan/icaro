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

    prompt_sistema = """
    Você é um analista de inteligência de mercado focado em Relações Públicas e Comunicação Corporativa.
    Sua tarefa é analisar o mercado das últimas 24 horas e identificar riscos e oportunidades para a seguinte lista de clientes ativos:
    - In Press Porter Novelli: Claro, Mercado Livre, Mercado Pago, Ambev, Prio, Vibra, Naturgy, Engie, Seara, PepsiCo, Prio, Gerdau, Einstein.
    - FleishmanHillard: Google, Shein, Stone, Mastercard, Samsung, Bayer, McKinsey, Cury Construtora.

    Gere um array em formato JSON estrito contendo as oportunidades reais encontradas.
    Cada objeto do array deve seguir rigorosamente este modelo:
    {
        "data": "DD/MM/AAAA",
        "agencia": "Nome exato da Agência",
        "setor": "Setor macro da oportunidade",
        "marcas": ["Marca1", "Marca2"],
        "descricao": "Texto analítico resumido com o gatilho e impacto de até 300 caracteres.",
        "produtos": ["Produto1", "Produto2"],
        "palavra_chave_imagem": "Termo em inglês simples e corporativo para buscar uma imagem conceitual da notícia"
    }
    """

    print("🔍 Consultando a API do Google para descobrir os modelos liberados para a sua chave...")
    modelos_prioritarios = []
    
    try:
        # Busca dinâmica: Pede para a API listar exatamente o que você tem permissão de usar
        for m in client.models.list():
            nome_limpo = m.name.replace('models/', '')
            # Filtra apenas modelos de texto da família Gemini
            if 'gemini' in nome_limpo and ('flash' in nome_limpo or 'pro' in nome_limpo):
                modelos_prioritarios.append(nome_limpo)
        print(f"✅ Modelos autorizados encontrados! Top 3: {modelos_prioritarios[:3]}")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível mapear dinamicamente. Usando versões fixas numéricas. Erro: {e}")
        # Fallback de segurança com os nomes numéricos exatos para chaves novas
        modelos_prioritarios = ['gemini-1.5-flash-002', 'gemini-1.5-pro-002', 'gemini-1.5-flash-8b']

    # Se a API retornar vazio por algum motivo, garante que temos as versões base
    if not modelos_prioritarios:
        modelos_prioritarios = ['gemini-1.5-flash-002', 'gemini-1.5-pro-002']

    print("\n🧠 Solicitando análise de cenários ao Gemini...")
    
    configuracao_json = types.GenerateContentConfig(
        response_mime_type="application/json"
    )

    resposta = None
    modelo_utilizado = None

    # O robô agora testa os modelos válidos encontrados até um funcionar
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
        oportunidades = json.loads(conteudo_bruto)
        print(f"✅ Análise de dados concluída. {len(oportunidades)} oportunidades estruturadas.")
    except Exception as e:
        print(f"❌ ERRO ao decodificar o JSON gerado pelo modelo {modelo_utilizado}: {e}")
        print(f"Retorno bruto obtido:\n{resposta.text}")
        exit(1)

    print("🖼️ Buscando imagens contextuais seguras via SafeSearch...")
    for op in oportunidades:
        termo = op.get("palavra_chave_imagem", "corporate business")
        op["imagem"] = obter_imagem_noticia_segura(termo)
        if "palavra_chave_imagem" in op:
            del op["palavra_chave_imagem"]

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
