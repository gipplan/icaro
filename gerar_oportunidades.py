import os
import json
import re
from google import genai
from google.genai import types

def carregar_playbook():
    try:
        with open('playbook.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Nenhum playbook personalizado encontrado. Siga as diretrizes de Diretor Sênior de PR."

def gerar_oportunidades():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave da API não encontrada nas variáveis de ambiente.")
    
    client = genai.Client(api_key=api_key)
    
    print("🔍 Diagnosticando modelos disponíveis para a sua chave de API...")
    try:
        modelos_disponiveis = [m.name for m in client.models.list() if "gemini" in m.name]
        print(f"Modelos encontrados: {modelos_disponiveis}")
    except Exception as e:
        print(f"Aviso: Não foi possível listar os modelos. Erro: {e}")
    
    playbook_texto = carregar_playbook()

    prompt = f"""
Atue como Í.C.A.R.O., o motor de inteligência e curadoria editorial corporativa. Execute a varredura comercial diária e cruzamento de dados de hoje, identificando riscos e oportunidades de relações públicas e comunicação corporativa. Foque nas 5 a 10 pautas mais quentes do dia no total.

⚠️ PRIORIDADE DE BUSCA: Dê prioridade máxima na varredura para identificar notícias reais sobre **iFood** e **Stone**. 
**REGRA DE VERACIDADE ESTRITA:** Você SÓ deve incluir pautas para essas marcas se houver fatos factuais e comprovados na mídia nas últimas 48h. Se não houver nenhum fato real e noticioso sobre elas, **NÃO INVENTE, NÃO ALUCINE e NÃO AS INCLUA no JSON final**. Prefira entregar um JSON sem iFood e Stone a entregar um fato fictício. Preencha a cota de 5 a 10 pautas com outras marcas da lista que tenham notícias reais.

Você deve executar OBRIGATORIAMENTE duas frentes de busca:

**FRENTE 1: Radar de Marcas**
Busque fatos relevantes ocorridos nas últimas 24/48 horas estritamente para a seguinte lista de clientes (utilize a categoria para preencher o campo 'agencia' no JSON):

**Clientes In Press Porter Novelli:**
Canais Globo, Editora Globo, IDB Maraey, Maratona do Rio, Rio Open, Sail GP, ICT Costa Rica, Globo Internacional, Globo Portugal, Riot Games, Seara, happn, Fundação Mapfre, MAPFRE, Open Society, Fundação Ford Foundation, Sony Music, Taboaço, Reyou, Engie, Yara, RZK Energia, Siemens Energy, Abihpec, DSM, Bunge, Matrix, Agrolend, Ambev, Electrolux, Emma Colchões, Gallo, General Mills, Randstad, Unilever, Rexona, Americanas, Betano, Caixa Consórcio, Caixa Seguradora, Chevron, CNP, FenaSaúde, Firjan, IBS Energy, Karoon, Naturgy, Rio Mais, Prio, Seadrill, TAESA, Vibra, White Martins, Abecs, Atos, AWS, Black Rock, Banco Mercantil, BBCE, Cisco, CLARO, Equinix, FICO, HPE, Intelbras, Mercado Bitcoin, Iron Mountain, Madrona Advogados, Sicredi, Solis Investimentos, JOVI, PhizChat, Wiz, Cidade Center Norte, Mercado Livre, Mercado Pago, Natura, Avon, São Leopoldo Mandic, McDonalds, Compra Agora, Senac SP, SAEA, Insper, iFood, Klabin, Abasp, Penske, Bla Bla Car, IBJR, Corteva, ArcelorMittal, Localiza, Belgo Arames, Direcional, Farmax, Norsk Hydro, Grupo Sada, Vale, Veolia, GSK, Afya, Servier, Roche farma, Roche Dia, MV, Medsenior, Johnson & Johnson, Henkel, TIC Trens, Motiva (CCR), GOL/Smiles, IBGC, eureciclo, Mattel, Royal Canin, PepsiCo, Herbalife.

**Clientes FleishmanHillard:**
Abrintel, Harsco, ICC, LANXESS, Oz, Bayer, HCor, Albert Einstein, Philips do Brasil, Philips Medical, Samsung, Stone, Kellanova, Google, Mastercard, Shein, State Grid, Hitachi, McKinsey, Abrabe, General Motors, Sicredi Brasília, ABDE, Belo Sun, Beiersdorf, Cury Construtora, Newell, Onçafari, Votorantim, Veracel, Softys, Guerbet.

**FRENTE 2: Radar Macroeconômico (Setorial)**
Identifique movimentações governamentais, regulatórias ou de mercado que gerem impacto crítico para os setores:
- Tecnologia, IA e Eletroeletrônicos
- E-commerce, Varejo e Logística
- Energia, Mineração e Siderurgia (ESG)
- Finanças e Fintechs
- Aviação e Turismo

**DIRETRIZES PARA A "TÁTICA SUGERIDA" (NÍVEL DIRETOR DE PR):**
Atue como um Diretor Sênior de Comunicação Corporativa. Suas recomendações não podem ser óbvias ou operacionais (NUNCA sugira "fazer press release" ou "postar nas redes").
Sua tática sempre deve começar com um verbo no gerúndio e justificar o impacto no negócio.
Use EXCLUSIVAMENTE as estratégias e gatilhos listados no playbook da agência abaixo para formular as recomendações:

--- INÍCIO DO PLAYBOOK ---
{playbook_texto}
--- FIM DO PLAYBOOK ---

**DIRETRIZES DE SAÍDA (JSON STRICT):**
1. Para as notícias da Frente 1, adicione o campo "tipo": "marca". O campo "titulo" deve ser vazio.
2. Para as notícias da Frente 2, adicione o campo "tipo": "setor" e preencha o campo "titulo" com o tema macro.
3. Entregue a resposta EXCLUSIVAMENTE em formato de array JSON válido, sem markdown, sem textos antes ou depois.
4. Estrutura do objeto: tipo, titulo (se macro), agencia, setor, marcas (array), descricao (Fato + Tática baseada no playbook), produtos (array com 1 a 3 produtos de PR), link_noticia, data (formato DD/MM/AAAA usando a data de hoje) e imagem (URL - busque fotos realistas de bancos de imagens gratuitos se não tiver a fonte).
"""

    print("Enviando requisição para a API do Gemini usando o modelo 3.5 Flash...")
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            tools=[{"google_search": {}}]
        )
    )
    
    texto_resposta = response.text
    
    if "```json" in texto_resposta:
        texto_resposta = texto_resposta.split("```json")[1].split("```")[0].strip()
    elif "```" in texto_resposta:
        texto_resposta = texto_resposta.split("```")[1].split("```")[0].strip()
        
    texto_resposta = texto_resposta.strip()

    try:
        # 1. Transforma o resultado de hoje em uma lista Python
        novas_oportunidades = json.loads(texto_resposta)
        
        # 2. Prepara uma lista vazia para o histórico
        historico = []
        
        # 3. Se o arquivo já existir, lê o que tem lá dentro e guarda na lista de histórico
        if os.path.exists('oportunidades.json'):
            with open('oportunidades.json', 'r', encoding='utf-8') as f:
                conteudo = f.read()
                if conteudo.strip():
                    try:
                        historico = json.loads(conteudo)
                    except json.JSONDecodeError:
                        print("Aviso: O arquivo antigo estava vazio ou inválido. Iniciando um novo.")
        
        # 4. Junta as duas listas (a velha e a nova)
        if isinstance(historico, list) and isinstance(novas_oportunidades, list):
            historico.extend(novas_oportunidades)
        else:
            historico = novas_oportunidades
            
        # 5. Salva a lista gigante e atualizada de volta no arquivo json, usando formatação bonita
        with open('oportunidades.json', 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=4)
            
        print("Sucesso! As novas pautas foram adicionadas ao histórico do oportunidades.json.")
        
    except json.JSONDecodeError:
        print("Erro: A resposta da API não foi um JSON válido. Veja a resposta crua:")
        print(texto_resposta)
        raise

if __name__ == "__main__":
    gerar_oportunidades()
