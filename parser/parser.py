from openpyxl import load_workbook
from enum import Enum

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
        
        for fila in range(2, self.maxRows()):
            Empleado = self._LoadEmployee(fila)
            self.Empleados.append(Empleado)

        return self.Empleados


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
        matriz = self.hoja.cell(row=fila, column=9).value
        Empleado['HorPermitidos'] = matriz.split(',')
        matriz = self.hoja.cell(row=fila, column=10).value
        Empleado['HorPreferidos'] = matriz.split(',')
        matriz = self.hoja.cell(row=fila, column=11).value
        Empleado['PuestosPermitidos'] = matriz.split(',')
        matriz = str(self.hoja.cell(row=fila, column=12).value)
        Empleado['PuestosAfinidad'] = matriz.split(',')
        Empleado['FechaFinContrato'] = self.hoja.cell(row=fila, column=13).value

        # Cargamos la jornada semanal
        for d in range(7):
            ecol = d + 14
            JornadaSemanal.append( self.hoja.cell(row=fila, column=ecol).value)
        Empleado['JornadaSemanal'] = JornadaSemanal

        return Empleado

def main():
    
    lx = ExcelLoad('Empleados.xlsx')
    res = lx.LoadEmployees()
    

    print (res)


if __name__ == "__main__":
    main()