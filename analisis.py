import os
import tempfile
import pandas as pd
from ydata_profiling import ProfileReport
from load_dataframe import cargar_dataframe, analizar_nulos_por_columna, get_file_metadata
from graficos_r import generar_histograma_r, generar_barras_r, generar_boxplot_r

class AnalizadorDatos:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.metadata = None
        self.nulos_por_columna = None
        self.reporte_path = None
        self.graficos = {}
        
    def cargar_datos(self) -> bool:
        """Carga y valida los datos"""
        self.df, error = cargar_dataframe(self.file_path)
        if error:
            print(error)
            return False
        
        self.metadata = get_file_metadata(self.file_path)
        self.nulos_por_columna = analizar_nulos_por_columna(self.df)
        return True
    
    def generar_reporte_nulos(self) -> str:
        """Genera un reporte detallado de valores nulos por columna"""
        if not self.nulos_por_columna:
            return "No hay datos de nulos disponibles"
            
        reporte = "=== ANÁLISIS DE VALORES NULOS POR COLUMNA ===\n\n"
        reporte += f"Total filas en dataset: {len(self.df)}\n"
        reporte += f"Total columnas: {len(self.df.columns)}\n\n"
        
        for col in self.nulos_por_columna:
            reporte += f"Columna: {col['nombre_columna']} ({col['tipo_dato']})\n"
            reporte += f"  - Valores nulos: {col['total_nulos']} ({col['porcentaje_nulos']}%)\n"
            reporte += f"  - Valores no nulos: {col['no_nulos']} ({col['porcentaje_no_nulos']}%)\n"
            reporte += f"  - Valores únicos: {col['valores_unicos']}\n"
            
            if col['ejemplo_valores']:
                reporte += f"  - Ejemplos: {', '.join(col['ejemplo_valores'])}\n"
            else:
                reporte += "  - Ejemplos: TODOS SON NULOS\n"
            
            # Recomendación basada en porcentaje de nulos
            if col['porcentaje_nulos'] > 30:
                reporte += "  - RECOMENDACIÓN: Considerar eliminar o imputar esta columna\n"
            elif col['porcentaje_nulos'] > 0:
                reporte += "  - RECOMENDACIÓN: Evaluar imputación de valores\n"
            else:
                reporte += "  - RECOMENDACIÓN: Sin problemas de nulos\n"
            
            reporte += "\n"
        
        return reporte
    
    def generar_reporte(self, minimal: bool = True) -> str:
        """Genera reporte de profiling"""
        try:
            self.reporte_path = tempfile.NamedTemporaryFile(
                suffix='.html', 
                delete=False
            ).name
            
            profile = ProfileReport(
                self.df,
                title=f"Reporte de Análisis - {self.metadata['nombre']}",
                minimal=minimal,
                explorative=True
            )
            profile.to_file(self.reporte_path)
            return self.reporte_path
        except Exception as e:
            print(f"Error generando reporte: {e}")
            return None
    
    def generar_graficos(self, columnas_analisis: list) -> dict:
        """Genera gráficos para las columnas especificadas"""
        os.makedirs("graficos", exist_ok=True)
        
        for col in columnas_analisis:
            if col not in self.df.columns:
                continue
                
            output_path = f"graficos/{col}.png"
            
            if pd.api.types.is_numeric_dtype(self.df[col]):
                path = generar_histograma_r(self.df, col, output_path)
                if path:
                    self.graficos[col] = {'tipo': 'histograma', 'path': path}
                    
                # Gráfico adicional si hay una columna categórica adecuada
                categoricas = [c for c in self.df.columns 
                             if pd.api.types.is_categorical_dtype(self.df[c]) 
                             or pd.api.types.is_object_dtype(self.df[c])]
                if categoricas and len(self.df[categoricas[0]].unique()) <= 10:
                    path = generar_boxplot_r(self.df, col, categoricas[0], f"graficos/{col}_by_{categoricas[0]}.png")
                    if path:
                        self.graficos[f"{col}_by_{categoricas[0]}"] = {'tipo': 'boxplot', 'path': path}
            else:
                path = generar_barras_r(self.df, col, output_path)
                if path:
                    self.graficos[col] = {'tipo': 'barras', 'path': path}
        
        return self.graficos
    
    def resumen_analisis(self) -> dict:
        """Genera un resumen estructurado del análisis"""
        return {
            'metadata': self.metadata,
            'estadisticas': {
                'filas': len(self.df),
                'columnas': len(self.df.columns),
                'columnas_con_nulos': sum(1 for col in self.nulos_por_columna if col['total_nulos'] > 0),
                'columnas_completas': sum(1 for col in self.nulos_por_columna if col['total_nulos'] == 0)
            },
            'nulos_por_columna': self.nulos_por_columna,
            'graficos_generados': list(self.graficos.keys()),
            'rutas': {
                'reporte': self.reporte_path,
                'graficos': {k: v['path'] for k, v in self.graficos.items()}
            }
        }


def analisis_completo(file_path: str, columnas_analisis: list = None):
    """Función principal para ejecutar análisis completo"""
    analizador = AnalizadorDatos(file_path)
    
    if not analizador.cargar_datos():
        return None
    
    # Si no se especifican columnas, usar las que tienen menos del 50% de nulos
    if not columnas_analisis:
        columnas_validas = [
            col['nombre_columna'] for col in analizador.nulos_por_columna 
            if col['porcentaje_nulos'] < 50
        ]
        columnas_analisis = columnas_validas  # Limitar a 5 columnas por defecto
    
    # Generar outputs
    analizador.generar_reporte()
    analizador.generar_graficos(columnas_analisis)
    
    # Imprimir reporte de nulos en consola
    print(analizador.generar_reporte_nulos())
    
    return analizador.resumen_analisis()


if __name__ == "__main__":
    # Ejemplo de uso con análisis mejorado de nulos
    resumen = analisis_completo(
        file_path="Grammy Award Nominees and Winners 1958-2024.csv"
    )
    
    if resumen:
        print("\n=== RESUMEN GENERAL ===")
        print(f"Columnas con nulos: {resumen['estadisticas']['columnas_con_nulos']}")
        print(f"Columnas completas: {resumen['estadisticas']['columnas_completas']}")
        
        print("\nTop 5 columnas con más nulos:")
        for col in resumen['nulos_por_columna'][:5]:
            print(f"- {col['nombre_columna']}: {col['porcentaje_nulos']}% nulos")