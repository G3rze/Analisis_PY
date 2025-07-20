import os
import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.packages import importr
import matplotlib.pyplot as plt

# Configuración de temas y estilos en R
def configurar_estilos_r():
    """Configura temas y estilos globales para ggplot2"""
    ro.r("""
    library(ggplot2)
    library(RColorBrewer)
    
    # Tema personalizado
    tema_personalizado <- theme_minimal() +
        theme(
            text = element_text(family = "sans", size = 12),
            plot.title = element_text(size = 16, face = "bold", hjust = 0.5),
            plot.subtitle = element_text(size = 12, hjust = 0.5),
            axis.title = element_text(face = "bold"),
            legend.position = "top",
            panel.grid.major = element_line(color = "gray90"),
            panel.grid.minor = element_blank(),
            plot.margin = unit(c(1, 1, 1, 1), "cm")
        )
    
    # Paleta de colores
    colores <- brewer.pal(8, "Set2")
    """)

# Configurar estilos al importar el módulo
configurar_estilos_r()

def generar_histograma_r(df: pd.DataFrame, columna: str, output_path: str) -> str:
    """
    Genera un histograma estilizado con ggplot2
    """
    try:
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_df = ro.conversion.py2rpy(df[[columna]])
        
        ro.r(f"""
        library(ggplot2)
        p <- ggplot({r_df.r_repr()}, aes(x={columna})) +
            geom_histogram(
                binwidth = diff(range({r_df.r_repr()}${columna}, na.rm=TRUE))/30,
                fill = "#2c7fb8", 
                color = "#ffffff", 
                alpha = 0.8
            ) +
            labs(
                title = "Distribución de {columna}",
                x = "{columna}",
                y = "Frecuencia"
            ) +
            tema_personalizado +
            scale_fill_brewer(palette = "Set2")
        
        ggsave(
            filename = "{output_path}",
            plot = p,
            width = 10,
            height = 6,
            dpi = 300
        )
        """)
        
        return output_path if os.path.exists(output_path) else None
    
    except Exception as e:
        print(f"Error al generar histograma: {e}")
        return None


def generar_barras_r(df: pd.DataFrame, columna: str, output_path: str) -> str:
    """
    Genera gráfico de barras para variables categóricas
    """
    try:
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_df = ro.conversion.py2rpy(df[[columna]])
        
        ro.r(f"""
        library(ggplot2)
        library(dplyr)
        
        top_data <- {r_df.r_repr()} %>%
            group_by({columna}) %>%
            summarise(count = n()) %>%
            arrange(desc(count)) %>%
            head(10)
        
        p <- ggplot(top_data, aes(
                x = reorder({columna}, count), 
                y = count,
                fill = {columna}
            )) +
            geom_bar(stat = "identity") +
            coord_flip() +
            labs(
                title = "Top 10 categorías en {columna}",
                x = "",
                y = "Conteo"
            ) +
            tema_personalizado +
            scale_fill_brewer(palette = "Set2") +
            theme(legend.position = "none")
        
        ggsave(
            filename = "{output_path}",
            plot = p,
            width = 10,
            height = 6,
            dpi = 300
        )
        """)
        
        return output_path if os.path.exists(output_path) else None
    
    except Exception as e:
        print(f"Error al generar gráfico de barras: {e}")
        return None


def generar_boxplot_r(df: pd.DataFrame, columna: str, grupo: str, output_path: str) -> str:
    """
    Genera boxplot comparativo por grupos
    """
    try:
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_df = ro.conversion.py2rpy(df[[columna, grupo]])
        
        ro.r(f"""
        p <- ggplot({r_df.r_repr()}, aes(
                x = {grupo}, 
                y = {columna},
                fill = {grupo}
            )) +
            geom_boxplot(
                alpha = 0.7,
                outlier.color = "#e34a33"
            ) +
            labs(
                title = "Distribución de {columna} por {grupo}",
                x = "{grupo}",
                y = "{columna}"
            ) +
            tema_personalizado +
            scale_fill_brewer(palette = "Set2") +
            theme(axis.text.x = element_text(angle = 45, hjust = 1))
        
        ggsave(
            filename = "{output_path}",
            plot = p,
            width = 10,
            height = 6,
            dpi = 300
        )
        """)
        
        return output_path if os.path.exists(output_path) else None
    
    except Exception as e:
        print(f"Error al generar boxplot: {e}")
        return None