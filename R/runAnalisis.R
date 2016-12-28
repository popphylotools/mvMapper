library(adegenet)

Rosenberg <- read.structure("Rosenberg_783msats.str", n.ind=1048, n.loc=783,  onerowperind=F, col.lab=1, col.pop=2, col.others=c(3:5), row.marknames=NULL, NA.char="-9", ask=FALSE, quiet=FALSE)

dapc1 <-dapc(Rosenberg, n.pca=20, n.da=200)

saveRDS(dapc1, file="./data/dapc.rds")
