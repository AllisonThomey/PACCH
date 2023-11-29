#file for making fathom vulnerable population bar charts
library(tidyverse)
library(ggplot2)

folder <- dirname(rstudioapi::getSourceEditorContext()$path)

data_fath <- read.csv(file.path('data', 'processed', 'BGD', 'fathom', 'csv', 
"FU_1in1000(1).{}", "v2_vul_pop.csv" ))

# Grouped
ggplot(data_fath, aes(fill=fath_pop, y=fath_pop, x=gid_id)) + 
    geom_bar(position="dodge", stat="identity")

path = file.path('data', 'processed', 'results', 'v2_fath_plot.png' )
ggsave(path)