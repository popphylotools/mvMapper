library(adegenet)

dapc1 <- readRDS("dapc.txt")

for (name in names(dapc1)[is.element(names(dapc1), list("assign", "eig", "ind.coord", "posterior", "grp"))]) { write.csv(dapc1[name], file = paste(name, "csv", sep="."), na="") }