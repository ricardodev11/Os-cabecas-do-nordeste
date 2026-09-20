"""API routes for managing quest runs."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ....core.dependencies import (
    get_agent_profile_repository,
    get_post_mortem_repository,
    get_public_alpha_service,
    get_quest_repository,
    get_ranking_repository,
    get_replay_event_repository,
    get_sandbox_runner,
    get_run_repository,
)
from ....models import PostMortem, ReplayEvent, Run, RunArtifact, RunCreate
from ....models.battle import BattleRunBundle
from ....repositories.base import (
    AgentProfileRepository,
    PostMortemRepository,
    QuestRepository,
    RankingRepository,
    ReplayEventRepository,
    RunRepository,
)
from ....core.rate_limit import enforce_rate_limit
from ....services.artifact_service import ArtifactService
from ....services.execution_service import ExecutionService
from ....services.post_mortem_service import PostMortemService
from ....services.public_alpha_service import PublicAlphaService
from ....services.replay_service import ReplayService
from ....services.run_service import RunService
from ....sandbox.runner import SandboxRunner


router = APIRouter()


def _build_service(
    run_repository: RunRepository,
    quest_repository: QuestRepository,
    profile_repository: AgentProfileRepository,
) -> RunService:
    return RunService(run_repository, quest_repository, profile_repository)


def _build_execution_service(
    replay_repository: ReplayEventRepository,
    post_mortem_repository: PostMortemRepository,
    ranking_repository: RankingRepository,
    sandbox_runner: SandboxRunner,
) -> ExecutionService:
    return ExecutionService(
        replay_repository,
        post_mortem_repository,
        ranking_repository,
        sandbox_runner,
    )


def _find_battle_run_bundle(
    alpha: PublicAlphaService, run_id: str
) -> BattleRunBundle | None:
    """Resolve a run owned by the SQL alpha engine (battle runs)."""
    for battle in alpha.list_battles():
        for bundle in alpha.get_battle_replay(battle.id).runs:
            if bundle.run.id == run_id:
                return bundle
    return None


def _resolve_run(alpha: PublicAlphaService, run_id: str) -> BattleRunBundle | None:
    """Return a battle bundle for the matching run (in-memory or battle engine)."""
    return _find_battle_run_bundle(alpha, run_id)


@router.get("/", response_model=List[Run], summary="Listar runs")
def list_runs(
    run_repository: RunRepository = Depends(get_run_repository),
    quest_repository: QuestRepository = Depends(get_quest_repository),
    profile_repository: AgentProfileRepository = Depends(get_agent_profile_repository),
):
    """Return all runs."""
    service = _build_service(run_repository, quest_repository, profile_repository)
    return service.list_runs()


@router.get("/{run_id}", response_model=Run, summary="Detalhar run")
def get_run(
    run_id: str,
    run_repository: RunRepository = Depends(get_run_repository),
    quest_repository: QuestRepository = Depends(get_quest_repository),
    profile_repository: AgentProfileRepository = Depends(get_agent_profile_repository),
    alpha: PublicAlphaService = Depends(get_public_alpha_service),
):
    """Return a single run (in-memory engine or alpha battle engine)."""
    run = _build_service(run_repository, quest_repository, profile_repository).get_run(run_id)
    if run is None:
        bundle = _resolve_run(alpha, run_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        run = bundle.run
    return run


@router.post("/", response_model=Run, status_code=status.HTTP_201_CREATED, summary="Criar run")
def create_run(
    run_in: RunCreate,
    request: Request,
    run_repository: RunRepository = Depends(get_run_repository),
    quest_repository: QuestRepository = Depends(get_quest_repository),
    profile_repository: AgentProfileRepository = Depends(get_agent_profile_repository),
    replay_repository: ReplayEventRepository = Depends(get_replay_event_repository),
    post_mortem_repository: PostMortemRepository = Depends(get_post_mortem_repository),
    ranking_repository: RankingRepository = Depends(get_ranking_repository),
    sandbox_runner: SandboxRunner = Depends(get_sandbox_runner),
):
    """Create a new run for an existing quest and agent profile."""
    enforce_rate_limit(request, "battle-write")
    service = _build_service(run_repository, quest_repository, profile_repository)
    try:
        run = service.create_run(run_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    quest = service.get_quest_for_run(run)
    profile = service.get_profile_for_run(run)
    execution_service = _build_execution_service(
        replay_repository, post_mortem_repository, ranking_repository, sandbox_runner
    )
    completed_runs = len(service.list_runs())
    run = execution_service.execute(run, quest, profile, completed_runs)
    return service.save_run(run)


@router.get("/{run_id}/replay", response_model=list[ReplayEvent], summary="Replay da run")
def get_replay(
    run_id: str,
    run_repository: RunRepository = Depends(get_run_repository),
    replay_repository: ReplayEventRepository = Depends(get_replay_event_repository),
    alpha: PublicAlphaService = Depends(get_public_alpha_service),
):
    """Return replay events for a run (in-memory engine or alpha battle engine)."""
    if run_repository.get(run_id) is None:
        bundle = _resolve_run(alpha, run_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        return bundle.replay
    service = ReplayService(replay_repository)
    return service.list_events(run_id)


@router.get("/{run_id}/post-mortem", response_model=PostMortem, summary="Post-mortem da run")
def get_post_mortem(
    run_id: str,
    run_repository: RunRepository = Depends(get_run_repository),
    post_mortem_repository: PostMortemRepository = Depends(get_post_mortem_repository),
    alpha: PublicAlphaService = Depends(get_public_alpha_service),
):
    """Return the post-mortem for a run (in-memory engine or alpha battle engine)."""
    if run_repository.get(run_id) is None:
        bundle = _resolve_run(alpha, run_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        return bundle.post_mortem
    service = PostMortemService(post_mortem_repository)
    post_mortem = service.get_for_run(run_id)
    if post_mortem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post-mortem not found")
    return post_mortem


@router.get("/{run_id}/artifacts", response_model=list[RunArtifact], summary="Listar artefatos da run")
def list_artifacts(
    run_id: str,
    run_repository: RunRepository = Depends(get_run_repository),
    alpha: PublicAlphaService = Depends(get_public_alpha_service),
):
    """Return artifact metadata for a run (in-memory engine or alpha battle engine)."""
    run = run_repository.get(run_id)
    if run is None:
        bundle = _resolve_run(alpha, run_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        run = bundle.run
    service = ArtifactService()
    return service.list_artifacts(run)


@router.get(
    "/{run_id}/artifacts/{artifact_name}",
    response_model=RunArtifact,
    summary="Ler artefato da run",
)
def get_artifact(
    run_id: str,
    artifact_name: str,
    run_repository: RunRepository = Depends(get_run_repository),
    alpha: PublicAlphaService = Depends(get_public_alpha_service),
):
    """Return artifact content for a run (in-memory engine or alpha battle engine)."""
    run = run_repository.get(run_id)
    if run is None:
        bundle = _resolve_run(alpha, run_id)
        if bundle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
        run = bundle.run
    service = ArtifactService()
    artifact = service.get_artifact(run, artifact_name)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return artifact
