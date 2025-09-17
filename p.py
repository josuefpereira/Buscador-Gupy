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
        except Exception as e: print(f"FALHA NO DOWNLOAD: {e}"); return pd.DataFrame()
    try:
        df = pd.read_csv(NOME_ARQUIVO_CIDADES)
        df_filtrado = df[['nome', 'codigo_uf', 'latitude', 'longitude']].copy()
        df_filtrado.rename(columns={'codigo_uf': 'uf'}, inplace=True); df_filtrado.dropna(inplace=True)
        return df_filtrado
    except Exception as e: print(f"ERRO AO LER CSV: {e}"); return pd.DataFrame()

app = Flask(__name__)
# Configuração de CORS para aceitar requisições do seu site no Netlify
CORS(app, resources={r"/get-cities-in-view": {"origins": "https://jobbmapper.netlify.app"}})
df_cidades = obter_dados_cidades()
if not df_cidades.empty: print(f">>> Arquivo de cidades carregado com sucesso! Total de {len(df_cidades)} cidades válidas.")

@app.route('/')
def health_check(): return "API do Jobb Mapper está no ar."

@app.route('/get-cities-in-view', methods=['POST'])
def get_cities_in_view():
    # ... (toda a lógica da função permanece a mesma)
    if df_cidades.empty: return jsonify({'message': 'Erro: Base de dados não carregada.'})
    data = request.get_json(); bounds = data.get('bounds')
    if not bounds: return jsonify({'error': 'Coordenadas não fornecidas.'})
    # ... (resto da lógica igual)
    return jsonify({'gupy_url': url_gupy})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)