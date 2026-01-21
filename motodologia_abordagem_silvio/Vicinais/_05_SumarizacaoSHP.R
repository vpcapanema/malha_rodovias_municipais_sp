############ JUNCAO FACE DE LOGRADOUROS #######################################
# clear all
# if (!require('plotly')) {install.packages('plotly', dependencies = TRUE)}
rm(list=ls())
gc()
# packages
library(tidyverse)
library(sf)
library(sp)
library(readxl)
library(writexl)
# Directory
dirp <- getwd()

# Reading mun data
#DER <- sf::st_read(dsn = gsub(basename(dirp),'Div_reg',dirp), layer = 'LimiteMunicipal_SEADE', options = 'ENCODING=UTF-8', stringsAsFactors = FALSE)
SHPMUN <- sf::st_read(dsn = paste0(dirp,'/Div_reg'), layer = 'LimiteMunicipal_SEADE', options = 'ENCODING=UTF-8', stringsAsFactors = FALSE)
SHPDER <- sf::st_read(dsn = paste0(dirp,'/Rodovias Municipais_20250516'), layer = 'Rodovias_municipais_wgsutm23s_intesect_mun', options = 'ENCODING=UTF-8', stringsAsFactors = FALSE)
SHPOSM <- sf::st_read(dsn = paste0(dirp), layer = '_04_DER_AU_FL_SP_OSM_wgs84Utm23s', options = 'ENCODING=UTF-8', stringsAsFactors = FALSE)
# Getting list 

MUN <- data.frame(Cod_ibge=SHPMUN$Cod_ibge, Municipio=SHPMUN$Municipio, GID_RA=SHPMUN$GID_RA, RA=SHPMUN$RA, Area_Km2=SHPMUN$Area_Km2)
DER <- data.frame(Cod_ibge=SHPDER$Cod_ibge, metros=SHPDER$metros)
DER$cont <- 1
DER1 <- aggregate(DER[c('metros','cont')], by = list(DER$Cod_ibge), FUN = 'sum')

OSM <- data.frame(Cod_ibge=SHPOSM$Cod_ibge, metros=SHPOSM$metros, area_urb=SHPOSM$area_urb, malha_der=SHPOSM$malha_der)
  # manter apenas rodovias fora da area uraban (area_urb=0) e da faixa de dominio das rodovias (malha_der=0)
OSM1 <- OSM[(OSM$area_urb==0 & OSM$malha_der==0),]
OSM1$cont <- 1
OSM2 <- aggregate(OSM1[c('metros','cont')], by = list(OSM1$Cod_ibge), FUN = 'sum')

MUN1 <- merge(MUN, DER1, by.x='Cod_ibge', by.y='Group.1', all.x=TRUE)
colnames(MUN1)[c(6,7)]<-c('Vic_DER_metros','Vic_DER_qtde')
MUN1 <- merge(MUN1, OSM2, by.x='Cod_ibge', by.y='Group.1', all.x=TRUE)
colnames(MUN1)[c(8,9)]<-c('Vic_OSM_metros','Vic_OSM_qtde')


# Save excel
lista_tabelas <- list("DER_vs_OSM" = MUN1)
write_xlsx(lista_tabelas, paste0(dirp,'/_06_Comparacao_DER_vs_OSM.xlsx'))



