# coding=utf8
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import psycopg2

class HandleRefreshFromPPP():

    def __init__(self, path, host, port, db_name, user, password):
        self.folder = Path(path)
        self.conn = psycopg2.connect("host='{0}' port='{1}' dbname='{2}' user='{3}' password='{4}'".format(
            host, port, db_name, user, password))
        self.map_orbit = {
            'ULTRA-RÁPIDA': 2,
            'RÁPIDA': 3,
            'FINAL': 4
        }

    def readPPP(self):
        # Possibility : update the timestamp of measure's beginning from PPP and orbita(has domain)
        files = [x for x in self.folder.rglob('*.txt') if '6_Processamento_PPP' in x.parts]
        correct_txts = []
        for item in files:
            if(not item.match("**/*LEIAME*")):
                correct_txts.append(item)
        
        for correct_txt in correct_txts:
            with correct_txt.open(mode='r') as txtfile:
                point = {}
                page_content = txtfile.readlines()
                point['altitude_geometrica'] = re.findall(r'[0-9]{1,},[0-9]{1,2}', page_content[15])
                point['altitude_geometrica'] = str(point['altitude_geometrica']).replace(",", ".")
                point['altitude_geometrica'] = str(point['altitude_geometrica']).replace("[", "")
                point['altitude_geometrica'] = str(point['altitude_geometrica']).replace("]", "")
                point['altitude_geometrica'] = str(point['altitude_geometrica']).replace("'", "")
                point['norte'] = re.findall(r'[0-9]{7},[0-9]{3}', page_content[19])
                point['norte'] = str(point['norte']).replace(",", ".")
                point['norte'] = str(point['norte']).replace("[", "")
                point['norte'] = str(point['norte']).replace("]", "")
                point['norte'] = str(point['norte']).replace("'", "")
                point['leste'] = re.findall(r'[0-9]{6},[0-9]{3}', page_content[20])
                point['leste'] = str(point['leste']).replace(",", ".")
                point['leste'] = str(point['leste']).replace("[", "")
                point['leste'] = str(point['leste']).replace("]", "")
                point['leste'] = str(point['leste']).replace("'", "")
                # point['altitude_geometrica'] = point['altitude_geometrica'].replace(',', '.')
                point['cod_ponto'] = re.findall(r'MARCO  (.+)', page_content[2]) # remover espaço em branco
                point['cod_ponto'] = str(point['cod_ponto']).replace("[", "")
                point['cod_ponto'] = str(point['cod_ponto']).replace("]", "")
                point['cod_ponto'] = str(point['cod_ponto']).replace("'", "")
                point['cod_ponto'] = str(point['cod_ponto']).replace(" ", "")
                point['modelo_geoidal'] = re.findall(r'MODELO (.+)', page_content[22])
                point['modelo_geoidal'] = str(point['modelo_geoidal']).replace("[", "")
                point['modelo_geoidal'] = str(point['modelo_geoidal']).replace("]", "")
                point['modelo_geoidal'] = str(point['modelo_geoidal']).replace("'", "")
                point['freq_processada'] = re.findall(r'FREQ   (.+)', page_content[9]) # remover espaço em branco
                point['freq_processada'] = str(point['freq_processada']).replace(" ", "")
                point['freq_processada'] = str(point['freq_processada']).replace("[", "")
                point['freq_processada'] = str(point['freq_processada']).replace("]", "")
                point['freq_processada'] = str(point['freq_processada']).replace("'", "")
                data = re.findall(r'\d\d\d\d/\d\d/\d\d', page_content[0])
                point['data_processamento'] = datetime.strptime(data[0], '%Y/%m/%d')  
                orbita_str = re.findall(r'ORBITA (.+)', page_content[11])
                point['orbita'] = self.map_orbit[orbita_str[0]]
                point['altitude_ortometrica'] = re.findall(r'[0-9]{1,},[0-9]{1,2}', page_content[25])
                point['altitude_ortometrica'] = str(point['altitude_ortometrica']).replace(",", ".")
                point['altitude_ortometrica'] = str(point['altitude_ortometrica']).replace("[", "")
                point['altitude_ortometrica'] = str(point['altitude_ortometrica']).replace("]", "")
                point['altitude_ortometrica'] = str(point['altitude_ortometrica']).replace("'", "")
                point['meridiano_central'] = re.findall(r'-[0-9]{1,2}', page_content[21])
                point['meridiano_central'] = str(point['meridiano_central']).replace(",", ".")
                point['meridiano_central'] = str(point['meridiano_central']).replace("[", "")
                point['meridiano_central'] = str(point['meridiano_central']).replace("]", "")
                point['meridiano_central'] = str(point['meridiano_central']).replace("'", "")
                point['fuso'] = self.getFuso(int(point['meridiano_central']))
                lat = re.findall(r'-?[0-9]{2} [0-9]{2} [0-9]{2},[0-9]{4}', page_content[13])[0]
                lon = re.findall(r'-?[0-9]{2} [0-9]{2} [0-9]{2},[0-9]{4}', page_content[14])[0]
                point['latitude'], point['longitude'] = self.evaluateCoords(lat, lon)
                print(point)
                self.updateDB(point)

    def updateDB(self, point):
        with self.conn.cursor() as cursor:
            cursor.execute(u'''
            UPDATE bpc.ponto_controle_p
            SET norte='{norte}', leste='{leste}', altitude_geometrica='{altitude_geometrica}', altitude_ortometrica='{altitude_ortometrica}',
            freq_processada='{freq_processada}', latitude='{latitude}', longitude='{longitude}', geom=ST_GeomFromText('POINT({longitude} {latitude})', 4674),
            data_processamento='{data_processamento}', meridiano_central='{meridiano_central}', orbita={orbita}, modelo_geoidal='{modelo_geoidal}', fuso='{fuso}'
            WHERE cod_ponto='{cod_ponto}'
            '''.format(**point))
            self.conn.commit()

    @staticmethod
    def evaluateCoords(lat, lon):
        lat_deg, lat_min, lat_seg = re.findall(r'(.{2,3}) (\d\d) (.{7})', lat)[0]
        lon_deg, lon_min, lon_seg = re.findall(r'(.{2,3}) (\d\d) (.{7})', lon)[0]

        if float(lat_deg) > 0:
            new_lat = float(lat_deg) + float(lat_min)/60 + float(lat_seg.replace(',', '.'))/3600
        else:
            new_lat = float(lat_deg) - float(lat_min)/60 - float(lat_seg.replace(',', '.'))/3600

        if float(lon_deg) > 0:
            new_lon = float(lon_deg) + float(lon_min)/60 + float(lon_seg.replace(',', '.'))/3600
        else:
            new_lon = float(lon_deg) - float(lon_min)/60 - float(lon_seg.replace(',', '.'))/3600
        return new_lat, new_lon
    
    @staticmethod
    def getFuso(centralMeridian):
        return -(-(180 + centralMeridian)//6) # Equivalent to ceil


if __name__ == "__main__":
    test = HandleRefreshFromPPP(*sys.argv[1:])
    test.readPPP()