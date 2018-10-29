# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Group Stats Classes
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

from math import sqrt
from typing import List, Optional, Tuple, Union
from qgis.core import QgsVectorLayer
from qgis.PyQt.QtCore import (QAbstractListModel,
                              QAbstractTableModel,
                              QByteArray,
                              QCoreApplication,
                              QDataStream,
                              QEvent,
                              QIODevice,
                              QItemSelectionModel,
                              QMimeData,
                              QModelIndex,
                              QObject,
                              Qt)
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QIcon
from qgis.PyQt.QtWidgets import QTableView, QWidget

mime_types = {
    'list': 'application/x-groupstats-fieldList',
    'colrow': 'application/x-groupstats-fieldColumnRow',
    'value': 'application/x-groupstats-fieldValue'
}


class Calculation(QObject):
    """
    A class containing functions that perform statistical computations.
    """

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        # List of ID, name and calculation function
        self.list = {
            0: (QCoreApplication.translate(
                'Calculation', 'count'), self.count),
            1: (QCoreApplication.translate(
                'Calculation', 'sum'), self.sum),
            2: (QCoreApplication.translate(
                'Calculation', 'mean'), self.mean),
            3: (QCoreApplication.translate(
                'Calculation', 'variance'), self.variance),
            4: (QCoreApplication.translate(
                'Calculation', 'standard deviation'), self.standard_deviation),
            5: (QCoreApplication.translate(
                'Calculation', 'median'), self.median),
            6: (QCoreApplication.translate(
                'Calculation', 'minimum'), self.minimum),
            7: (QCoreApplication.translate(
                'Calculation', 'maximum'), self.maximum),
            8: (QCoreApplication.translate(
                'Calculation', 'unique'), self.unique)
        }
        self.listText = (0, 8)
        self.textName = ''
        for i in self.listText:
            self.textName = self.textName + self.list[i][0] + ', '
        self.textName = self.textName[:-2]

    def count(self, result: list) -> int:
        """
        Number of matching rows.
        """
        return len(result)

    def maximum(self, result: list) -> Union[float, int]:
        """
        Maximum value in the result.
        """
        return max(result)

    def mean(self, result: list) -> float:
        """
        Average of the given set of results.
        """
        return self.sum(result) / self.count(result)

    def median(self, result: list) -> Union[float, int]:
        """
        Median of values.
        """
        result.sort()
        count = self.count(result)
        if count == 1:
            median = result[0]
        else:
            position = count / 2
            if count % 2 == 0:
                median = (result[position] + result[position - 1]) / 2
            else:
                median = result[count]

        return median

    def minimum(self, result: list) -> Union[float, int]:
        """
        Minimum value in the result.
        """
        return min(result)

    def standard_deviation(self, result: list) -> float:
        """
        Population's standard deviation.
        """
        return sqrt(self.variance(result))

    def sum(self, result: list) -> Union[float, int]:
        """
        Summation of results.
        """
        return sum(result)

    def unique(self, result: list) -> int:
        """
        Number of unqie values.
        """
        return len(set(result))

    def variance(self, result: list) -> Union[float, int]:
        """
        Population's variance.
        """
        variance = 0
        for x in result:
            variance = variance + (x - self.mean(result))**2
        return variance / self.count(result)


