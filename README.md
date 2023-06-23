# wApp - Web App Store
A web app store to mprove web app discoverability
Hosted on [free tier Azure](https://wappstore.azurewebsites.net/) (Might be slow)

## 🏃 Getting Started
## Running the project
It is recommended to just use the Devcontainer in this repository. It automatically installs all dependencies like Poetry and Node.
Therfore only an editor supporting Devcontainers like VS Code and Docker is required. Alternatively you can use GitHub Codespaces and you only need an account that has free Codespace access (or money).

## 🤖 Used Tech or "Tech Stack"
Things I used or got inspired from
- FastAPI
    - and their great in depth docs
- TailwindUI Components
    - to develop UI faster with the help of their hight quality components. The components were adapted and changed to my needs for the project as it is intended to be used. It costs money but I used and will use their Tailwindcss and TailwindUI heavily before and will continue using it as it saves me a lot of time which makes it worth to me.
- TailwindCSS
- Docker
- W3C Web Manifesdt documentation
- MDN documentation
- DevContainer
- Azure Hosting
- Poetry
- Publish PyPi
- Jinja2
- GitHub Actions

## ✨ Random Idea List ✨
Things I might want to add or try out
- Use picture element with source elements representing the manifest icons to let browser decide which one to load to improve speed
- Charge money for premium apps. This would allow for premium Web apps which are currently hard to implement as developers would need their own billing and user authZ/authN. Premium apps can then upon opening verify through OpenID Connect with our System that the User signed in to the appstore has bought the app and redirect seemlessly to the app. This could also be an Idea to offer an OpenID Connect SaaS through a different angle than other offerings currently available. Current offerings require to connect it with and app but we could offer the app with the auth system all in one.

## 🐛 Known Issues
When starting the container VS Code might complain that the Python Extension has not loaded or needs to be installed. Just follow VS Code recommendations and you should be fine.
