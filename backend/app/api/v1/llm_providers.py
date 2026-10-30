"""LLM Provider CRUD + connectivity test endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_llm_provider_or_404, get_session
from app.models.llm import LLMProvider
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.llm import (
    LLMProviderCreate,
    LLMProviderResponse,
    LLMProviderUpdate,
    LLMProviderTestResponse,
)
from app.services.llm.provider import LLMProviderFactory
from app.utils.logger import logger

router = APIRouter()


@router.get("", response_model=PaginatedResponse[LLMProviderResponse])
async def list_providers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    """List all configured LLM providers."""
    query = select(LLMProvider)
    count_q = select(func.count(LLMProvider.id))

    total = (await db.execute(count_q)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(LLMProvider.name).offset(offset).limit(page_size)
    )
    providers = result.scalars().all()

    items = [
        LLMProviderResponse(
            id=p.id,
            name=p.name,
            provider_type=p.provider_type.value,
            api_base=p.api_base,
            default_model=p.default_model,
            extra_params=p.extra_params or {},
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in providers
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.post("", response_model=LLMProviderResponse, status_code=201)
async def create_provider(
    data: LLMProviderCreate,
    db: AsyncSession = Depends(get_session),
):
    """Add a new LLM provider."""
    from app.models.llm import ProviderType

    # Check for duplicate name
    existing = await db.execute(
        select(LLMProvider).where(LLMProvider.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Provider '{data.name}' already exists")

    provider = LLMProvider(
        name=data.name,
        provider_type=ProviderType(data.provider_type),
        api_base=data.api_base,
        api_key_encrypted=data.api_key,  # TODO: Fernet encrypt in production
        default_model=data.default_model,
        extra_params=data.extra_params,
        is_active=data.is_active,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type.value,
        api_base=provider.api_base,
        default_model=provider.default_model,
        extra_params=provider.extra_params or {},
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.get("/{provider_id}", response_model=LLMProviderResponse)
async def get_provider(
    provider: LLMProvider = Depends(get_llm_provider_or_404),
):
    """Get provider detail."""
    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type.value,
        api_base=provider.api_base,
        default_model=provider.default_model,
        extra_params=provider.extra_params or {},
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.put("/{provider_id}", response_model=LLMProviderResponse)
async def update_provider(
    data: LLMProviderUpdate,
    provider: LLMProvider = Depends(get_llm_provider_or_404),
    db: AsyncSession = Depends(get_session),
):
    """Update a provider."""
    from app.models.llm import ProviderType

    update_data = data.model_dump(exclude_unset=True)
    if "provider_type" in update_data and update_data["provider_type"]:
        update_data["provider_type"] = ProviderType(update_data["provider_type"])
    if "api_key" in update_data:
        update_data["api_key_encrypted"] = update_data.pop("api_key")

    for key, value in update_data.items():
        if hasattr(provider, key) and value is not None:
            setattr(provider, key, value)

    await db.commit()
    await db.refresh(provider)

    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type.value,
        api_base=provider.api_base,
        default_model=provider.default_model,
        extra_params=provider.extra_params or {},
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.delete("/{provider_id}", response_model=MessageResponse)
async def delete_provider(
    provider: LLMProvider = Depends(get_llm_provider_or_404),
    db: AsyncSession = Depends(get_session),
):
    """Delete a provider."""
    await db.delete(provider)
    await db.commit()
    return MessageResponse(message=f"Provider '{provider.name}' deleted")


@router.post("/{provider_id}/test", response_model=LLMProviderTestResponse)
async def test_provider(
    provider: LLMProvider = Depends(get_llm_provider_or_404),
):
    """Test provider connectivity by making a real API call.

    Sends a minimal prompt to verify the API key and endpoint work.
    """
    try:
        llm = LLMProviderFactory.create_from_model(provider)
        success, message = await llm.test_connection()
        return LLMProviderTestResponse(
            success=success,
            message=message,
        )
    except ImportError as e:
        return LLMProviderTestResponse(
            success=False,
            message=f"Missing dependency: {e}",
        )
    except Exception as e:
        logger.error(f"Provider test failed: {e}")
        return LLMProviderTestResponse(
            success=False,
            message=f"Connection failed: {e}",
        )
