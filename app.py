from fastapi.staticfiles import StaticFiles

app.mount(
    "/dashboard",
    StaticFiles(directory="out_api/dashboard"),
    name="dashboard"
)
