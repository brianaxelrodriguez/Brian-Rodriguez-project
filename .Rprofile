# --- LABORATORIO IA: INICIO OPTIMIZADO ---
if (interactive()) {
  suppressMessages({
    library(DBI)
    library(odbc)
  })
  
  traer_sql <- function(tabla, limite = 1000) {
    con <- dbConnect(odbc::odbc(), dsn = "Postgres_IA", pwd = "cure_1982")
    df <- dbGetQuery(con, paste0("SELECT * FROM ", tabla, " LIMIT ", limite))
    dbDisconnect(con)
    return(df)
  }
  
  cat("\n--- LABORATORIO IA VINCULADO (Modo Interactivo) ---\n")
}
