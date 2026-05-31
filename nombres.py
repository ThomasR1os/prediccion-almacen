import pandas as pd
import random

path=r"C:\Users\User\Downloads\prueba.xlsx"

df=pd.read_excel(path)
print(df)
# Lista de nombres comunes (puedes expandirla con más nombres)
nombres_masculinos = ['Alejandro', 'Daniel', 'Mateo', 'Sebastián', 'Nicolás', 'Gabriel', 'Santiago', 'Manuel', 'Diego', 'Andrés']
nombres_femeninos = ['Sofía', 'Valentina', 'Isabella', 'Camila', 'Valeria', 'Mariana', 'Luciana', 'Daniela', 'Gabriela', 'Victoria']
# Función para obtener un nombre aleatorio de la lista
nombres_completos = nombres_masculinos + nombres_femeninos
# Función para obtener un nombre aleatorio de la lista
def generar_nombre_aleatorio():
    return random.choice(nombres_completos)

# 1. Crea la nueva columna 'Nombre_Alumno'
df['NOMBRE_ALUMNO'] = [generar_nombre_aleatorio() for _ in range(len(df))]

# 2. Reordena las columnas para poner 'Nombre_Alumno' al principio
# Obtén la lista de todas las columnas actuales
columnas = df.columns.tolist()

# Mueve 'Nombre_Alumno' al inicio de la lista
columnas.insert(0, columnas.pop(columnas.index('NOMBRE_ALUMNO')))

# Reindexa el DataFrame con el nuevo orden de columnas
df = df[columnas]
print(df)
df.to_excel("prueba_mejorada.xlsx")