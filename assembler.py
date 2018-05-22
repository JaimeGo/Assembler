import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
import codecs

#string del principio del archivo

begin = "library IEEE;\n\
use IEEE.STD_LOGIC_1164.ALL;\n\
use IEEE.STD_LOGIC_UNSIGNED.ALL;\n\
USE IEEE.NUMERIC_STD.ALL;\n\
\n\
entity ROM is\n\
PORT (\
address : in std_logic_vector (11 downto 0);\n\
dataout : out std_logic_vector (32 downto 0)\n\
);\n\
end ROM;\n\
\n\
architecture Behavioral of ROM is\n\
\n\
type memory_array is array (0 to ((2**12)-1) ) of std_logic_vector (32 downto 0);\n\
\n\
signal memory : memory_array:= (\n\
"

#string del final del archivo

end = "\n\
);\n\
begin\n\
\n\
dataout <= memory(to_integer(unsigned(address)));\n\
\n\
end Behavioral;"


#class encargada de la Gui (PyQt5)
class Formulario(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setupUi(self)

        self.pushButton.clicked.connect(self.generar)

        self.lineEdit.setText(os.path.dirname(os.path.abspath(__file__)) + "/")

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 300)
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setGeometry(QtCore.QRect(110, 180, 161, 32))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(60, 90, 271, 16))
        self.label.setObjectName("label")
        self.lineEdit = QtWidgets.QLineEdit(Form)
        self.lineEdit.setGeometry(QtCore.QRect(30, 120, 331, 21))
        self.lineEdit.setObjectName("lineEdit")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        self.lineEdit.setText(os.path.dirname(os.path.abspath(__file__)) + "/")

    #esto existe porque se ocupo qtdesigner
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton.setText(_translate("Form", "Generar archivo"))
        self.label.setText(_translate("Form", "Introduzca el path del archivo en assembly:"))

    #funcion del boton de la GUI
    def generar(self):
        self.path = self.lineEdit.text()

        parser = Parser()

        lista_lineas = []
        with codecs.open(self.path, "r", "utf-8") as inst_file:
            for line in inst_file:
                lista_lineas.append(line)

        parser.obtener_labels_y_lineas(lista_lineas)

        parser.file.write(begin)

        parser.parsear(lista_lineas)

        parser.literal = "0000000000000000"

        inicio = parser.contador_inst
        for i in range(inicio + 1, 4096):
            parser.wr("nop")


        parser.es_ultima_linea = True
        parser.wr("nop")


        parser.file.write(end)

        parser.file.close()

        self.close()

