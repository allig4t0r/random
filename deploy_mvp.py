import gitlab

from datetime import datetime, timezone
from time import sleep

import gitlab.v4
import gitlab.v4.objects

from joblib import Parallel, delayed
from tqdm import tqdm

# GitLab server URL and personal access token
GITLAB_URL = 'https://git.ic-group.ru/'
PRIVATE_TOKEN = 'glpat-'
BILLING_URL = 'https://git.ic-group.ru/billing'
DEPLOY_CHECK_DELAY = 20
SOURCE_BRANCH = "atatat"
TARGET_BRANCH = "atatatatat"
DEPLOY_BRANCH = "mvp-dev"
FORCE_TARGET_BRANCH_REMOVAL = True
BATCH_SIZE = 3
FILE_PROJ = "billing_mvpdev_projects"
FILE_LOG = "deploy.log"
EXCLUDED_PROJ = ["https://git.ic-group.ru/billing/back/dotnet/billing-cdr-splitter.git", 
                "https://git.ic-group.ru/billing/back/python/cloud-payments-bercut.git"]

def check_deploy(project: int | gitlab.v4.objects.Project, branch=DEPLOY_BRANCH, pipe_id=False) -> bool:
    deploy_job = False
    global failed_build
    global success_deploy
    global failed_deploy
    if isinstance(project, int):
        project = gl.projects.get(project)
    try:
        if not pipe_id:
            pipe = project.pipelines.latest(ref=branch)
            log_write(f"Got latest pipeline with id {pipe.id} for project {project.name}")
        elif pipe_id:
            pipe = project.pipelines.get(pipe_id)
            log_write(f"Got pipeline with id {pipe.id} for project {project.name}")
    except Exception as e:
        log_write(f"Failed to get {branch} pipeline for project {project.name}, {e}")
        return False

    while True:
        jobs = pipe.jobs.list()
        for job in jobs:
            if job.stage == "deploy":
                deploy_job = project.jobs.get(job.id)
        if not deploy_job:
            log_write(f"No deploy job found for project {project.name} and project id {project.id}")
            return False
        if deploy_job.status == "skipped":
            for job in jobs:
                if job.stage == "build":
                    build_job = project.jobs.get(job.id)
            failed_build.append(build_job.web_url)
            log_write(f"Deploy job for project {project.name} was skipped (probably build stage failed)")
            return False
        elif deploy_job.finished_at is None:
            sleep(10)
        elif deploy_job.status == "success":
            success_deploy.append(deploy_job.web_url)
            log_write(f"Deploy job finished with status {deploy_job.status} for project {project.name}")
            return True
        elif deploy_job == "failed":
            failed_deploy.append(deploy_job.web_url)
            log_write(f"Deploy job finished with status {deploy_job.status} for project {project.name}")
            return False

def run_deploy(project: int | gitlab.v4.objects.Project, branch: str) -> bool:
    if isinstance(project, int):
        project = gl.projects.get(project)
    log_write(f"Processing project {project.name} with id {project.id}")
    try:
        pipeline = project.pipelines.create({'ref': branch})
        log_write(f"Created pipeline for branch {branch} in project {project.name}")
        sleep(DEPLOY_CHECK_DELAY)
        result = check_deploy(project.id, branch, pipe_id=pipeline.id)
        return result
    except Exception as e:
        log_write(f"Failed to create pipeline for branch {branch} in project {project.name}, {e}")
        return False

def create_branch(project: gitlab.v4.objects.Project,
                  source_branch=SOURCE_BRANCH,
                  target_branch=TARGET_BRANCH,
                  force_target_branch_removal=FORCE_TARGET_BRANCH_REMOVAL) -> bool:
    try:
        project.branches.get(target_branch)
        branch_exists = True
        log_write(f"Branch {target_branch} in project {project.name} exists")
    except Exception:
        branch_exists = False
        log_write(f"NO branch {target_branch} in project {project.name}")
    if branch_exists:
        if force_target_branch_removal:
            try:
                project.branches.delete(target_branch)
                log_write(f"Branch {target_branch} for project {project.name} was deleted")
            except Exception as e:
                log_write(f"Failed to delete branch {target_branch} for project {project.name}, {e}")
    try:
        log_write(f"Creating branch {target_branch} from {source_branch}...")
        project.branches.create({
            'branch': target_branch,
            'ref': source_branch
        })
        log_write(f"Success! Created branch {target_branch} for project {project.name}")
    except Exception as e:
        log_write(f"Failed to create branch {target_branch} for project {project.name}, {e}")

def protect_branch(project: gitlab.v4.objects.Project,
                   branch: str) -> None:
    try:
        project.protectedbranches.get(branch)
        log_write(f"Protected branch {branch} for project {project.name} already exists")
    except Exception:
        project.protectedbranches.create({
            'name': branch,
            'merge_access_level': gitlab.const.AccessLevel.MAINTAINER,
            'push_access_level': gitlab.const.AccessLevel.MAINTAINER
        })
        log_write(f"Success! Created protected branch {branch} for project {project.name}")

