args <- commandArgs(TRUE)
p <- args[1]

.libPaths(p)

#source('http://bioconductor.org/biocLite.R', local=TRUE)
#biocLite()
#biocLite('dada2')

install.packages("BiocManager", lib = p, repos = "http://cran.us.r-project.org", dependencies = TRUE)
library("BiocManager", lib=p)
BiocManager::install(c("Biostrings", "ShortRead", "IRanges", "XVector", "BiocGenerics"), lib = p, ask=FALSE)

BiocManager::install("dada2", lib=p, ask=FALSE)
