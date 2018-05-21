from openpyxl import load_workbook
from enum import Enum
from operator import itemgetter


class Pesos(Enum):
    P_No_Disponible = 0  # No planificable
    P_Disponible = 1    # Coste mínimo
    P_Horario = 9  # Penalización por Horario no preferente
    P_Jornada = 49 # Penalización por Jornada no preferente
    P_Puesto = 99 # Pensalización por puesto no preferente
    P_Festivo = 799 # Penalización por planificar en festivo
    P_Maximo = 999 # Penalización máxima

class ExcelLoad():

    def __init__(self, documento=None):
        
        self.Empleados = []
        self.hoja = None

        if not documento is None:
            wb = load_workbook(filename = documento)
            self.hoja = wb['Empleados']
        
    
    def OpenXlsx(self, documento):

        wb = load_workbook(filename = documento)
        self.hoja = wb['Empleados']


    def maxRows(self):
        
        # ws.min_col, ws.min_row, ws.max_col, ws.max_row 
        return (self.hoja.max_row)

   
    def LoadEmployees(self):

        Empleado = {}

        for fila in range(2, self.maxRows()+1):
            Empleado = self._LoadEmployee(fila)
            self.Empleados.append(Empleado)

        return self.Empleados


    def _AdaptarLista(self, lista):

        res = []
        _lista = lista.split(',')

        for elem in _lista:
            s = elem.strip()
            res.append(s)

        return res


    def _LoadEmployee(self, fila):

        Empleado = {}
        JornadaSemanal = []

        # Lectura de la hoja excel de empleados y sus características

        Empleado['Id'] = self.hoja.cell(row=fila, column=1).value
        Empleado['Nombre'] = self.hoja.cell(row=fila, column=2).value
        Empleado['Prioridad'] = self.hoja.cell(row=fila, column=3).value
        Empleado['HorasAcumuladas'] = self.hoja.cell(row=fila, column=4).value
        Empleado['HorasContrato'] = self.hoja.cell(row=fila, column=5).value
        Empleado['VacDisfrutadas'] = self.hoja.cell(row=fila, column=6).value
        Empleado['VacContrato'] = self.hoja.cell(row=fila, column=7).value
        Empleado['FestAnterior'] = self.hoja.cell(row=fila, column=8).value
        matriz = self._AdaptarLista(self.hoja.cell(row=fila, column=9).value)
        Empleado['HorPermitidos'] = matriz
        matriz = self._AdaptarLista(self.hoja.cell(row=fila, column=10).value)
        Empleado['HorPreferidos'] = matriz
        matriz = self._AdaptarLista(self.hoja.cell(row=fila, column=11).value)
        Empleado['PuestosPermitidos'] = matriz
        matriz = self._AdaptarLista(self.hoja.cell(row=fila, column=12).value)
        Empleado['PuestosAfinidad'] = matriz
        Empleado['FechaFinContrato'] = self.hoja.cell(row=fila, column=13).value

        # Cargamos la jornada semanal
        for d in range(7):
            ecol = d + 14
            JornadaSemanal.append( self.hoja.cell(row=fila, column=ecol).value)
        Empleado['JornadaSemanal'] = JornadaSemanal

        return Empleado

class Orientador():

    def __init__(self, Empleados):

        self.Empleados = Empleados
        self.planPesos  = []
        self.plaPesosDia = {}

    def cargaEmpleados(self, Empleados):

        self.Empleados = Empleados


    def calculaPesosDia(selfs):

        '''
        Para cada dia calcula el peso de cada dia segun las caracteristicas de cada empleado y dia
        :return:
        '''


    def filtrarEmpPorPuesto(self, Puesto):
        '''
        Filtra el diccionario de empleados segun el puesto en concreto
        :return: Una lista de empleados que coinciden con el puesto solicitado
        '''

        res = []

        for empleado in self.Empleados:
            if Puesto in empleado['PuestosPermitidos']:
                idx = empleado['PuestosPermitidos'].index(Puesto)
                empleado['PuestosAfinidad'] = empleado['PuestosAfinidad'][idx]
                res.append(empleado)

        # Ordenamos por prioridad y luego por afinidad
        ordenado_afi = sorted(res, key=itemgetter('PuestosAfinidad'), reverse=True)
        ordenado_pri = sorted(ordenado_afi, key=itemgetter('Prioridad'))

        return ordenado_pri

    def filtrarEmpPorHorario(self, Horario):
        '''
        Filtra el diccionario de empleados segun el horario en concreto
        :return: Una lista de empleados que coinciden con el horario solicitado
        '''

        res = []
        pref = []

        for empleado in self.Empleados:
            if Horario in empleado['HorPermitidos']:
                print(empleado['Nombre'])
                res.append(empleado)

        temp = res
        for empleado in res:
            print(empleado['Nombre'] + ' ' + str(empleado['HorPreferidos']))
            if Horario in empleado['HorPreferidos']:
                print (empleado['Nombre'] + ' ' + str(empleado['HorPreferidos']))
                pref.append(empleado)
                temp.remove(empleado)

        pref.append(temp)

        return pref

def main():
    
    lx = ExcelLoad('Empleados.xlsx')
    res = lx.LoadEmployees()

    for idx,emp in enumerate(res, start=1):
        print ('RES,#' + str(idx)+ ' ' + str(emp)  )

    orientador = Orientador(res)
    # puestos = orientador.filtrarEmpPorPuesto('Operario')
    horarios = orientador.filtrarEmpPorHorario('MA')

    for idx,emp in enumerate(horarios, start=1):
        print ('#' + str(idx)+ ' ' + str(emp)  )


if __name__ == "__main__":
    main()