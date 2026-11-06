"""API route for triggering repository ingestion and code parsing."""

from fastapi import APIRouter, HTTPException, status

from backend.app.ingestion.models import (
    EmptyRepoError,
    IngestionError,
    IngestionRequest,
    IngestionResponse,
    InvalidRepoUrlError,
    RepoAccessError,
    RepoLimitExceededError,
    RepoNotFoundError,
)
from backend.app.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post(
    "",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest and parse a public GitHub repository",
    description=(
        "Validates the repository URL, retrieves metadata and archive without executing code, "
        "applies file filtering, and parses source files into structured code chunks."
    ),
)
async def ingest_repository(request: IngestionRequest) -> IngestionResponse:
    """Ingest a public GitHub repository and return summary metadata and parsing statistics."""
    pipeline = IngestionPipeline()
    try:
        response, _ = await pipeline.ingest_url(request.repo_url)
        return response
    except InvalidRepoUrlError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc
    except RepoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except EmptyRepoError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.message,
        ) from exc
    except RepoLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=exc.message,
        ) from exc
    except RepoAccessError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc
    except IngestionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during repository ingestion: {exc}",
        ) from exc
