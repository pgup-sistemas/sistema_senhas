# Utilitário para impressão de senha (Linux e Windows)
import os
import sys
from datetime import datetime

def imprimir_senha(senha, tipo, nome_clinica=None):
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

    if sys.platform.startswith('win'):
        # Impressão no Windows
        if not win32print or not win32ui or not Image or not ImageWin or not ImageFont or not ImageDraw:
            return False, 'pywin32 e pillow não instalados.'
        try:
            printer_name = win32print.GetDefaultPrinter()
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
            font = ImageFont.truetype("arial.ttf", 28) if os.path.exists("C:/Windows/Fonts/arial.ttf") else ImageFont.load_default()
            img = Image.new('L', (384, 320), 255)
            draw = ImageDraw.Draw(img)
            y = 10
            for line in texto.split('\n'):
                w, h = draw.textsize(line, font=font)
                draw.text(((384-w)//2, y), line, font=font, fill=0)
                y += h + 6
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
