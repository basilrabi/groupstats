# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Group Stats Dialog
                                 A QGIS plugin
 Summary statistics for vector layers data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-08-20
        git sha              : $Format:%H$
        copyright            : (C) 2012 by Rayo
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
import webbrowser

from typing import Any, List, Optional, Tuple, Union
from qgis.core import QgsProject, QgsVectorLayer
# from qgis.gui import QgsSearchQueryBuilder
from qgis.PyQt.QtCore import QCoreApplication, QModelIndex, QObject, Qt
from qgis.PyQt.QtWidgets import (QApplication,
                                 QFileDialog,
                                 QMainWindow,
                                 QMessageBox)

from .groupstats_classes import (Calculation,
                                 ColRowWindow,
                                 FieldWindow,
                                 ResultsModel,
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

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)
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

        self.ui.calculate.clicked.connect(self.showResult)
        self.ui.clear.clicked.connect(self.clearSelection)
        # self.ui.filterButton.clicked.connect(self.setFilter)
        self.ui.layer.currentIndexChanged.connect(self.refreshFields)

        self.windowField = FieldWindow(self)    # tm1
        self.windowRow = ColRowWindow(self)     # tm2
        self.windowColumn = ColRowWindow(self)  # tm3
        self.windowValue = ValueWindow(self)    # tm4
        self.windowResult = None                # tm5
        self.ui.fieldList.setModel(self.windowField)
        self.ui.rows.setModel(self.windowRow)
        self.ui.columns.setModel(self.windowColumn)
        self.ui.values.setModel(self.windowValue)
        self.windowRow.setOtherModels(self.windowColumn, self.windowValue)
        self.windowColumn.setOtherModels(self.windowRow, self.windowValue)
        self.windowValue.setOtherModels(self.windowRow, self.windowColumn)

        self.windowRow.rowsInserted.connect(self.enableCalculations)
        self.windowRow.rowsRemoved.connect(self.enableCalculations)
        self.windowColumn.rowsInserted.connect(self.enableCalculations)
        self.windowColumn.rowsRemoved.connect(self.enableCalculations)
        self.windowValue.rowsInserted.connect(self.enableCalculations)
        self.windowValue.rowsRemoved.connect(self.enableCalculations)

        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionCopySelected.triggered.connect(self.copySelected)
        self.ui.actionSaveCSV.triggered.connect(self.exportCSV)
        self.ui.actionSaveCSVSelected.triggered.connect(self.exportCSVSelected)
        self.ui.actionShowPanel.triggered.connect(self.showControlPanel)
        self.ui.actionShowSelected.triggered.connect(self.showOnMap)
        self.ui.actionTutorial.triggered.connect(self.showTutorial)

        self.ui.results.verticalHeader().sortIndicatorChanged \
            .connect(self.sortRow)

    def clearSelection(self) -> None:
        """
        Clears windows with selected rows, columns and values.

        wyczyscWybor
        """
        self.windowRow.removeRows(
            0, self.windowRow.rowCount(), QModelIndex())
        self.windowColumn.removeRows(
            0, self.windowColumn.rowCount(), QModelIndex())
        self.windowValue.removeRows(
            0, self.windowValue.rowCount(), QModelIndex())
        self.ui.filter.setPlainText('')

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
        if self.ui.results.model() is None:
            QMessageBox.information(
                None,
                QCoreApplication.translate('GroupStats', 'Information'),
                QCoreApplication.translate('GroupStats',
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
            # If the 'only checked' option, download the indexes of the
            # selected fields?
            indices = self.ui.results.selectedIndexes()
            if not indices:
                QMessageBox.information(
                    None,
                    QCoreApplication.translate('GroupStats', 'Information'),
                    QCoreApplication.translate('GroupStats',
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

    def enableCalculations(self) -> None:
        """
        Not sure what are three arguments for, may be to accept the signals.

        blokujObliczenia
        """
        columns = self.windowColumn.tab
        rows = self.windowRow.tab
        values = self.windowValue.tab

        # If there are numbers (attributes or geometry) in the value field and
        # some calculating function has been selected, enable calculate button.
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
                (QCoreApplication.translate('GroupStats', 'Length'), 1)]
        elif layer.geometryType() == 2:
            fields['geometry'] = [
                (QCoreApplication.translate('GroupStats', 'Perimeter'), 1),
                (QCoreApplication.translate('GroupStats', 'Area'), 2),
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

        self.windowField = FieldWindow(self)
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

    # def setFilter(self) -> None:
    #     """
    #     Set feature filter.

    #     ustawFiltr
    #     """
    #     # Get the selected layer
    #     index = self.ui.layer.currentIndex()
    #     layer_id = self.ui.layer.itemData(index)
    #     layer = QgsProject.instance().mapLayer(layer_id)

    #     # Get text from the window and display the query window
    #     text = self.ui.filter.toPlainText()
    #     query = QgsSearchQueryBuilder(layer)
    #     query.setSearchString(text)
    #     query.exec_()
    #     self.ui.filter.setPlainText(query.searchString())

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
        else:
            self.refreshFields(0)

        self.ui.layer.blockSignals(False)

    def showControlPanel(self) -> None:
        """
        Display control panel.

        pokazPanelSterowania
        """
        self.ui.controlPanel.setVisible(True)

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
            if data is None:
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

    def showResult(self):
        """
        Perform calculations and send them to display.

        pokazWynik
        """
        # Tuple[Tuple[str, str, int]]
        selected_rows = tuple(self.windowRow.tab)
        selected_columns = tuple(self.windowColumn.tab)
        selected_ValCalc = tuple(self.windowValue.tab)

        # Reading a field that has been selected for calculation.
        # Only one is allowed.
        # List[Tuple[str, str, int]]
        value = [x for x in selected_ValCalc if x[0] != 'calculation'][0]

        # Set the calculation function depending on the type of the selected
        # value.
        if value[0] == 'geometry':
            if value[2] == 1:
                fun = lambda feat: feat.geometry().length()
            elif value[2] == 2:
                fun = lambda feat: feat.geometry().area()
        elif value[0] == 'text':
            fun = lambda feat: None if not feat.attribute(value[1]) else \
                feat.attribute(value[1])
        elif value[0] == 'number':
            fun = lambda feat: None if not feat.attribute(value[1]) else \
                float(feat.attribute(value[1]))

        # Get selected layer
        index = self.ui.layer.currentIndex()
        layer_id = self.ui.layer.itemData(index)
        layer = QgsProject.instance().mapLayer(layer_id)

        selected_features_id = layer.selectedFeatureIds()
        only_selected = self.ui.onlySelected.isChecked()

        tmp_layer = QgsVectorLayer(layer.source(),
                                   layer.name(),
                                   layer.providerType())
        tmp_layer.setCrs(layer.crs())
        filter_str = self.ui.filter.toPlainText()
        layer_filter = layer.subsetString()
        if not layer_filter and filter_str:
            tmp_layer.setSubsetString(filter_str)
        elif layer_filter and filter_str:
            tmp_layer.setSubsetString('{} and {}'.format(layer_filter,
                                                         filter_str))

        provider = tmp_layer.dataProvider()
        features = provider.getFeatures()

        # Dictionary on results {((row) (column)): [[values], [indexes]} ??
        results = {}

        # Compute percent_factor for progress monitoring
        n_features = provider.featureCount()
        if n_features:
            percent_factor = 100 / n_features
        else:
            percent_factor = 100

        progress = 0
        count_null = 0

        for f in features:
            if not only_selected or \
                    (only_selected and f.id() in selected_features_id):
                key_col = []
                key_row = []
                key = ()

                for k in selected_columns:
                    if k[0] == 'geometry':
                        if k[2] == 1:
                            key_col.append(f.geometr().length())
                        elif k[2] == 2:
                            key_col.append(f.geometry().area())
                    elif k[0] in ['text', 'number']:
                        if f.attribute(k[1]) is None:
                            new_key_kol = ''
                        else:
                            new_key_kol = f.attribute(k[1])
                        key_col.append(new_key_kol)

                for k in selected_rows:
                    if k[0] == 'geometry':
                        if k[2] == 1:
                            key_row.append(f.geometry().length())
                        elif k[2] == 2:
                            key_row.append(f.geometry().area())
                    elif k[0] in ['text', 'number']:
                        if f.attribute(k[1]) is None:
                            new_key_row = ''
                        else:
                            new_key_row = f.attribute(k[1])
                        key_row.append(new_key_row)

                key = (tuple(key_row), tuple(key_col))

                value_to_calculate = fun(f)
                if value_to_calculate is not None or \
                        self.ui.useNULL.isChecked():
                    if value_to_calculate is None:
                        count_null += 1
                        if value[0] == 'number':
                            value_to_calculate = 0

                    # If the key exists then a new value is added to the list.
                    if key in results:
                        results[key][0].append(value_to_calculate)
                    # If the key does not exist then a new list is created.
                    else:
                        results[key] = [[value_to_calculate], []]

                    results[key][1].append(f.id())

                else:
                    count_null += 1

                # Display progress
                progress += percent_factor
                self.statusBar().showMessage(
                    QCoreApplication.translate(
                        'GroupStats', 'Calculate...'
                    ) + '{:.2f}'.format(progress)
                )
        self.statusBar().showMessage(
            self.statusBar().currentMessage() +
            ' |  ' +
            QCoreApplication.translate('GroupStats', 'generate view...'))

        # Find unique row and column keys (separately)
        keys = list(results.keys())
        row_set = set([])
        col_set = set([])
        for key in keys:
            # Add keys to the collection to reject repetition
            row_set.add(key[0])
            col_set.add(key[1])
        rows = list(row_set)
        cols = list(col_set)

        # Create dictionary for rows and columns for faster searching.
        row_dict = {}
        col_dict = {}
        for n, row in enumerate(rows):
            row_dict[row] = n
        for n, col in enumerate(cols):
            col_dict[col] = n

        calculations = [
            [x[2] for x in selected_ValCalc if x[0] == 'calculation'],
            [x[2] for x in selected_rows if x[0] == 'calculation'],
            [x[2] for x in selected_columns if x[0] == 'calculation'], ]

        # Take only a non-empty part of the list to calculate.
        if calculations[0]:
            calculation = calculations[0]
        elif calculations[1]:
            calculation = calculations[1]
        else:
            calculation = calculations[2]

        # Create empty array for data (rows x columns)
        data = []
        for x in range(max(len(rows), len(rows) * len(calculations[1]))):
            data.append(
                max(len(cols), len(cols) * len(calculations[2])) * [('', ())])

        # Calculate of values ​​for all keys
        for x in keys:
            # row and column number in the data table for the selected key
            krow = row_dict[x[0]]
            kcol = col_dict[x[1]]
            # Perform all calculations for all keys.
            for n, y in enumerate(calculation):
                # At the right side of the equation is a list of 2:
                # 1. Resulting computation
                # 2. A list of feature ID's used in the computation
                if calculations[1]:
                    data[krow * len(calculations[1]) + n][kcol] = [
                        self.calculation.list[y][1](results[x][0]),
                        results[x][1]]
                elif calculations[2]:
                    data[krow][kcol * len(calculations[2]) + n] = [
                        self.calculation.list[y][1](results[x][0]),
                        results[x][1]]
                else:
                    data[krow][kcol] = [
                        self.calculation.list[y][1](results[x][0]),
                        results[x][1]]

        attributes = {}
        for i in range(provider.fields().count()):
            attributes[i] = provider.fields().at(i)

        row_names = []
        for x in selected_rows:
            if x[0] == 'geometry':
                row_names.append(x[1])
            elif x[0] != 'calculation':
                row_names.append(attributes[x[2]].name())
        col_names = []
        for x in selected_columns:
            if x[0] == 'geometry':
                col_names.append(x[1])
            elif x[0] != 'calculation':
                col_names.append(attributes[x[2]].name())

        # Insert names of rows and columns with calculations.
        calc_col_name = ()
        calc_row_name = ()
        if calculations[1]:
            calc = [self.calculation.list[x][0] for x in calculations[1]]
            _rows = [w + (o,) for w in rows for o in calc]
            _cols = cols
            calc_row_name = (QCoreApplication.translate(
                'GroupStats', 'Function'),)
        elif calculations[2]:
            calc = [self.calculation.list[x][0] for x in calculations[2]]
            _cols = [w + (o,) for w in cols for o in calc]
            _rows = rows
            calc_col_name = (QCoreApplication.translate(
                'GroupStats', 'Function'),)
        else:
            _cols = cols
            _rows = rows

        if _rows and _rows[0]:
            _rows.insert(0, tuple(row_names) + calc_row_name)
        if _cols and _cols[0]:
            _cols.insert(0, tuple(col_names) + calc_col_name)

        if _rows and _cols:
            self.ui.results.setUpdatesEnabled(False)
            self.windowResult = ResultsModel(data, _rows, _cols, layer)
            self.ui.results.setModel(self.windowResult)

            for i in range(len(_cols[0]), 0, -1):
                self.ui.results.verticalHeader() \
                    .setSortIndicator(i - 1, Qt.AscendingOrder)
            for i in range(len(_rows[0]), 0, -1):
                self.ui.results.horizontalHeader() \
                    .setSortIndicator(i - 1, Qt.AscendingOrder)

            message = self.statusBar().currentMessage()
            percent_factor = 100 / self.windowResult.columnCount()
            progress = 0

            for i in range(self.windowResult.columnCount()):
                self.ui.results.resizeColumnToContents(i)
                progress += percent_factor
                self.statusBar() \
                    .showMessage(message + '{:.2f}'.format(progress))
            self.ui.results.setUpdatesEnabled(True)

            record = 'records'
            if count_null == 1:
                record = 'record'

            if self.ui.useNULL.isChecked() and count_null:
                null_text = QCoreApplication.translate(
                    'GroupStats', ' (used {} {} with null value in {} field)'
                    .format(count_null, record, value[1]))
            elif not self.ui.useNULL.isChecked() and count_null:
                null_text = QCoreApplication.translate(
                    'GroupStats',
                    ' (not used {} {} with null value in {} field)'
                    .format(count_null, record, value[1]))
            else:
                null_text = ''
            self.statusBar().showMessage(
                message +
                ' | ' +
                QCoreApplication.translate('GroupStats', 'done. ') +
                null_text, 20000)
        else:
            try:
                del self.windowResult
            except AttributeError:
                pass

            self.statusBar().showMessage(QCoreApplication.translate(
                'GroupStats', 'No data found.'), 10000)

    def showTutorial(self) -> None:
        """
        Open tutorial link.

        pokazTutorial
        """
        url = 'http://underdark.wordpress.com/2013/02/02/group-stats-tutorial/'
        webbrowser.open_new_tab(url)

    def sortRow(self, row: int, descending: bool) -> None:
        """
        sortRows
        """
        self.ui.results.model().sortRow(row, descending)
