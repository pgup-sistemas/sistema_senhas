from flask import render_template, request, redirect, url_for, flash, make_response, Blueprint
from datetime import datetime, date
from ..models import db, Senha, TipoAtendimento, Configuracao
import os
import sys
try:
    import cups
except ImportError:
    cups = None
try:
    import win32print
    import win32ui
    from PIL import Image, ImageWin, ImageFont, ImageDraw
except ImportError:
    win32print = None
    win32ui = None
    Image = None
    ImageWin = None
    ImageFont = None
    ImageDraw = None

public_bp = Blueprint('public', __name__)

# Função utilitária para buscar configs

def get_config():
    config_keys = ['nome_clinica', 'mensagem_painel']
    configs = {c.chave: c.valor for c in Configuracao.query.filter(Configuracao.chave.in_(config_keys))}
    return configs

def imprimir_senha(senha, tipo, nome_clinica=None):
    """
    Imprime o ticket da senha em impressora térmica via CUPS (Linux) ou win32print (Windows).
    """
    if sys.platform.startswith('win'):
        # Impressão no Windows
        if not win32print or not win32ui or not Image or not ImageWin or not ImageFont or not ImageDraw:
            return False, 'pywin32 e pillow não instalados.'
        try:
            printer_name = win32print.GetDefaultPrinter()
            # Monta o texto formatado
            texto = []
            if nome_clinica:
                texto.append(nome_clinica.upper())
            texto.append('='*24)
            texto.append(f'SENHA: {tipo.sigla}{senha.numero:03d}')
            texto.append(f'Tipo: {tipo.nome}')
            texto.append(f'Data: {senha.data_emissao.strftime("%d/%m/%Y")}')
            texto.append(f'Hora: {datetime.now().strftime("%H:%M:%S")}')
            texto.append('='*24)
            texto.append('Aguarde ser chamado.')
            texto = '\n'.join(texto)
            # Cria imagem para impressão (simula ticket)
            font = ImageFont.truetype("arial.ttf", 28) if os.path.exists("C:/Windows/Fonts/arial.ttf") else ImageFont.load_default()
            img = Image.new('L', (384, 320), 255)
            draw = ImageDraw.Draw(img)
            y = 10
            for line in texto.split('\n'):
                w, h = draw.textsize(line, font=font)
                draw.text(((384-w)//2, y), line, font=font, fill=0)
                y += h + 6
            # Envia para impressora
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            hDC.StartDoc("Senha Clínica")
            hDC.StartPage()
            dib = ImageWin.Dib(img)
            dib.draw(hDC.GetHandleOutput(), (0,0,384,320))
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            return True, 'Impressão enviada.'
        except Exception as e:
            return False, str(e)
    else:
        # Linux/CUPS ESC-POS
        if not cups:
            return False, 'pycups não instalado.'
        try:
            conn = cups.Connection()
            printers = conn.getPrinters()
            if not printers:
                return False, 'Nenhuma impressora encontrada.'
            printer_name = list(printers.keys())[0]
            ESC = '\x1B'
            GS = '\x1D'
            texto = b''
            texto += ESC.encode() + b'@'  # reset
            texto += ESC.encode() + b'a' + b'1'  # centralizar
            if nome_clinica:
                texto += (nome_clinica.upper() + '\n').encode('utf-8')
            texto += b'========================\n'
            texto += ESC.encode() + b'!' + b'0x30'  # fonte dupla
            texto += f'SENHA: {tipo.sigla}{senha.numero:03d}\n'.encode('utf-8')
            texto += ESC.encode() + b'!' + b'0x00'  # fonte normal
            texto += f'Tipo: {tipo.nome}\n'.encode('utf-8')
            texto += f'Data: {senha.data_emissao.strftime("%d/%m/%Y")}\n'.encode('utf-8')
            texto += f'Hora: {datetime.now().strftime("%H:%M:%S")}\n'.encode('utf-8')
            texto += b'========================\n'
            texto += b'Aguarde ser chamado.\n\n\n'
            texto += GS.encode() + b'V' + b'\x00'  # corte total
            temp_path = '/tmp/senha_escpos.txt'
            with open(temp_path, 'wb') as f:
                f.write(texto)
            conn.printFile(printer_name, temp_path, "Senha Clínica", {"raw": "true"})
            return True, 'Impressão enviada.'
        except Exception as e:
            return False, str(e)

def emitir_senha_e_salvar(tipo_id):
    tipo = TipoAtendimento.query.get(tipo_id)
    if not tipo:
        return None, None, 'Tipo de atendimento inválido.'
    hoje = date.today()
    ultima_data = Configuracao.query.filter_by(chave='ultima_data_emissao').first()
    if not ultima_data or ultima_data.valor != hoje.strftime('%Y-%m-%d'):
        Senha.query.delete()
        db.session.commit()
        if not ultima_data:
            ultima_data = Configuracao(chave='ultima_data_emissao', valor=hoje.strftime('%Y-%m-%d'))
            db.session.add(ultima_data)
        else:
            ultima_data.valor = hoje.strftime('%Y-%m-%d')
        db.session.commit()
    ultima_senha = Senha.query.filter_by(tipo_id=tipo.id, data_emissao=hoje).order_by(Senha.numero.desc()).first()
    proximo_numero = 1 if not ultima_senha else ultima_senha.numero + 1
    senha = Senha(numero=proximo_numero, tipo_id=tipo.id, data_emissao=hoje)
    db.session.add(senha)
    db.session.commit()
    return senha, tipo, None

#@public_bp.route('/', methods=['GET', 'POST'])
#def emitir_senha():
#    tipos = TipoAtendimento.query.all()
#    configs = get_config()
#    senha_emitida = None
#    tipo_emitido = None
#    erro = None
#    if request.method == 'POST':
#        tipo_id = request.form.get('tipo_id')
#        senha_emitida, tipo_emitido, erro = emitir_senha_e_salvar(tipo_id)
#        if senha_emitida:
#            sucesso, msg = imprimir_senha(senha_emitida, tipo_emitido, nome_clinica=configs.get('nome_clinica'))
#            if not sucesso:
#                flash(f'Erro ao imprimir: {msg}', 'danger')
#        elif erro:
#            flash(erro, 'danger')
#    return render_template('public/emitir_senha.html', tipos=tipos, senha_emitida=senha_emitida, tipo_emitido=tipo_emitido, config_nome_clinica=configs.get('nome_clinica'), config_mensagem_painel=configs.get('mensagem_painel'))

@public_bp.route('/')
def landing():
    return render_template('public/landing.html')

@public_bp.route('/monitor')
def monitor():
    configs = get_config()
    return render_template('public/monitor.html', config_nome_clinica=configs.get('nome_clinica'), config_mensagem_painel=configs.get('mensagem_painel'))

@public_bp.route('/ajuda')
def ajuda():
    configs = get_config()
    return render_template('ajuda.html', nome_clinica=configs.get('nome_clinica'))
