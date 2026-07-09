library(DBI)
library(odbc)

# Solo esto en la consola de R:
con <- dbConnect(odbc::odbc(),
    dsn = "Postgres_IA",
    uid = "postgres",
    pwd = "cure_1982"
)

print(dbListTables(con))