class ListModel(QAbstractListModel):
    """
    A window with attribute list.
    Data stored in the list: [(attribute type, name, id), ...]
    """

    def __init__(
            self, main_window: QObject,
            parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.tab = []
        self.main_window = main_window
        self.calculation = Calculation(self)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Union[
            str, QIcon, None]:
        """
        Returns data from the table cell?
        """
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return None

        row = index.row()

        if role == Qt.DisplayRole:
            return self.tab[row][1]
        elif role == Qt.DecorationRole:
            if self.tab[row][0] == 'geometry':
                icon = QIcon(':/plugins/groupstats/icons/geom.png')
            elif self.tab[row][0] == 'calculation':
                icon = QIcon(':/plugins/groupstats/icons/calc.png')
            elif self.tab[row][0] == 'text':
                icon = QIcon(':/plugins/groupstats/icons/alpha.png')
            else:
                icon = QIcon(':/plugins/groupstats/icons/digits.png')
            return icon

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Item flags.
        """
        flags = super().flags(index)
        if index.isValid():
            return flags | \
                Qt.ItemIsDragEnabled | \
                Qt.ItemIsEnabled | \
                Qt.ItemIsSelectable
        return Qt.ItemIsDropEnabled

    def insertRows(
            self, row: int, number: int, index: QModelIndex,
            data: List[Tuple[str, str, int]]) -> bool:
        """
        Insert field list.
        """
        self.beginInsertRows(index, row, row + number - 1)
        for n in range(number):
            self.tab.insert(row + n, data[n])
        self.endInsertRows()
        return True

    def mimeData(
            self, indices: Union[QModelIndex, List[QModelIndex]],
            mimeType: str = mime_types['list']) -> QMimeData:
        """
        MIME data.
        """
        mimeData = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)

        for index in indices:
            row = index.row()
            stream.writeBytes(self.tab[row][0].encode('utf-8'))
            stream.writeBytes(self.tab[row][1].encode('utf-8'))
            stream.writeInt16(self.tab[row][2])

        mimeData.setData(mimeType, data)

        return mimeData

    def mimeTypes(self) -> List[str]:
        """
        mimeTypes
        """
        return [mime_types['list'], mime_types['colrow'], mime_types['value']]

    def removeRows(self, row: int, number: int, index: QModelIndex) -> bool:
        """
        Remove rows from self.tab.
        """
        self.beginRemoveRows(index, row, row + number - 1)
        del self.tab[row:(row + number)]
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QModelIndex()) -> int:  # pylint: disable=W0613
        """
        rowCount
        """
        return len(self.tab)

    def supportedDragActions(self) -> Qt.DropAction:
        """
        Drag actions.
        """
        return Qt.MoveAction

    def supportedDropActions(self) -> Qt.DropAction:
        """
        Drop actions
        """
        return Qt.MoveAction


class FieldWindow(ListModel):
    """
    Model for a window with a list of available fields.
    """

    def dropMimeData(
            self, data: QMimeData, action: Qt.DropAction, row: int,
            column: int, parent: QModelIndex) -> bool:
        """
        Not sure what is this about but copied still.
        """
        # pylint: disable=W0613
        return True

    def removeRows(self, row: int, number: int, index: QModelIndex) -> bool:
        """
        Not sure what is this about but copied still.
        """
        return True


class ValueWindow(ListModel):
    """
    A model for a window with values ​​to be calculated.
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.modelRows = None
        self.modelColumns = None

    def dropMimeData(
            self, mimeData: QMimeData, action: Qt.DropAction, row: int,
            column: int, index: QModelIndex) -> bool:
        """
        Drop MIME data.
        """
        # pylint: disable=W0613
        if mimeData.hasFormat(mime_types['list']):
            mime_type = mime_types['list']
        elif mimeData.hasFormat(mime_types['colrow']):
            mime_type = mime_types['colrow']
        elif mimeData.hasFormat(mime_types['value']):
            mime_type = mime_types['value']
        else:
            return False

        data = mimeData.data(mime_type)
        stream = QDataStream(data, QIODevice.ReadOnly)
        data_set = []
        while not stream.atEnd():
            stream_type = stream.readBytes().decode('utf-8')
            name = stream.readBytes().decode('utf-8')
            id = stream.readInt16()  # pylint: disable=W0622
            field = (stream_type, name, id)
            dataRC = self.modelRows + self.modelColumns
            all_data = dataRC + self.tab

            if len(self.tab) >= 2:
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'Value field may contain a maximum of two entries.'
                    ), 15000)
                return False

            elif stream_type == 'calculation' and \
                stream_type in [x[0] for x in all_data] and \
                    mime_type == mime_types['list']:
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'Function can be droped in only one area.'
                    ), 15000)
                return False

            elif len(self.tab) == 1 and stream_type != 'calculation' and \
                    self.tab[0][0] != 'calculation':
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'One of the items in the Value field must be a '
                        'function.'
                    ), 15000)
                return False

            elif len(self.tab) == 1 and \
                    ((stream_type == 'text' and
                      self.tab[0][2] not in self.calculation.listText) or
                     (id not in self.calculation.listText and
                      self.tab[0][0] == 'text')):
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'For the text value, function can only be one of '
                        '{}.'.format(self.calculation.textName)
                    ), 15000)
                return False

            elif stream_type == 'text' and \
                    [x for x in dataRC if x[0] == 'calculation' and
                     x[2] not in self.calculation.listText]:
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'For the text value function can only be one of '
                        '{}.'.format(self.calculation.textName)
                    ), 15000)
                return False

            data_set.append(field)

        self.insertRows(row, len(data_set), index, data_set)
        return True

    def mimeData(
            self, indices: Union[QModelIndex, List[QModelIndex]]) -> QMimeData:
        """
        MIME data
        """
        # pylint: disable=W0221
        return super().mimeData(indices, mime_types['value'])

    def setOtherModels(
            self,
            modelRows: 'ColRowWindow',
            modelColumns: 'ColRowWindow') -> None:
        """
        Set data for other models.
        """
        self.modelRows = modelRows.tab
        self.modelColumns = modelColumns.tab


