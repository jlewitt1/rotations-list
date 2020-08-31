# Lottery System
http://rotations-lottery.herokuapp.com/

## About 
* Web application to help medical school students manage the process of selecting their desired hospital rotations
* Each registered user assigns points/weights to each rotation, with higher points representing a stronger desire to select first in the rotations lottery
* Project status: working/prototype
* Support for multiple universities 

## Screenshots
Home Screen
![Home Screen](./static/screenshots/main1.PNG?raw=true "Home Screen")

Profile Page - used for allocating points across all rotations
![Profile Screen](./static/screenshots/profile.PNG?raw=true "Profile Screen")

Results Page - filter results for school / graduating class by date or rotation name
![Dates/Rotations Screen](./static/screenshots/results1.PNG?raw=true "Dates/Rotations Screen")

Lottery Results - final lottery order showing name, points allocated, and selection ranking
![Lottery Results Screen](./static/screenshots/results2.PNG?raw=true "Lottery Results Screen")

Admin Home - Manage all users / lottery history / start a new lottery
![Admin Home Screen](./static/screenshots/admin_home.PNG?raw=true "Admin Home Screen")

Launch a new lottery as Admin - based on registered users or an excel file 
![Admin Lottery Screen](./static/screenshots/admin_lottery.PNG?raw=true "Admin Lottery Screen")

## Stack
* Flask-SQLAlchemy
* Postgres
* Heroku
