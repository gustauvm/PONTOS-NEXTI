import re
from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from io import BytesIO

app = Flask(__name__)

def extrair_id_da_pagina(texto_pagina):
    try:
        # 1. Limpeza: Remove aspas e normaliza espaços para o texto ficar linear
        texto_limpo = texto_pagina.replace('"', '').replace('\n', ' ').replace('\r', ' ')
        
        # 2. Estratégia Principal: Procura o padrão de matrícula (ex: 719-4854 ou 818-4325)
        # O padrão busca qualquer sequência de números que tenha um traço e termine em 4 dígitos
        busca_padrao = re.search(r'(\d+-\d{4})', texto_limpo)
        
        if busca_padrao:
            matricula_encontrada = busca_padrao.group(1)
            # Remove o traço e pega apenas os 4 últimos
            so_numeros = matricula_encontrada.replace('-', '')
            id_final = int(so_numeros[-4:])
            return id_final
        
        # 3. Estratégia de Reserva: Se não achar o padrão acima, tenta achar a palavra Matrícula
        busca_chave = re.search(r'Matr[íi]cula[:\s\W]+([\d\-]+)', texto_limpo, re.IGNORECASE)
        if busca_chave:
            num = re.sub(r'\D', '', busca_chave.group(1))
            if len(num) >= 4:
                return int(num[-4:])
        
        return 999999
    except:
        return 999999

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('pdf_files')
        if not file or file.filename == '':
            return "Selecione o arquivo PDF.", 400

        reader = PdfReader(file)
        lista_paginas = []

        print(f"\n--- Analisando {len(reader.pages)} páginas ---")

        for i in range(len(reader.pages)):
            pagina = reader.pages[i]
            texto = pagina.extract_text()
            
            # Identifica o ID (ex: 4325)
            id_final = extrair_id_da_pagina(texto)
            lista_paginas.append({'id': id_final, 'obj': pagina})
            
            # Mostra o progresso no terminal para você acompanhar
            if (i + 1) % 25 == 0 or i == 0:
                print(f"Processando: {i+1}/{len(reader.pages)} páginas...")

        # ORDENAÇÃO MATEMÁTICA: Agora o 4325 virá antes do 4854
        lista_paginas.sort(key=lambda x: x['id'])

        # Montagem do PDF final reordenado
        writer = PdfWriter()
        for item in lista_paginas:
            writer.add_page(item['obj'])

        output = BytesIO()
        writer.write(output)
        output.seek(0)

        print("--- PDF Reordenado com Sucesso ---")
        return send_file(output, as_attachment=True, download_name='RELATORIO_ORDENADO_FINAL.pdf')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)