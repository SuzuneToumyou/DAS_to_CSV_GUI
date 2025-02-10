#!/usr/bin/python3
# coding: utf-8

import os
import glob
import pandas as pd
import numpy as np
import tqdm
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class DASConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 400, 200)
        self.setWindowTitle('DASデータをCSV変換')
        self.setAcceptDrops(True)

        layout = QVBoxLayout()
        self.label = QLabel('ここにファイルをドラッグ＆ドロップしてください')
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            self.convert_files(files[0])

    def convert_files(self, input_file):
        QMessageBox.information(self, 'CSV変換入力ファイル', input_file)

        # 出力フォルダ選択ダイアログの表示
        QMessageBox.information(self, 'DASデータをCSV変換', '出力フォルダを選択してください！')
        o_name = QFileDialog.getExistingDirectory(self, '出力フォルダを選択', os.path.abspath(os.path.dirname(__file__)))
        QMessageBox.information(self, 'CSV変換出力フォルダ', o_name)

        chk = os.path.basename(input_file)
        chkd = chk[0:1]
        if chkd == "N" or chkd == "I":
            f = open(input_file, "rb")
        else:
            f = open(input_file, "r", encoding="utf-8")
        das_file = os.path.splitext(os.path.basename(input_file))[0]
        out_file_name = os.path.join(o_name, das_file + ".csv")

        io = []
        vo = []
        data_num = 16384
        header_len = 1024

        hxnum = f.read()

        if hxnum[0:2] == b"IR":
            header_len = 2048
            v_cof = 0.125
            i_cof = 0.03125

            for i in range(data_num):
                i_data = hxnum[header_len+i*12:header_len+i*12+2]
                v_data = hxnum[header_len+i*12+2:header_len+i*12+4]
                v_data = bin(int.from_bytes(v_data, byteorder='big'))
                i_data = bin(int.from_bytes(i_data, byteorder='big'))
                polarity_v = int(bin(int(v_data, 0) >> 15), 0)

                if polarity_v == 1:
                    v_data = (int(bin(int(v_data, 0) ^ 0b1111111111111111), 0)+1) * (-1)
                else:
                    v_data = int(v_data, base=2)
                polarity_i = int(bin(int(i_data, 0) >> 15), 0)
                if polarity_i == 1:
                    i_data = (int(bin(int(i_data, 0) ^ 0b1111111111111111), 0)+1) * (-1)
                else:
                    i_data = int(i_data, base=2)
                io.append(i_data * i_cof)
                vo.append(v_data * v_cof)
        elif hxnum[0:2] == "AA" or hxnum[0:2] == "GS":
            data_len = 4
            v_cof = 0.25
            i_cof = 0.0625

            for i in range(data_num):
                v_data = hxnum[header_len+i*4:header_len+i*4+4]
                polarity_v = int(bin(int("0x" + v_data, 0) >> 15), 0)
                if polarity_v == 1:
                    v_data = (int(bin(int("0x" + v_data, 0) ^ 0b1111111111111111), 0)+1) * (-1)
                else:
                    v_data = int("0x" + v_data, 0)

                i_start = header_len + data_num * data_len
                i_data = hxnum[i_start+i*4:i_start+i*4+4]
                polarity_i = int(bin(int("0x" + i_data, 0) >> 15), 0)
                if polarity_i == 1:
                    i_data = (int(bin(int("0x" + i_data, 0) ^ 0b1111111111111111), 0)+1) * (-1)
                else:
                    i_data = int("0x" + i_data, 0)
                io.append(i_data * i_cof)
                vo.append(v_data * v_cof)
        else:
            data_len = 2
            v_cof = 2.0
            i_cof = 0.5

            for i in range(data_num):
                v_data = hxnum[header_len+i*4:header_len+i*4+2]
                i_data = hxnum[header_len+i*4+2:header_len+i*4+4]
                v_data = bin(int.from_bytes(v_data, byteorder='little'))
                i_data = bin(int.from_bytes(i_data, byteorder='little'))
                polarity_v = int(bin(int(v_data, 0) >> 15), 0)

                if polarity_v == 1:
                    v_data = (int(bin(int(v_data, 0) ^ 0b1111111111111111), 0)+1) * (-1)
                else:
                    v_data = int(v_data, base=2)
                polarity_i = int(bin(int(i_data, 0) >> 15), 0)
                if polarity_i == 1:
                    i_data = (int(bin(int(i_data, 0) ^ 0b1111111111111111), 0)+1) * (-1)
                else:
                    i_data = int(i_data, base=2)
                io.append(i_data * i_cof)
                vo.append(v_data * v_cof)

        outlist = [io, vo]
        name = ["Ｉｏ(mA)", "Ｖｏ(V)"]
        outframe = pd.DataFrame(outlist, index=name)
        outframe = outframe.T
        outframe.to_csv(out_file_name, encoding="utf-8_sig")
        f.close()

if __name__ == '__main__':
    app = QApplication([])
    ex = DASConverter()
    app.exec_()