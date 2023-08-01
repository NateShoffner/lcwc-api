# LCWC API

Third-party REST API for the [LCWC](https://www.lcwc911.us/live-incident-list) since they don't have their own and the site is very unreliable.

Utilizes [FastAPI](https://fastapi.tiangolo.com/) and [uvicorn](https://www.uvicorn.org/) for the web server and [lcwc](https://pypi.org/project/lcwc/) for the data scraping.



## Development 

    uvicorn app.main:app --reload


## Disclaimer

This project is not affiliated or endorsed by the LCWC.