# just set the  filename variable to 'packets_timestamp' prefix of the test files, to get them to load

capture = read.csv(file=paste(filename, "capture.csv", sep='_'), header=FALSE)
timestamp = read.csv(file=paste(filename, "timestamp.csv", sep='_'), header=FALSE)
capture.m = as.matrix(capture)
timestamp.m = as.matrix(timestamp)


stat.tests <- function(data){
  r1 = c()
  r2 = c()
  for (i in c(1:length(data[,1]))){
    r1[i] = wilcox.test(data[2,], data[i,])$p.value
    r2[i] = ks.test(data[2,], data[i,])$p.value
    }

  res1 = which(unlist(r1) < 0.05/(length(data[,1])-1))
  res2 = which(unlist(r2) < 0.05/(length(data[,1])-1))
  print(r1)
  print(res1)
  print(r2)
  print(res2)
}

plot.mean.median.box <- function(capture.m, timestamp.m, sanity=FALSE, save=FALSE){
  X11(bg="white")
  par(mfrow=c(2,3))
  if(sanity){
    xnames <- c('GOOD', 'GOOD', 'GOOD')
  } else{
    xnames <- c('GOOD', 'BAD', 'BAAD')
  }
  boxplot(t(capture.m), main="Capture timestamp", names=xnames)
  barplot(rowMeans(capture.m, na.rm=TRUE), main="Capture timestamp mean", names=xnames)
  barplot(rowMedians(capture.m, na.rm=TRUE), main="Capture timestamp median", names=xnames)
  boxplot(t(timestamp.m), main="TCP timestamp", names=xnames)
  barplot(rowMeans(timestamp.m, na.rm=TRUE), main="TCP timestamp mean", names=xnames)
  barplot(rowMedians(timestamp.m, na.rm=TRUE), main="TCP timestamp median", names=xnames)

  if(save){
    dev.copy(png,filename=paste(filename, "boxplot_mean_avg.png",sep='_'), width=1200, height=800)
    dev.off()
  }
}


plot.cdf <- function(data, sanity=FALSE, save=FALSE){
  X11(bg="white")
  if(sanity){
    names <- c('GOOD', 'GOOD', 'GOOD')
    par(mfrow=c(2,2))
  } else{
    par(mfrow=c(1,3))
    names <- c('GOOD', 'BAD', 'BAAD')
  }


  # Set colors for the CDF.
  aCDFcolor <- rgb(0,1,0)
  bCDFcolor <- rgb(0,0,1)
  cCDFcolor <- rgb(1,0,0)
  colors <- c(aCDFcolor, bCDFcolor, cCDFcolor)

  # Plot CDFs in separate plots
  for (i in c(1:length(data[,1])))
  {
    plot(ecdf(data[i,]), col=colors[i], main=paste(names[i],'CDF'), xlim=c(min(data[i,]),quantile(data[i,],0.99)))
  }
  if (sanity)
  {
    # Create a single chart with all 3 CDF plots for sanity check.
    plot(ecdf(data[1,]), col=aCDFcolor, main=NA, xlim=c(min(data),quantile(data,0.99)))
    plot(ecdf(data[2,]), col=bCDFcolor, add=T)
    plot(ecdf(data[3,]), col=cCDFcolor, add=T)

    # Add a legend to the chart.
    legend('right', names, fill=colors, border=NA)
  }
  if(save){
    height = 400
    if(sanity)
    {
      height = 1200
    }
    dev.copy(png,filename=paste(filename, "cdf.png",sep='_'),width=1200,height=height)
    dev.off()
  }
}

plot.qq.normal <- function(data, sanity=FALSE, save=FALSE){
  X11(bg="white")
  par(mfrow=c(1,3))

  if(sanity){
    names <- c('GOOD', 'GOOD', 'GOOD')
  } else{
    names <- c('GOOD', 'BAD', 'BAAD')
  }

  for (i in c(1:length(data[,1]))){
    qqnorm(data[i,], pch = 1, frame = FALSE, main=names[i], ylim=c(min(data[i,]),quantile(data[i,],0.99)))
    qqline(data[i,], col = "steelblue", lwd = 2)
  }

  if(save){
    dev.copy(png,filename=paste(filename, "qqplot.png",sep='_'), width=1200,height=400)
    dev.off()
  }
}

runmedx <- function(data,x=1,k=3)
{
  for (runs in c(1:x)){
    for (i in c(1:length(data[,1]))){
      data[i,] <- runmed(data[i,],k=k)
    }
  }
  return(data)
}

