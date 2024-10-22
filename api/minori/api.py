''' api implementation '''
# pylint: disable=singleton-comparison

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

import minori.api_models as models
from minori.core_config import CORS_DOMAINS_ALLOWED, MINORI_VERSION
from minori.db.connection import dbconn, AsyncSessionDbInjectorMiddleware, AsyncSession
from minori.logger import logger

from minori.routers import albums, authors, authoraliases, images

@asynccontextmanager
async def lifespan(app: FastAPI): # pylint: disable=redefined-outer-name,unused-argument
    ''' Initialize the application '''

    await dbconn.start()

    yield

    await dbconn.stop()

app = FastAPI(
    title='minori',
    description='image album gallery application for use in isolated environments.',
    license_info={
        'name': 'MIT license',
        'url': 'https://opensource.org/license/mit/'
    },
    version=MINORI_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_DOMAINS_ALLOWED,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type'],
    max_age=86400
)
app.add_middleware(AsyncSessionDbInjectorMiddleware)
app.include_router(albums.router)
app.include_router(images.router)
app.include_router(authors.router)
app.include_router(authoraliases.router)

@app.get('/api/health', include_in_schema=False)
async def app_healthcheck(db: AsyncSession) -> models.HealthCheckResponseModel:
    ''' Application healthcheck; throws HTTP 500 errors when unhealthy '''

    try:
        await db.execute(text('SELECT 1'))
    except Exception as err: #
        logger.exception('Health check failure')
        raise HTTPException(500, 'Health check failure') from err

    return models.HealthCheckResponseModel(
        healthy=True
    )

@app.exception_handler(Exception)
async def error_handler(request: Request, err: Exception): # pylint: disable=unused-argument
    ''' error handler '''

    logger.exception(err)
    return JSONResponse(
        status_code=500,
        content={'error': 'Unknown server error.'}
    )
