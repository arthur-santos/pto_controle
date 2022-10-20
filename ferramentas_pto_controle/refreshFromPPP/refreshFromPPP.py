# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PontoControle
                                 A QGIS plugin
 Ferramentas para a gerência de pontos de controle
                              -------------------
        begin                : 2019-11-18
        copyright            : (C) 2019 by 1CGEO/DSG
        email                : eliton.filho@eb.mil.br, arthur.santos@ime.eb.br, mateus.sereno@ime.eb.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = '1CGEO/DSG'
__date__ = '2019-11-18'
__copyright__ = '(C) 2019 by 1CGEO/DSG'
__revision__ = '$Format:%H$'


from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber)
from qgis.PyQt.QtCore import QCoreApplication
from .handleRefreshFromPPP import HandleRefreshFromPPP
from .handleRefreshFromCSV import HandleRefreshFromCSV

class RefreshFromPPP(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    OUTPUT = 'OUTPUT'
    METHOD = 'METHOD'
    FOLDER = 'FOLDER'
    CSVFILE = 'CSVFILE'
    SERVERIP = 'SERVERIP'
    PORT = 'PORT'
    BDNAME = 'BDNAME'
    USER = 'USER'
    PASSWORD = 'PASSWORD'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.addParameter(
            QgsProcessingParameterEnum(
                self.METHOD,
                self.tr('Selecione o método (PPP ou RTE)'),
                options=['PPP', 'RTE']
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFile(
                self.FOLDER,
                self.tr('Selecionar a pasta caso tenha escolhido PPP (caso tenha escolhido RTE não selecionar nada)'),
                behavior=QgsProcessingParameterFile.Folder,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.CSVFILE,
                self.tr('Selecionar o arquivo CSV caso tenha escolhido RTE (caso tenha escolhido PPP não selecionar nada)'),
                behavior=QgsProcessingParameterFile.File,
                extension='csv',
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.SERVERIP,
                self.tr('Insira o IP do computador'),
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PORT,
                self.tr('Insira a porta'),
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.BDNAME,
                self.tr('Insira o nome do banco de dados'),
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.USER,
                self.tr('Insira o usuário do PostgreSQL'),
                optional=True
            )
        )

        password = QgsProcessingParameterString(
            self.PASSWORD,
            self.tr('Insira a senha do PostgreSQL'),
            optional=True
        )
        password.setMetadata({
            'widget_wrapper':
            'ferramentas_pto_controle.utils.wrapper.MyWidgetWrapper'})

        self.addParameter(password)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        method = self.parameterAsEnum(parameters, self.METHOD, context)
        server_ip = self.parameterAsString(parameters, self.SERVERIP, context)
        port = self.parameterAsInt(parameters, self.PORT, context)
        bdname = self.parameterAsString(parameters, self.BDNAME, context)
        user = self.parameterAsString(parameters, self.USER, context)
        password = self.parameterAsString(parameters, self.PASSWORD, context)
        if method == 0:
            folder = self.parameterAsFile(parameters, self.FOLDER, context)
            refreshPPP = HandleRefreshFromPPP(folder, server_ip, port, bdname, user, password)
            refreshPPP.readPPP()
            self.OUTPUT = 'PPP'
            return {self.OUTPUT: ''}    
        if method == 1:
            csvfile = self.parameterAsFile(parameters, self.CSVFILE, context)
            refreshCSV = HandleRefreshFromCSV(server_ip, port, bdname, user, password, csvfile)
            refreshCSV.readCSV()
            self.OUTPUT = 'RTE'
            return {self.OUTPUT: ''}
        
        

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return '7.A- Atualizar banco com dados do PPP'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return None

    def shortHelpString(self):
        """
        Retruns a short helper string for the algorithm
        """
        return self.tr('''
        ATENÇÃO: Essa rotina deve ser utilizada caso o usuário deseje atualizar o banco de dados com informações do PPP. Caso deseje atualizar o banco de dados com informações do RTE deverá utilizar a  rotina "7.B- Atualizar banco com dados do RTE"
        
        Esta rotina atualiza o banco de dados com os dados do PPP. 
        Os parâmetros necessários para essa rotina são:
        - Pasta com a estrutura de pontos de controle (deve estar validada de pela ferramenta Data Validation)
        - Parâmetros de conexão do banco:
            -- IP da máquina (se trabalhando localmente utilizar localhost)
            -- Porta (geralmente 5432 para PostgreSQL)
            -- Nome do banco a ser atualizado 
            -- Usuário do PostgreSQL
            -- Senha do PostgreSQL''')

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RefreshFromPPP()
