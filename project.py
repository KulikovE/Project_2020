import sqlite3
import sys
import time

from PyQt5 import uic  # Импортируем uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QTableWidgetItem
import numpy

id_uchitel = 0


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('avtorizacia.ui', self)  # Загружаем дизайн
        self.connection = sqlite3.connect("dnevnik.sqlite")
        self.cur = self.connection.cursor()
        self.pushButton.clicked.connect(self.run)
        # Обратите внимание: имя элемента такое же как в QTDesigner

    def run(self):
        rol = self.comboBox.currentText()
        login = self.lineEdit.text()
        parol = self.lineEdit_2.text()
        if login == '' or parol == '':
            self.label_4.setText('Заполните все поля.')
            return
        if rol == 'Ученик':
            res = self.cur.execute("""SELECT * FROM uchenik WHERE login=?""", (login,)).fetchall()
            if len(res) == 0:
                self.label_4.setText('Неверный логин.')
                self.lineEdit_2.setText('')
                return
            if parol == str(res[0][3]):
                klass = self.cur.execute("""SELECT name FROM klass WHERE id=?""", (res[0][4],)).fetchall()
                time.sleep(1)
                self.cur.close()
                self.connection.close()
                self.second_form = FormUchenik(self, res[0][1], klass[0][0])
                self.close()
                self.second_form.show()
            else:
                self.label_4.setText('Неверный пароль.')
                return

        if rol == 'Учитель':
            res = self.cur.execute("""SELECT * FROM uchitel WHERE login=?""", (login,)).fetchall()
            if len(res) == 0:
                self.label_4.setText('Неверный логин.')
                self.lineEdit_2.setText('')
                return
            if parol == str(res[0][3]):
                klass = self.cur.execute("""SELECT name FROM predmeti WHERE uchitel=?""", (res[0][0],)).fetchall()
                time.sleep(1)
                self.cur.close()
                self.connection.close()
                global id_uchitel
                id_uchitel = res[0][0]
                self.third_form = FormUchitel(self, res[0][1], klass[0][0])  # Имя учителя, название предмета

                self.close()
                self.third_form.show()
            else:
                self.label_4.setText('Неверный пароль.')
                return


class FormUchenik(QMainWindow):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi('uchenik.ui', self)
        self.connection = sqlite3.connect("dnevnik.sqlite")
        self.cur = self.connection.cursor()
        self.res = self.cur.execute("""SELECT * FROM predmeti WHERE klass in (SELECT id FROM klass WHERE name=?)""",
                                    (args[-1],)).fetchall()
        res = self.res
        spisok_predmetov = []
        for i in range(len(res)):
            spisok_predmetov.append(res[i][1])
        self.comboBox.addItems(spisok_predmetov)
        name = args[-2] + ', ' + args[-1]
        self.label.setText(name)
        self.name_uchen = args[-2]
        self.pushButton.clicked.connect(self.run)

    def run(self):
        predmet = self.comboBox.currentIndex()
        res1 = self.cur.execute(
            """SELECT ocenka, data FROM ocenki WHERE predmet=?
            AND uchenik in (SELECT id FROM uchenik WHERE name = ?)""",
            (self.res[predmet][0], self.name_uchen)).fetchall()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(len(res1))
        self.tableWidget.setHorizontalHeaderLabels(["Оценка", "Дата"])
        for i in range(len(res1)):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(res1[i][0])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(res1[i][1]))
        self.tableWidget.resizeColumnsToContents()


