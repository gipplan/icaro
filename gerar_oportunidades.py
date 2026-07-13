import os
import json
import datetime
from google import genai
from google.genai import types  # Importa os tipos de configuração do novo SDK
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
    
    return "[https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600](https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600)"

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

    print("🧠 Solicitando análise de cenários ao Gemini (gemini-2.5-flash)...")
    try:
        # Configura o motor para forçar a saída em JSON puro, sem markdown block
        configuracao_json = types.GenerateContentConfig(
            response_mime_type="application/json"
        )
        
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',  # Modelo atualizado e suportado em 2026
            contents=prompt_sistema,
            config=configuracao_json
        )
        
        # Como forçamos o tipo MIME, a resposta vem como string JSON pura
        conteudo_bruto = resposta.text.strip()
        oportunidades = json.loads(conteudo_bruto)
        print(f"✅ Análise concluída. {len(oportunidades)} oportunidades identificadas.")
        
    except Exception as e:
        print(f"❌ ERRO ao processar ou decodificar o retorno da IA: {e}")
        if 'resposta' in locals():
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