#clase para convertir a decimal y a binario
class Converter:

    #convierte los argumentos a decimal
    def args_a_dec(self, inst, arg_1, arg_2, dict_labels, in_data):

        lista_args = []

        #la lista añade inst si inst contiene numeros (caso especial en que inst es un elemento de un arreglo)
        lista_params_cambiar=[arg_1,arg_2]
        if in_data and not arg_1 and not arg_2:
            lista_params_cambiar.append(inst)

        for arg in lista_params_cambiar:
            if arg:
                if arg not in dict_labels.keys():

                    if inst not in ["JMP", "JEQ", "JNE", "JGT", "JGE", "JLT", "JLE", "JCR"]:

                        if "d" in arg:
                            busq = "d"
                        elif "b" in arg:
                            busq = "b"
                        elif "h" in arg:
                            busq = "h"
                        else:
                            busq = None

                        if busq:

                            pos_key_fin = arg.rfind(busq) + 1
                            pos_key_ini = arg.rfind(" ", 0, pos_key_fin - 1)

                            if pos_key_ini == -1:
                                pos_key_ini = 0
                            if pos_key_fin == -1:
                                pos_key_fin = len(arg)

                            if "(" in arg[:pos_key_ini] and ")" in arg[pos_key_fin:]:

                                for i in range(1, 10):

                                    if arg[pos_key_ini] == " ":
                                        arg = arg[:pos_key_ini] + arg[pos_key_ini + 1:]
                                        pos_key_fin -= 1
                                        pos_key_ini -= 1

                                    if arg[pos_key_ini] == "(":
                                        break

                                for j in range(1, 10):

                                    if arg[pos_key_fin] == " ":
                                        arg = arg[:pos_key_fin] + arg[pos_key_fin + 1:]

                                    if arg[pos_key_fin] == ")":
                                        break

                            if pos_key_ini > 0:
                                ante_char = arg[pos_key_ini]

                            else:
                                ante_char = " "

                            if pos_key_fin < len(arg) - 1:

                                pos_char = arg[pos_key_fin + 1]
                            else:

                                pos_char = " "

                            meaning = {"b": 2, "d": 10, "h": 16}

                            if (ante_char == " " or ante_char == "(" or ante_char == ",") and \
                                    (pos_char == " " or pos_char == ")" or pos_char == ",") and not \
                                    (arg.isalpha() and busq is not "h"):
                                if pos_key_fin - pos_key_ini <= 2 or (pos_key_ini == 0 and arg[pos_key_ini] is not "("):
                                    lista_args.append(str(int(arg[0:pos_key_fin - 1], meaning[busq])))
                                else:
                                    lista_args.append(str(int(arg[pos_key_ini + 1:pos_key_fin - 1], meaning[busq])))

                            else:
                                lista_args.append(arg)
                        else:
                            lista_args.append(arg)

                    else:
                        lista_args.append(arg)
                else:
                    lista_args.append(arg)
            else:
                lista_args.append(arg)

        return lista_args

    # 101 -> 010 (no complemento a 2)
    def complemento(self, x):
        res = ""
        for i in range(0, 16):
            if x[i] == "0":
                res = res + "1"
            else:
                res = res + "0"

        return res

    #suma de numeros binarios
    def suma_bin(self, x, y):
        over_flow = 0
        res = ""
        for i in range(0, 16):
            if x[15 - i] == "0" and y[15 - i] == "0":

                res = str(over_flow) + res
                over_flow = 0
            elif (x[15 - i] == "1" and y[15 - i] == "0") or (x[15 - i] == "0" and y[15 - i] == "1"):
                num = over_flow + 1
                if num > 1:
                    num = 0
                    over_flow = 1
                else:
                    over_flow = 0
                res = str(num) + res

            elif x[15 - i] == "1" and y[15 - i] == "1":
                num = over_flow + 2
                if num > 2:
                    num = 1
                    over_flow = 1
                else:
                    num = 0
                    over_flow = 1
                res = str(num) + res

        return res

    #resta de numeros binarios
    def resta_bin(self, x, y):
        noty = self.complemento(y)
        c2y = self.suma_bin(noty, "0000000000000001")
        resta = self.suma_bin(x, c2y)

        return resta

    #convierte a binario de 16 bits
    def a_binario_16(self, num_dec):
        num_dec = int(num_dec)

        return '{0:016b}'.format(num_dec)

    #convierte a decimal de 16 bits
    def a_decimal_16(self, inicial):

        res = 0

        for i in range(0, 16):
            res += (2 ** (15 - i)) * int(inicial[i])

        return int(res)