class ColRowWindow(ListModel):
    """
    Model for windows with field lists for rows and columns.
    """

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.modelRC = None
        self.modelValue = None

    def dropMimeData(
            self, mimeData: QMimeData, action: Qt.DropAction, row: int,
            column: int, index: QModelIndex) -> bool:
        """
        Drop MIME data.
        """
        # pylint: disable=W0613
        if mimeData.hasFormat(mime_types['list']):
            mime_type = mime_types['list']
        elif mimeData.hasFormat(mime_types['colrow']):
            mime_type = mime_types['colrow']
        elif mimeData.hasFormat(mime_types['value']):
            mime_type = mime_types['value']
        else:
            return False

        data = mimeData.data(mime_type)
        stream = QDataStream(data, QIODevice.ReadOnly)
        data_set = []

        while not stream.atEnd():
            stream_type = stream.readBytes().decode('utf-8')
            name = stream.readBytes().decode('utf-8')
            id = stream.readInt16()  # pylint: disable=W0622
            field = (stream_type, name, id)
            modelRCV = self.modelRC + self.modelValue

            if stream_type == 'calculation' and \
                stream_type in [x[0] for x in modelRCV] and \
                    mime_type == mime_types['list']:
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'Function can be droped in only one area.'
                    ), 15000)
                return False

            elif (field in self.modelRC or field in self.tab) and \
                    mime_type in [mime_types['list'], mime_types['value']]:
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'This field has already been droped.'
                    ), 15000)
                return False

            elif stream_type == 'calculation' and \
                id not in self.calculation.listText and \
                    'text' in [x[0] for x in self.modelValue]:
                self.main_window.statusBar() \
                    .showMessage(QCoreApplication.translate(
                        'GroupStats',
                        'For the text value, function can only be one of '
                        '{}.'.format(self.calculation.textName)
                    ), 15000)
                return False

            data_set.append(field)

        self.insertRows(row, len(data_set), index, data_set)
        return True

    def mimeData(
            self, indices: Union[QModelIndex, List[QModelIndex]]) -> QMimeData:
        """
        MIME data.
        """
        # pylint: disable=W0221
        return super().mimeData(indices, mime_types['colrow'])

    def setData(self, index: int, value: list) -> None:
        """
        Sets data.
        """
        self.tab.insert(index, value)

    def setOtherModels(self, modelA: 'ColRowWindow',
                       modelB: ValueWindow) -> None:
        """
        Set data for other models.
        """
        self.modelRC = modelA.tab
        self.modelValue = modelB.tab


