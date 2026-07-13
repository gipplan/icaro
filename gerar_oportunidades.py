import os
import json
import datetime
import google.generativeai as genai
from duckduckgo_search import DDGS

# 1. Configuração das APIs
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# 2. Função de Busca Segura de Imagens
def obter_imagem_noticia_segura(termo_busca):
    """Busca uma imagem relacionada usando DuckDuckGo com SafeSearch Estrito"""
    try:
        with DDGS() as ddgs:
            # safesearch='on' garante o filtro estrito contra conteúdo sensível/adulto
            resultados = list(ddgs.images(termo_busca, safesearch='on', max_results=1))
            if resultados and 'image' in resultados[0]:
                return resultados[0]['image']
    except Exception as e:
        print(f"Erro ao buscar imagem para '{termo_busca}': {e}")
    
    # Fallback: Imagem corporativa neutra e segura caso a busca falhe
    return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600"

# 3. Prompt de Contexto com a Carteira de Clientes (Resumo exemplificado)
PROMPT_SISTEMA = """
Você é um analista de inteligência de mercado focado em Relações Públicas e Comunicação Corporativa.
Sua tarefa é analisar o mercado das últimas 24 horas e identificar riscos e oportunidades para a seguinte lista de clientes ativos:
- In Press: Claro, Mercado Livre, Mercado Pago, Ambev, Prio, Vibra, Naturgy, Engie, Seara, PepsiCo, Prio, Gerdau, Einstein.
- FleishmanHillard: Google, Shein, Stone, Mastercard, Samsung, Bayer, McKinsey, Cury Construtora.

Gere um array em formato JSON estrito, sem formatações adicionais ou markdown, contendo as oportunidades reais encontradas.
Cada objeto do array deve seguir rigorosamente este modelo:
{
    "data": "DD/MM/AAAA",
    "agencia": "Nome exato da Agência",
    "setor": "Setor macro da oportunidade",
    "marcas": ["Marca1", "Marca2"],
    "descricao": "Texto analítico resumido com o gatilho e impacto de até 300 caracteres.",
    "produtos": ["Produto1", "Produto2"],
    "palavra_chave_imagem": "Termo em inglês simples e corporativo para buscar uma imagem conceitual da notícia (Ex: 'solar energy infrastructure', 'cybersecurity banking')"
}
"""

def executar_radar():
    model = genai.GenerativeModel('gemini-pro')
    
    # Executa a análise do dia
    hoje = datetime.date.today().strftime("%d/%m/%m")
    resposta = model.generate_content(f"{PROMPT_SISTEMA}\n execute a varredura para o dia de hoje.")
    
    try:
        # Limpa possíveis blocos de código markdown que o modelo envie
        conteudo_limpo = resposta.text.strip().replace("```json", "").replace("```", "")
        oportunidades = json.loads(conteudo_limpo)
        
        # Enriquece o JSON injetando as URLs das imagens seguras na ponta
        for op in oportunidades:
            termo = op.get("palavra_chave_imagem", "corporate business")
            op["imagem"] = obter_imagem_noticia_segura(termo)
            # Remove a chave temporária de busca para limpar o arquivo final
            if "palavra_chave_imagem" in op:
                del op["palavra_chave_imagem"]
        
        # Grava o resultado final que o front-end vai ler
        with open("oportunidades.json", "w", encoding="utf-8") as f:
            json.dump(oportunidades, f, ensure_ascii=False, indent=4)
            
        print("Arquivo oportunidades.json atualizado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao processar o retorno do Gemini: {e}")
        print(resposta.text)

if __name__ == "__main__":
    executar_radar()
