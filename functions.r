# just set the  filename variable to 'packets_timestamp' prefix of the test files, to get them to load
library('data.table')
library('matrixStats')

get.data <- function(filename){
  capture = fread(file=paste(filename, ".csv", sep=''), header=FALSE)
  return(as.matrix(capture))
}


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
  par(mfrow=c(2,2))
  if(sanity){
    names <- c('GOOD', 'GOOD', 'GOOD')
  } else{
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
  #if (sanity)
  #{
    # Create a single chart with all 3 CDF plots for sanity check.
    plot(ecdf(data[1,]), col=aCDFcolor, main=NA, xlim=c(min(data),quantile(data,0.99)))
    plot(ecdf(data[2,]), col=bCDFcolor, add=T)
    plot(ecdf(data[3,]), col=cCDFcolor, add=T)

    # Add a legend to the chart.
    legend('right', names, fill=colors, border=NA)
  #}
  if(save){
    dev.copy(png,filename=paste(filename, "cdf.png",sep='_'),width=1200,height=1200)
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
  require("lattice")
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
  # generate all combinations for the data
  v = c(1:length(data[,1]))
  combinations = t(combn(v, 2))
  ret = c()
  for (i in c(1:length(combinations[,1]))){
    pval = suppressWarnings(ks.test(data[combinations[i,1],], data[combinations[i,2],])$p.value)
    cat(combinations[i,1]," vs ",combinations[i,2]," - ", pval, "\n")
    ret <- c(ret,pval)
  }
  return(ret)
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

scatter.plot <- function(data, sanity=FALSE, save=FALSE){
  if(sanity){
    names <- c('GOOD', 'GOOD', 'GOOD')
  } else{
    names <- c('GOOD', 'BAD', 'BAAD')
  }
  for (i in c(1:length(data[,1]))){
    X11(bg="white")
    plot(data[i,], main=paste(names[i]," (batch ",i,")",sep=''), ylim=c(quantile(data[i,],0.1),quantile(data[i,],0.98)))
    if(save){
      dev.copy(png,filename=paste(filename, "_scatter_",names[i],"_",i,".png",sep=''), width=1920,height=1080)
      dev.off()
    }
  }
}

get.interval <- function(data, i, j){
  data = sort(data)
  return(split(data, cut(data, breaks = quantile(data,c(i,j)), include.lowest=TRUE, labels="interval"))$interval)
}

save.everything <- function(data, sanity=FALSE){
  plot.qq.normal(data, sanity=sanity, save=TRUE)
  plot.cdf(data, sanity=sanity, save=TRUE)
  plot.levelplot(data, save=TRUE)
  scatter.plot(data, sanity=sanity, save=TRUE)
}

compare.percentiles <- function(a,b, samples=1000, start=0, end=1, e=0){
  cat("P - A vs B -> greater\n")
  a= sort(a)
  b=sort(b)
  a_count = 0  
  b_count = 0
  a_diff = 0
  b_diff = 0
  e_count = 0
  for(i in c(1:samples)){
    p = start + (i*(end-start))/samples
    qa = quantile(a,p)
    qb = quantile(b,p)
    gt = "A"
    if(qa == qb){
      gt = "A==B"
    }
    else if(abs(qa-qb) - e <= 0){
      #account for accuraccy adjustment
      e_count = e_count + 1
      gt = "A==B"
    }
    else if(qa < qb){
      gt="B"
      b_count = b_count +1
      b_diff = b_diff + abs(qa-qb)
    }
    else{
      a_count = a_count + 1
      a_diff = a_diff + abs(qa-qb)
    }
    
    cat(p, " - ", qa, " vs. ", qb," -> ",gt,"\n")
  }
  a_pct = a_count/(a_count+b_count)
  b_pct = b_count/(a_count+b_count)
  cat("A: ", a_pct, " B:", b_pct," pct. tied",(samples-a_count-b_count)/samples,
  "\nScore", abs(a_pct-b_pct)*((a_count+b_count)/samples), "\n",
  samples, " quantile samples between quantiles ", start, " - ", end, "\n",
  "e adjustments: ", (e_count)/samples, "\n",
  "e adjusted score: ", abs(a_pct-b_pct)*((a_count+b_count+e_count)/samples), "\n")
}


percentile.filter <- function(data, down=0.1, up=0.9)
{
  ret = data[data > quantile(data, down)]
  return(ret[ret < quantile(ret,up)])
}

print.statistics <- function(data, down=0.1, up=0.9){
  cat("Unchanged data:\nMean\tMedian\n")
  for (i in c(1:length(data[,1]))){
      cat(mean(data[i,]),"\t", median(data[i,]),"\n")
  }

  cat("Filtered data (",down,"-",up,"):\nMean\tMedian\n")
  for (i in c(1:length(data[,1]))){
      cat(mean(percentile.filter(data[i,], down, up)),"\t", median(percentile.filter(data[i,], down, up)),"\n")
  }

}

pcf <- function(data, down=0.1, up=0.9){
  ret = data.table()
  for (i in c(1:length(data[,1]))){
    mod_data = percentile.filter(data[i,], down, up)
    ret = cbind(ret, append(mod_data, rep(NA, (length(data[1,]) - length(mod_data))), after=length(mod_data)))
  }
  return(t(ret))
}

profiling.check.errors <- function(data, down=0.1, up=0.9){
  v1 = ks.test.all(data)
  v2 = ks.test.all(pcf(data,down, up))
  combinations = combn(c(1:length(data[,1])), 2)
  
  cat("FN for unaltered data: ", length(v1[v1 < 0.05])/length(combinations[1,]), "\n")
  cat("FN for filtered data (",down,"-",up,"): ", length(v2[v2 < 0.05])/length(combinations[1,]), "\n")
}


get.data.cross <- function(set1, set2, different=TRUE){
  # generates FN/FP statistics for two sets.
  stopifnot("Both sets must have the same number of rows" = length(set1[,1]) == length(set2[,1]))

  combinations = expand.grid(rep(list(1:length(set1[,1])), 2))
  ret = c()
  for (i in c(1:length(combinations[,1]))){
    pval = suppressWarnings(ks.test(set1[combinations[i,1],], set2[combinations[i,2],])$p.value)
    cat(combinations[i,1]," vs ",combinations[i,2]," - ", pval, "\n")
    ret <- c(ret,pval)
  }
  if(different){
    # looking at wrongly pointed out "same distribution" - 
    cat("FN:", length(ret [ret > 0.05])/length(combinations[,1]), "\n")
  }
  else{
    # looking at wrongly pointed out "different distributions"
    cat("FP:", length(ret [ret <= 0.05])/length(combinations[,1]), "\n")
  }
  return(ret)

}

merge.data <- function(set1, set2){
  ret = t(set1)
  set2 = t(set2)
  for (i in c(1:length(set2[1,]))){
    ret = cbind(ret, set2[,i])
  }

  return(ret)
}