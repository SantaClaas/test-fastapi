# wApp - Web App Store
Improve Web App discoverability

## 📖 About
TODO explain where the motivation is coming from and what this intends to solve

### 📏 Scope
#### What is included
- Add apps from their page or manifest url
- View Apps in a list
##### TODO
- View details of an app
- Persist apps through sessions
- Delete an app
#### What is left out
- Authentication and authorization

## 🏃 Getting Started
## Running the project
It is recommended to just use the Devcontainer in this repository. It automatically installs all dependencies like Poetry and Node.
Therfore only an editor supporting Devcontainers like VS Code and Docker is required. Alternatively you can use GitHub Codespaces and you only need an account that has free Codespace access (or money).

## 👏 Attribution
Things I used or got inspired from
TODO links
- FastAPI
    - and their great in depth docs
- TailwindUI Components
    - to develop UI faster with the help of their hight quality components. The components were adapted and changed to my needs for the project as it is intended to be used. It costs money but I used and will use their Tailwindcss and TailwindUI heavily before and will continue using it as it saves me a lot of time which makes it worth to me.
- Docker
- W3C Web Manifesdt documentation
- MDN documentation

## ✨ Random Idea List ✨
Things I might want to add or try out
- Try installing third party apps by returning their manifest url (with adapted links) as manifest in the HTML for the browser to pick up
- Use picture element with source elements representing the manifest icons to let browser decide which one to load to improve speed