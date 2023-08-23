# Poverty Analytics for Climate-driven Coastal Hazards (pacch)

This repository houses the data and code used for paper entitled "Assessment of the poverty-line population vulnerable to climate-driven coastal flooding in Low and Middle Income Countries (LMICs)"

A warming climate leads to sea level rise, exposing an increasing quantity of the global population to coastal flooding hazards. While this topic has been researched previously, most of the assessments focus only on quantifying the number of vulnerable individuals, overlooking the resources at each individual’s disposal. 

Particularly in Low and Middle Income Countries (LMICs), there is growing concern around the bottom 40% of the income distribution in each country, as these individuals have less capability to adapt when coastal hazard events occur. Indeed, it is this bottom 40% where limited government resources should be best targeted to achieve maximum impact, given the propensity for this group to be in poverty. Decision makers urgently need this information to design adaptation plans and future welfare support. 

To our knowledge, this is the first LMIC assessment which combines climate scenarios of coastal flooding, with microestimates of relative wealth, to enable government adaptation strategies and welfare assistance to be targeted at those who most need support the most.

Data
----
All data utilized are open-source. The following datasets are required to run the code:

- WorldPop 2020 global mosaic
- GADM global regional boundaries
- Microwealth estimates from Chi et al. (2022)
- WRI Aqueduct coastal flooding hazard layers for the RISES-AM model 


Getting Started 
---------------
To begin working with the codebase you will need to run the following scripts (in this order):

- preprocessing.py 
- run.py


Contributors
------------
- Allison Thomey
- Edward Oughton