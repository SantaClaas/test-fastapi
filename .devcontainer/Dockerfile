# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.245.0/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version (use -bullseye variants on local arm64/Apple Silicon): 3, 3.10, 3.9, 3.8, 3.7, 3.6, 3-bullseye, 3.10-bullseye, 3.9-bullseye, 3.8-bullseye, 3.7-bullseye, 3.6-bullseye, 3-buster, 3.10-buster, 3.9-buster, 3.8-buster, 3.7-buster, 3.6-buster
ARG VARIANT="3-bullseye"
FROM mcr.microsoft.com/devcontainers/python:0-${VARIANT}
# Installing node with nvm from image here and not with the feature because I am assuming it is faster since it is included in the image then
# The command is copied from the feature https://github.com/devcontainers/features/tree/main/src/node
# Please tell me if my assumption is wrong
RUN . ${NVM_DIR}/nvm.sh && nvm install --lts

# Installing poetry with pipx from imag https://python-poetry.org/docs/#installing-with-pipx
RUN pipx install poetry