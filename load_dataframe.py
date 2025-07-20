import os
import pandas as pd
from typing import Tuple, Optional, Dict, List
import datetime

def cargar_dataframe(file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Carga un DataFrame desde múltiples formatos con validación robusta
    """
    if not os.path.exists(file_path):
        return None, f"Error: El archivo {file_path} no existe"
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8', na_values=['', 'NA', 'NULL', 'NaN'])
        elif ext in ('.xls', '.xlsx'):
            df = pd.read_excel(file_path, na_values=['', 'NA', 'NULL', 'NaN'])
        elif ext == '.parquet':
            df = pd.read_parquet(file_path)
        elif ext == '.json':
            df = pd.read_json(file_path)
        else:
            return None, f"Error: Formato {ext} no soportado"
        
        # Convertir strings a categorías para optimización
        for col in df.select_dtypes(include=['object']):
            if len(df[col].unique()) / len(df[col]) < 0.5:
                df[col] = df[col].astype('category')
                
        return df, None
        
    except Exception as e:
        return None, f"Error al cargar {file_path}: {str(e)}"

def analizar_nulos_por_columna(df: pd.DataFrame) -> List[Dict]:
    """
    Analiza valores nulos por columna con métricas detalladas
    
    Returns:
        Lista de diccionarios con:
        - nombre_columna
        - tipo_dato
        - total_nulos
        - porcentaje_nulos
        - no_nulos
        - porcentaje_no_nulos
        - ejemplo_valores (3 primeros no nulos)
    """
    analisis = []
    total_filas = len(df)
    
    for columna in df.columns:
        nulos = df[columna].isnull().sum()
        no_nulos = total_filas - nulos
        porcentaje_nulos = (nulos / total_filas) * 100 if total_filas > 0 else 0
        valores_unicos = df[columna].nunique()
        
        # Ejemplos de valores (excluyendo nulos)
        ejemplos = []
        if no_nulos > 0:
            ejemplos = df[columna].dropna().head(3).tolist()
            # Convertir a string si es necesario para serialización
            ejemplos = [str(x) for x in ejemplos]
        
        analisis.append({
            'nombre_columna': columna,
            'tipo_dato': str(df[columna].dtype),
            'total_nulos': nulos,
            'porcentaje_nulos': round(porcentaje_nulos, 2),
            'no_nulos': no_nulos,
            'porcentaje_no_nulos': round(100 - porcentaje_nulos, 2),
            'valores_unicos': valores_unicos,
            'ejemplo_valores': ejemplos
        })
    
    # Ordenar por porcentaje de nulos descendente
    return sorted(analisis, key=lambda x: x['porcentaje_nulos'], reverse=True)

def get_file_metadata(file_path: str) -> Dict:
    """
    Obtiene metadatos detallados del archivo
    """
    stats = os.stat(file_path)
    return {
        'nombre': os.path.basename(file_path),
        'ruta': os.path.abspath(file_path),
        'tamaño_bytes': stats.st_size,
        'tamaño_mb': round(stats.st_size / (1024 * 1024), 2),
        'fecha_modificacion': datetime.datetime.fromtimestamp(stats.st_mtime),
        'extension': os.path.splitext(file_path)[1].lower(),
        'encoding': 'utf-8'  # Se puede detectar con chardet si es necesario
    }
