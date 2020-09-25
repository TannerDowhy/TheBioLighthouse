args <- commandArgs(TRUE)
p <- args[1]
.libPaths(p)
#library("dada2", lib.loc=p);
library("dada2")
packageVersion("dada2")
# Path setup
path <- args[2]
filt_path <- file.path(path, "filtered")
merged_files <- list.files(path, pattern=args[3])
filterAndTrim(file.path(path, merged_files), file.path(filt_path, merged_files), rm.phix=FALSE, truncLen=as.integer(args[4]),  multithread=TRUE)

filts <- list.files(filt_path, pattern=args[3], full.names=TRUE)
sample.names <- sapply(strsplit(basename(filts), args[5]), `[`, 1)
names(filts) <- sample.names

# Learn the errors
set.seed(as.integer(args[6]))
err_merged <- learnErrors(filts, nbases=as.integer(args[7]), MAX_CONSIST=as.integer(args[8]), multithread=TRUE, randomize=TRUE)

dds <- vector("list", length(sample.names))
names(dds) <- sample.names

#dadaF <- dada(filts, err=err_merged, multithread=TRUE)

for(sam in sample.names) {
    cat("Processing:", sam, "\n")
    derep <- derepFastq(filts[[sam]])
    dds[[sam]] <- dada(derep, err=err_merged, multithread=TRUE)
}
# Construct sequence table and write to disk
seqtab <- makeSequenceTable(dds)
collapseNoMismatch(seqtab)

write.csv(seqtab, file=args[9])
saveRDS(seqtab, args[10])
