import os
import pandas as pd
from ydata_profiling import ProfileReport
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.packages import importr
import tempfile
import matplotlib.pyplot as plt

# Configurar la carpeta para gráficos
os.makedirs("graphics", exist_ok=True)

def generar_grafico_python(df, columna, path):
    """Alternativa usando matplotlib"""
    try:
        plt.figure(figsize=(10, 6))
        
        if pd.api.types.is_numeric_dtype(df[columna]):
            plt.hist(df[columna].dropna(), bins=30, color='steelblue', edgecolor='black')
            plt.title(f"Histograma de {columna}")
        else:
            top_10 = df[columna].value_counts().nlargest(10)
            top_10.sort_values().plot(kind='barh', color='steelblue')
            plt.title(f"Top 10 categorías de {columna}")
        
        plt.tight_layout()
        plt.savefig(path)
        plt.close()
        return path
    except Exception as e:
        print(f"Error al generar gráfico con matplotlib: {e}")
        return None

def generar_grafico_r(df, columna, path):
    """Generar gráfico usando R (versión actualizada)"""
    try:
        # Importar paquetes R
        grdevices = importr("grDevices")
        ggplot2 = importr("ggplot2")
        
        # Convertir DataFrame a R usando el nuevo método
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_df = ro.conversion.py2rpy(df[[columna]])
        
        # Configurar dispositivo gráfico
        grdevices.png(file=path, width=800, height=600)
        
        # Generar gráfico según el tipo de dato
        if pd.api.types.is_numeric_dtype(df[columna]):
            ro.r(f"""
            p <- ggplot({r_df.r_repr()}, aes(x={columna})) +
                geom_histogram(binwidth=30, fill='steelblue', color='black') +
                ggtitle("Histograma de {columna}") +
                theme_minimal()
            print(p)
            """)
        else:
            ro.r(f"""
            top_data <- head(sort(table({r_df.r_repr()}${columna}), decreasing=TRUE), 10)
            top_df <- data.frame(Var1=names(top_data), Freq=as.integer(top_data))
            p <- ggplot(top_df, aes(x=reorder(Var1, Freq), y=Freq)) +
                geom_bar(stat="identity", fill='steelblue') +
                coord_flip() +
                ggtitle("Top 10 categorías de {columna}") +
                theme_minimal()
            print(p)
            """)
        
        grdevices.dev_off()
        return path if os.path.exists(path) else None
    except Exception as e:
        print(f"Error al generar gráfico con R: {e}")
        return None

def analizar_data(file, ver_descripcion, columna_grafico):
    if file is None:
        return "Sube un archivo .csv", None, None

    try:
        df = pd.read_csv(file)
        descripcion = df.describe(include='all').to_string() if ver_descripcion else ""
        
        grafico_path = "graphics/graphic.png"
        if columna_grafico in df.columns:
            # Primero intentar con R
            ruta_grafico = generar_grafico_r(df, columna_grafico, grafico_path)
            
            # Si falla R, usar Python
            if not ruta_grafico:
                ruta_grafico = generar_grafico_python(df, columna_grafico, grafico_path)
            
            grafico_path = ruta_grafico
        else:
            grafico_path = None

        # Crear reporte
        report_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False).name
        profile = ProfileReport(df, title="Reporte de perfilado", minimal=True)
        profile.to_file(report_file)
        print(df.columns)

        return descripcion, grafico_path, report_file

    except Exception as e:
        print(f"Error en analizar_data: {e}")
        return None, None, None

if __name__ == "__main__":
    file_path = "Grammy Award Nominees and Winners 1958-2024.csv"
    
    if os.path.exists(file_path):
        descripcion, ruta_grafico, ruta_reporte = analizar_data(
            file_path,
            ver_descripcion=True,
            columna_grafico="Award Name"
        )
        print("Descripción:\n", descripcion)
        print("Ruta gráfico:", ruta_grafico)
        print("Ruta reporte:", ruta_reporte)
        
    else:
        print(f"Archivo {file_path} no encontrado.")