# Preliminaries
#-------------------------------------------------
rm(list = ls())
setwd("./projects/opentable")

library(tidyverse)
library(rgl)
library(nat)
library(viridisLite)
library(viridis)
library(hrbrthemes)
library(lubridate)

openings_df <- read.csv('output/2020-12-03_YoY_Seated_Diner_Data_Cleaned.csv',stringsAsFactors = FALSE)
openings_df$date_c <- as.Date(openings_df$date, format='%Y-%m-%d')
#library(esquisse)
#options("esquisse.display.mode" = "browser")
# & (openings_df$localityPosition<4)

#69b3a2
country = 'Mexico'
data = openings_df[(openings_df$isDateAfterMarch == 'Yes') ,]
maxCutOffDate = max(data$date)
minCutOffDate = min(data$date)
data = data[data$country==country, ]
#data$date = as.Date(data$date, format = "%m/%d/%Y")
#str(data)
# limit=c(as.Date("2020-04-01"), as.Date(as.Date("2020-10-31")))
#69b3a2
#FF3368
#FF33BB

tmp <- data %>%
  mutate(locality2=locality)

tmp %>%
  ggplot(aes(x=date_c, y=openingRate, group = 1)) +
    geom_line( data=tmp %>% dplyr::select(-locality), aes(group=locality2), color="grey", size=0.5, alpha=0.5) +
    geom_line( aes(color=locality), color="#FF3368", size=.4)+
    #geom_label(data=data%>%filter(over_sell_date=='Yes'), aes(label=date))+
    scale_color_viridis(discrete = TRUE) +
    theme_ipsum() + 
    theme(
      legend.position="none",
      plot.title = element_text(size=14),
      panel.grid = element_blank()
    ) +
    scale_x_date(breaks = as.Date(c(minCutOffDate, maxCutOffDate)), position='top', date_labels = '%b %d') +
    ggtitle("") +
    facet_wrap(~locality)

    
