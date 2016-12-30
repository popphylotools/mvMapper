dapc1 <- readRDS("./data/dapc.rds")

for (name in names(dapc1)[is.element(names(dapc1), list("assign", "eig", "ind.coord", "posterior", "grp"))]) { write.csv(dapc1[name], file = paste("./data/", name, ".csv", sep=""), na="") }