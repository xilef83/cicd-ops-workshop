# Exercise 2: Containers, build, push and train in an image

In the demo we built a container from a simple command, explored how
a container can be built with a recipe and what affects how fast this
recipe runs. The `Dockerfile` in the repository already contains this fix.

Now let's let the CI do all of this for us.

You only change the `Dockerfile`, the workflow files in `.github/workflows/`, and add one new file.

## Goals

- Control what goes into an image.
- Push an image to a registry, and find it there.
- Run a job in an image from the registry, instead of from the code.

## The workflows

- `.github/workflows/docker.yml` runs on every push.
  Its `build` job builds the image from the `Dockerfile`, and lists the files in it.
- `.github/workflows/train-docker.yml` is meant to train the model in an image from the registry.
  It doesn't work yet.

Images are stored in the GitHub container registry (GHCR), under `ghcr.io/<you>/<repository>`.
Each image has one or more tags, written after a `:`, e.g. `ghcr.io/<you>/<repository>:main`.

## Tasks

### Task 1: What goes into the image?

1. Push any change, e.g. add a line to this file.

2. Open the new run of the **Docker** workflow, and the `build` job.
3. Open the step **Show the files in the image**.

**Questions**

- Which files does the training need?
- Which files are in the image but are not needed? Which of them could be a problem?

Now leave out of the image every file that the training does not need.
Push, and check the step again.

**Done when**: the step lists only `requirements.txt` and the files in `src/`.

<details>
<summary>Hint</summary>

`COPY . .` copies the whole build context: the folder given to `docker build`, here the root of the repository.
A file named `.dockerignore`, at the root of the repository, lists the files to leave out of the build context.
It uses the same patterns as `.gitignore`.

Careful: `*.md` only matches files at the root. `**/*.md` matches them in every folder.

</details>

<details>
<summary>Answer</summary>

The training needs `requirements.txt` to install the dependencies, and the code in `src/`.
Everything else is only extra weight: the documentation, the tests, the CI files, and the whole Git history in `.git`.
A secret, e.g. a `.env` file with a token, would end up in the image too, and anyone who can pull the image can read it.

You can list what to leave out:

```text
.git
.github
**/__pycache__
model/
tests/
**/*.md
```

Or leave out everything, and list what to keep, with `!`.
This also keeps out the files that someone adds later:

```text
# Leave out everything, then add back what the training needs.
*
!requirements.txt
!src/
**/__pycache__
```

</details>

### Task 2: Push the image to the registry

The `build` job builds the image, but the image disappears when the job ends.
Complete the `TODO (Task 2)` in `.github/workflows/docker.yml`, so that the job:

1. Logs in to `ghcr.io`.
2. Adds a second tag to the image: the branch name.
3. Pushes both tags: the commit SHA and the branch name.

Then push, and find your image: on your fork's page, look for **Packages** in the right column.

**Questions**

- Which tags does your image have?
- Push a second commit. Which tags does the registry show now?
- Which tag would you use to always get the newest image? And to get the image of one exact commit?

<details>
<summary>Hint</summary>

- The job gets a token to talk to GitHub, `${{ secrets.GITHUB_TOKEN }}`. The workflow already allows it to push images, with `packages: write`.
- `docker login ghcr.io -u <user> --password-stdin` reads the token from its input, so the token does not show up in the command.
- `docker tag <image> <new name>` gives an image a second name. `docker push <name>` uploads it.
- GitHub sets [environment variables](https://docs.github.com/en/actions/reference/workflows-and-actions/variables#default-environment-variables) in every job, e.g. `GITHUB_SHA` and `GITHUB_REF_NAME`.

</details>

<details>
<summary>Answer</summary>

Replace the `TODO (Task 2)` with:

```yaml
      - name: Log in to the registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin
      - name: Push the image
        run: |
          docker tag "$IMAGE:$GITHUB_SHA" "$IMAGE:$GITHUB_REF_NAME"
          docker push "$IMAGE:$GITHUB_SHA"
          docker push "$IMAGE:$GITHUB_REF_NAME"
```

After the second push, the registry has 3 tags: one per commit, and the branch name.
The commit tag points to one build, and never changes.
The branch tag moves to the newest build on every push.
Use the branch tag to get the newest image, and the commit tag to get exactly the code of one commit.

</details>

### Task 3: Train in the image

The **Train (Docker)** workflow should pull an image from the registry, and run the training in it.
It has no checkout step: the code and its dependencies all come from the image.

1. Complete the `TODO (Task 3)` in `.github/workflows/train-docker.yml`. Push.
2. Open the **Actions** tab, select **Train (Docker)** on the left, and click **Run workflow**.
   Choose the `main` branch, and enter an image tag: `main`, or the full SHA of one of your commits.
3. When the run is done, download the `model` artifact from the run's page.

Then train automatically after every build: in `.github/workflows/docker.yml`, uncomment the `train` job under `TODO (Task 3)`. Push.

**Questions**

- Where do you find the full SHA of a commit?
- Run the workflow with the SHA of an older commit. Which code trained the model?
- What happens to `model/` if you leave out the `-v` option of `docker run`?

**Done when**: a push runs `build`, then `train`, and the `train` job has a `model` artifact.

<details>
<summary>Hint</summary>

- The registry needs a login to pull, just as it did to push in Task 2.
- `docker pull <image>` downloads an image. `docker run --rm <image>` runs its `CMD`, here the training.
- The training writes to `/app/model` in the container. `-v ./model:/app/model` makes that folder the job's `model/` folder, which the upload step then saves.

</details>

<details>
<summary>Answer</summary>

Replace the `Train` step with:

```yaml
      - name: Log in to the registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin
      - name: Pull the image
        run: docker pull "$IMAGE"
      - name: Train
        run: docker run --rm -v ./model:/app/model "$IMAGE"
```

`docker run` would also pull the image by itself, but a separate step shows in the log how long the download takes.

The full SHA of a commit is on the commit's page, or behind the copy button in the list of commits.
The image of an older commit contains the code of that commit, whatever the branch looks like now.
That is how you reproduce an older model.

Without `-v`, the training writes the model inside the container.
`--rm` deletes the container when it stops, and the model with it.
The upload step then finds no `model/` folder.

</details>

## Extensions

The extensions are optional.
Only start one once you're happy with the tasks.

### Label the image with its commit

**Goal**: the image itself says which commit it was built from.

**Done when**: the `build` job's log shows the label, with the SHA of your push.

**Pointers**

- In the `Dockerfile`, `ARG GIT_COMMIT=unknown` declares a build argument, and `LABEL org.opencontainers.image.revision=$GIT_COMMIT` stores it in the image.
- Pass the value with `docker build --build-arg GIT_COMMIT=$GITHUB_SHA`.
- Print it with `docker inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' <image>`.
- Where in the `Dockerfile` should the two lines go? Remember the layer cache from the demo.
