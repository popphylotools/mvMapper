library(adegenet)

bcur <- read.structure("world_bcur_97outliers.str", n.ind=224, n.loc=97,  onerowperind=F, col.lab=1, col.pop=2, col.others=c(3,4,5,6), row.marknames=NULL, NA.char="-9", ask=FALSE, quiet=FALSE)

dapc1 <-dapc(bcur, n.pca=20, n.da=200)

saveRDS(dapc1, file = "dapc.txt", ascii = TRUE, compress = FALSE)

for (name in names(dapc1)[is.element(names(dapc1), list("assign", "eig", "ind.coord", "posterior", "grp"))]) { write.csv(dapc1[name], file = paste(name, "csv", sep="."), na="") }