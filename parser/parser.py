from openpyxl import load_workbook

def main():
    wb = load_workbook(filename = 'Empleados.xlsx')
    hoja = wb['Empleados']

    ''' Variables
    '''
    Empleado = {}
    Empleados = []

    Disponibilidad = []

    # Lectura de la hoja excel de empleados y sus características
    Empleado['Id'] = hoja['A2'].value
    Empleado['Nombre'] = hoja['B2'].value
    Empleado['Prioridad'] = hoja['C2'].value
    Empleado['HorasAcumuladas'] = hoja['D2'].value
    Empleado['HorasContrato'] = hoja['E2'].value
    Empleado['VacDisfrutadas'] = hoja['F2'].value
    Empleado['VacContrato'] = hoja['G2'].value
    Empleado['FestAnterior'] = hoja['H2'].value
    matriz = hoja["I2"].value
    Empleado['HorPermitidos'] = matriz.split(',')
    matriz = hoja['J2'].value
    Empleado['HorPreferidos'] = matriz.split(',')
    matriz = hoja['K2'].value
    Empleado['PuestosPermitidos'] = matriz.split(',')
    matriz = str(hoja['L2'].value)
    Empleado['PuestosAfinidad'] = matriz.split(',')
    Empleado['FechaFinContrato'] = hoja['M2'].value
    dias = hoja['N2'].value
    Empleado['Dias'] = dias  #Numero de dias enviados para planificar

    Empleados.append(Empleado)
    erow = 2
    for d in range(dias):
        print (d)
        Disponibilidad[d] = hoja.cell(row=erow, column=2)
        print (Disponibilidad[d])

    #print (Empleados[0]['Nombre'])

if __name__ == "__main__":
    main()