class ResultsModel(QAbstractTableModel):
    """
    Model for the window with the results of calculations.
    """

    def __init__(
            self,
            data: List[Tuple],
            rows: List[Tuple],
            columns: List[Tuple],
            layer: QgsVectorLayer,
            parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.tab = data
        self.rows = rows
        self.columns = columns
        self.layer = layer

        # Shift coordinates so the data starts at (0, 0)
        self.offsetX = max(1, len(rows[0]))
        self.offsetY = max(1, len(columns[0]))

        # Offset column to make room for row names
        if rows[0] and columns[0]:
            self.offsetY += 1

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Count the number of columns?
        """
        # pylint: disable=W0613
        if self.rows[0] and self.columns[0]:
            l = len(self.columns) + len(self.rows[0]) - 1
        elif self.rows[0] and not self.columns[0]:
            l = len(self.rows[0]) + 1
        elif not self.rows[0] and self.columns[0]:
            l = len(self.columns)
        else:
            l = 2

        return l

    # TODO: type hints for the following cases: Qt.DisplayRole and Qt.UserRole
    def data(self, index: QModelIndex,
             role: Qt.ItemDataRole = Qt.DisplayRole) -> Union[
                 None, QBrush, QFont, Qt.AlignmentFlag, str]:
        """
        Returns data from the table cell?
        """
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return None

        row = index.row() - self.offsetY
        column = index.column() - self.offsetX

        if role == Qt.DisplayRole:
            # Table cell data
            if row >= 0 and column >= 0:
                return self.tab[row][column][0]
            # Row descriptions?
            elif column < 0 and row >= 0 and self.rows[0]:
                return self.rows[row + 1][column]
            # Row title field?
            elif row == -1 and column < 0 and self.rows[0]:
                return self.rows[0][column]
            # Column description and names?
            elif column >= -1 and row < 0 and self.columns[0]:
                if self.rows[0]:
                    # Break line?
                    if row == -1:
                        return ''
                    # Descriptions and column names if there is a break line?
                    return self.columns[column + 1][row + 1]
                # Column descriptions and names if there is no break line?
                return self.columns[column + 1][row]

        elif role == Qt.UserRole:
            if row >= 0 and column >= 0:
                return self.tab[row][column][1]

        elif role == Qt.UserRole + 1:
            if row < 0 and column >= 0:
                return 'column'
            elif row >= 0 and column < 0:
                return 'row'
            elif row >= 0 and column >= 0:
                return 'data'

        # Cell filling
        elif role == Qt.BackgroundRole:
            if row < 0 or column < 0:
                # Gray for cells with descriptions and names
                color = QColor(245, 235, 235)
                brush = QBrush(color)
                return brush

        elif role == Qt.TextAlignmentRole:
            if column < 0 and row < -1 and self.rows:
                return Qt.AlignRight | Qt.AlignVCenter
            elif column >= 0 and row < 0:
                return Qt.AlignHCenter | Qt.AlignVCenter
            elif column >= 0 and row >= 0:
                return Qt.AlignRight | Qt.AlignVCenter

        elif role == Qt.FontRole:
            if row < 0 and column < 0:
                font = QFont()
                font.setBold(True)
                return font

        return None

    def rowCount(self, parent=QModelIndex()) -> int:  # pylint: disable=W0613
        """
        Row count
        """
        return max(2, len(self.rows) + len(self.columns[0]))

    def sort(self, column: int, descending: bool = False) -> None:
        """
        Sorts the table according to the selected column.
        """
        if len(self.rows) == 1:
            return

        # A temporary list for a sorted column
        tmp = []

        # If 1 column?
        # Select data for sorting
        if column >= self.offsetX:
            # n : n-th row
            # d : data in row
            for n, d in enumerate(self.tab):
                tmp.append((n, d[column - self.offsetX][0]))
        else:
            # Sort row names
            for n, d in enumerate(self.rows[1:]):
                # Change numbers in characters to float.
                # This is to correctly sort numbers.
                parsed = False
                if not isinstance(d[column], float):
                    try:
                        number = float(d[column])
                    except ValueError:
                        pass
                    else:
                        parsed = True

                if parsed:
                    tmp.append((n, number))
                else:
                    tmp.append((n, d[column]))

        # Sort ascending
        try:
            tmp.sort(key=lambda x: x[1])
        except TypeError:
            print('Cannot sort column with empty cell.')
            return
        if descending:
            # Sort descending
            tmp.reverse()

        # Temporarily store data
        data2 = tuple(self.tab)
        # Temporarily store row data
        rows2 = tuple(self.rows)

        self.tab = []
        self.rows = []
        # Add row names only
        self.rows.append(rows2[0])

        # Arrange all data and row descriptions using the sorted list
        for i in tmp:
            self.tab.append(data2[i[0]])
            self.rows.append(rows2[i[0] + 1])

        # Data change signal
        top_left = self.createIndex(0, 0)
        bottom_right = self.createIndex(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)

    def sortRow(self, row: int, descending: bool = False) -> None:
        """
        Sorts the table according to the selected row.
        """
        if len(self.columns) == 1:
            return

        # A temporary list for a sorted row
        tmp = []

        # Select data for sorting
        if row >= self.offsetY:
            # n : n-th column
            # d : data in row
            for n, d in enumerate(self.tab[row - self.offsetY]):
                tmp.append((n, d[0]))
        else:
            # Sort column names
            for n, d in enumerate(self.columns[1:]):
                # Change numbers in characters to float.
                # This is to correctly sort numbers.
                parsed = False
                if not isinstance(d[row], float):
                    try:
                        number = float(d[row])
                    except ValueError:
                        pass
                    else:
                        parsed = True

                if parsed:
                    tmp.append((n, number))
                else:
                    tmp.append((n, d[row]))

        # Sort ascending
        try:
            tmp.sort(key=lambda x: x[1])
        except TypeError:
            print('Cannot sort row with empty cell.')
            return
        if descending:
            # Sort descending
            tmp.reverse()

        # Temporarily store data
        data2 = tuple(self.tab)
        # Temporarily store column data
        columns2 = tuple(self.columns)

        self.tab = []
        self.columns = []
        # Add column names only
        self.columns.append(columns2[0])

        # Arrange all data using the sorted list
        for j in data2:
            row = []
            for i in tmp:
                row.append(j[i[0]])
            self.tab.append(tuple(row))

        # Arrange column descriptuins using the sorted list
        for i in tmp:
            self.columns.append(columns2[i[0] + 1])

        # Data change signal
        top_left = self.createIndex(0, 0)
        bottom_right = self.createIndex(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)


class ResultsWindow(QTableView):
    """
    Window with calculation results.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setSortingEnabled(True)
        self.setObjectName('results')
        self.verticalHeader().setSortIndicatorShown(True)
        self.clicked.connect(self.checkAll)

    def checkAll(self, index: QModelIndex) -> None:
        """
        Select or deselect all data after clicking on the corner of the table.
        """
        selected_cell_type = self.model().data(index, Qt.UserRole + 1)

        # Check if the corner is celected
        if selected_cell_type not in ['data', 'row', 'column']:
            # If the corner is selected, mark all data
            if self.selectionModel().isSelected(index):
                self.selectAll()
            else:
                self.clearSelection()

    def selectionCommand(
            self, index: QModelIndex,
            event: Optional[QEvent] = None
    ) -> QItemSelectionModel.SelectionFlag:
        """
        Adds selection of entire rows and columns when the table header is
        selected.
        """
        # http://doc.qt.io/qt-5/qabstractitemview.html#selectionCommand
        # http://doc.qt.io/qt-5/qitemselectionmodel.html#SelectionFlag-enum
        flag = super().selectionCommand(index, event)
        selected_cell_type = self.model().data(index, Qt.UserRole + 1)

        if selected_cell_type == 'row':
            return flag | QItemSelectionModel.Rows
        elif selected_cell_type == 'column':
            return flag | QItemSelectionModel.Columns
        return flag
