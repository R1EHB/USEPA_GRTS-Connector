## "C:\Users\ebeck\OneDrive - Environmental Protection Agency (EPA)\Sync4OneDrive\GRTS2025\GRTS-R-Pull-V2\DataOutput\HUC-NewEng-test.pandas.xlsx"
##
##
## Using panda generated version of excel


## total_319_funds	project_dollars	program_dollars	epa_other
## other_federal	state_funds	state_in_kind	local_funds
## other_funds	local_in_kind	total_budget


library(skimr)

library(readxl)
library(dplyr)
library(vioplot)
library(lubridate)
library(readr)
library(openxlsx)
library(feather)
library(ggplot2)


infile <- '../DataOutput/GRTS-Data-NewEng-byHUC.pandas.xlsx'

R_outfile <- '../DataOutput/HUC-NewEng-cleaned.Rdata'
F_outfile <- '../DataOutput/HUC-NewEng-cleaned.feather'
Ex_outfile <-'../DataOutput/HUC-NewEng-cleaned.xlsx'

GRTS_df <- read_excel(path=infile)


## Drop out NY State which was kept for debugging purposes in an earlier step

GRTS_df <- subset(GRTS_df, state!="NY")

## Fix Name for first column

colnames(GRTS_df)[1] <- 'data_seq'

## Key type Conversions

GRTS_df$project_start_date <- mdy(GRTS_df$project_start_date)


GRTS_df$n_lbsyr <- as.numeric(GRTS_df$n_lbsyr)
GRTS_df$p_lbsyr <- as.numeric(GRTS_df$p_lbsyr)
GRTS_df$sed_tonsyr <- as.numeric(GRTS_df$sed_tonsyr)
GRTS_df$FakeHUC <- as.numeric(GRTS_df$huc_12)
GRTS_df$total_319_funds <- parse_number(GRTS_df$total_319_funds)
GRTS_df$project_dollars <- parse_number(GRTS_df$project_dollars)
GRTS_df$program_dollars <- parse_number(GRTS_df$program_dollars)
GRTS_df$epa_other <- parse_number(GRTS_df$epa_other)
GRTS_df$other_federal <- parse_number(GRTS_df$other_federal)
GRTS_df$state_funds <- parse_number(GRTS_df$state_funds)
GRTS_df$state_in_kind <- parse_number(GRTS_df$state_in_kind)
GRTS_df$local_funds <- parse_number(GRTS_df$local_funds)
GRTS_df$other_funds <- parse_number(GRTS_df$other_funds)
GRTS_df$local_in_kind <- parse_number(GRTS_df$local_in_kind)
GRTS_df$total_budget <- parse_number(GRTS_df$total_budget)

skim(GRTS_df)
print (min (GRTS_df$n_lbsyr, na.rm=TRUE))
print (min (GRTS_df$p_lbsyr, na.rm=TRUE))
print (min (GRTS_df$sed_tonsyr, na.rm=TRUE))

x_origin <- year (ymd(19960101))
x_end <- year (ymd(20260101))

year_date <- year(GRTS_df$project_start_date)

GRTS_df$year_date <- year_date

plot(year_date,GRTS_df$n_lbsyr,log="y",xlim=c(x_origin, x_end),
     ylim=c(0.1,110000), main="lbs N per Year Reduced log10",
     xlab="Year", ylab= "lbs N")

# head(GRTS_df[,27:34])


ggplot (data=subset(GRTS_df,n_lbsyr>0.000001), aes(y=log10(n_lbsyr), x=approp_year)) +
    geom_point(aes(color=state)) +xlim (1996,2025) +
    ylim(-2,6) +
    labs(title = "lbs N per Year Reduced Log10", subtitle= "By state")

hist (log10(GRTS_df$n_lbsyr), main="N Reductions lbs / Year Per Project Histogram",
      xlab="Log N Reductions (10^x)", xlim=c(-6,6))

# boxplot (GRTS_df$n_lbsyr, main ="N boxplot")


plot(year_date,GRTS_df$p_lbsyr,log="y",xlim=c(x_origin, x_end),
     ylim=c(0.1,110000), main="lbs P per Year Reduced log10",
     xlab="Year", ylab= "lbs P")

ggplot (data=subset(GRTS_df,p_lbsyr>0.000001), aes(y=log10(p_lbsyr), x=approp_year)) +
    geom_point(aes(color=state)) +xlim (1996,2025) +
    ylim(-2,5) +
    labs(title = "lbs P per Year Reduced Log10", subtitle= "By state")


hist (log10(GRTS_df$p_lbsyr), main="P Reductions lbs / Year Per Project Histogram",
      xlab="Log P Reductions (10^x)", xlim=c(-4.5,4.5))

# boxplot (GRTS_df$p_lbsyr, main ="P boxplot")

plot(year_date,GRTS_df$sed_tonsyr,log="y",xlim=c(x_origin, x_end),
     ylim=c(0.1,110000), main="Tons Sediment per Year Reduced log10",
     xlab="Year", ylab= "Tons Sediment")

ggplot (data=subset(GRTS_df,sed_tonsyr>0.000001), aes(y=log10(sed_tonsyr), x=approp_year)) +
    geom_point(aes(color=state)) +xlim (1996,2025) +
    ylim(-2,4) +
    labs(title = "Tons Sediment per Year Reduced Log10", subtitle= "By state")


hist (log10(GRTS_df$sed_tonsyr), main="Sediment Reductions tons / Year Per Project Histogram",
      xlab="Log Sediment Reductions (10^x)", xlim=c(-7,7))


# boxplot (GRTS_df$sed_tonsyr, main ="Sediment  boxplot")

## Save Altered Datasets

save(GRTS_df, file=R_outfile)

write_feather(GRTS_df, F_outfile)
              
write.xlsx(GRTS_df,Ex_outfile)

q()


