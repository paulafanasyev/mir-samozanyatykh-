"""
FNS API integration — NO MOCK DATA
Returns 503 if API unavailable
"""

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/fns", tags=["fns"])


class FNSUnavailableError(Exception):
    pass


class FNSInvalidReceiptError(Exception):
    pass


async def call_real_fns_api(fiscal_data: str):
    """Real FNS API call"""
    import os
    fns_api_key = os.environ.get("FNS_API_KEY")
    if not fns_api_key:
        raise FNSUnavailableError("FNS API key not configured")

    # TODO: Implement real FNS API integration
    # Example:
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(
    #         "https://api.fns.ru/check",
    #         params={"fiscal_data": fiscal_data},
    #         headers={"Authorization": f"Bearer {fns_api_key}"},
    #         timeout=10
    #     )
    #     if response.status_code == 503:
    #         raise FNSUnavailableError("FNS API unavailable")
    #     return response.json()

    raise FNSUnavailableError("FNS API integration not yet implemented")


@router.get("/check-receipt")
async def check_fns_receipt(
    fiscal_data: str,
    current_user: User = Depends(get_current_user)
):
    """Check FNS receipt — returns 503 if API unavailable"""
    try:
        result = await call_real_fns_api(fiscal_data)
        return result
    except FNSUnavailableError:
        raise HTTPException(
            503,
            detail={
                "error": "fns_unavailable",
                "message": "FNS API temporarily unavailable. Please try again later."
            }
        )
    except FNSInvalidReceiptError:
        raise HTTPException(400, "Invalid receipt data")
