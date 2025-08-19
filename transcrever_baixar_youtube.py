import os
import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit
)
import yt_dlp

def limpar_segmento(texto):
    texto = re.sub(r'<c>|</c>', '', texto)
    texto = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', texto)
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto.lower().split()

def parse_vtt(caminho):
    segmentos = []
    with open(caminho, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    bloco = []
    for linha in linhas:
        if re.match(r'\d{2}:\d{2}:\d{2}\.\d{3} -->', linha):
            if bloco:
                texto = ' '.join([l.strip() for l in bloco if l.strip()])
                if texto:
                    segmentos.append(texto)
                bloco = []
        elif linha.strip() and not re.match(r'\d{2}:\d{2}:\d{2}\.\d{3} -->', linha):
            bloco.append(linha.strip())
    if bloco:
        texto = ' '.join([l.strip() for l in bloco if l.strip()])
        if texto:
            segmentos.append(texto)
    return segmentos

def baixar_legenda_youtube(url):
    # Extrai info para pegar o título
    with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
        info = ydl.extract_info(url, download=False)
    # Remove espaços e caracteres problemáticos do título
    titulo = re.sub(r'[^\w\-]', '_', info.get('title', 'video'))
    saida = titulo + ".%(ext)s"
    opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['pt'],
        'outtmpl': saida,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    # Procura por qualquer arquivo de legenda gerado
    # Busca por qualquer arquivo .vtt ou .srt na pasta
    legendas = [arq for arq in os.listdir('.') if arq.endswith('.vtt') or arq.endswith('.srt')]
    # Se só existe uma legenda, retorna ela
    if len(legendas) == 1:
        return legendas[0]
    # Se há várias, tenta encontrar uma que contenha parte do título
    for arq in legendas:
        if titulo[:15] in arq:
            return arq
    # Se não achou, retorna a primeira
    if legendas:
        return legendas[0]
    return None

class TranscritorYoutube(QWidget):
    def baixar_video(self):
        url = self.input_url.text().strip()
        if not url:
            self.label_status_video.setText("Insira uma URL válida.")
            return
        self.label_status_video.setText("Baixando vídeo...")
        QApplication.processEvents()
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            titulo = info.get('title', 'video').replace(' ', '_')
            saida = titulo + '.mp4'
            opts = {
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                'outtmpl': saida,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.label_status_video.setText(f'Vídeo baixado: {saida}')
        except Exception as e:
            self.label_status_video.setText(f'Erro: {e}')
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transcritor YouTube")
        self.resize(600, 600)
        layout = QVBoxLayout(self)

        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Cole a URL do vídeo do YouTube aqui")
        layout.addWidget(self.input_url)


        self.btn_baixar = QPushButton("Baixar Legenda")
        self.btn_baixar.clicked.connect(self.baixar_legenda)
        layout.addWidget(self.btn_baixar)

        self.btn_baixar_video = QPushButton("Baixar Vídeo 720p")
        self.btn_baixar_video.clicked.connect(self.baixar_video)
        layout.addWidget(self.btn_baixar_video)

        self.label_status = QLabel("")
        layout.addWidget(self.label_status)

        self.label_status_video = QLabel("")
        layout.addWidget(self.label_status_video)

        self.btn_salvar = QPushButton("Salvar Legenda Limpa")
        self.btn_salvar.clicked.connect(self.salvar_legenda)
        self.btn_salvar.setEnabled(False)
        layout.addWidget(self.btn_salvar)

        self.segmentos = []
        self.arquivo_legenda = None


    def baixar_legenda(self):
        url = self.input_url.text().strip()
        if not url:
            self.label_status.setText("Insira uma URL válida.")
            return
        self.label_status.setText("Baixando legenda...")
        caminho = baixar_legenda_youtube(url)
        if not caminho:
            self.label_status.setText("Legenda não encontrada.")
            return
        else:
            self.label_status.setText(f"Legenda baixada com sucesso: {caminho}")
        self.segmentos = parse_vtt(caminho)
        self.arquivo_legenda = caminho
        if not self.segmentos:
            self.label_status.setText("Legenda vazia ou não processada.")
            return
        self.label_status.setText(f"Legenda baixada e limpa ({len(self.segmentos)} linhas). Arquivo: {caminho}")
        self.btn_salvar.setEnabled(True)

    def salvar_legenda(self):
        if not self.segmentos:
            return
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar legenda limpa", "", "TXT (*.txt)")
        if caminho:
            with open(caminho, "w", encoding="utf-8") as f:
                for seg in self.segmentos:
                    f.write(' '.join(limpar_segmento(seg)) + "\n")
            self.label_status.setText("Legenda salva!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TranscritorYoutube()
    win.show()
    sys.exit(app.exec_())
