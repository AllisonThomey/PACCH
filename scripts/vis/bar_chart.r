library(tidyverse)

folder <- dirname(rstudioapi::getSourceEditorContext()$path)
data <- read.csv(file.path('data', 'processed', 'results', 'csv', 'global_vul_pop.csv'))


#  #then plot
print(data)

ggplot(data, aes(fill=iso3, y=pop_est, x=income_group)) + 
    geom_bar(position="stack", stat="identity")


path = file.path('data', 'processed', 'results', 'test_plot.png' )
ggsave(path)