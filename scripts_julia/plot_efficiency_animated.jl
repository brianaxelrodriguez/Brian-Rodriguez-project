using RCall, DataFrames, CSV

# 1. Cargar y transformar Score (0 a 1)
path = "C:/Users/brian/Documents/Proyectos_IA/resultados_eficiencia_final.csv"
df_results = CSV.read(path, DataFrame)

# Invertimos el score: 1.0 es la frontera (max eficiencia), tendiendo a 0 es ineficiente
# Usamos el scoring de Farrell
df_results.eficiencia_farrell = 1.0 ./ df_results.eficiencia_dea

# 2. Enviar a R
@rput df_results

# 3. Bloque de R sin caracteres unicode (tildes/enie)
R"""
library(ggplot2)
library(gganimate)
library(ggrepel)

# Generar el grafico animado
p <- ggplot(df_results, aes(x = gasto_real_pcapita, y = tasa_mortalidad_mil, color = eficiencia_farrell)) +
  geom_point(aes(size = poblacion), alpha = 0.8) +
  geom_text_repel(aes(label = provincia), size = 4, max.overlaps = 10) +
  scale_color_gradient(low = "red", high = "green") +
  theme_minimal() +
  labs(
    title = "Evolucion Eficiencia Salud: Ano {frame_time}",
    subtitle = "Frontera DEA (0-1) | Gasto vs Mortalidad",
    x = "Gasto Real Per Capita",
    y = "Mortalidad (cada 1.000 hab)",
    color = "Eficiencia (Farrell)",
    size = "Poblacion"
  ) +
  transition_time(anio) +
  ease_aes('linear')

# Renderizar a GIF
anim_save("C:/Users/brian/Documents/Proyectos_IA/eficiencia_salud_animada.gif", 
          animation = animate(p, nframes = 100, fps = 5, width = 800, height = 600, renderer = gifski_renderer()))
"""

println("✅ ¡GIF Animado generado con score 0-1! Revisa 'eficiencia_salud_animada.gif'")