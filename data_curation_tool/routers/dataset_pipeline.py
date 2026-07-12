from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import (
    DatasetPipelineBranchEvaluateRequest,
    DatasetPipelineBranchExportRequest,
    DatasetPipelinePlanRequest,
    DatasetPipelineRulesRequest,
    DatasetPipelineTrainerHandoffRequest,
    ThreeDPrintPackageRequest,
)

router = APIRouter(prefix="/dataset-pipeline", tags=["dataset-pipeline"])


@router.get("/catalog")
def catalog(request: Request):
    return ctx(request).dataset_pipeline.catalog()


@router.post("/rules")
def rules(payload: DatasetPipelineRulesRequest, request: Request):
    return ctx(request).dataset_pipeline.build_rules(payload)


@router.post("/plan")
def plan(payload: DatasetPipelinePlanRequest, request: Request):
    return ctx(request).dataset_pipeline.plan_pipeline(payload)


@router.post("/evaluate-branch")
def evaluate_branch(payload: DatasetPipelineBranchEvaluateRequest, request: Request):
    return ctx(request).dataset_pipeline.evaluate_branch(payload)


@router.post("/export-branch")
def export_branch(payload: DatasetPipelineBranchExportRequest, request: Request):
    return ctx(request).dataset_pipeline.export_branch(payload)


@router.post("/trainer-handoff")
def trainer_handoff(payload: DatasetPipelineTrainerHandoffRequest, request: Request):
    return ctx(request).dataset_pipeline.trainer_handoff(payload)


@router.get("/3d-print/tools")
def three_d_print_tools(request: Request):
    return ctx(request).dataset_pipeline.three_d_print_tool_catalog()


@router.post("/3d-print/package")
def three_d_print_package(payload: ThreeDPrintPackageRequest, request: Request):
    return ctx(request).dataset_pipeline.create_3d_print_package(payload)
