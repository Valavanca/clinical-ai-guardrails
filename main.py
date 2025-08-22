from tests.orchestrator.agent import get_system

# wandb_project = f'{os.getenv("WANDB_ENTITY")}/{os.getenv("WANDB_PROJECT")}'
# weave.init(project_name=wandb_project)

system = get_system()
system.run_validation(
    "Assess `src/clinical_ai_guardrails/notebooks/1.train.ipynb`",
    max_steps=6,
    # ui='gradio'
)