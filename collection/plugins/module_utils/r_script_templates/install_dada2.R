args <- commandArgs(TRUE)
p <- args[1]
c <- args[2]

.libPaths(p)

install.packages("BiocManager", lib = p, repos = "http://cran.us.r-project.org", dependencies = TRUE)
library("BiocManager", lib.loc=p)
install.packages("Rcpp", lib = p, repos = "http://cran.us.r-project.org", dependencies = TRUE)
install.packages("ggplot2", lib = p, repos = "http://cran.us.r-project.org", dependencies = TRUE)
install.packages("reshape2", lib = p, repos = "http://cran.us.r-project.org", dependencies = TRUE)
install.packages("RcppParallel", lib = p, repos = "http://cran.us.r-project.org", dependencies = TRUE)
update.packages(checkBuilt = TRUE, lib = p, repos = "http://cran.us.r-project.org")
install.packages("RCurl", lib = p, repos = "http://cran.us.r-project.org", dependencies = TRUE)
BiocManager::install(c("Biostrings", "ShortRead", "IRanges", "XVector", "BiocGenerics"), lib = p)
update.packages(checkBuilt = TRUE, lib = p)
#install.packages(c, lib = p, repos = NULL, type = "source", dependencies = c("Depends"))
install.packages(c, lib = p, repos = NULL, type = "source", dependencies = c("Depends"))