def protect_version_tag(project: gitlab.v4.objects.Project) -> None:
    try:
        project.protectedtags.get('*.*.*')
        log_write(f"Protected tag *.*.* for project {project.name} already exists")
    except Exception:
        project.protectedtags.create({
            'name': '*.*.*',
            'create_access_level': gitlab.const.AccessLevel.MAINTAINER
        })
        log_write(f"Protected tag *.*.* for project {project.name} was created")

# def merge_and_deploy(project: int | gitlab.v4.objects.Project) -> bool:
#     if isinstance(project, int):
#         project = gl.projects.get(project)
    
def get_projects_list(env=DEPLOY_BRANCH, as_urls=False) -> list:
    gitlab_projects=[]
    projects = gl.projects.list(get_all=True)
    print("GOt all Gitlab projects")
    log_write("GOt all Gitlab projects")

    # with open(FILE_PROJ) as file_projects:
    #     projects_to_process = file_projects.read().splitlines()

    for project in projects:
        if project.http_url_to_repo.startswith(BILLING_URL) and \
            project.ci_config_path == 'default-project-ci/billing/.gitlab-ci.yml@dev-ops/ci-cd' and \
            project.http_url_to_repo not in EXCLUDED_PROJ:

            branches = project.branches.list(get_all=True)
            got_branch = False
            for branch in branches:
                if branch.name == env:
                    got_branch = True
            if not got_branch:
                continue
            if as_urls:
                gitlab_projects.append(project.http_url_to_repo)
            else:
                gitlab_projects.append(project)
    print(f"Loaded {len(gitlab_projects)} projects")
    log_write(f"Loaded {len(gitlab_projects)} projects")
    if len(gitlab_projects) == 0:
        print("No projects to process")
        log_write("No projects to process")
        return False
    print()
    log_write()
    return gitlab_projects

def print_summary() -> None:
    # global failed_build
    # global success_deploy
    # global failed_deploy
    print("\nDeploy was successful for jobs:\n")
    log_write("\nDeploy was successful for jobs:\n")
    for job in success_deploy:
        print(job)
        log_write(job)

    print("\nBuild failed for jobs:\n")
    log_write("\nBuild failed for jobs:\n")

    for job in failed_build:
        print(job)
        log_write(job)

    print("\nDeploy failed for jobs:\n")
    log_write("\nDeploy failed for jobs:\n")
    for job in failed_deploy:
        print(job)
        log_write(job)

def log_write(text=''):
    with open(FILE_LOG, mode="a") as logs:
        logs.write(f"{text}\n")

def main() -> None:

    log_write()
    log_write("========================================================")
    log_write(f"Date and time in UTC: {datetime.now(timezone.utc).isoformat()}")

    global failed_build
    global success_deploy
    global failed_deploy
    failed_build = []
    success_deploy = []
    failed_deploy = []

    gitlab_projects = get_projects_list()
    # gitlab_projects = [670,665,608,646]

    if not gitlab_projects:
        return

    # print(f"Creating branch {TARGET_BRANCH} from {SOURCE_BRANCH} for all projects")
    # log_write(f"Creating branch {TARGET_BRANCH} from {SOURCE_BRANCH} for all projects")
    # Parallel(n_jobs=BATCH_SIZE)(
    #     delayed(create_branch)(project, SOURCE_BRANCH, TARGET_BRANCH, FORCE_TARGET_BRANCH_REMOVAL)
    #     for project in tqdm(gitlab_projects)
    # )
    # print()
    # log_write()

    # print(f"Protecting branch {TARGET_BRANCH} in all projects")
    # log_write(f"Protecting branch {TARGET_BRANCH} in all projects")
    # Parallel(n_jobs=BATCH_SIZE)(
    #     delayed(protect_branch)(project, TARGET_BRANCH)
    #     for project in tqdm(gitlab_projects)
    # )
    # print()
    # log_write()

    # print("Protecting tag *.*.* in all projects")
    # log_write("Protecting tag *.*.* in all projects")
    # Parallel(n_jobs=BATCH_SIZE)(
    #     delayed(protect_version_tag)(project)
    #     for project in tqdm(gitlab_projects)
    # )
    # print()
    # log_write()

    print(f"Starting deploy in all projects for branch {DEPLOY_BRANCH}....")
    log_write(f"Starting deploy in all projects for branch {DEPLOY_BRANCH}....")
    Parallel(n_jobs=BATCH_SIZE, require='sharedmem')(
        delayed(run_deploy)(project, DEPLOY_BRANCH)
        for project in tqdm(gitlab_projects)
    )
    print()
    log_write()

    # print(f"Starting marge and deploy in all projects for branch {TARGET_BRANCH}....")
    # log_write(f"Starting merge and deploy in all projects for branch {TARGET_BRANCH}....")
    # Parallel(n_jobs=BATCH_SIZE)(
    #     delayed(merge_and_deploy)(project)
    #     for project in tqdm(gitlab_projects)
    # )
    # print()
    # log_write()

    print(f"Finished processing {len(gitlab_projects)} gitlab projects")
    log_write(f"Finished processing {len(gitlab_projects)} gitlab projects")

    print_summary()

if __name__ == '__main__':
    # Initialize the GitLab connection
    gl = gitlab.Gitlab(GITLAB_URL, private_token=PRIVATE_TOKEN)
    main()