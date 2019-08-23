library('matrixStats')

# get filename
args = commandArgs(trailingOnly=TRUE)
if (length(args)==0) {
    stop('Filename prefix needs to be supplied', call.=FALSE)
}else {
    filename = args[1]
}

# read the data
capture = read.csv(file=paste(filename, "capture.csv", sep='_'), header=FALSE)
timestamp = read.csv(file=paste(filename, "timestamp.csv", sep='_'), header=FALSE)
capture.m = as.matrix(capture)
timestamp.m = as.matrix(timestamp)

# plot the differences between tcp timestamps and capture timestamps
png(file = paste(filename,"plot.png",sep='_'), width=800, height=800)
par(mfrow=c(2,3))
xnames = c("GOOD", "BAD", "BAAD")
boxplot(t(capture.m), main="Capture timestamp", names=xnames)
barplot(rowMeans(capture.m, na.rm=TRUE), main="Capture timestamp mean", names=xnames)
barplot(rowMedians(capture.m, na.rm=TRUE), main="Capture timestamp median", names=xnames)
boxplot(t(timestamp.m), main="TCP timestamp", names=xnames)
barplot(rowMeans(timestamp.m, na.rm=TRUE), main="TCP timestamp mean", names=xnames)
barplot(rowMedians(timestamp.m, na.rm=TRUE), main="TCP timestamp median", names=xnames)
dev.off()

# run tests on all parts against BAAD packets
r1 = c()
r2 = c()
for (i in c(1:length(capture.m[,1]))){
  r1[i] = wilcox.test(capture.m[3,], capture.m[i,])$p.value
  r2[i] = ks.test(capture.m[3,], capture.m[i,])$p.value}

res1 = which(unlist(r1) < 0.05/(length(capture.m[,1])-1))
res2 = which(unlist(r2) < 0.05/(length(capture.m[,1])-1))
print(res1)
print(res2)
