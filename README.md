# LCWC API

Third-party REST API for the [LCWC](https://www.lcwc911.us/live-incident-list) to faciliate the need for one.

Utilizes [FastAPI](https://fastapi.tiangolo.com/), [uvicorn](https://www.uvicorn.org/) for the web server, [peewee](https://docs.peewee-orm.com/en/latest/) as an ORM and [lcwc](https://pypi.org/project/lcwc/) for the data fetching.

**This is a work in progress and is not yet ready for production use.**

## Development (Local)

    uvicorn app.main:app --reload

## Development (Docker)

    docker-compose up --build

## Disclaimer

This project is not affiliated or endorsed by the LCWC and is not an official API. This project is for educational purposes only. Use at your own risk.

## License

[MIT](https://choosealicense.com/licenses/mit/)