from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.security import rate_limit, require_access_token
from app.schemas import AnalysisResult, BriefRequest, BriefResponse, DemoPair, ReportRequest
from app.services.georef import NO_GEO_MESSAGE, fit_geo_transform
from app.services.inference import (
    list_demo_pairs,
    resolve_demo_image,
    resolve_demo_pair,
    run_inference,
)
from app.services.narrator import generate_brief
from app.services.report import generate_report_pdf
from app.services.scoring import score_mask

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_-]+")

app = FastAPI(
    title="Disaster Damage Triage API",
    description="Satellite building damage assessment — Team DarkNem",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "inference_mode": settings.inference_mode,
        "demo_pairs": len(list_demo_pairs()),
    }


@app.get("/demo/pairs", response_model=list[DemoPair])
def demo_pairs() -> list[DemoPair]:
    return [DemoPair(**p) for p in list_demo_pairs()]


@app.get("/demo/images/{filename}")
def demo_image(filename: str) -> FileResponse:
    try:
        path = resolve_demo_image(filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    return FileResponse(path)


@app.post(
    "/analyze",
    response_model=AnalysisResult,
    dependencies=[Depends(rate_limit), Depends(require_access_token)],
)
async def analyze(
    pre_image: UploadFile | None = File(None),
    post_image: UploadFile | None = File(None),
    demo_pair_id: str | None = Form(None),
) -> AnalysisResult:
    job_id = uuid.uuid4().hex
    job_dir = settings.upload_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    out_dir = settings.output_dir / job_id

    if demo_pair_id:
        try:
            pair = resolve_demo_pair(demo_pair_id)
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Demo pair not found: {demo_pair_id}",
            )

        pre_path = Path(pair["pre_path"])
        post_path = Path(pair["post_path"])

    else:
        if pre_image is None or post_image is None:
            raise HTTPException(
                status_code=400,
                detail="Provide pre_image and post_image uploads, or demo_pair_id",
            )

        pre_path = job_dir / Path(pre_image.filename or "pre.png").name
        post_path = job_dir / Path(post_image.filename or "post.png").name

        with pre_path.open("wb") as f:
            shutil.copyfileobj(pre_image.file, f)

        with post_path.open("wb") as f:
            shutil.copyfileobj(post_image.file, f)

    mask_path, mode = run_inference(pre_path, post_path, out_dir)

    result = score_mask(
        mask_path,
        grid_rows=settings.grid_rows,
        grid_cols=settings.grid_cols,
    )

    result.inference_mode = mode
    result.pair_id = demo_pair_id or pre_path.stem.replace("_pre_disaster", "")

    transform = fit_geo_transform(demo_pair_id) if demo_pair_id else None

    if transform:
        result.geo_available = True
        for zone in result.zones:
            x0, y0, width, height = zone.bbox
            lat, lng = transform.pixel_to_latlng(x0 + width / 2, y0 + height / 2)
            zone.centroid_lat = round(lat, 6)
            zone.centroid_lng = round(lng, 6)
    else:
        result.geo_available = False
        result.geo_message = NO_GEO_MESSAGE

    return result


@app.post(
    "/brief",
    response_model=BriefResponse,
    dependencies=[Depends(rate_limit), Depends(require_access_token)],
)
async def brief(body: BriefRequest) -> BriefResponse:
    return await generate_brief(body.analysis, body.context)


@app.post(
    "/report/pdf",
    dependencies=[Depends(rate_limit), Depends(require_access_token)],
)
async def report_pdf(body: ReportRequest) -> Response:
    pdf_bytes = generate_report_pdf(body.analysis, body.brief)

    raw_name = body.analysis.pair_id or "upload"
    safe_name = _SAFE_FILENAME_RE.sub("_", raw_name).strip("_") or "upload"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="disasteriq-report-{safe_name}.pdf"'
        },
    )


@app.post(
    "/analyze-and-brief",
    dependencies=[Depends(rate_limit), Depends(require_access_token)],
)
async def analyze_and_brief(
    pre_image: UploadFile | None = File(None),
    post_image: UploadFile | None = File(None),
    demo_pair_id: str | None = Form(None),
    context: str | None = Form(None),
) -> dict:
    analysis = await analyze(
        pre_image=pre_image,
        post_image=post_image,
        demo_pair_id=demo_pair_id,
    )

    brief_resp = await generate_brief(analysis.model_dump(), context)

    return {"analysis": analysis, "brief": brief_resp}