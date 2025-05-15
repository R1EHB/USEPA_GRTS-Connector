---
title: GRTS Connector, aka Shrimp & GRiTS
author: Erik Beck
date: May 8, 2025

---

# USEPA_GRTS-Connector #
Data Connector to the USEPA Data System GRTS (Grants Results and
Tracking System) for enhanced analysis.

# Disclaimer #
This is not an official USEPA product. This is an unofficial work of
USEPA staff.

# Overview #

This is a small suite of R and Python programs to access and analyze
data in EPA's Grants Results Tracking System (GRTS) for Clean Water
Act Section 319 Nonpoint Source Program implementation. 

One key component needed for this is to extract hydrologic unit codes
(HUC) from the US Geological Survey's Watershed Boundary Dataset (WBD)
at all code levels supported by the WBD (2,4,6,8,10,12,14,and
16). These codes are combined with a set of older HUCs in use by EPA,
but no longer used by USGS.

These codes (namely, at the twelve digit or HUC12 level) are then used
to request data from a GRTS application programming interface (API)
corresponding to that HUC. This is currently the only API used;
therefore polling by HUC12 is a key step.

# General Organization #
There are three related parts of this system; written to be used
together, they can be adapted for use separately.

In typical use sequence, they are:

## WBD_Retrieval_HUC_Extraction ##
The R code to pull the HUC information from the USGS spatial dataset,
and add in the older, deprecated HUC numbers.

## GRTS_Retrieval ##
The Python code

## GRTS_Data_Analysis ##
The R code to 


# Computer Languages Used #

## Python ##
Python is used to poll the GRTS API, retrieve the data, do some
initial processing, and write data files for further cleaning and
analytical work.

Python was chosen for this part of process because the GRTS API
returns a nested JSON structure, and Python was a better pairing with
the coder (yours truly) to properly disentangle and convert the JSON
response into a more traditional flat-file data format. 


## R ##
R is used to extract the HUC information from USGS' WBD, which is in a
geospatial format. Notably, it creates lists of HUCs at the various
levels for the USA, its territories, and

### R Markdown ###
Some of the R code is written in the R Markdown (Rmd) format to
facilitate documentation.

## Data ##

# How to Run #



# See Also #
