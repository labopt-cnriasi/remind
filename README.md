# remind
Reverse Manufacturing Innovation Decision System

This repository is aimed at contained developments of the optimization tools for the REMInD Project.

# Things needed to run the project
create a new environment with python 3.7 and activate it  
install django: $ `conda install django`  
install django-tables2: $ `pip install django-tables2`  
install mip: $ `pip install mip`  
install gurobi: $ `conda install gurobi`  
install pandas: $ `conda install pandas`  
install matplotlib: $ `conda install matplotlib`  
install module import_export:  
   $ `pip install django-import-export`  
   or $ `conda install django-import-export`  
install module bootstrap: $ `conda install django-bootstrap4`  
install folium: $ `pip install folium`
install OSRM server (Open Source Routing Machine) https://github.com/Project-OSRM/osrm-backend  
### Gurobi
A license of gurobi is needed to run the project without errors. In a next release Gurobi license will be required only if you select to optimize via gurobi solver.
