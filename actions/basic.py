"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
import os
import sys
from datetime import date

from PyQt4.QtGui import QIntValidator
from PyQt4.QtGui import QItemSelectionModel

from parent import ParentAction
from PyQt4.QtSql import QSqlTableModel
from PyQt4.QtGui import QAbstractItemView, QTableView, QLineEdit,QComboBox

from ..ui.tree_manage import TreeManage
from ..ui.multirow_selector import Multirow_selector
import utils

from functools import partial

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(plugin_path)


class Basic(ParentAction):
    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'basic' """
        self.minor_version = "3.0"
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)
        self.selected_year = None
        self.plan_year = None

    def set_tree_manage(self, tree_manage):
        self.tree_manage = tree_manage

    def set_project_type(self, project_type):
        self.project_type = project_type

    def main_tree_manage(self):
        """ Button 01: Tree selector """

        dlg_tree_manage = TreeManage()
        utils.setDialog(dlg_tree_manage)
        dlg_tree_manage.setFixedSize(300, 170)

        self.load_settings(dlg_tree_manage)

        validator = QIntValidator(1, 9999999)
        dlg_tree_manage.txt_year.setValidator(validator)
        table_name = 'planning'
        dlg_tree_manage.rejected.connect(partial(self.close_dialog, dlg_tree_manage))
        dlg_tree_manage.btn_cancel.pressed.connect(partial(self.close_dialog, dlg_tree_manage))
        dlg_tree_manage.btn_accept.pressed.connect(partial(self.get_year, dlg_tree_manage, table_name))
        self.populate_cmb_years(table_name, dlg_tree_manage.cbx_years)

        #TODO borrar estas tres lineas
        utils.setWidgetText(dlg_tree_manage.txt_year, '2020')
        utils.setChecked(dlg_tree_manage.chk_year, True)
        utils.set_combo_itemData(dlg_tree_manage.cbx_years, '2020', 1)

        dlg_tree_manage.exec_()

    def populate_cmb_years(self, table_name, combo):
        # """
        # sql = ("SELECT current_database()")
        # rows = self.controller.get_rows(sql)
        # """
        sql = ("SELECT DISTINCT(plan_year)::text, plan_year::text FROM "+self.schema_name+"."+table_name +""
               " WHERE plan_year::text != ''")
        self.controller.log_info(str(sql))
        rows = self.controller.get_rows(sql)
        utils.set_item_data(combo, rows, 1)


    def get_year(self, dialog, table_name):
        update = False
        self.selected_year = None

        if dialog.txt_year.text() != '':
            self.plan_year = utils.getWidgetText(dialog.txt_year)
            sql = ("SELECT DISTINCT(plan_year) FROM "+self.schema_name+"."+table_name + ""
                   " WHERE plan_year ='"+utils.getWidgetText(dialog.txt_year)+"'")
            row = self.controller.get_row(sql)
            if row:
                update = True

            if utils.isChecked(dialog.chk_year):
                self.selected_year = utils.get_item_data(dialog.cbx_years, 0)
            else:
                self.selected_year = self.plan_year
            self.close_dialog(dialog)
            self.tree_selector(update)

        else:
            message = "Any recuperat es obligatori"
            self.controller.show_warning(message)
            return None


    def tree_selector(self, update = False, recover=False):

        dlg_selector = Multirow_selector()
        utils.setDialog(dlg_selector)
        self.load_settings(dlg_selector)

        dlg_selector.setWindowTitle("Tree selector")

        tableleft = 'v_plan_mu'
        tableright = 'planning'
        id_table_left = 'mu_id'
        id_table_right = 'mu_id'

        dlg_selector.selected_rows.setSelectionBehavior(QAbstractItemView.SelectRows)
        dlg_selector.all_rows.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Button selec
        dlg_selector.btn_select.pressed.connect(partial(self.rows_selector, dlg_selector, id_table_left, tableright, id_table_right, tableleft))
        dlg_selector.all_rows.doubleClicked.connect(partial(self.rows_selector, dlg_selector, id_table_left, tableright, id_table_right, tableleft))

        # Button unselect
        dlg_selector.btn_unselect.pressed.connect(partial(self.rows_unselector, dlg_selector, tableright, id_table_right, tableleft))
        dlg_selector.selected_rows.doubleClicked.connect(partial(self.rows_unselector, dlg_selector, tableright, id_table_right, tableleft))
        # Populate QTableView
        self.fill_table(dlg_selector, tableright, tableleft)
        self.fill_main_table(dlg_selector, tableleft)

        # Filter field
        dlg_selector.txt_search.textChanged.connect(partial(self.fill_main_table, dlg_selector, tableleft, set_edit_triggers=QTableView.NoEditTriggers))
        dlg_selector.txt_selected_filter.textChanged.connect(partial(self.fill_table, dlg_selector, tableright, tableleft, set_edit_triggers=QTableView.NoEditTriggers))



        dlg_selector.btn_close.pressed.connect(partial(self.close_dialog, dlg_selector))
        dlg_selector.rejected.connect(partial(self.close_dialog, dlg_selector))

        dlg_selector.exec_()



    def fill_main_table(self, dialog, table_name,  set_edit_triggers=QTableView.NoEditTriggers):
        """ Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """
        # Set model
        model = QSqlTableModel()
        model.setTable(self.schema_name + "." + table_name)
        model.setEditStrategy(QSqlTableModel.OnFieldChange)
        model.setSort(0, 0)
        model.select()

        dialog.all_rows.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())

        # Get all ids from Qtable selected_rows
        id_all_selected_rows = self.select_all_rows(dialog.selected_rows, 'mu_id')

        # Convert id_all_selected_rows to string
        ids = "0, "
        for x in range(0, len(id_all_selected_rows)):
            ids += str(id_all_selected_rows[x]) + (", ")
        ids = ids[:-2] + ""

        # Attach model to table view
        expr = " mu_name ILIKE '%" + dialog.txt_search.text() + "%'"
        expr += " AND mu_id NOT IN ("+ids+")"
        dialog.all_rows.setModel(model)
        dialog.all_rows.model().setFilter(expr)


    def fill_table(self, dialog, tableright, tableleft, set_edit_triggers=QTableView.NoEditTriggers):
        """ Set a model with selected filter.
        Attach that model to selected table
        @setEditStrategy:
            0: OnFieldChange
            1: OnRowChange
            2: OnManualSubmit
        """

        # Set model
        model = QSqlTableModel()
        model.setTable(self.schema_name + "." + tableright)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setSort(0, 0)
        model.select()

        dialog.selected_rows.setEditTriggers(set_edit_triggers)
        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())
        # Attach model to table view

        expr = " mu_id::text ILIKE '%" + dialog.txt_selected_filter.text() + "%'"

        if self.selected_year is not None:
            expr += " AND plan_year ='" + str(self.selected_year) + "'"
        dialog.selected_rows.setModel(model)
        dialog.selected_rows.model().setFilter(expr)

        # Set year to plan to all rows in list
        for x in range(0, model.rowCount()):
            index = dialog.selected_rows.model().index(x,2)
            model.setData(index, self.plan_year)

        sql = ("SELECT * FROM " + self.schema_name+"."+tableright + " "
               " WHERE plan_year = "+self.selected_year+" order by id")
        rows = self.controller.get_rows(sql)

        for x in range(len(rows)):
            combo = QComboBox()
            sql = "SELECT DISTINCT(work_id) FROM " + self.schema_name+"."+tableleft + " ORDER BY work_id"
            row = self.controller.get_rows(sql)

            utils.fillComboBox(combo, row, False)
            row = rows[x]
            priority = row[7]

            utils.setSelectedItem(combo, str(priority))
            i = dialog.selected_rows.model().index(x, 7)

            dialog.selected_rows.setIndexWidget(i, combo)
            combo.setStyleSheet("background:#E6E6E6")
            combo.currentIndexChanged.connect(partial(self.update_combobox_values, dialog.selected_rows, combo, x))


    def update_combobox_values(self, qtable, combo, x):
        """ Insert combobox.currentText into widget (QTableView) """
        index = qtable.model().index(x, 7)
        qtable.model().setData(index, combo.currentText())

    def rows_selector(self, dialog, id_table_left, tableright, id_table_right, tableleft):
        """ Copy the selected lines in the @qtable_all_rows and in the @table table """
        left_selected_list = dialog.all_rows.selectionModel().selectedRows()
        if len(left_selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message)
            return
        # Get all selected ids
        field_list = []
        for i in range(0, len(left_selected_list)):
            row = left_selected_list[i].row()
            id_ = dialog.all_rows.model().record(row).value(id_table_left)
            field_list.append(id_)

        # Select all rows and get all id
        self.select_all_rows(dialog.selected_rows, id_table_right)

        for i in range(0, len(left_selected_list)):
            self.controller.log_info(str(left_selected_list[i]))
            row = left_selected_list[i].row()
            values = ""
            if dialog.all_rows.model().record(row).value(id_table_left) != None:
                values += "'" + str(dialog.all_rows.model().record(row).value(id_table_left)) + "', "
            else:
                values += 'null, '
            if dialog.all_rows.model().record(row).value('work_id') != None:
                values += "'" + str(dialog.all_rows.model().record(row).value('work_id')) + "', "
            else:
                values += 'null, '
            values += "'"+self.plan_year+"', "
            values = values[:len(values) - 2]

            # Check if mul_id and year_ already exists in planning
            sql = ("SELECT " + id_table_right + ""
                   " FROM " + self.schema_name + "." + tableright + ""
                   " WHERE " + id_table_right + " = '" + str(field_list[i]) + "'"
                   " AND plan_year ='"+str(self.plan_year)+"'")

            row = self.controller.get_row(str(sql))
            if row is not None:
                # if exist - show warning
                message = "Id already selected"
                self.controller.show_info_box(message, "Info", parameter=str(field_list[i]))
            else:
                # Put a new row in QTableView
                #dialog.selected_rows.model().insertRow(dialog.selected_rows.verticalHeader().count())

                sql = ("INSERT INTO " + self.schema_name + "." + tableright + ""
                       " (mu_id, work_id, plan_year) "
                       " VALUES (" + values + ")")
                self.controller.log_info(str(sql))
                self.controller.execute_sql(sql)

        # Refresh
        self.fill_table(dialog, tableright, tableleft)
        self.fill_main_table(dialog, tableleft)
        #self.set_table_columns(dialog.selected_rows, tableright)

    def select_all_rows(self, qtable, id, clear_selection=True):
        """ retrun list of index in @qtable"""
        # Select all rows and get all id
        qtable.selectAll()
        right_selected_list = qtable.selectionModel().selectedRows()
        right_field_list = []
        for i in range(0, len(right_selected_list)):
            row = right_selected_list[i].row()
            id_ = qtable.model().record(row).value(id)
            right_field_list.append(id_)
        if clear_selection:
            qtable.clearSelection()
        return right_field_list

    def rows_unselector(self, dialog, tableright, field_id_right, tableleft):

        query = ("DELETE FROM " + self.schema_name + "." + tableright + ""
                 " WHERE  plan_year='" + self.plan_year + "' AND " + field_id_right + " = ")
        selected_list = dialog.selected_rows.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_warning(message)
            return
        field_list = []
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            id_ = str(dialog.selected_rows.model().record(row).value(field_id_right))
            field_list.append(id_)
        for i in range(0, len(field_list)):
            sql = (query + "'" + str(field_list[i]) + "'")
            self.controller.execute_sql(sql)
        # Refresh model with selected filter
        self.fill_table(dialog, tableright, tableleft)
        self.fill_main_table(dialog, tableleft)


    def get_table_columns(self, tablename):
        # Get columns name in order of the table
        sql = ("SELECT column_name FROM information_schema.columns"
               " WHERE table_name = '" + tablename +"'"
               " AND table_schema = '" + self.schema_name.replace('"', '') + "'"
               " ORDER BY ordinal_position")
        column_name = self.controller.get_rows(sql)
        return column_name



    def accept_changes(self, qtable):
        model = qtable.model()
        model.database().transaction()
        if model.submitAll():
            model.database().commit()
        else:
            model.database().rollback()


    def cancel_changes(self, qtable):
        model = qtable.model()
        model.revertAll()
        model.database().rollback()