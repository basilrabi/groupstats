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

import csv

from typing import Any, List, Optional, Tuple, Union
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QCoreApplication, QModelIndex, Qt
from qgis.PyQt.QtWidgets import (QApplication,
                                 QFileDialog,
                                 QMainWindow,
                                 QMessageBox)

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
        self.windowColumn = ColRowWindow(self)  # tm3
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
        # some calculating function has been selected, enabe calculate button.
        if ('geometry' in [a[0] for a in values] or
                'number' in [a[0] for a in values]) and \
                'calculation' in [a[0] for a in columns + rows + values]:
            self.ui.calculate.setEnabled(True)
        # If there is a text attribute in the value field and exactly one
        # function has been selected - counter
        elif 'text' in [a[0] for a in values] and \
                [a for a in columns + rows + values if a[0] == 'calculation']:
            self.ui.calculate.setEnabled(True)
        else:
            self.ui.calculate.setEnabled(False)

    def clearSelection(self) -> None:
        """
        Clears windows with selected rows, columns and values.

        wyczyscWybor
        """
        pass

    def copy(self) -> None:
        """
        Copy all data to clipboard.

        kopiowanie
        """
        text, success = self.download(formatText=True)
        if success:
            clip_board = QApplication.clipboard()
            clip_board.setText(text)

    def copySelected(self) -> None:
        """
        Copy selected data to clipboard.

        kopiowanieZaznaczonych
        """
        text, success = self.download(allData=False, formatText=True)
        if success:
            clip_board = QApplication.clipboard()
            clip_board.setText(text)

    def download(self,
                 allData: Optional[bool] = True,
                 formatText: Optional[bool] = False) -> Tuple[
                     Union[None, str, List[List[Any]]], bool]:
        """
        Download data from the results table.

        pobierzDaneZTabeli
        """
        if not self.ui.results.model():
            QMessageBox.information(
                None,
                QCoreApplication.translate('groupstats', 'Information'),
                QCoreApplication.translate('groupstats',
                                           'No data to save/copy.')
            )
            return None, False

        text = ''
        data = []
        nCol = self.windowResult.columnCount()
        nRow = self.windowResult.rowCount()
        rows = []
        columns = []

        if not allData:
            # If the 'only checked' option, download the indexes of the selected
            # fields?
            indices = self.ui.results.selectedIndexes()
            if not indices:
                QMessageBox.information(
                    None,
                    QCoreApplication.translate('groupstats', 'Information'),
                    QCoreApplication.translate('groupstats',
                                               'No data selected.')
                )
                return None, False
            for i in indices:
                columns.append(i.column())
                rows.append(i.row())

        # Copy the data from the table
        for i in range(nRow):
            if allData or i in rows or i < self.windowResult.offsetY:
                row = []
                for j in range(nCol):
                    if allData or j in columns or \
                            j < self.windowResult.offsetX:
                        row.append(str(
                            self.windowResult.createIndex(i, j).data()
                        ))
                data.append(row)

        if formatText:
            for m, i in enumerate(data):
                if m:
                    # If new row, add carriage return
                    text = text + chr(13)
                for n, j in enumerate(i):
                    if n:
                        # At every column, add horizontal tab
                        text = text + chr(9)
                    text = text + j
            return text, True

        return data, True

    def exportCSV(self) -> None:
        """
        Save all data to a csv file.

        eksportCSV
        """
        data, success = self.download()
        if success:
            self.saveDataToFile(data)

    def exportCSVSelected(self) -> None:
        """
        Save selected data to a csv file.

        eksportCSVZaznaczonych
        """
        data, success = self.download(allData=False)
        if success:
            self.saveDataToFile(data)

    def saveDataToFile(self, data: List[List[Any]]) -> None:
        """
        Write data to a  file.

        zapiszDaneWPliku
        """
        file_window = QFileDialog()
        file_window.setAcceptMode(1)
        file_window.setDefaultSuffix('csv')
        file_window.setNameFilters(['CSV Files (*.csv)', 'All Files (*)'])
        if file_window.exec_() == 0:
            return
        file_name = file_window.selectedFiles()[0]
        csv_file = open(file_name, 'wt')
        csv_writer = csv.writer(csv_file, delimiter=',')
        for i in data:
            csv_writer.writerow([x for x in i])
        csv_file.close()

    def showOnMap(self) -> None:
        """
        Show selected features on map canvas.

        pokazNaMapie
        """
        # Get index of seletected fields
        indices = self.ui.results.selectedIndexes()

        ids = []
        for i in indices:
            # Get indices of objects to show
            data = i.data(Qt.UserRole)
            if not data:
                # Reject rows with headings?
                data = ()
            for j in data:
                ids.append(j)

        if ids:
            # Highlight and zoom to selected features
            self.windowResult.layer.select(ids)
            self.iface.mapCanvas().zoomToSelected(self.windowResult.layer)
            if len(ids) == 1 and self.windowResult.layer.geometryType() == 0:
                # If selected feature is only a point, set a 1:1000 scale zoom.
                self.iface.mapCanvas().zoomScale(1000)

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
