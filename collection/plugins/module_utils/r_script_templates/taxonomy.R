args <- commandArgs(TRUE)
p <- args[1]
.libPaths(p)
library("dada2");
packageVersion("dada2")
# Merge multiple runs (if necessary)
st <- readRDS(args[2])
# Remove chimeras
seqtab2 <- st[,nchar(colnames(st)) %in% 50:500]
seqtab <- removeBimeraDenovo(seqtab2, method=args[3], multithread=TRUE)
# Assign taxonomy
tax <- assignTaxonomy(seqtab, args[4], multithread=FALSE)
# Write to disk
write.csv(seqtab, args[5])
write.csv(tax, args[6])
#saveRDS(seqtab, args[7])
#saveRDS(tax, args[8])
