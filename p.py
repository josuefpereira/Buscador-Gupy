import pandas as pd
from flask import Flask, render_template, request, jsonify
from urllib.parse import quote
import requests
import os
from flask_cors import CORS

# --- CONFIGURAÇÕES ---
NOME_ARQUIVO_CIDADES = 'cidades_brasil.csv'
URL_DADOS = 'https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/csv/municipios.csv'
LIMITE_CIDADES = 80

# --- DICIONÁRIOS ---
estado_map = { 'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins' }
ibge_uf_map = { '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO', '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP', '41': 'PR', '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF' }

def obter_dados_cidades():
    if not os.path.exists(NOME_ARQUIVO_CIDADES):
        try: 
            print("Baixando arquivo de cidades...")
            response = requests.get(URL_DADOS); response.raise_for_status()
            with open(NOME_ARQUIVO_CIDADES, 'wb') as f: f.write(response.content)
            print("Download concluído!")
        except Exception as e: 
            print(f"FALHA NO DOWNLOAD: {e}")
            return pd.DataFrame()
    
    print(f"Lendo arquivo local '{NOME_ARQUIVO_CIDADES}'...")
    try:
        # Lê o arquivo CSV baixado
        df = pd.read_csv(NOME_ARQUIVO_CIDADES)
        
        # --- CORREÇÃO IMPORTANTE AQUI ---
        # O arquivo baixado tem as colunas 'nome', 'latitude', 'longitude', e 'codigo_uf'.
        # Vamos garantir que estamos usando esses nomes exatos.
        colunas_necessarias = ['nome', 'latitude', 'longitude', 'codigo_uf']
        
        # Verifica se todas as colunas necessárias existem no arquivo
        if not all(coluna in df.columns for coluna in colunas_necessarias):
            print("!!!!!! ERRO: O arquivo CSV baixado não contém as colunas esperadas.")
            print(f"Colunas encontradas: {list(df.columns)}")
            return pd.DataFrame()

        df_filtrado = df[colunas_necessarias].copy()
        df_filtrado.rename(columns={'codigo_uf': 'uf'}, inplace=True)
        df_filtrado.dropna(inplace=True)
        return df_filtrado
    except Exception as e: 
        print(f"ERRO AO LER OU PROCESSAR O CSV: {e}")
        return pd.DataFrame()

app = Flask(__name__)
CORS(app, resources={r"/get-cities-in-view": {"origins": "https://jobbmapper.netlify.app"}})
df_cidades = obter_dados_cidades()
if not df_cidades.empty:
    print(f">>> Arquivo de cidades carregado com sucesso! Total de {len(df_cidades)} cidades válidas.")

@app.route('/')
def health_check(): 
    return "API do Jobb Mapper está no ar."

@app.route('/get-cities-in-view', methods=['POST'])
def get_cities_in_view():
    # ... (O resto do código da função permanece o mesmo) ...
    if df_cidades.empty: return jsonify({'message': 'Erro: A base de dados de cidades não foi carregada.'})
    data = request.get_json(); bounds = data.get('bounds')
    term = data.get('term', '').strip(); company = data.get('company', '').strip()
    sort = data.get('sort'); pwd = data.get('pwd'); workplaceTypes = data.get('workplaceTypes')
    if not bounds: return jsonify({'error': 'Coordenadas não fornecidas.'})
    north_east = bounds.get('_northEast'); south_west = bounds.get('_southWest')
    mask = ( (df_cidades['latitude'] <= north_east['lat']) & (df_cidades['latitude'] >= south_west['lat']) & (df_cidades['longitude'] <= north_east['lng']) & (df_cidades['longitude'] >= south_west['lng']) )
    cidades_visiveis = df_cidades[mask]
    if cidades_visiveis.empty: return jsonify({'message': 'Nenhuma cidade encontrada na área.'})
    lista_nomes_cidades = cidades_visiveis['nome'].tolist()
    if len(lista_nomes_cidades) > LIMITE_CIDADES: return jsonify({'message': f'Área muito grande. Selecione menos de {LIMITE_CIDADES} cidades.'})
    base_url = "https://portal.gupy.io/job-search/"; params = []
    termo_de_busca_completo = f"{term} {company}".strip()
    if termo_de_busca_completo: params.append(f"term={quote(termo_de_busca_completo)}")
    if sort and '_' in sort: sortBy, sortOrder = sort.split('_'); params.append(f"sortBy={sortBy}&sortOrder={sortOrder}")
    codigo_uf = cidades_visiveis['uf'].iloc[0]; sigla_estado = ibge_uf_map.get(str(int(codigo_uf)))
    nome_completo_estado = estado_map.get(sigla_estado, sigla_estado) if sigla_estado else "Estado Desconhecido"
    params.append(f"state={quote(nome_completo_estado)}"); params.append(f"city[]={quote(','.join(lista_nomes_cidades))}")
    if pwd: params.append("pwd=true")
    if workplaceTypes: params.append(f"workplaceTypes[]={','.join(workplaceTypes)}")
    url_gupy = base_url + "&".join(params)
    return jsonify({'gupy_url': url_gupy})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)