class Parser:
    def __init__(self):

        # contador para ver cuantas lineas rellenar al final
        self.contador_inst = 0

        self.literal = "0000000000000000"

        #al identificarse el string key, se llama a la funcion value de este diccionario
        self.dict_inst = {
            "MOV": self.mov,
            "ADD": self.add,
            "SUB": self.sub,
            "AND": self.andd,
            "OR": self.orr,
            "NOT": self.nott,
            "XOR": self.xorr,
            "SHL": self.shl,
            "SHR": self.shr,
            "INC": self.inc,
            "CMP": self.cmp,
            "JMP": self.jmp,
            "JEQ": self.jeq,
            "JNE": self.jne,
            "JGT": self.jgt,
            "JLT": self.jlt,
            "JGE": self.jge,
            "JLE": self.jle,
            "JCR": self.jcr,
            "DEC": self.dec,
            "NOP": self.nop,
            "PUSH":self.push,
            "POP":self.pop,
            "CALL":self.call,
            "RET":self.ret,
            "IN":self.inn

        }

        #la funcion wr (write) ocupa este diccionario para escribir los opcodes en el archivo de salida
        self.dict_opcodes = {
            "movab": "00000000000000001",
            "movba": "00000000000000010",
            "movalit": "00000000000000011",
            "movblit": "00000000000000100",
            "movadir": "00000000000000101",
            "movbdir": "00000000000000110",
            "movdira": "00000000000000111",
            "movdirb": "00000000000001000",
            "movadirb":"00000000000001001",#new
            "movbdirb":"00000000000001010",#new
            "movdirba":"00000000000001011",#new
            "movdirblit":"00000000000001100",#new
            "addab": "00000000000001101",
            "addba": "00000000000001110",
            "addalit": "00000000000001111",
            "addblit": "00000000000010000",
            "addadir": "00000000000010001",
            "addbdir": "00000000000010010",
            "adddir": "00000000000010011",
            "addadirb":"00000000000010100",#new
            "addbdirb":"00000000000010101",#new
            "subab": "00000000000010110",
            "subba": "00000000000010111",
            "subalit": "00000000000011000",
            "subblit": "00000000000011001",
            "subadir": "00000000000011010",
            "subbdir": "00000000000011011",
            "subdir": "00000000000011100",
            "subadirb": "00000000000011101",  # new
            "subbdirb": "00000000000011110",  # new
            "andab": "00000000000011111",
            "andba": "00000000000100000",
            "andalit": "00000000000100001",
            "andblit": "00000000000100010",
            "andadir": "00000000000100011",
            "andbdir": "00000000000100100",
            "anddir": "00000000000100101",
            "andadirb": "00000000000100110",  # new
            "andbdirb": "00000000000100111",  # new
            "orab": "00000000000101000",
            "orba": "00000000000101001",
            "oralit": "00000000000101010",
            "orblit": "00000000000101011",
            "oradir": "00000000000101100",
            "orbdir": "00000000000101101",
            "ordir": "00000000000101110",
            "oradirb": "00000000000101111",  # new
            "orbdirb": "00000000000110000",  # new
            "xorab": "00000000000110001",
            "xorba": "00000000000110010",
            "xoralit": "00000000000110011",
            "xorblit": "00000000000110100",
            "xoradir": "00000000000110101",
            "xorbdir": "00000000000110110",
            "xordir": "00000000000110111",
            "xoradirb": "00000000000111000",  # new
            "xorbdirb": "00000000000111001",  # new
            "nota": "00000000000111010",
            "notba": "00000000000111011",
            "notdira": "00000000000111100",
            "notdirba":"00000000000111101",#new
            "shla": "00000000000111110",
            "shlba": "00000000000111111",
            "shldira": "00000000001000000",
            "shldirba": "00000000001000001",  # new
            "shra": "00000000001000010",
            "shrba": "00000000001000011",
            "shrdira": "00000000001000100",
            "shrdirba": "00000000001000101",  # new
            "inca": "00000000001000110",
            "incb": "00000000001000111",
            "incdir": "00000000001001000",
            "incdirb": "00000000001001001",  # new
            "deca": "00000000001001010",
            "cmpab": "00000000001001011",
            "cmpalit": "00000000001001100",
            "cmpadir": "00000000001001101",
            "cmpadirb": "00000000001001110",  # new
            "jmp": "00000000001001111",
            "jeq": "00000000001010000",
            "jne": "00000000001010001",
            "jgt": "00000000001010010",
            "jge": "00000000001010011",
            "jlt": "00000000001010100",
            "jle": "00000000001010101",
            "jcr": "00000000001010110",
            "nop": "00000000000000000",#los siguientes son nuevos

            "pusha":"00000000001010111",
            "pushb":"00000000001011000",
            "popa1":"00000000001011001",
            "popa2":"00000000001011010",
            "popb1":"00000000001011011",
            "popb2":"00000000001011100",
            "calllit":"00000000001011101",
            "ret1":"00000000001011110",
            "ret2":"00000000001011111",
            "inalit":"00000000001100000",
            "inblit":"00000000001100001",
            "indirblit":"00000000001100010"


        }

        #archivo de salida
        self.file = open("codes.txt", "w")

        #instancia de la clase para convertir entre decimal y binario
        self.conv = Converter()

        #registro A
        self.a = "0000000000000000"

        # registro B
        self.b = "0000000000000000"

        #memoria
        self.mem = {}

        #contador de lineas añadidas al archivo de salida. Se ocupa para rellenar despues
        self.contador_lineas = 0

        # key: numero del contador, value: linea
        self.dict_lineas = {}

        # key: nombre label, value: numero del contador
        self.dict_labels = {}

        # key: nombre variable, value: valor variable
        self.dict_variables = {}

        self.in_data = True

        self.in_code = False

        self.contador_var_usadas = 0

        # key:nombre var, value: dir en mem
        self.dict_nombre_dir_var = {}

        #se ocupa porque la ultima linea es sin coma
        self.es_ultima_linea = False

        # al saltar debemos considerar las instrucciones añadidas al procesar las variables de DATA
        # Requieren 3 instrucciones en vez de 1 (por eso se desplaza el jump)
        self.desplazo_var = 0

    #funcion para escribir en el archivo de salida (literal + opcode)
    def wr(self, codigo):

        if not self.es_ultima_linea:
            self.file.write("\"" + self.literal + self.dict_opcodes[codigo] + "\"" + "," + "\n")

        else:
            self.file.write("\"" + self.literal + self.dict_opcodes[codigo] + "\"" + "\n")

    #saca los labels y las lineas a sus respectivos diccionarios antes de parsear
    def obtener_labels_y_lineas(self, lista_lineas):
        cuantas_inst = 0
        hay_label = False
        label = ""

        for i in range(0, len(lista_lineas)):
            line = lista_lineas[i]
            self.dict_lineas[i] = line

            line = line.strip()

            if hay_label:
                self.dict_labels[label] = cuantas_inst
                hay_label = False

            if ":" in line and "DATA" not in line and "CODE" not in line:
                hay_label = True
                label = line[:line.find(":")]

            inst_end = line.find(" ")
            inst = line[0:inst_end].strip()

            if inst in self.dict_inst.keys():
                cuantas_inst += 1

        print(self.dict_labels)

    def obtener_labels_y_lineas222(self, lista_lineas):
        cuantas_inst = 0
        hay_label = False
        label = ""

        for i in range(0, len(lista_lineas)):
            line = lista_lineas[i]
            self.dict_lineas[i] = line

            line = line.strip()

            if hay_label:
                self.dict_labels[label] = cuantas_inst
                hay_label = False

            if ":" in line and "DATA" not in line and "CODE" not in line:
                hay_label = True
                label = line[:line.find(":")]

            inst_end = line.find(" ")
            inst = line[0:inst_end].strip()

            if inst in self.dict_inst.keys():
                cuantas_inst += 1

        print(self.dict_labels)


    #permite obtener literal para todas las funciones
    def obtener_literal(self, inst, arg_1, arg_2):


        if arg_1:
            if "(B)" not in arg_1:
                if "(" not in arg_1:
                    if arg_1.isdigit():
                        self.literal = self.conv.a_binario_16(arg_1)
                else:
                    arg_1.strip()
                    self.literal = self.conv.a_binario_16(arg_1[1:-1])

        if arg_2:
            if "(B)" not in arg_2:
                if "(" not in arg_2:
                    if arg_2.isdigit():
                        self.literal = self.conv.a_binario_16(arg_2)
                else:
                    arg_2.strip()
                    self.literal = self.conv.a_binario_16(arg_2[1:-1])

        if inst in ["JMP", "JEQ", "JNE", "JGT", "JGE", "JLT", "JLE", "JCR","CALL"]:
            self.literal = self.conv.a_binario_16(self.dict_labels[arg_1] + self.desplazo_var)




    #reemplaza las variables en la linea antes de procesarla
    def reemplazo_variables(self, line):
        if ":" not in line and self.in_code:



            for key, val in self.dict_nombre_dir_var.items():

                if key in line:

                    pos_key_fin = line.rfind(key) + len(key)

                    pos_key_ini = line.rfind(key) - 1

                    if pos_key_fin >= len(line):
                        pos_key_fin = len(line) - 1

                    if "(" in line[:pos_key_ini] and ")" in line[pos_key_fin:]:

                        for i in range(1, 10):

                            if line[pos_key_ini] == " ":
                                line = line[:pos_key_ini] + line[pos_key_ini + 1:]
                                pos_key_fin -= 1
                                pos_key_ini -= 1

                            if line[pos_key_ini] == "(":
                                break

                        for j in range(1, 10):

                            if line[pos_key_fin] == " ":
                                line = line[:pos_key_fin] + line[pos_key_fin + 1:]

                            if line[pos_key_fin] == ")":
                                break

                    ante_char = line[pos_key_ini]
                    pos_char = line[pos_key_fin]

                    if ante_char == "(" and pos_char == ")":

                        pos_coma = line.find(",")
                        pos_par = line.find(")")

                        if pos_coma < pos_par and pos_coma != -1:
                            line = line.replace(key, str(val))
                        else:
                            line = line.replace(key, str(val))





                    elif (ante_char == " " or ante_char == ",") and \
                            (pos_char == " " or pos_char == ","):

                        line = line.replace(key, "(" + str(self.dict_nombre_dir_var[key]) + ")")

        return line

    # esto es para procesar las variables en la seccion de DATA
    # (son 3 instrucciones con los literales correspondientes)
    def variables_escritura(self, val, dir):

        val = self.conv.a_binario_16(val)

        dir = self.conv.a_binario_16(dir)

        self.literal = str(val)

        self.wr("movalit")

        self.literal = str(dir)

        self.wr("movdira")

        self.literal = str(self.conv.a_binario_16(0))

        self.wr("movalit")

        self.contador_inst += 3

        self.desplazo_var += 3

    #funcion principal que procesa una linea
    def parsear_linea(self, line):
        print(line)

        if "CODE" in line:
            self.in_data = False
            self.in_code = True

        # sacamos los comentarios
        pos_slash = line.find("//")
        if pos_slash is not -1:
            line = line[:pos_slash]

        line = line.strip()
        self.dict_lineas[self.contador_lineas] = line

        # ignoramos los labels
        if ":" in line and "DATA" not in line and "CODE" not in line:
            line = line[line.find(":") + 1:].strip()

        # reemplazamos por las variables
        line = self.reemplazo_variables(line)

        self.contador_lineas += 1

        #lo siguiente es para obtener los args en el formato correcto
        inst_end_1 = line.find(" ")
        inst_end_2 = line.find("\t")

        inst_end=inst_end_1 if inst_end_1>inst_end_2 else inst_end_2

        if inst_end == -1:
            inst_end = len(line)
        inst = line[0:inst_end]

        inst_args = line[inst_end + 1:]
        lista_args = inst_args.split(",")

        arg_1 = lista_args[0].strip()
        arg_2 = lista_args[1].strip() if len(lista_args) > 1 else None

        # conversion de argumentos bin, dec y hex
        lista_args = self.conv.args_a_dec(inst, arg_1, arg_2, self.dict_labels, self.in_data)

        arg_1 = lista_args[0]
        arg_2 = lista_args[1]

        if len(lista_args)==3:
            inst=lista_args[2]

        # obtenemos el literal. Puede provenir de (Dir) o de Lit
        self.obtener_literal(inst, arg_1, arg_2)

        #si la instruccion es valida, se llama a la funcion correspondiente (Ej: add)
        if inst in self.dict_inst.keys():
            self.contador_inst += 1
            self.dict_inst[inst](arg_1, arg_2)



        # asignacion de var (seccion DATA)
        elif line:
            if "DATA" not in line and "CODE" not in line and self.in_data:

                self.declarar_variables(inst,arg_1)


    def declarar_variables(self,nombre, arg_1):
        nombre=nombre.strip()


        #si no es parte de un arreglo (o es el primer valor)
        if arg_1:
            self.dict_nombre_dir_var[nombre] = self.contador_var_usadas
            self.variables_escritura(arg_1, self.contador_var_usadas)

            self.mem[self.contador_var_usadas] = arg_1

        #si es parte de un arreglo
        else:
            self.variables_escritura(nombre, self.contador_var_usadas)

            self.mem[self.contador_var_usadas] = nombre

        self.contador_var_usadas += 1




    #recibe la lista de lineas y las manda a ser parseadas
    def parsear(self, lista_lineas):
        for line in lista_lineas:
            self.parsear_linea(line)

    def mov(self, arg_1=None, arg_2=None):


        if arg_1 == "A":
            if "(B" in arg_2:
                self.wr("movadirb")



            elif "(" in arg_2:

                self.wr("movadir")

            elif arg_2 == "B":

                self.wr("movab")

            else:

                self.wr("movalit")


        elif arg_1 == "B":
            if "(B" in arg_2:
                self.wr("movbdirb")

            elif "(" in arg_2:

                self.wr("movbdir")

            elif arg_2 == "A":

                self.wr("movba")

            else:

                self.wr("movblit")

        elif "(B" in arg_1:
            if arg_2 == "A":

                self.wr("movdirba")

            else:

                self.wr("movdirblit")


        elif "(" in arg_1:


            if arg_2 == "A":

                self.wr("movdira")



            elif arg_2 == "B":

                self.wr("movdirb")

    def add(self, arg_1=None, arg_2=None):


        if arg_1 == "A":
            if "(B" in arg_2:

                self.wr("addadirb")
            elif "(" in arg_2:

                self.wr("addadir")

            elif arg_2 == "B":

                self.wr("addab")

            else:

                self.wr("addalit")


        elif arg_1 == "B":
            if "(B" in arg_2:

                self.wr("addbdirb")
            elif "(" in arg_2:

                self.wr("addbdir")

            elif arg_2 == "A":

                self.wr("addba")

            else:

                self.wr("addblit")

        elif "(" in arg_1:

            self.wr("adddir")

    def sub(self, arg_1=None, arg_2=None):



        if arg_1 == "A":
            if "(B" in arg_2:

                self.wr("subadirb")
            elif "(" in arg_2:

                self.wr("subadir")

            elif arg_2 == "B":

                self.wr("subab")

            else:

                self.wr("subalit")

        elif arg_1 == "B":
            if "(B" in arg_2:

                self.wr("subbdirb")
            elif "(" in arg_2:

                self.wr("subbdir")

            elif arg_2 == "A":

                self.wr("subba")

            else:

                self.wr("subblit")

        elif "(" in arg_1:

            self.wr("subdir")

    def andd(self, arg_1=None, arg_2=None):


        if arg_1 == "A":
            if "(B" in arg_2:

                self.wr("andadirb")
            elif "(" in arg_2:

                self.wr("andadir")

            elif arg_2 == "B":

                self.wr("andab")

            else:

                self.wr("andalit")

        elif arg_1 == "B":
            if "(B" in arg_2:

                self.wr("andbdirb")
            elif "(" in arg_2:

                self.wr("andbdir")

            elif arg_2 == "A":

                self.wr("andba")

            else:

                self.wr("andblit")

        elif "(" in arg_1:

            self.wr("anddir")

    def orr(self, arg_1=None, arg_2=None):


        if arg_1 == "A":
            if "(B" in arg_2:

                self.wr("oradirb")
            elif "(" in arg_2:

                self.wr("oradir")

            elif arg_2 == "B":

                self.wr("orab")


            else:

                self.wr("oralit")

        elif arg_1 == "B":
            if "(B" in arg_2:

                self.wr("orbdirb")
            elif "(" in arg_2:

                self.wr("orbdir")

            elif arg_2 == "A":

                self.wr("orba")

            else:

                self.wr("orblit")

        elif "(" in arg_1:

            self.wr("ordir")

    def xorr(self, arg_1=None, arg_2=None):


        if arg_1 == "A":
            if "(B" in arg_2:

                self.wr("xoradirb")
            elif "(" in arg_2:

                self.wr("xoradir")

            elif arg_2 == "B":

                self.wr("xorab")

            else:

                self.wr("xoralit")

        elif arg_1 == "B":
            if "(B" in arg_2:

                self.wr("xorbdirb")
            elif "(" in arg_2:

                self.wr("xorbdir")

            elif arg_2 == "A":

                self.wr("xorba")

            else:

                self.wr("xorblit")

        elif "(" in arg_1:

            self.wr("xordir")

    def nott(self, arg_1=None, arg_2=None):


        if arg_1 == "A":

            self.wr("nota")


        elif arg_1 == "B":

            if arg_2 == "A":
                self.wr("notba")

        elif "(B" in arg_1:

            self.wr("notdirba")

        elif "(" in arg_1:

            self.wr("notdira")

    def shl(self, arg_1=None, arg_2=None):


        if arg_1 == "A":

            self.wr("shla")


        elif arg_1 == "B":
            if arg_2 == "A":
                self.wr("shlba")

        elif "(B" in arg_1:

            self.wr("shldirba")

        elif "(" in arg_1:

            self.wr("shldira")

    def shr(self, arg_1=None, arg_2=None):


        if arg_1 == "A":

            self.wr("shra")


        elif arg_1 == "B":
            if arg_2 == "A":
                self.wr("shrba")

        elif "(B" in arg_1:

            self.wr("shrdirba")

        elif "(" in arg_1:

            self.wr("shrdira")

    def inc(self, arg_1=None, arg_2=None):


        if arg_1 == "A":

            self.wr("inca")

        elif arg_1 == "B":

            self.wr("incb")

        elif "(B" in arg_1:

            self.wr("incdirb")

        elif "(" in arg_1:

            self.wr("incdir")

    def dec(self, arg_1=None, arg_2=None):


        self.wr("deca")

    def cmp(self, arg_1=None, arg_2=None):

        if "(B" in arg_1:

            self.wr("cmpadirb")

        elif "(" in arg_2:
            self.wr("cmpadir")


        elif arg_2 == "B":
            arg_2_mod = self.conv.a_decimal_16(self.b)
            self.wr("cmpab")
        else:
            arg_2_mod = int(arg_2)
            self.wr("cmpalit")

    def jmp(self, arg_1=None, arg_2=None):


        self.wr("jmp")

    def jeq(self, arg_1=None, arg_2=None):


        self.wr("jeq")

    def jne(self, arg_1=None, arg_2=None):

        self.wr("jne")

    def jgt(self, arg_1=None, arg_2=None):


        self.wr("jgt")

    def jlt(self, arg_1=None, arg_2=None):

        self.wr("jlt")

    def jge(self, arg_1=None, arg_2=None):

        self.wr("jge")

    def jle(self, arg_1=None, arg_2=None):


        self.wr("jle")

    def jcr(self, arg_1=None, arg_2=None):


        self.wr("jcr")

    def nop(self, arg_1=None, arg_2=None):

        self.literal = "0000000000000000"
        self.wr("nop")


    #funciones nuevas

    def push(self, arg_1=None, arg_2=None):


        if arg_1 == "A":

            self.wr("pusha")

        elif arg_1 == "B":

            self.wr("pushb")

    def pop(self, arg_1=None, arg_2=None):


        if arg_1 == "A":
            self.contador_inst += 1
            self.wr("popa1")
            self.wr("popa2")

        elif arg_1 == "B":
            self.contador_inst += 1
            self.wr("popb1")
            self.wr("popb2")

        self.desplazo_labels_pop_ret()

    def call(self, arg_1=None, arg_2=None):


        self.wr("calllit")

    def ret(self, arg_1=None, arg_2=None):

        self.contador_inst += 1
        self.wr("ret1")
        self.wr("ret2")

        self.desplazo_labels_pop_ret()

    def inn(self, arg_1=None, arg_2=None):


        if arg_1 == "A":

            self.wr("inalit")

        elif arg_1 == "B":

            self.wr("inblit")

        elif arg_1 == "(B)":

            self.wr("indirblit")


    def desplazo_labels_pop_ret(self):

        for key, value in self.dict_labels.items():
            if value>=self.contador_inst:
                self.dict_labels[key]+=1



if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    form = Formulario()
    form.show()
    app.exec_()
