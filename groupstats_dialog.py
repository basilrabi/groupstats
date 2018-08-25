# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GroupStatsDialog
                                 A QGIS plugin
 Summary statistics for vector layers data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-08-20
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Basil Eric Rabi
        email                : ericbasil.rabi@gmail.com
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

from typing import List, Tuple
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QCoreApplication, QModelIndex
from qgis.PyQt.QtWidgets import QMainWindow

from .groupstats_classes import (Calculation,
                                 ColRowWindow,
                                 FieldWindow,
                                 ResultsWindow,
                                 ValueWindow)
from .groupstats_ui import Ui_GroupStatsDialog

mime_types = {
    'list': 'application/x-groupstats-fieldList',
    'colrow': 'application/x-groupstats-fieldColumnRow',
    'value': 'application/x-groupstats-fieldValue'
}


class GroupStatsDialog(QMainWindow):
    """
    Plugin dialog.
    """

    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_GroupStatsDialog()
        self.ui.setupUi(self)
        self.ui.results = ResultsWindow(self.ui.centralwidget)
        self.ui.horizontalLayout.addWidget(self.ui.results)
        self.calculation = Calculation(self)
        self.ui.fieldList.setAcceptDrops(True)
        self.ui.fieldList.setModelColumn(2)
        self.ui.rows.setAcceptDrops(True)
        self.ui.columns.setAcceptDrops(True)
        self.ui.values.setAcceptDrops(True)

        self.windowField = FieldWindow(self)   # tm1
        self.windowRow = ColRowWindow(self)    # tm2
        self.windowColumn = ColRowWindow(self) # tm3
        self.windowValue = ValueWindow(self)   # tm4
        self.ui.fieldList.setModel(self.windowField)
        self.ui.rows.setModel(self.windowRow)
        self.ui.columns.setModel(self.windowColumn)
        self.ui.values.setModel(self.windowValue)
        self.windowRow.setOtherModels(self.windowColumn, self.windowValue)
        self.windowColumn.setOtherModels(self.windowRow, self.windowValue)
        self.windowValue.setOtherModels(self.windowRow, self.windowColumn)

    def blockCalculations(self) -> None:
        """
        blokujObliczenia
        """
        columns = self.windowColumn.data
        rows = self.windowRow.data
        values = self.windowValue.data

        # If there are numbers (attributes or geometry) in the value field and
        # some calculating function has been selected
        pass

    def clearSelection(self) -> None:
        """
        Clears windows with selected rows, columns and values.

        wyczyscWybor
        """
        pass

    def refreshFields(self, index: int) -> None:
        """
        Run after selecting a layer from the list. Sets a new list of fields to
        choose from and deletes windows with already selected fields.

        wyborWarstwy
        """
        # Get ID of the selected layer
        layer_id = self.ui.layer.itemData(index)
        layer = QgsProject.instance().mapLayer(layer_id)
        provider = layer.dataProvider()
        attributes = provider.fields()

        if not isinstance(attributes, dict):
            temp_attributes = {}
            for i in range(attributes.count()):
                temp_attributes[i] = attributes.at(i)
            attributes = temp_attributes

        fields = {}

        if not layer.geometryType():
            # point
            fields['geometry'] = []
        elif layer.geometryType() == 1:
            # line
            fields['geometry'] = [
                (QCoreApplication.translate('groupstats', 'Length'), 1),
            ]
        elif layer.geometryType() == 2:
            fields['geometry'] = [
                (QCoreApplication.translate('groupstats', 'Perimeter'), 1),
                (QCoreApplication.translate('groupstats', 'Area'), 2),
            ]

        # Separate number fields and text fields of the layer
        fields['number'] = []
        fields['text'] = []
        # pylint: disable=W0622
        for id, attribute in attributes.items():
            if attribute.isNumeric():
                fields['number'].append((attribute.name(), id))
            else:
                fields['text'].append((attribute.name(), id))

        fields['calculation'] = []
        calculations = self.calculation.list
        for id, text in calculations.items():
            fields['calculation'].append((text[0], id))

        del self.windowField
        # Insert field lists

        self.windowField = FieldWindow()
        self.ui.fieldList.setModel(self.windowField)
        keys = ['calculation', 'geometry']
        for i in keys:
            j = fields[i]
            j.sort(key=lambda x: x[0].lower())
            rows = []
            for k, l in j:
                rows.append((i, k, l))
            self.windowField.insertRows(0, len(rows), QModelIndex(), rows)

        keys = ['number', 'text']
        rows = []
        for i in keys:
            j = fields[i]
            for k, l in j:
                rows.append((i, k, l))
        rows.sort(key=lambda x: x[1].lower())
        self.windowField.insertRows(0, len(rows), QModelIndex(), rows)
        self.clearSelection()

    def showResult(self):
        """
        Perform calculations and send them to display.

        pokazWynik
        """
        # selected_rows
        # selected_columns
        # selected_value_comp
        pass

    def setLayers(self, layers: List[Tuple[str, str]]) -> None:
        """
        Adds the available qgis layers to the window.

        ustawWarstwy
        """
        index = self.ui.layer.currentIndex()

        if index != -1:
            # id of previously selected layer
            layer_id = self.ui.layer.itemData(index)

        # fill comboBox with a new list of layers
        self.ui.layer.blockSignals(True)
        self.ui.layer.clear()
        layers.sort(key=lambda x: x[0].lower())
        for i in layers:
            self.ui.layer.addItem(i[0], i[1])

        if index != -1:
            index2 = self.ui.layer.findData(layer_id)
            if index2 != -1:
                self.ui.layer.setCurrentIndex(index2)
            else:
                self.refreshFields(0)