class FormUchitel(QMainWindow):
    def __init__(self, *args):  # Имя учителя, название предмета
        super().__init__()
        uic.loadUi('uchitel.ui', self)
        self.connection = sqlite3.connect("dnevnik.sqlite")
        self.cur = self.connection.cursor()
        # self.id_uchitel = args[-3]
        self.res = self.cur.execute(
            """SELECT name, id FROM klass WHERE id in (SELECT klass FROM predmeti WHERE uchitel in 
            (SELECT id FROM uchitel WHERE name=?))""",
            (args[-2],)).fetchall()  # тут название класса(9а), id класса
        res = self.res
        spisok_klass = []
        for i in range(len(res)):
            spisok_klass.append(res[i][0])
        self.comboBox.addItems(spisok_klass)
        name = args[-2] + ', ' + args[-1]  # args[-2] - Имя учителя, args[-1]- предмет; заголовок
        self.label.setText(name)
        self.name_uchit = args[-2]
        self.pushButton.clicked.connect(self.read_ucheniki)
        self.pushButton_2.clicked.connect(self.save_oc)

    def read_ucheniki(self):
        data_kalend = self.calendarWidget.selectedDate()  # Получаем выбранную дату
        data_kalend = (str(data_kalend))[18:]
        self.data_kalend = data_kalend
        klass = self.comboBox.currentIndex()  # Индекс выбранного класса из выпадающего списка
        global id_uchitel
        id_predmet = self.cur.execute("""SELECT id FROM predmeti WHERE klass =? AND uchitel=?""",
                                      (self.res[klass][1], id_uchitel)).fetchall()  # id предмета для вывода оценок
        id_predmet = id_predmet[0][0]
        self.id_predmet = id_predmet
        res1 = self.cur.execute(
            """SELECT name, id FROM uchenik WHERE klass= ?""",
            (self.res[klass][1],)).fetchall()  # ВЫбираем учеников выбранного класса
        res2 = self.cur.execute("""SELECT ocenka, uchenik FROM ocenki WHERE data=? AND predmet=?""", (
            data_kalend, id_predmet)).fetchall()  # выбираем оценки для учеников на выбранную дату
        res3 = self.cur.execute("""SELECT ocenka FROM ocenki WHERE predmet=?""", (
            id_predmet,)).fetchall()  # выбираем оценки для учеников на выбранную дату
        vse_ocenki_klassa = []
        for i in range(len(res3)):
            vse_ocenki_klassa.append(res3[i][0])
        a = numpy.mean(vse_ocenki_klassa)
        a = round(a, 1)
        self.label_4.setText(str(a))
        self.res1 = res1
        self.res2 = res2
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(len(res1))
        self.tableWidget.setHorizontalHeaderLabels(["ФИО ученика", "Оценка"])
        for i in range(len(res1)):
            flag = 0
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(res1[i][0])))
            for j in range(len(res2)):
                if res1[i][1] == int(res2[j][1]):
                    self.tableWidget.setItem(i, 1, QTableWidgetItem(str(res2[j][0])))
                    flag = 1
            if flag == 0:
                self.tableWidget.setItem(i, 1, QTableWidgetItem(''))
        self.tableWidget.resizeColumnsToContents()

    def save_oc(self):
        self.res2 = self.cur.execute("""SELECT ocenka, uchenik FROM ocenki WHERE data=? AND predmet=?""", (
            self.data_kalend, self.id_predmet)).fetchall()  # выбираем оценки для учеников на выбранную дату
        for i in range(len(self.res1)):
            flag = 0
            for j in range(len(self.res2)):
                if self.res1[i][1] == int(self.res2[j][1]):  # Если оценка уже была, значит её обновляем
                    flag = 1
                    if self.tableWidget.item(i, 1).text() == '':  # Оценку удаляем
                        self.cur.execute("""DELETE FROM ocenki WHERE uchenik=? AND data=? AND predmet=?""", (
                            self.res1[i][1], self.data_kalend, self.id_predmet))
                        self.connection.commit()
                    else:
                        self.cur.execute("""UPDATE ocenki SET ocenka=? WHERE uchenik=? AND data=? AND predmet=?""", (
                            int(self.tableWidget.item(i, 1).text()), int(self.res1[i][1]), str(self.data_kalend),
                            int(self.id_predmet)))
                        self.connection.commit()

            if flag == 0:  # Если оценки не было, значит добавляем её
                if self.tableWidget.item(i, 1).text() != '':
                    self.cur.execute("""INSERT INTO ocenki(ocenka, predmet, data, uchenik) VALUES(?, ?, ?, ?)""", (
                        int(self.tableWidget.item(i, 1).text()), self.id_predmet, str(self.data_kalend),
                        self.res1[i][1]))
                    self.connection.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())