plot.levelplot <- function(data, save=FALSE){
  X11()
  h <- hist(data, breaks=200,plot=FALSE)
  breaks = c(h$breaks)
  mids = c(h$mids)
  hm <- rbind(hist(data[1,], breaks=breaks, plot=FALSE)$counts)
  for (i in c(2:length(data[,1]))) {
    hm <- rbind(hm, hist(data[i,], breaks=breaks, plot=FALSE)$counts)}
  
  d = data.frame(x=rep(seq(1, nrow(hm), length=nrow(hm)), ncol(hm)),
                y=rep(mids, each=nrow(hm)),
                z=c(hm))
  levelplot(z~x*y, data=d, xlab="Query", ylab="time (s)",ylim=c(min(data), quantile(data, 0.99)))

  if(save){
    dev.copy(png,filename=paste(filename, "levelplot.png",sep='_'), width=900,height=900)
    dev.off()
  }
}

show.quantile <- function(data, q, sanity=FALSE){
  X11(bg="white")
  par(mfrow=c(1,3))

  if(sanity){
    names <- c('GOOD', 'GOOD', 'GOOD')
  } else{
    names <- c('GOOD', 'BAD', 'BAAD')
  }

  for (i in c(1:length(data[,1]))){
    plot(sort(data[i,]), main=names[i], ylim=c(min(data[i,]),quantile(data[i,],q)))

  }
}

box.test <- function(sample1, sample2, i, j){
  s1i = quantile(sample1, i)
  s1j = quantile(sample1, j)

  s2i = quantile(sample2, i)
  s2j = quantile(sample2, j)

  arr <- array(c(c(s1i,s2i),c(s1j,s2j)), dim=c(2,2))

  # select 'bigger' interval
  # assume s2 bigger
  smaller = 1
  bigger = 2
  if (s2i <= s1i){
    # s1 is bigger
    smaller = 2
    bigger = 1
  }

  cat("Sample 1: ",s1i,"-",s1j, "\n")
  cat("Sample 2: ",s2i,"-",s2j, "\n")


  if (arr[smaller,1] < arr[bigger,1] && arr[smaller,2] < arr[bigger,1]){
    return(bigger)
    cat("Sample ", bigger, " is bigger.\n")
  } else{
    cat("Samples are not statistically different.\n")
    return(FALSE)
  }
}

box.test.all <- function(data, i=0.0, j=0.05){
  # cross test all samples
  cat("1 vs 2 - ", box.test(data[1,], data[2,], i, j), "\n")
  cat("1 vs 3 - ", box.test(data[1,], data[3,], i, j), "\n")
  cat("2 vs 3 - ", box.test(data[2,], data[3,], i, j), "\n")
}

ks.test.all <- function(data){
  # cross test all samples
  cat("1 vs 2 - ", suppressWarnings(ks.test(data[1,], data[2,])$p.value), "\n")
  cat("1 vs 3 - ", suppressWarnings(ks.test(data[1,], data[3,])$p.value), "\n")
  cat("2 vs 3 - ", suppressWarnings(ks.test(data[2,], data[3,])$p.value), "\n")
}


self.test <- function(data, i=0.0, j=0.05){
  # self test by splitting in half
  l =  length(data)
  mid = length(data) %/% 2
  cat("K-S test: ",suppressWarnings(ks.test(data[0:mid], data[mid:l])$p.value), "\n")
  cat("Wilcox test: ",wilcox.test(data[0:mid], data[mid:l])$p.value, "\n")
  cat("Box test:\n")
  box.test(data[0:mid], data[mid:l], i, j)
}

self.test.all <- function(data,i=0.0, j=0.05){
  for (x in c(1:length(data[,1]))){
    cat("Sample ",x,":\n")
    self.test(data[x,], i, j)
    cat("\n")
  }
}

scatter.plot <- function(data, sanity=FALSE){
  if(sanity){
    names <- c('GOOD', 'GOOD', 'GOOD')
  } else{
    names <- c('GOOD', 'BAD', 'BAAD')
  }
  for (i in c(1:length(data[,1]))){
    X11()
    plot(data[i,], main=paste(names[i]," (batch ",i,")",sep=''), ylim=c(quantile(data[i,],0.1),quantile(data[i,],0.98)))
  }
}

save.everything <- function(data, sanity=FALSE){
  plot.qq.normal(data, sanity=sanity, save=TRUE)
  plot.cdf(data, sanity=sanity, save=TRUE)
  plot.levelplot(data, save=TRUE)
}